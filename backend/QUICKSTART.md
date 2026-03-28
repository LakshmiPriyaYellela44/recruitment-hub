"""
Quick-Start Guide: Testing the Event-Driven System
===================================================

## Step 1: Start the Backend

```bash
cd d:\recruitment\backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Starting Recruitment Platform...
INFO:     ✓ Database initialized and ready
INFO:     SQSClient initialized
INFO:     SNSClient instance created
INFO:     SNS configured to route messages to SQS
INFO:     ✓ Event infrastructure initialized
INFO:     ✓ Resume worker started (listening on resume-processing-queue)
INFO:     Application startup complete
```

## Step 2: Authenticate

Get authentication token:

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "candidate@example.com",
    "password": "password123"
  }'

# Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {...}
}

# Save token for next requests
export TOKEN="eyJhbGc..."
```

## Step 3: Upload a Resume

```bash
# Create a test PDF (or use existing resume.pdf)
curl -X POST http://localhost:8000/api/resumes/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@resume.pdf"

# Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "resume.pdf",
  "file_type": "pdf",
  "status": "UPLOADED",
  "message": "Resume uploaded successfully. Processing started."
}

# Note the resume ID for later monitoring
export RESUME_ID="550e8400-e29b-41d4-a716-446655440000"
```

## Step 4: Monitor Queue in Real-Time

Open another terminal and watch the queue:

```bash
# Terminal 2: Monitor queue
watch -n 1 'curl -s http://localhost:8000/api/debug/queue-stats | jq'

# Output updates every second:
{
  "queue_name": "resume-processing-queue",
  "depth": 1,                 # 1 message in queue
  "total_messages": 1,        # 1 total sent
  "total_processed": 0,       # 0 successfully processed
  "dlq_depth": 0,             # 0 in dead-letter queue
  "created_at": "2026-03-27T10:30:00"
}

# After 2-5 seconds (processing time):
{
  "queue_name": "resume-processing-queue",
  "depth": 0,                 # Queue empty
  "total_messages": 1,        # 1 total sent
  "total_processed": 1,       # 1 successfully processed!
  "dlq_depth": 0,             # 0 in dead-letter queue
  "created_at": "2026-03-27T10:30:00"
}
```

## Step 5: View Resume Status

```bash
# Get resume details
curl -X GET http://localhost:8000/api/resumes/$RESUME_ID \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "resume.pdf",
  "file_type": "pdf",
  "status": "PARSED",          # Changed from UPLOADED to PARSED!
  "created_at": "2026-03-27T10:30:00",
  "parsed_data": {
    "skills": ["Python", "FastAPI", "SQL"],
    "experiences": [
      {
        "job_title": "Senior Developer",
        "company_name": "Tech Corp",
        "years": 5
      }
    ],
    "education": [
      {
        "degree": "BS",
        "institution": "State University"
      }
    ]
  }
}
```

## Step 6: Check Logs

Monitor the worker logs to see processing steps:

```
Terminal 1 (where uvicorn is running):

INFO: SNS published message to SQS
  extra={'topic': 'resume-upload', 'queue': 'resume-processing-queue', ...}

INFO: Worker picked up message from queue
  extra={'queue': 'resume-processing-queue', 'resume_id': '550e8400...', 'retry_count': 0}

INFO: Successfully processed resume
  extra={'resume_id': '550e8400...', 'status': 'PARSED', ...}

INFO: Message deleted from queue after successful processing
  extra={'resume_id': '550e8400...', 'message_id': '...'}

INFO: Batch processing completed
  extra={'queue': 'resume-processing-queue', 'successful': 1, 'failed': 0, 'exceptions': 0}
```

## Test Scenario 1: Multiple Resume Uploads (Concurrent Processing)

```bash
# Upload 5 resumes quickly
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/resumes/upload \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@resume.pdf" &
done
wait

# Monitor queue - should show rapid processing:
# depth: 5 → 4 → 3 → 2 → 1 → 0
# (Messages process as worker picks them up)

# Check final stats
curl http://localhost:8000/api/debug/queue-stats | jq '.total_processed'
# Output: 5
```

## Test Scenario 2: Simulate Processing Failure

To test retry logic, temporarily modify `ResumeService.process_resume()`:

```python
# In app/modules/resume/service.py
async def process_resume(self, resume_id: UUID) -> Resume:
    # Add this at the beginning to simulate 50% failure rate:
    import random
    if random.random() < 0.5:
        raise Exception("Simulated processing error")
    
    # Continue with rest of function...
```

Then upload resumes:

```bash
# Upload a resume
curl -X POST http://localhost:8000/api/resumes/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@resume.pdf"

# Watch logs and queue - you should see:
# Attempt 1 (immediate): ERROR
# Attempt 2 (after 2 sec): SUCCESS or ERROR
# Attempt 3 (after 4 sec): SUCCESS or ERROR
# Attempt 4 (after 8 sec): SUCCESS or ERROR

# Or check queue stats for failures
curl http://localhost:8000/api/debug/queue-stats | jq '.dlq_depth'
```

## Test Scenario 3: Verify Dead-Letter Queue

```bash
# Create many resume uploads with injected processing failure
# Keep error rate at 100% to force messages to DLQ

# After 4 failed attempts per message, check DLQ:
curl http://localhost:8000/api/debug/dlq-messages | jq

# Response:
{
  "dlq": "resume-processing-queue-dlq",
  "message_count": 5,
  "messages": [
    {
      "id": "dlq-msg-...",
      "original_queue": "resume-processing-queue",
      "body": {
        "sns_message_id": "msg-...",
        "sns_topic": "resume-upload",
        "timestamp": "2026-03-27T...",
        "data": {
          "resume_id": "550e8400...",
          "user_id": "550e8400...",
          "s3_key": "...",
          "file_type": "pdf"
        }
      },
      "retry_count": 3,
      "moved_at": "2026-03-27T10:35:00",
      "original_created_at": "2026-03-27T10:35:00"
    }
  ]
}
```

## Test Scenario 4: Concurrent Workers

Simulate multiple workers processing same queue:

```bash
# Terminal 1: Worker 1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Worker 2 (if architecture supports it)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Terminal 3: Upload many resumes
for i in {1..20}; do
  curl -X POST http://localhost:8000/api/resumes/upload \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@resume.pdf" &
done
wait

# Monitor queue - both workers process concurrently
watch -n 1 'curl -s http://localhost:8000/api/debug/queue-stats | jq .depth'

# You should see faster processing with 2 workers vs 1 worker
```

## Performance Testing

```bash
# Single resume upload timing
time curl -X POST http://localhost:8000/api/resumes/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@resume.pdf" > /dev/null

# Expected: ~100-500ms for upload + queue

# Batch upload timing
time bash -c '
  for i in {1..100}; do
    curl -X POST http://localhost:8000/api/resumes/upload \
      -H "Authorization: Bearer $TOKEN" \
      -F "file=@resume.pdf" > /dev/null &
  done
  wait
'

# Expected: ~5-10 seconds for 100 concurrent uploads
# Processing happens in background (check with queue-stats)

# Check processing throughput
# Start: curl http://localhost:8000/api/debug/queue-stats | jq .total_processed
# Wait 1 minute
# End: curl http://localhost:8000/api/debug/queue-stats | jq .total_processed
# Throughput = (End - Start) / 60 messages per second
```

## Debugging Commands

```bash
# View raw queue statistics (detailed)
curl http://localhost:8000/api/debug/queue-stats | jq '.'

# View only queue depth
curl http://localhost:8000/api/debug/queue-stats | jq '.depth'

# View processing rate
curl http://localhost:8000/api/debug/queue-stats | jq '.total_processed'

# View dead-letter queue
curl http://localhost:8000/api/debug/dlq-messages | jq '.message_count'

# Follow logs in real-time
# On Linux/Mac/WSL:
tail -f app.log | grep -E "SNS|SQS|Worker|processed"

# On Windows (in separate terminal):
Get-Content -Path app.log -Wait | Select-String -Pattern "SNS|SQS|Worker|processed"
```

## Stopping the System

```bash
# Stop the backend (in Terminal 1)
# Press Ctrl+C

# Expected shutdown output:
Shutting down Recruitment Platform...
✓ Resume worker stopped
✓ Recruitment Platform shutdown complete
```

## Common Issues and Solutions

### Issue: Worker not starting
**Solution:**
```
Check if EventConfig.initialize() is called in main.py
Check if start_resume_worker() is executed
View logs for error messages
```

### Issue: Messages stuck in queue
**Solution:**
```bash
# Check if worker is running
curl http://localhost:8000/api/debug/queue-stats

# Check logs for processing errors
grep "ERROR" app.log

# If worker is hung, restart it
# Ctrl+C to stop uvicorn
# Restart uvicorn
```

### Issue: High retry count in DLQ
**Solution:**
```
1. Check ResumeService.process_resume() logic
2. Check if S3 (file storage) has the file
3. Check if parser is working correctly
4. Check database connectivity
```

### Issue: Memory growing over time
**Solution:**
```
1. Check queue depth - should be < 100
2. Reduce MAX_MESSAGES_PER_POLL from 10 to 5
3. Reduce poll frequency (increase POLL_INTERVAL_SECONDS)
4. Check for message size bloat in parsed_data
```

## Next Steps

1. ✅ Upload and process test resumes
2. ✅ Verify queue stats and DLQ
3. ✅ Test retry logic with injected failures
4. ✅ Monitor performance and throughput
5. ⬜ (Optional) Add more topics/queues for other events
6. ⬜ (Optional) Upgrade to real AWS SNS/SQS
7. ⬜ (Optional) Add message filtering by SNS
8. ⬜ (Optional) Add metrics collection (Prometheus/CloudWatch)
"""
