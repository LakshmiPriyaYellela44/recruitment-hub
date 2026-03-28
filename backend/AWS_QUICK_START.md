# AWS Migration Quick Start

## Prerequisites
- AWS Account with an IAM user that has programmatic access
- boto3 and aioboto3 installed (`pip install boto3 aioboto3`)
- Your AWS credentials saved

## Quick Start (10 minutes)

### 1. Complete AWS Console Setup (5 minutes)
Follow the [AWS_MIGRATION_GUIDE.md](./AWS_MIGRATION_GUIDE.md#aws-console-setup) for:
- Create S3 bucket
- Create SNS topic
- Create SQS queue
- Subscribe SQS to SNS
- Configure SES
- Create IAM policy & attach to user

### 2. Update Configuration (1 minute)

Copy `.env.example.aws` to `.env`:
```bash
cp .env.example.aws .env
```

Edit `.env` with your AWS credentials:
```env
AWS_ENABLED=True
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
S3_BUCKET_NAME=recruitment-resumes-prod
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789:recruitment-resume-uploads
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789/recruitment-resume-processing
SES_FROM_EMAIL=noreply@recruitment.com

# Disable mocks
S3_MOCK_ENABLED=False
SNS_MOCK_ENABLED=False
SQS_MOCK_ENABLED=False
SES_MOCK_ENABLED=False
QUEUE_MOCK_ENABLED=False
```

### 3. Install Dependencies (1 minute)
```bash
pip install boto3>=1.26.0 aioboto3>=12.0.0
```

### 4. Test Real AWS (3 minutes)

Run integration tests:
```bash
cd backend
pytest tests/test_aws_integration.py -v
```

Expected output:
```
✓ test_s3_upload_and_download PASSED
✓ test_sns_publish PASSED
✓ test_sqs_send_and_receive PASSED
✓ test_ses_send_email PASSED
✓ test_end_to_end_resume_flow PASSED
```

### 5. Start Backend
```bash
cd backend
python -m uvicorn app.main:app --reload
```

Monitor logs for:
```
✓ Event infrastructure initialized successfully (using real AWS SNS/SQS)
✓ SESClient initialized for sender: noreply@recruitment.com
✓ S3Client initialized for bucket: recruitment-resumes-prod
```

### 6. Test Upload Flow

Upload a resume:
```bash
curl -X POST http://localhost:8000/resumes/upload \
  -F "file=@test_resume.pdf" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Monitor AWS:
- **S3**: Check file appears in bucket
- **SNS Console**: Check message published
- **SQS Console**: Check message delivered to queue
- **Backend logs**: Watch worker processing

## Troubleshooting

### Error: `InvalidClientTokenId`
- Check `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `.env`
- Regenerate access key in IAM console

### Error: `NoSuchBucket`
- Verify `S3_BUCKET_NAME` exists in your AWS account
- Check spelling matches exactly

### Error: `MessageRejected` (SES)
- Email address not verified in SES console
- Verify email or upgrade from sandbox mode

### Error: `AccessDenied`
- Check IAM user has attached policy from Step 7 in main guide
- Verify policy includes S3, SNS, SQS, SES permissions

### Everything works but messages aren't processing
- Check SNS → SQS subscription is created
- Verify SQS queue is subscribed to SNS topic
- Check worker is running (Should see "Resume worker started" in logs)

## Rollback to Mocks

If issues occur, quickly rollback:

```bash
# Edit .env
AWS_ENABLED=False
S3_MOCK_ENABLED=True
SNS_MOCK_ENABLED=True
SQS_MOCK_ENABLED=True
SES_MOCK_ENABLED=True
QUEUE_MOCK_ENABLED=True

# Restart backend
```

## Files Modified

```
app/
  ├── aws_services/              # NEW - Real AWS clients
  │   ├── __init__.py
  │   ├── s3_client.py
  │   ├── sns_client.py
  │   ├── sqs_client.py
  │   └── ses_client.py
  ├── core/
  │   └── config.py              # UPDATED - New settings
  ├── events/
  │   └── config.py              # UPDATED - Real AWS support
  ├── modules/
  │   ├── resume/
  │   │   └── service.py         # UPDATED - Configurable S3
  │   └── email/
  │       └── template_service.py# UPDATED - Configurable SES
  └── workers/
      └── resume_worker.py       # UPDATED - Real SQS polling

tests/
  └── test_aws_integration.py     # NEW - Integration tests

.env.example.aws                 # NEW - AWS config template
AWS_MIGRATION_GUIDE.md           # NEW - Complete guide
```

## Next Steps

1. Complete all AWS setup (10-20 minutes)
2. Run integration tests to verify
3. Test with real E2E flow
4. Monitor CloudWatch logs (optional)
5. Archive old mock implementation when confident

For detailed information, see [AWS_MIGRATION_GUIDE.md](./AWS_MIGRATION_GUIDE.md)
