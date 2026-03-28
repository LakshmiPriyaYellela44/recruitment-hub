"""
Event-Driven Architecture with SNS/SQS Integration
===================================================

This document describes the enhanced recruitment backend system with a production-ready 
event-driven architecture using SNS (Simple Notification Service) and SQS (Simple Queue Service).

## Architecture Overview

### Components

1. **SNSClient** - Publisher that routes events to SQS queues
2. **SQSClient** - Queue manager with retry logic and dead-letter queue support
3. **SQSResumeWorker** - Consumer that polls SQS and processes messages
4. **EventConfig** - Centralized configuration and initialization

### Message Flow

```
Resume Upload Request (HTTP)
    ↓
ResumeService.upload_resume()
    ↓
SNSClient.publish(topic="resume-upload", message)
    ↓
SNS receives message and routes to SQS
    ↓
SQSClient.send_message(queue="resume-processing-queue", message)
    ↓
SQSResumeWorker polls queue continuously
    ↓
Worker receives message with:
  - resume_id
  - user_id
  - s3_key
  - file_type
  - retry_count (incremented on failures)
    ↓
ResumeService.process_resume(resume_id)
    ↓
On Success: Delete message from queue
On Failure:
  - If retries < MAX_RETRIES (3): Re-queue with incremented count + exponential backoff
  - If retries >= MAX_RETRIES: Move to Dead-Letter Queue (DLQ)
```

## File Structure

```
app/
├── aws_mock/
│   └── sns_client.py          # Enhanced SNS + SQS clients
├── events/
│   ├── __init__.py
│   └── config.py              # EventConfig for initialization
├── workers/
│   └── resume_worker.py       # SQS polling worker (updated)
├── modules/
│   └── resume/
│       └── service.py         # ResumeService (uses EventConfig SNS)
└── main.py                    # FastAPI app with worker startup
```

## Key Features

### 1. Decoupled Architecture
- Resume upload service doesn't directly process resumes
- Publisher (SNS) is decoupled from consumer (SQS worker)
- Easy to add more workers, queues, or processors in the future

### 2. Reliability & Retries
- Messages are not lost on processing failures
- Automatic retry with exponential backoff: 2^retry_count seconds
- Maximum 3 retries before moving to DLQ
- Example flow:
  - Attempt 1 (immediate)
  - Attempt 2 (after 2 seconds)
  - Attempt 3 (after 4 seconds)
  - Attempt 4 (after 8 seconds)
  - If still fails → move to DLQ

### 3. Dead-Letter Queue (DLQ)
- Failed messages aren't discarded
- Stored in `resume-processing-queue-dlq` for manual inspection
- Operators can debug and replay messages from DLQ

### 4. Visibility Timeout
- Messages hidden from queue while being processed
- Prevents duplicate processing
- Can be extended if processing takes longer

### 5. Queue Monitoring
- Real-time queue statistics
- Dead-letter queue inspection
- Debug endpoints for monitoring

## Usage

### 1. Automatic Initialization

The system initializes automatically on app startup:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    EventConfig.initialize()  # Initializes SNS/SQS
    worker_task = asyncio.create_task(start_resume_worker(sqs_client))
    
    yield
    
    # Shutdown
    worker_task.cancel()
```

### 2. Publishing Events

Resume upload automatically publishes to SNS:

```python
# In ResumeService.upload_resume():
await self.sns_client.publish(
    topic="resume-upload",
    message={
        "resume_id": str(created_resume.id),
        "user_id": str(user_id),
        "s3_key": s3_key,
        "file_type": file_ext
    }
)
# SNS internally routes to SQS queue "resume-processing-queue"
```

### 3. Monitoring Queue Status

```bash
# Get queue statistics
curl http://localhost:8000/api/debug/queue-stats

Response:
{
  "queue_name": "resume-processing-queue",
  "depth": 5,                    # Current messages in queue
  "total_messages": 100,         # Total messages ever sent
  "total_processed": 95,         # Messages successfully processed
  "dlq_depth": 0,                # Messages in DLQ
  "created_at": "2026-03-27T..."
}
```

```bash
# Get dead-letter queue messages
curl http://localhost:8000/api/debug/dlq-messages

Response:
{
  "dlq": "resume-processing-queue-dlq",
  "message_count": 2,
  "messages": [
    {
      "id": "dlq-msg-...",
      "original_queue": "resume-processing-queue",
      "body": {...},
      "retry_count": 3,          # Failed after 3 retries
      "moved_at": "2026-03-27T...",
      "original_created_at": "2026-03-27T..."
    }
  ]
}
```

## Configuration

### Topic to Queue Mapping

In `SNSClient._topic_to_queue`:

```python
_topic_to_queue = {
    "resume-upload": "resume-processing-queue",
    # Add more topics here for future events:
    # "profile-updated": "profile-processing-queue",
    # "candidate-verified": "verification-queue",
}
```

### Worker Parameters

In `SQSResumeWorker`:

```python
MAX_RETRIES = 3                    # Maximum retry attempts
POLL_INTERVAL_SECONDS = 2          # Queue polling interval
MAX_MESSAGES_PER_POLL = 10         # Messages per poll
```

## Logging

All operations are logged with detailed context:

```
SNS publishes message to SQS:
  "SNS published message to SQS"
  topic=resume-upload
  queue=resume-processing-queue
  sns_message_id=msg-...
  sqs_message_id=msg-...

Worker picks up message:
  "Worker picked up message from queue"
  queue=resume-processing-queue
  message_id=msg-...
  resume_id=550e8400-e29b-41d4-a716-446655440000
  retry_count=0

Processing succeeded:
  "Successfully processed resume"
  resume_id=550e8400-e29b-41d4-a716-446655440000
  status=PARSED
  message_id=msg-...

Message deleted after success:
  "Message deleted from queue after successful processing"
  resume_id=550e8400-e29b-41d4-a716-446655440000
  message_id=msg-...

Retry on failure:
  "Will retry message processing"
  resume_id=550e8400-e29b-41d4-a716-446655440000
  message_id=msg-...
  retry_count=1
  max_retries=3
  backoff_seconds=2

Max retries exceeded:
  "Max retries exceeded - moving to dead-letter queue"
  resume_id=550e8400-e29b-41d4-a716-446655440000
  message_id=msg-...
  retry_count=3
```

## Production Considerations

### 1. Scaling Workers
To scale processing, run multiple worker instances:

```bash
# Worker instance 1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Worker instance 2 (different process)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Load balancer in front of both instances
```

### 2. Upgrading to Real AWS Services
To use actual AWS SNS/SQS:

1. Replace `SNSClient` with boto3 `SNS` client
2. Replace `SQSClient` with boto3 `SQS` resource
3. Update `EventConfig` to initialize AWS clients:

```python
import boto3

class EventConfig:
    @classmethod
    def initialize(cls):
        # Connect to AWS
        sns = boto3.client('sns', region_name='us-east-1')
        sqs = boto3.resource('sqs', region_name='us-east-1')
        
        # Subscribe SQS to SNS topic
        topic_arn = sns.create_topic(Name='resume-upload')['TopicArn']
        queue = sqs.create_queue(QueueName='resume-processing-queue')
        
        sns.subscribe(
            TopicArn=topic_arn,
            Protocol='sqs',
            Endpoint=queue.attributes['QueueArn']
        )
```

### 3. Message Retention
Configure queue retention policy (how long messages stay in queue):
- Default: 4 days
- For critical operations: 14 days
- For low-priority: 1 day

### 4. Monitoring & Alerts
Set up CloudWatch alarms:
- Queue depth exceeds threshold → scale up workers
- DLQ receives messages → alert ops team
- Processing time exceeds SLA → investigate bottlenecks

## Testing

### Manual Testing

1. Upload a resume:
```bash
curl -X POST http://localhost:8000/api/resumes/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@resume.pdf"
```

2. Check queue stats:
```bash
curl http://localhost:8000/api/debug/queue-stats
```

3. Check worker logs:
```
grep "Worker picked up message" app.log
grep "Successfully processed" app.log
```

### Testing Failure Scenarios

To test retry logic, temporarily inject errors in `ResumeService.process_resume()`:

```python
async def process_resume(self, resume_id: UUID) -> Resume:
    # Simulate failure for testing
    if random.random() < 0.5:  # 50% failure rate
        raise Exception("Simulated processing error")
    
    # Continue with normal processing...
```

Then observe:
1. Messages retry with exponential backoff
2. After 3 failures, messages move to DLQ
3. Queue stats show the progression

## Future Enhancements

1. **Priority Queues**: High-priority resumes processed first
2. **Topic Subscriptions**: Multiple workers processing same queue
3. **Message Filtering**: SNS filters messages based on criteria
4. **Event Replay**: Replay messages from DLQ or historical queue
5. **Metrics Collection**: Emit metrics to CloudWatch/Prometheus
6. **Circuit Breaker**: Stop processing if error rate exceeds threshold

## Troubleshooting

### Messages accumulating in queue?
- Check worker logs for errors
- Increase `MAX_MESSAGES_PER_POLL` to process more concurrently
- Scale up worker instances

### Messages in DLQ?
- Check the error in message body
- Fix the underlying issue
- Replay messages using management API

### High memory usage?
- Reduce `MAX_MESSAGES_PER_POLL`
- Reduce poll interval
- Check for message size bloat

### Worker not starting?
- Check EventConfig.initialize() is called
- Verify SQSClient is properly instantiated
- Check import paths in main.py
"""
