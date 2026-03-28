"""
Before vs After: Architecture Comparison
=========================================

## BEFORE: Direct SNS Subscriber Model

### Architecture Diagram
```
API Request
    ↓
ResumeService.upload_resume()
    ↓
SNSClient.publish("resume-upload", message)
    ↓
SNSClient finds subscribers for "resume-upload"
    ↓
For each subscriber, asyncio.create_task(subscriber(message))
    ↓
ResumeWorker.handle_resume_upload() executed
    ↓
ResumeService.process_resume(resume_id)
```

### Problems
- ❌ No message queue = messages lost if worker crashes
- ❌ No retry mechanism = failed processes are forgotten
- ❌ Worker must be running when message published
- ❌ No visibility into failed messages
- ❌ Can't scale horizontally (single in-memory list)
- ❌ No message lifecycle tracking
- ❌ No dead-letter queue for analysis
- ❌ Tight coupling between SNS and workers

### Code Structure
```
SNSClient:
  - _subscribers: Dict[str, List[callable]]
  - publish(topic, message): Calls subscribers directly
  - subscribe(topic, callback): Registers callback

ResumeWorker:
  - __init__(): Subscribes to SNS
  - handle_resume_upload(): Direct callback
```

### Reliability Model
```
Upload → Publish to SNS → Find subscribers → Call them now
                                              ↓
                                          If error: LOST!
```

---

## AFTER: SNS → SQS → Worker Model

### Architecture Diagram
```
API Request
    ↓
ResumeService.upload_resume()
    ↓
SNSClient.publish("resume-upload", message)
    ↓
SNSClient.set_sqs_client() configured?
    ├─ YES: Route to SQS
    │   └─ SQSClient.send_message(queue, enriched_message)
    │       ↓
    │   Queue: resume-processing-queue
    │   [msg1] [msg2] [msg3]
    │       ↓
    │   SQSResumeWorker.poll_queue() running in background
    │       ↓
    │   receive_messages(queue, max_messages=10)
    │       ↓
    │   process_message(msg) for each
    │       ├─ Extract resume_id
    │       ├─ ResumeService.process_resume(resume_id)
    │       └─ On success: delete_message()
    │          On failure: Retry logic
    │
    └─ NO: Fallback to direct subscribers (backward compat)
```

### Benefits
- ✅ Messages queued = survive worker crashes
- ✅ Automatic retry with exponential backoff (2^retry_count)
- ✅ Messages waiting in queue = processed when worker starts
- ✅ Failed messages visible in dead-letter queue
- ✅ Multiple workers can process same queue
- ✅ Message lifecycle tracked (created_at, visible_at, retry_count)
- ✅ Dead-letter queue for debugging/replay
- ✅ Loose coupling via durable queue
- ✅ Production-ready reliability

### Code Structure
```
SNSClient:
  - _subscribers: Dict[str, List[callable]]
  - _topic_to_queue: Dict[str, str]  # NEW
  - _sqs_client: Optional[SQSClient]  # NEW
  - set_sqs_client(sqs_client)  # NEW
  - publish(topic, message):  # ENHANCED
    - If SQS configured: Route to queue
    - Else: Call subscribers

SQSClient:  # COMPLETELY NEW
  - _queues: Dict[str, Dict[str, Any]]
  - _dead_letter_queues: Dict[str, list]
  - send_message(queue, message): Queue message
  - receive_messages(queue, max_messages): Get messages
  - delete_message(queue, receipt_handle): Remove after success
  - extend_visibility_timeout(queue, handle): Extend processing
  - send_message_to_dead_letter_queue(queue, message): Move failed
  - get_queue_stats(queue): Statistics
  - get_dead_letter_messages(queue): View failed messages

SQSResumeWorker:  # COMPLETELY NEW
  - poll_queue(): Continuously polls SQS
  - process_message(message): Processes single message
  - Retry logic: Exponential backoff + DLQ

EventConfig:  # NEW
  - initialize(): Set up SNS/SQS
  - get_sns_client(): Singleton access
  - get_sqs_client(): Singleton access
```

### Reliability Model
```
Upload → Publish to SNS → Route to SQS → Queue message
                                              ↓
                                         Worker polls queue
                                              ↓
                                         Process message
                                              ↓
                                         Process attempts:
                                         1. Success → Delete
                                         2. Fail (retry < 3) → Re-queue + backoff
                                         3. Fail (retry >= 3) → Move to DLQ
                                              ↓
                                         Operators can:
                                         - View DLQ
                                         - Fix issue
                                         - Replay message
```

---

## Detailed Comparison Table

| Aspect | BEFORE | AFTER |
|--------|--------|-------|
| **Message Durability** | ❌ Lost if crash | ✅ Persisted in queue |
| **Retry Logic** | ❌ None | ✅ Exponential backoff (3 retries) |
| **Dead-Letter Queue** | ❌ No DLQ | ✅ Messages > 3 failures move to DLQ |
| **Visibility Timeout** | ❌ Not applicable | ✅ Prevents duplicate processing |
| **Worker Scalability** | ❌ Single subscriber | ✅ Multiple workers polling queue |
| **Message Tracking** | ⚠️ Minimal | ✅ Full lifecycle metadata |
| **Backwards Compat** | ✅ Original | ✅ Can disable SQS routing |
| **Monitoring** | ❌ No endpoints | ✅ /api/debug/queue-stats |
| **DLQ Inspection** | ❌ No DLQ | ✅ /api/debug/dlq-messages |
| **Startup Speed** | ✅ Instant | ⚠️ Creates clients (+50ms) |
| **Memory Usage** | 🟢 < 10KB | 🟡 ~ 100-500KB (queue storage) |
| **Code Complexity** | 🟢 Simple | 🟡 Medium (proper error handling) |
| **Production Ready** | ❌ No | ✅ Yes |
| **Cloud Migration** | 🔴 Hard | 🟢 Easy (swap mock clients) |

---

## Message Lifecycle Comparison

### BEFORE: Direct Subscriber

```
Message Lifecycle:
1. create_task(subscriber(message))
2. Subscriber starts executing
3. Success or Failure (no recovery)
4. Message gone

State Tracking:
- Minimal (callback execution state only)
```

### AFTER: Queue-Based

```
Message Lifecycle:
1. send_message(queue, message)
   - State: QUEUED, retry_count=0, created_at=now, visible_at=now

2. Worker receives_messages()
   - State: RESERVED, visible_at=future (hidden from other workers)

3. process_message()
   - Sub-state: PROCESSING, visible_at=future (extended if needed)

4a. On Success:
    - delete_message()
    - State: DELETED, processed_at=now

4b. On Failure (retry < 3):
    - send_message(queue, enriched_message, retry_count++)
    - State: QUEUED, retry_count=retry_count+1, visible_at=future+backoff

4c. On Failure (retry >= 3):
    - send_message_to_dead_letter_queue()
    - State: DLQ, retry_count=3, moved_at=now

Full Tracking:
- id, body, retry_count, created_at, visible_at, state
```

---

## Performance Implications

### BEFORE: Direct Subscriber

```
Latency:
- Publish to process: 0-10ms (immediate asyncio.create_task)
- No queuing delays

Throughput:
- Limited by subscriber execution time
- No batching

Load:
- High CPU if many subscribers
- No backpressure

Scalability:
- No horizontal scaling possible
```

### AFTER: Queue-Based

```
Latency:
- Publish to queue: 1-5ms (message enqueue)
- Queue to process: 2000ms (poll interval) + processing time
- Total: 2-20 seconds (depends on queue depth)

Throughput:
- Limited by worker(s) processing capacity
- Can batch up to 10 messages per poll
- ~300 messages/minute per worker
- Scales linearly with worker count

Load:
- Low CPU for publisher
- Backpressure built-in (queue depth limits)
- Graceful degradation

Scalability:
- Add workers to increase throughput
- Share same queue across multiple workers
- Each worker polls independently
```

---

## Error Scenario Examples

### Scenario: Worker Crashes During Message Processing

**BEFORE:**
```
1. Message published
2. Worker started processing
3. Worker crashes
4. Result: MESSAGE LOST ❌
5. User resume never processed
```

**AFTER:**
```
1. Message sent to queue
2. Worker receives message (visible_at set to future)
3. Worker starts processing
4. Worker crashes
5. visible_at expires → message becomes visible again
6. Another worker picks it up
7. Result: MESSAGE PROCESSED ✅
```

### Scenario: Temporary Service Outage

**BEFORE:**
```
1. Message published
2. Worker tries to call ResumeService
3. Service temporarily down (5 seconds)
4. Worker gets error
5. Result: PROCESSING FAILED, MESSAGE LOST ❌
6. No recovery possible
```

**AFTER:**
```
1. Message sent to queue
2. Worker gets message
3. Worker tries to call ResumeService
4. Service temporarily down
5. Worker gets error
6. Retries enabled:
   - Retry 1: Wait 2 sec, try again → fails
   - Retry 2: Wait 4 sec, try again → fails
   - Retry 3: Wait 8 sec, try again → success!
7. Result: MESSAGE EVENTUALLY PROCESSED ✅
```

### Scenario: Unrecoverable Error

**BEFORE:**
```
1. Message published
2. Worker tries to process resume
3. Resume file corrupted, parsing fails
4. Worker gets error
5. Result: MESSAGE LOST ❌
6. No way to debug or recover
```

**AFTER:**
```
1. Message sent to queue
2. Worker gets message
3. Worker tries to process resume
4. Attempt 1: Parsing fails
5. Retry 1: Parsing fails
6. Retry 2: Parsing fails
7. Retry 3: Parsing fails
8. All retries exhausted
9. Move to DLQ
10. Operators can:
    - View DLQ message with all details
    - Understand why it failed
    - Manually fix or re-upload resume
    - Replay message
11. Result: DEBUGGABLE & RECOVERABLE ✅
```

---

## Code Evolution Example

### Resume Upload Flow

**BEFORE:**
```python
class ResumeService:
    def __init__(self, db):
        self.sns_client = SNSClient()  # New instance every service
    
    async def upload_resume(self, user_id, file):
        # ... validation, S3 upload ...
        
        # Publish event
        await self.sns_client.publish(
            topic="resume-upload",
            message={"resume_id": str(resume.id), ...}
        )
        # Subscribers called immediately via asyncio.create_task
        # No queue, no retry, no tracking

class ResumeWorker:
    def __init__(self):
        self.sns_client = SNSClient()
        # Subscribe to topic - handler called on publish
        self.sns_client.subscribe("resume-upload", 
            self.handle_resume_upload)
    
    async def handle_resume_upload(self, message):
        # Direct callback - if error, message lost
        resume_id = message["resume_id"]
        await service.process_resume(resume_id)
```

**AFTER:**
```python
class ResumeService:
    def __init__(self, db):
        # Use singleton SNS from EventConfig
        self.sns_client = EventConfig.get_sns_client()  # Shared instance
    
    async def upload_resume(self, user_id, file):
        # ... validation, S3 upload ...
        
        # Publish event (same API)
        await self.sns_client.publish(
            topic="resume-upload",
            message={"resume_id": str(resume.id), ...}
        )
        # SNS internally routes to SQS queue
        # Message persisted, tracking enabled, retries supported

class SQSResumeWorker:
    def __init__(self, sqs_client):
        self.sqs_client = sqs_client
    
    async def poll_queue(self):
        # Continuous polling loop
        while self.is_running:
            messages = await self.sqs_client.receive_messages(
                "resume-processing-queue",
                max_messages=10
            )
            
            for message in messages:
                success = await self.process_message(message)
                
                if success:
                    # Delete on success
                    await self.sqs_client.delete_message(...)
                # On failure: retry logic handles re-queueing
    
    async def process_message(self, message):
        # Process with retry & DLQ support
        resume_id = message["body"]["data"]["resume_id"]
        
        try:
            await service.process_resume(resume_id)
            return True
        except Exception as e:
            retry_count = message["retry_count"]
            if retry_count < 3:
                # Re-queue with incremented count
                await self.sqs_client.send_message(...)
            else:
                # Move to DLQ
                await self.sqs_client.send_message_to_dead_letter_queue(...)
            return False
```

Key Improvements:
1. ✅ SNS client from EventConfig (singleton)
2. ✅ SNS routes to SQS (transparent)
3. ✅ Worker uses polling instead of subscription
4. ✅ Automatic retries with backoff
5. ✅ DLQ for failed messages
6. ✅ Full message lifecycle tracking

---

## Migration Path: Incremental Adoption

### Phase 1: Dual Mode (Before)
```python
# SNS can work in two modes
SNSClient.disable_sqs_routing()  # Use old direct subscribers
# OR
SNSClient.set_sqs_client(sqs_client)  # Use new SQS routing
```

### Phase 2: Hybrid (Both Active)
```python
# Some topics use SNS directly, others use SQS
_topic_to_queue = {
    "resume-upload": "resume-processing-queue",  # Using SQS
    # "other-event": None,  # Using direct subscribers
}
```

### Phase 3: Full SQS (After)
```python
# All topics route through SQS/DLQ
_topic_to_queue = {
    "resume-upload": "resume-processing-queue",
    "profile-updated": "profile-processing-queue",
    "candidate-verified": "verification-queue",
}
```

### Phase 4: Cloud Migration (Future)
```python
# Replace mock SQS with AWS SQS
# Replace mock SNS with AWS SNS
# No application code changes needed!
```

---

## Summary

The transition from **Direct SNS Subscribers** to **SNS → SQS → Worker** represents
a fundamental shift in reliability and scalability:

**BEFORE:** Fast, simple, but fragile (messages lost on errors)
**AFTER:** Robust, scalable, production-ready (messages can be retried and debugged)

The implementation maintains backward compatibility while providing a clear path
to production-grade event-driven architecture.
"""
