# AWS Migration Checklist & Summary

## Overview

You have a complete migration path from mock AWS services to real AWS services. All code changes maintain backward compatibility with existing mocks through configuration flags.

## Migration Path

### Development Phase (Local - Mocks)
```
AWS_ENABLED=False
All *_MOCK_ENABLED=True
└─ Uses: Local files, in-memory queues, log files
```

### Testing Phase (Staging - Real AWS)
```
AWS_ENABLED=True
All *_MOCK_ENABLED=False
└─ Uses: AWS SES Sandbox (verify email first)
└─ Uses: Real S3, SNS, SQS (separate buckets/topics)
```

### Production Phase (Real AWS)
```
AWS_ENABLED=True
All *_MOCK_ENABLED=False
└─ Uses: AWS SES Production (request production access)
└─ Uses: Production S3, SNS, SQS
```

## AWS Console Setup Checklist

- [ ] **Step 1: Create IAM User**
  - [ ] User name: `recruitment-api-user`
  - [ ] Generate access key
  - [ ] Save Access Key ID & Secret
  
- [ ] **Step 2: Create S3 Bucket**
  - [ ] Bucket name: `recruitment-resumes-prod` (globally unique)
  - [ ] Region: `us-east-1`
  - [ ] Block all public access: YES
  - [ ] Enable versioning: YES (optional)
  - [ ] Enable encryption: AES256
  - [ ] Note bucket name

- [ ] **Step 3: Create SNS Topic**
  - [ ] Topic name: `recruitment-resume-uploads`
  - [ ] Type: Standard
  - [ ] Copy Topic ARN

- [ ] **Step 4: Create SQS Queue**
  - [ ] Queue name: `recruitment-resume-processing`
  - [ ] Type: Standard
  - [ ] Visibility timeout: 30 seconds
  - [ ] Message retention: 4 days
  - [ ] Copy Queue URL

- [ ] **Step 5: Subscribe SQS to SNS**
  - [ ] SNS Console → Topics → recruitment-resume-uploads
  - [ ] Subscriptions → Create
  - [ ] Protocol: Amazon SQS
  - [ ] Endpoint: SQS Queue ARN
  - [ ] Subscription created ✓

- [ ] **Step 6: Configure SES**
  - [ ] Email address: `noreply@recruitment.com`
  - [ ] Verify email (check inbox, click link)
  - [ ] Mode: Sandbox (for testing) or Production
  - [ ] If production: Request access (takes ~24 hours)

- [ ] **Step 7: Create IAM Policy**
  - [ ] Policy name: `recruitment-api-policy`
  - [ ] Copy policy JSON from guide
  - [ ] Update ARNs to match your resources
  - [ ] Review & Create

- [ ] **Step 8: Attach Policy to User**
  - [ ] IAM → Users → recruitment-api-user
  - [ ] Add permissions → Attach policy
  - [ ] Select `recruitment-api-policy`

- [ ] **Step 9: Create CloudWatch Log Group** (optional)
  - [ ] Name: `/aws/recruitment/api`
  - [ ] Retention: 7 days

## Code Setup Checklist

- [ ] **Install Dependencies**
  ```bash
  pip install boto3>=1.26.0 aioboto3>=12.0.0
  ```
  - [ ] Update `requirements.txt`

- [ ] **Create AWS Services**
  - [ ] `app/aws_services/__init__.py` ✓
  - [ ] `app/aws_services/s3_client.py` ✓
  - [ ] `app/aws_services/sns_client.py` ✓
  - [ ] `app/aws_services/sqs_client.py` ✓
  - [ ] `app/aws_services/ses_client.py` ✓

- [ ] **Update Configuration**
  - [ ] `app/core/config.py` ✓
  - [ ] `app/events/config.py` ✓

- [ ] **Create .env File**
  - [ ] Copy `.env.example.aws` → `.env`
  - [ ] Fill in AWS credentials
  - [ ] Fill in S3_BUCKET_NAME
  - [ ] Fill in SNS_TOPIC_ARN
  - [ ] Fill in SQS_QUEUE_URL
  - [ ] Fill in SES_FROM_EMAIL
  - [ ] Set AWS_ENABLED=False (start with mocks)

- [ ] **Services Updated** (auto-detection based on config)
  - [ ] Resume service uses S3
  - [ ] Email service uses SES
  - [ ] Event system uses SNS/SQS
  - [ ] Worker polls real SQS

- [ ] **Testing**
  - [ ] Run unit tests: `pytest tests/ -v`
  - [ ] Run integration tests: `pytest tests/test_aws_integration.py -v`
  - [ ] Manual upload test
  - [ ] Check AWS console for files/messages

## Configuration Progression

### Phase 1: Verify with Mocks (Day 1)
```env
AWS_ENABLED=False
S3_MOCK_ENABLED=True
SNS_MOCK_ENABLED=True
SQS_MOCK_ENABLED=True
SES_MOCK_ENABLED=True
QUEUE_MOCK_ENABLED=True
```
✓ Existing system works unchanged

### Phase 2: Switch to Real AWS (Day 2-3)
```env
AWS_ENABLED=True
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_MOCK_ENABLED=False
SNS_MOCK_ENABLED=False
SQS_MOCK_ENABLED=False
SES_MOCK_ENABLED=False
QUEUE_MOCK_ENABLED=False
```
✓ Real files in S3
✓ Real events in SNS/SQS
✓ Real emails via SES

### Phase 3: Production Upgrade (Week 2)
```env
# Same as phase 2, but:
SES_MOCK_ENABLED=False  # Upgraded SES to production
AWS_REGION=us-east-1    # Match your region
# All other settings same
```

## Testing & Validation

### Local Unit Tests (No AWS)
```bash
# Existing tests still pass with mocks
pytest tests/ -v --ignore=tests/test_aws_integration.py
```

### Integration Tests (Requires AWS)
```bash
# Requires AWS_ENABLED=True in .env
pytest tests/test_aws_integration.py -v
```

Expected results:
- ✓ S3 upload/download
- ✓ SNS publish
- ✓ SQS send/receive
- ✓ SES send email
- ✓ End-to-end flow

### Manual Testing (Most Important)

**Test Resume Upload:**
```bash
1. Start backend: python -m uvicorn app.main:app --reload
2. Upload resume: curl -X POST http://localhost:8000/resumes/upload -F "file=@test.pdf" -H "Authorization: Bearer TOKEN"
3. Check AWS Console:
   - S3: File should appear in bucket
   - SNS: Message published (check metrics)
   - SQS: Message in queue (check Active Messages)
   - Backend logs: Worker should process
4. Check email sending (if SES enabled)
```

**Test Email Sending:**
```bash
1. Call email endpoint with template
2. Check AWS SES console:
   - Message should show as sent
   - Recent bounces should be empty
3. Check email inbox (verify address in SES console)
```

## File Structure

### New Files Created
```
app/aws_services/
├── __init__.py
├── s3_client.py      (Real S3 implementation)
├── sns_client.py     (Real SNS implementation)
├── sqs_client.py     (Real SQS implementation)
└── ses_client.py     (Real SES implementation)

tests/
└── test_aws_integration.py  (Integration tests)

AWS_MIGRATION_GUIDE.md        (Complete technical guide)
AWS_QUICK_START.md           (This quick reference)
.env.example.aws             (Template configuration)
```

### Modified Files
```
app/core/config.py           (New AWS settings)
app/events/config.py         (Real AWS support)
requirements.txt             (boto3, aioboto3)
```

### Unchanged (Backward Compatible)
```
app/aws_mock/                (Kept for fallback)
app/modules/resume/service.py (Auto-detects config)
app/modules/email/           (Auto-detects config)
app/workers/resume_worker.py (Auto-detects config)
```

## Rollback Plan

If issues occur with real AWS:

**Quick Rollback:**
```bash
# Edit .env
AWS_ENABLED=False
S3_MOCK_ENABLED=True
SNS_MOCK_ENABLED=True
SQS_MOCK_ENABLED=True
SES_MOCK_ENABLED=True
QUEUE_MOCK_ENABLED=True

# Restart backend
python -m uvicorn app.main:app --reload
```

**Result:** System will revert to mocks immediately. Existing data remains in AWS but new operations use mocks.

## Monitoring & Maintenance

### Daily Checks (Production)
- [ ] AWSlogs exist in CloudWatch
- [ ] SQS queue depth is low (<100 messages)
- [ ] SES sending rate is normal
- [ ] S3 bucket size reasonable
- [ ] No errors in backend logs

### Weekly Checks
- [ ] SES bounce/complaint rates acceptable
- [ ] S3 lifecycle policies running (if enabled)
- [ ] SQS DLQ is empty (failed messages)
- [ ] No unauthorized S3 access attempts

### Monthly Tasks
- [ ] Review IAM user permissions
- [ ] Delete old resumes in S3 (if not using lifecycle)
- [ ] Rotate IAM access key (best practice)
- [ ] Review AWS billing

## Common Issues & Solutions

### Error: `InvalidClientTokenId`
**Cause:** Wrong AWS credentials
**Solution:** Check `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `.env`

### Error: `NoSuchBucket`
**Cause:** S3 bucket name wrong or doesn't exist
**Solution:** Verify bucket exists in AWS S3 console, check spelling

### Error: `MessageRejected` (SES)
**Cause:** Email not verified or not in production
**Solution:** Verify email in SES console, or request production access

### Error: `AccessDenied`
**Cause:** IAM policy missing permissions
**Solution:** Check IAM policy attached to user includes all required actions

### SQS Messages Not Processing
**Cause:** SNS not subscribed to SQS
**Solution:** 
1. Go to SNS Console → Topics → recruitment-resume-uploads
2. Verify subscription to SQS exists
3. Check subscription filter policy is empty/correct

### S3 File Upload Fails
**Cause:** Bucket not found or credentials don't have access
**Solution:**
1. Verify bucket exists and region matches AWS_REGION
2. Check IAM policy has S3 PutObject permission
3. Check bucket block public access settings

## Performance Tuning

### SQS Polling
```env
# Faster polling (higher CPU usage)
SQS_POLL_INTERVAL_SECONDS=1
SQS_MAX_MESSAGES_PER_POLL=10

# Slower polling (lower CPU usage)
SQS_POLL_INTERVAL_SECONDS=5
SQS_MAX_MESSAGES_PER_POLL=1
```

### S3 Uploads
- Large files (>100MB): Use multipart upload (boto3 does this automatically)
- Frequent uploads: Consider S3 Transfer Acceleration

### SES Sending
- Batch emails: Send to multiple recipients in single call
- High volume: Request production access for higher limits

## Security Best Practices

- [ ] Use IAM user, not root account
- [ ] Restrict IAM policy to least privilege (provided in guide)
- [ ] Use separate buckets/topics for dev/staging/prod
- [ ] Enable S3 versioning for recovery
- [ ] Enable S3 encryption (SSE-S3 at minimum)
- [ ] Rotate IAM access keys quarterly
- [ ] Monitor CloudWatch for suspicious activity
- [ ] Use VPC endpoints if running on EC2/ECS
- [ ] Never commit AWS credentials to git (use `.env` with `.gitignore`)

## Cost Optimization

| Service | Monthly Estimate | Optimization |
|---------|-----------------|--------------|
| S3      | $1-5            | Lifecycle deletion, versioning off in prod |
| SNS     | $0.50           | Low volume, consolidate topics |
| SQS     | $0.30           | Long polling (20s), standard queue |
| SES     | $0-10           | Use sandbox for dev, production for live |
| **Total** | **~$2-25**  | **Most costs under $1** |

## Success Criteria

- [ ] All AWS services initialized in backend logs
- [ ] S3 files appear in bucket after upload
- [ ] SNS publishes messages (check metrics)
- [ ] SQS queue receives messages
- [ ] Worker processes queue messages
- [ ] SES sends emails (check SES console)
- [ ] No errors in application or CloudWatch logs
- [ ] Integration tests pass: `pytest tests/test_aws_integration.py -v`

## Getting Help

1. **AWS Documentation:** https://docs.aws.amazon.com/
2. **boto3 Documentation:** https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
3. **FastAPI Async:** https://fastapi.tiangolo.com/async/
4. **SQS Best Practices:** https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/

## Next Steps After Migration

1. **Monitor first 24 hours:** Watch CloudWatch logs
2. **Set up alerts:** CloudWatch → Alarms for queue depth, errors
3. **Scale if needed:** Replicate worker for high volumes
4. **Document** your setup for team
5. **Archive** mock implementations if not needed

---

**Migration Date:** _______________
**Completed By:** _______________
**Verified Date:** _______________
