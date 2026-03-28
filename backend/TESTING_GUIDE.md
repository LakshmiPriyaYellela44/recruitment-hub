# 🧪 STEP-BY-STEP TESTING GUIDE

## Test Everything Works End-to-End

### Prerequisites
- Backend running: `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Worker running: `python run_worker.py`
- Frontend running: `npm start` (in frontend directory)
- Browser: Chrome, Firefox, or Edge with Developer Tools

---

## Test 1: Backend Verification (2 minutes)

### Step 1: Check Fixes Are Applied
```bash
cd d:\recruitment\backend
python verify_fixes.py
```

**Expected Output:**
```
✓ FOUND - SNS unwrapping code is present
✓ FOUND - Correct extraction path is used
✓ FOUND - PARSING status transition is present
✓ FOUND - Status polling endpoint is present

Status: READY FOR PRODUCTION ✓
```

### Step 2: Run Flow Tests
```bash
python test_resume_flow_fixed.py
```

**Expected Output:**
```
✓ SNS notification unwrapped successfully
✓ Successfully extracted resume_id
✓ Message extraction works correctly
✓ FastAPI app imported successfully

ALL TESTS PASSED ✓
```

---

## Test 2: Watch Logs While Uploading (5 minutes)

### Step 1: Open Three Terminals

**Terminal 1 - Backend:**
```bash
cd d:\recruitment\backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Worker:**
```bash
cd d:\recruitment\backend
python run_worker.py
```

**Terminal 3 - Watch Logs (optional):**
```bash
tail -f app.log  # or watch backend output
```

### Step 2: Upload Resume
1. Go to http://localhost:3000/dashboard
2. Click "Resumes" tab
3. Click "Choose File" → Select any PDF or DOCX
4. Click "Upload Resume" button

### Step 3: Watch Terminal 1 (Backend Logs)
**Should see:**
```
INFO:app.modules.resume.router:[POST /resumes/upload]
INFO:app.aws_services.s3_client:File uploaded to S3
INFO:app.aws_services.sns_client:Message published to SNS topic
INFO:     127.0.0.1:XXXXX - "POST /api/resumes/upload HTTP/1.1" 201 CREATED
```

### Step 4: Watch Terminal 2 (Worker Logs)
**Should see:**
```
INFO:app.workers.resume_worker:Received 1 message(s) from SQS
✓ NEW: Unwrapped SNS notification from SQS message
INFO:app.workers.resume_worker:Worker picked up message from queue
    resume_id: 550e8400-... ✓
INFO:app.workers.resume_worker:[process_resume] Status updated to PARSING ✓
INFO:app.workers.resume_worker:[process_resume] Resume parsing completed
INFO:app.workers.resume_worker:[process_resume] Status updated to PARSED ✓
INFO:app.workers.resume_worker:Successfully processed resume
INFO:app.workers.resume_worker:Message deleted from queue after successful processing
```

**Key Indicators:**
- ✓ "Unwrapped SNS notification" - FIX #1 working
- ✓ "Status updated to PARSING" - FIX #3 working
- ✓ "Status updated to PARSED" - FIX #3 working
- ✓ "Message deleted from queue" - Worker succeeded

---

## Test 3: Frontend Behavior (5 minutes)

### Step 1: Start Frontend
```bash
cd d:\recruitment\frontend
npm start
```

### Step 2: Open Browser Developer Tools
- Press `F12` to open Developer Tools
- Go to **Network tabs**
- Keep this open while testing

### Step 3: Upload Resume Without Refreshing
1. Clear browser cache: Ctrl+Shift+Delete
2. Login if needed
3. Go to Dashboard → Resumes
4. Upload a PDF file
5. **IMPORTANT: DON'T REFRESH THE PAGE**

### Step 4: Watch Network Tab
**Should see:**
- `POST /api/resumes/upload` (1 time) - Resume upload
- `GET /api/resumes/{id}` (multiple times every 2s) - Frontend polling for status

**Should NOT see:**
- ❌ Multiple `POST /api/resumes/upload` calls (repeated uploads)
- ❌ Errors in network requests

### Step 5: Watch UI
**Status sequence (watch without refresh):**
1. "Resume uploaded! Processing..." message appears
2. Status shows: `UPLOADED` (blue badge)
3. Wait 2-5 seconds...
4. Status shows: `PARSING` (gray badge)
5. Wait 3-10 seconds...
6. Status shows: `PARSED` (blue badge)
7. UI updates with resume in list ✓

**Profile section:**
1. Before upload: 0 Skills, 0 Experiences, 0 Educations
2. After parsing: Shows extracted data ✓
3. No page refresh needed ✓

---

## Test 4: Database Verification (3 minutes)

### Step 1: Check Resume Record
```sql
-- PostgreSQL/MySQL
SELECT id, file_name, status, created_at 
FROM resumes 
WHERE user_id = '<your_user_id>' 
ORDER BY created_at DESC 
LIMIT 1;
```

**Expected Output:**
```
id                           | file_name    | status | created_at
550e8400-e29b-41d4...       | document.pdf | PARSED | 2026-03-28...
```

**Status should be:** `PARSED` (not UPLOADED or FAILED)

### Step 2: Check Extracted Data
```sql
-- Check extracted skills
SELECT skill_name, proficiency 
FROM candidate_skills 
WHERE user_id = '<your_user_id>' 
ORDER BY created_at DESC;

-- Check extracted experiences
SELECT job_title, company_name, years 
FROM candidate_experiences 
WHERE user_id = '<your_user_id>' 
ORDER BY created_at DESC;

-- Check extracted education
SELECT degree, institution, field_of_study 
FROM candidate_educations 
WHERE user_id = '<your_user_id>' 
ORDER BY created_at DESC;
```

**Expected Output:** Populated with extracted data from resume

---

## Test 5: Error Case Handling (2 minutes)

### Step 1: Try Uploading Large File
1. Create/find a file > 10MB
2. Try to upload
3. Should see error: "File size must be less than 10MB"

### Step 2: Try Uploading Wrong File Type
1. Try uploading a .txt or .jpg file
2. Should see error: "Only PDF and DOCX files are supported"

### Step 3: Try Uploading Same File Twice
1. Upload a resume
2. Wait for it to complete
3. Upload the exact same file again
4. Should work fine - creates separate Resume record

---

## Test 6: Performance Test (3 minutes)

### Step 1: Upload Multiple Resumes
1. Upload 3 different resumes, one after another
2. Don't wait for each to complete

### Step 2: Monitor Performance
**Expected behavior:**
- All process in parallel
- Each has its own polling
- No blocking or timeouts
- All complete successfully

### Step 3: Check Logs
**Should see messages for all 3:**
```
INFO:app.workers.resume_worker:Worker picked up message... resume_1
INFO:app.workers.resume_worker:Worker picked up message... resume_2
INFO:app.workers.resume_worker:Worker picked up message... resume_3
```

---

## Test 7: Message Format Verification (2 minutes)

### Step 1: Check Message Flow
Add temporary logging to verify message unwrapping:

**In app/aws_services/sqs_client.py, look for:**
```python
if isinstance(body, dict) and body.get('Type') == 'Notification':
    logger.debug("Unwrapped SNS notification from SQS message")
```

**In logs, you should see:**
```
DEBUG:app.aws_services.sqs_client:Unwrapped SNS notification from SQS message
```

### Step 2: Verify No Errors
**Should NOT see:**
```
ERROR:app.workers.resume_worker:Invalid message format - missing resume_id
```

If you see this error:
1. Code hasn't been reloaded
2. Restart backend: Ctrl+C, then `python -m uvicorn ...`
3. Restart worker: Ctrl+C, then `python run_worker.py`

---

## Quick Test Checklist

Use this to verify everything works:

```
[ ] Backend returns 201 on resume upload
[ ] Worker receives message from SQS
[ ] Worker successfully unwraps SNS message
[ ] Worker extracts resume_id correctly
[ ] Worker updates status to PARSING
[ ] Worker parses file successfully
[ ] Worker updates status to PARSED
[ ] Database record updated with status PARSED
[ ] Skills extracted to database
[ ] Experiences extracted to database
[ ] Education extracted to database
[ ] Frontend polling detects status changes
[ ] Resume visible without page refresh
[ ] Profile updates automatically
[ ] No repeated errors in logs
[ ] Network tab shows clean flow (no repeated requests)
[ ] All 4 tests pass (verify_fixes.py, test_resume_flow_fixed.py)
```

**If all checked:** ✅ EVERYTHING WORKS!

---

## Common Issues During Testing

### Issue: Resume doesn't appear after 60 seconds
**Solution:**
1. Check worker is running: `ps aux | grep resume_worker`
2. Check backend logs for errors
3. Check database for resume record
4. If record exists with status="UPLOADED", worker didn't process it
5. Restart worker and try again

### Issue: Still seeing "Invalid message format" error
**Solution:**
1. Verify code changes: `python verify_fixes.py`
2. If not all ✓, manually check files
3. Restart backend: Full restart, not just reload
4. Restart worker: Full restart
5. Clear browser cache: Ctrl+Shift+Delete

### Issue: Profile data not populating
**Solution:**
1. Check resume status is PARSED (not just PARSING)
2. Check database: `SELECT * FROM candidate_skills WHERE user_id='...'`
3. If empty, check worker logs for sync errors
4. Manually run sync: Check CandidateService.sync_parsed_resume_data()

### Issue: Network tab shows repeated requests
**Solution:**
1. This shouldn't happen after fixes
2. If it does, check worker isn't crashing
3. Check SQS message isn't stuck
4. Clear queue: Stop worker, clear SQS, restart
5. Try uploading again

### Issue: Tests failing
**Solution:**
1. Run: `python verify_fixes.py` - Should show all ✓
2. If not showing ✓, code changes didn't apply
3. Check file exists: `ls app/aws_services/sqs_client.py`
4. Manually review code sections mentioned in fix guides
5. Re-apply fixes if needed

---

## Performance Expectations

**Typical Timeline:**
- Upload: < 1 second
- S3 storage: < 1 second  
- SNS publish: < 1 second
- SQS delivery: 0-2 seconds
- Worker parse (2 page resume): 2-5 seconds
- DB sync: 1-2 seconds
- **Total: 5-10 seconds**

**If taking longer:**
- Check resume file size (> 20 pages = longer)
- Check server load
- Check database connections
- Check SQS latency
- Check worker CPU usage

---

## Debugging Commands

### Check SQS Queue Depth
```bash
cd d:\recruitment\backend
python -c "
from app.aws_services.sqs_client import SQSClient
import asyncio

async def check():
    sqs = SQSClient()
    depth = sqs.get_queue_depth()
    print(f'Queue depth: {depth}')

asyncio.run(check())
"
```

### Check AWS Credentials
```bash
python -c "
from app.core.config import settings
print(f'AWS_ENABLED: {settings.AWS_ENABLED}')
print(f'AWS_REGION: {settings.AWS_REGION}')
print(f'SNS Topic: {settings.SNS_TOPIC_ARN[:50]}')
print(f'SQS Queue: {settings.SQS_QUEUE_URL[:50]}')
"
```

### Test SNS Publishing
```bash
python -c "
import asyncio
from app.aws_services.sns_client import SNSClient

async def test():
    sns = SNSClient()
    msg_id = await sns.publish('test-topic', {'test': 'message'})
    print(f'Published message: {msg_id}')

asyncio.run(test())
"
```

### Test Worker Processing
```bash
cd d:\recruitment\backend
python -c "
import asyncio
from app.workers.resume_worker import SQSResumeWorker
from app.aws_services.sqs_client import SQSClient

async def test():
    sqs = SQSClient()
    worker = SQSResumeWorker(sqs)
    # This won't do anything until messages in queue
    messages = await sqs.receive_messages('resume-processing-queue', max_messages=1)
    print(f'Messages in queue: {len(messages)}')
    for msg in messages:
        print(f'Message: {msg}')

asyncio.run(test())
"
```

---

## Success Indicators

When everything is working, you should see:

**Logs:**
```
✓ Unwrapped SNS notification
✓ Worker picked up message
✓ Status updated to PARSING
✓ Status updated to PARSED
✓ Message deleted from queue
```

**Network Tab:**
```
✓ 1x POST /api/resumes/upload
✓ Multiple GET /api/resumes/{id}
✗ No repeated uploads
✗ No 500 errors
```

**Database:**
```
✓ Resume status = PARSED
✓ Resume parsed_data populated
✓ candidate_skills created
✓ candidate_experiences created
✓ candidate_educations created
```

**Frontend:**
```
✓ Status visible without refresh
✓ Profile auto-updates
✓ No manual refresh needed
✓ No error messages
```

**User Experience:**
```
✓ Upload → Automatic update
✓ See status change in real-time
✓ Profile populates automatically
✓ Clean, professional flow
```

---

## Test Duration Summary

| Test | Duration | Pass/Fail |
|------|----------|-----------|
| 1. Backend Verification | 2 min | [ ] |
| 2. Log Monitoring | 5 min | [ ] |
| 3. Frontend Behavior | 5 min | [ ] |
| 4. Database Check | 3 min | [ ] |
| 5. Error Cases | 2 min | [ ] |
| 6. Performance | 3 min | [ ] |
| 7. Message Verification | 2 min | [ ] |
| **TOTAL** | **22 min** | [ ] |

---

## Final Verification

Once all tests pass, run this final check:

```bash
python verify_fixes.py && python test_resume_flow_fixed.py
```

**Expected Result:**
```
✓ All fixes verified
✓ All tests passed
✓ Ready for production
```

---

## 🎉 You're Done!

If all tests pass, your resume upload system is fully fixed and working correctly!

**Status: PRODUCTION READY** ✅

Next steps:
1. Deploy to production
2. Monitor logs for any issues
3. Celebrate! 🎊

---

*Testing Guide Complete*
*Last Updated: 2026-03-28*
