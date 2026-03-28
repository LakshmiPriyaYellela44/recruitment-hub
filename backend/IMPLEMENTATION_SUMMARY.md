"""
SQS-Based Event-Driven Architecture Implementation Summary
==========================================================

This document summarizes all changes made to implement a production-ready event-driven
architecture with SNS/SQS integration for reliable message processing.

## Changes Summary

### 1. Enhanced SNSClient (app/aws_mock/sns_client.py)

**Before:**
```python
class SNSClient:
    _subscribers: Dict[str, List[callable]] = {}
    
    async def publish(self, topic: str, message: Dict[str, Any]) -> str:
        # Directly called subscribers using asyncio.create_task()
    
    def subscribe(self, topic: str, callback: callable):
        # Added callback to subscribers list
```

**After:**
```python
class SNSClient:
    _subscribers: Dict[str, List[callable]] = {}
    _topic_to_queue: Dict[str, str] = {}          # NEW: Topic to queue mapping
    _sqs_client: Optional['SQSClient'] = None     # NEW: Reference to SQS
    _use_sqs: bool = True                         # NEW: Flag to enable SQS routing
    
    @classmethod
    def set_sqs_client(cls, sqs_client: 'SQSClient'):
        # NEW: Configure SNS to route through SQS
    
    @classmethod
    def disable_sqs_routing(cls):
        # NEW: For backward compatibility or testing
    
    async def publish(self, topic: str, message: Dict[str, Any]) -> str:
        # MODIFIED: Routes to SQS queue if configured
        # FALLBACK: Uses direct subscribers if SQS unavailable
```

**Key Changes:**
- Now routes messages to SQS instead of directly calling subscribers
- Maintains backward compatibility with direct subscriber model
- Enriches messages with metadata (timestamp, topic, SNS message ID)
- Configurable via `set_sqs_client()` method

### 2. Enhanced SQSClient (app/aws_mock/sns_client.py)

**New Implementation:**

```python
class SQSClient:
    _queues: Dict[str, Dict[str, Any]] = {}       # Queue storage with metadata
    _dead_letter_queues: Dict[str, list] = {}     # DLQ storage
    _MAX_RETRIES: int = 3                         # Configurable retry limit
    _DEFAULT_VISIBILITY_TIMEOUT: int = 30         # Seconds
    
    # NEW Methods:
    async def send_message()                      # ENHANCED: Supports retry_count
    async def receive_messages()                  # ENHANCED: Respects visibility timeout
    async def delete_message()                    # NEW: Remove processed messages
    async def extend_visibility_timeout()         # NEW: Extend processing time
    async def send_message_to_dead_letter_queue() # NEW: DLQ support
    def get_queue_stats()                         # NEW: Queue statistics
    def get_dead_letter_messages()                # NEW: View DLQ messages
```

**Features:**
- Message metadata tracking (created_at, retry_count, visibility_at)
- Visibility timeout simulation (messages hidden during processing)
- Automatic dead-letter queue management
- Queue statistics and monitoring

### 3. Completely Rewritten ResumeWorker (app/workers/resume_worker.py)

**Before:**
```python
class ResumeWorker:
    def __init__(self):
        self.sns_client = SNSClient()
        self.sns_client.subscribe("resume-upload", self.handle_resume_upload)
    
    async def handle_resume_upload(self, message: dict):
        # Direct callback when SNS publishes event
```

**After:**
```python
class SQSResumeWorker:
    def __init__(self, sqs_client: SQSClient):
        self.sqs_client = sqs_client
        # Uses SQS polling instead of SNS subscription
    
    async def poll_queue(self):
        # Continuously polls SQS queue
        # Fetches up to MAX_MESSAGES_PER_POLL messages
        # Processes each message concurrently
        # Handles errors with retry logic
    
    async def process_message(self, message: dict) -> bool:
        # Extracts resume_id from message
        # Calls ResumeService.process_resume()
        # On success: Deletes message from queue
        # On failure: Retries or moves to DLQ
```

**Key Improvements:**
- SQS polling instead of direct SNS callbacks
- Retry logic with exponential backoff (2^retry_count seconds)
- Dead-letter queue support for unrecoverable errors
- Concurrent message processing (batch mode)
- Detailed logging at each stage
- Graceful shutdown capability

**Retry Flow:**
1. Message received from queue
2. Process attempted
3. If error and retries < 3:
   - Increment retry_count
   - Exponential backoff: 2^retry_count seconds
   - Re-queue message
4. If retries >= 3:
   - Move to dead-letter queue
   - Delete from main queue

### 4. Updated ResumeService (app/modules/resume/service.py)

**Before:**
```python
class ResumeService:
    def __init__(self, db: AsyncSession):
        self.sns_client = SNSClient()  # Creates new instance
```

**After:**
```python
class ResumeService:
    def __init__(self, db: AsyncSession):
        self.sns_client = EventConfig.get_sns_client()  # Uses configured instance
```

**Impact:**
- Service no longer creates its own SNS client
- Uses centralized EventConfig for SNS instance
- Ensures all services use same SNS/SQS configuration
- No changes to upload_resume() or process_resume() methods

### 5. New EventConfig (app/events/config.py)

**New File:**
```python
class EventConfig:
    _sns_client: SNSClient = None
    _sqs_client: SQSClient = None
    _initialized: bool = False
    
    @classmethod
    def initialize(cls):
        # Creates and configures SNS/SQS clients
        # Sets up topic-to-queue mappings
        # Connects SNS to SQS
    
    @classmethod
    def get_sns_client(cls) -> SNSClient:
        # Returns/creates SNS client
    
    @classmethod
    def get_sqs_client(cls) -> SQSClient:
        # Returns/creates SQS client
    
    @classmethod
    def get_queue_stats(cls, queue_name: str) -> dict:
        # Returns queue statistics
    
    @classmethod
    def get_dead_letter_messages(cls, queue_name: str) -> list:
        # Returns DLQ messages
```

**Purpose:**
- Centralized event infrastructure initialization
- Singleton pattern for SNS/SQS clients
- Easy configuration and testing

### 6. Updated Main Application (app/main.py)

**Before:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init_db()
    # Shutdown: close_db()
```

**After:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup:
    # 1. init_db()
    # 2. EventConfig.initialize()  # NEW: Initialize SNS/SQS
    # 3. asyncio.create_task(start_resume_worker(sqs_client))  # NEW: Start worker
    
    # Shutdown:
    # 1. worker_task.cancel()  # NEW: Stop worker gracefully
    # 2. close_db()
```

**New Endpoints:**
```python
@app.get("/api/debug/queue-stats")
# Returns queue statistics (depth, total messages, processed count)

@app.get("/api/debug/dlq-messages")
# Returns messages in dead-letter queue
```

**Impact:**
- Worker starts automatically on app startup
- Worker runs in background as asyncio task
- Graceful shutdown when app terminates
- Monitoring endpoints for debugging

## Message Flow Architecture

```
                    ┌─────────────────────────────────────┐
                    │      Recruitment API (FastAPI)      │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │ POST /api/resumes/upload    │
                    │ (Resume Upload Endpoint)    │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │ ResumeService.upload_resume()       │
                    │ 1. Validate file                    │
                    │ 2. Upload to S3                     │
                    │ 3. Create resume record in DB       │
                    │ 4. Publish event to SNS             │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │ SNSClient.publish(                  │
                    │   topic="resume-upload",            │
                    │   message={...}                     │
                    │ )                                   │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │ SNS:                                │
                    │ 1. Check SQS is configured          │
                    │ 2. Enrich message with metadata     │
                    │ 3. Route to SQS queue               │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │ SQSClient.send_message(             │
                    │   queue_name="resume-processing...",│
                    │   message={...}                     │
                    │ )                                   │
                    └──────────────┬──────────────────────┘
                                   │
              ┌────────────────────▼────────────────────┐
              │  Queue: resume-processing-queue         │
              │  [msg1] [msg2] [msg3] ... [msgN]       │
              └────────────────────┬────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │ SQSResumeWorker.poll_queue()        │
                    │ (Runs continuously in background)   │
                    │ 1. Poll queue every 2 seconds       │
                    │ 2. Receive up to 10 messages        │
                    │ 3. Process each concurrently        │
                    └──────────────┬──────────────────────┘
                                   │
              ┌────────────────────▼────────────────────┐
              │ Each Message Processing:                │
              │ 1. Extract resume_id                    │
              │ 2. Call ResumeService.process_resume()  │
              │ 3. Parse resume                         │
              │ 4. Sync to candidate profile            │
              │ 5. Update resume status to PARSED       │
              └────────────────┬───────────────────────┘
                               │
                ┌──────────────▼──────────────┐
                │  Success?                   │
                └──┬───────────────────────┬──┘
                   │ YES                   │ NO
        ┌──────────▼────────────┐  ┌──────▼──────────────────┐
        │ Delete from queue     │  │ Retry Logic:            │
        │ Mark as PROCESSED     │  │ 1. retry_count++        │
        │ Log success           │  │ 2. If < 3: re-queue     │
        └───────────────────────┘  │    Backoff: 2^retry_count
                                    │ 3. If >= 3: → DLQ
                                    │    Log critical
                                    └─────────────────────────┘
```

## Error Handling & Resilience

### Scenario 1: Temporary Processing Failure
```
Attempt 1 (0s): Error: Network timeout
  → Re-queue with retry_count=1
Attempt 2 (2s): Error: Missing file
  → Re-queue with retry_count=2
Attempt 3 (4s): Error: Candidate service down
  → Re-queue with retry_count=3
Attempt 4 (8s): Success!
  → Delete from queue
```

### Scenario 2: Permanent Failure
```
Attempt 1 (0s): Error: Resume parsing failed
  → Re-queue
Attempt 2 (2s): Error: Resume parsing failed
  → Re-queue
Attempt 3 (4s): Error: Resume parsing failed
  → Re-queue
Attempt 4 (8s): Error: Resume parsing failed
  → retry_count >= MAX_RETRIES
  → Move to DLQ
  → Alert operators
```

### Scenario 3: Visibility Timeout
```
Worker picks message (visible_at set to now)
Processing takes 5 seconds (normal: 30s limit)
While visible_at > now: message hidden from other workers
Processing completes, message deleted
Alternative: If timeout exceeded:
  → Worker can call extend_visibility_timeout()
  → Allows more processing time
```

## Performance Implications

### Message Processing
- **Batch processing**: Up to 10 messages per poll cycle
- **Concurrent processing**: All 10 processed at once (asyncio.gather)
- **Poll interval**: 2 seconds (configurable)
- **Throughput**: ~300 messages/minute per worker

### Scaling Calculation
```
Target: 1000 resumes/minute
Throughput per worker: 300 resumes/minute
Workers needed: 1000 / 300 = 3.3 ≈ 4 workers
```

### Memory Impact
- Each message in queue: ~2KB
- Queue depth at any time: 10-50 messages (depends on processing time)
- Total queue memory: ~100-500KB (negligible)

## Testing Strategy

### Unit Tests
```python
async def test_sns_routes_to_sqs():
    # Verify SNS publishes to SQS

async def test_worker_processes_message():
    # Verify worker picks up and processes messages

async def test_retry_logic():
    # Verify retry count increments and backoff works

async def test_dlq_on_max_retries():
    # Verify message moves to DLQ after 3 failures
```

### Integration Tests
```python
async def test_end_to_end_resume_processing():
    # 1. Upload resume via API
    # 2. Verify message in queue
    # 3. Worker processes message
    # 4. Verify resume status = PARSED
    # 5. Verify message deleted from queue
```

### Load Tests
```python
async def test_high_throughput():
    # Upload 1000 resumes concurrently
    # Verify all processed within time limit
    # Monitor queue depth and worker performance
```

## Deployment Checklist

- [ ] Verify SNSClient enhanced with SQS routing
- [ ] Verify SQSClient has retry and DLQ support
- [ ] Verify SQSResumeWorker uses polling instead of subscriptions
- [ ] Verify ResumeService uses EventConfig.get_sns_client()
- [ ] Verify main.py initializes EventConfig
- [ ] Verify main.py starts resume worker on startup
- [ ] Verify main.py stops worker on shutdown
- [ ] Test queue stats endpoint: /api/debug/queue-stats
- [ ] Test DLQ endpoint: /api/debug/dlq-messages
- [ ] Upload a test resume and verify it processes
- [ ] Inject a failure and verify retry logic works
- [ ] Verify DLQ receives messages after max retries

## Rolling Back (if needed)

To revert to direct SNS subscriber model:
```python
# In main.py
EventConfig.initialize()
SNSClient.disable_sqs_routing()  # Disable SQS routing

# Messages will go to direct subscribers instead of queue
```

## Summary of Benefits

1. **Reliability**: Messages don't get lost on processing failures
2. **Scalability**: Multiple workers can process queue concurrently
3. **Decoupling**: Services don't need to know about workers
4. **Monitoring**: Queue stats and DLQ visibility
5. **Production-Ready**: Exponential backoff, retry limit, DLQ
6. **Backward Compatible**: Can disable SQS routing if needed
7. **Extensible**: Easy to add more topics and workers
8. **Testable**: Can test with mock SQS without AWS
"""
