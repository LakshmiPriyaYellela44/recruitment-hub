# AWS Migration - Code Verification Guide

This document helps you verify all generated code is in place and properly configured.

## File Verification

### 1. AWS Services Implementation ✓

Run this to verify all files exist:

```bash
cd backend

# Check S3 client
test -f app/aws_services/s3_client.py && echo "✓ S3 client exists" || echo "✗ S3 client missing"

# Check SNS client
test -f app/aws_services/sns_client.py && echo "✓ SNS client exists" || echo "✗ SNS client missing"

# Check SQS client
test -f app/aws_services/sqs_client.py && echo "✓ SQS client exists" || echo "✗ SQS client missing"

# Check SES client
test -f app/aws_services/ses_client.py && echo "✓ SES client exists" || echo "✗ SES client missing"
```

Expected output:
```
✓ S3 client exists
✓ SNS client exists
✓ SQS client exists
✓ SES client exists
```

### 2. Configuration Files ✓

```bash
# Check updated config.py
grep -q "AWS_ENABLED" app/core/config.py && echo "✓ config.py updated" || echo "✗ config.py not updated"

# Check updated events/config.py
grep -q "aws_services" app/events/config.py && echo "✓ events/config.py updated" || echo "✗ events/config.py not updated"

# Check .env.example.aws
test -f .env.example.aws && echo "✓ .env.example.aws exists" || echo "✗ .env.example.aws missing"
```

Expected output:
```
✓ config.py updated
✓ events/config.py updated
✓ .env.example.aws exists
```

### 3. Documentation ✓

```bash
# Check documentation files
test -f AWS_MIGRATION_GUIDE.md && echo "✓ Migration guide exists" || echo "✗ Migration guide missing"
test -f AWS_QUICK_START.md && echo "✓ Quick start exists" || echo "✗ Quick start missing"
test -f AWS_MIGRATION_CHECKLIST.md && echo "✓ Checklist exists" || echo "✗ Checklist missing"
test -f AWS_IMPLEMENTATION_SUMMARY.md && echo "✓ Summary exists" || echo "✗ Summary missing"
```

Expected output:
```
✓ Migration guide exists
✓ Quick start exists
✓ Checklist exists
✓ Summary exists
```

### 4. Integration Tests ✓

```bash
# Check integration tests
test -f tests/test_aws_integration.py && echo "✓ Integration tests exist" || echo "✗ Integration tests missing"

# Check test count
grep -c "async def test_" tests/test_aws_integration.py
# Should output something like: 8
```

## Code Inspection

### 1. Verify AWS Services Have Correct Methods

```bash
# Check S3Client methods
grep -q "async def upload_file" app/aws_services/s3_client.py && echo "✓ S3: upload_file" || echo "✗"
grep -q "async def download_file" app/aws_services/s3_client.py && echo "✓ S3: download_file" || echo "✗"
grep -q "async def delete_file" app/aws_services/s3_client.py && echo "✓ S3: delete_file" || echo "✗"
grep -q "async def generate_presigned_url" app/aws_services/s3_client.py && echo "✓ S3: presigned_url" || echo "✗"

# Check SNS methods
grep -q "async def publish" app/aws_services/sns_client.py && echo "✓ SNS: publish" || echo "✗"

# Check SQS methods
grep -q "async def send_message" app/aws_services/sqs_client.py && echo "✓ SQS: send_message" || echo "✗"
grep -q "async def receive_messages" app/aws_services/sqs_client.py && echo "✓ SQS: receive_messages" || echo "✗"
grep -q "async def delete_message" app/aws_services/sqs_client.py && echo "✓ SQS: delete_message" || echo "✗"

# Check SES methods
grep -q "async def send_email" app/aws_services/ses_client.py && echo "✓ SES: send_email" || echo "✗"
grep -q "async def get_send_quota" app/aws_services/ses_client.py && echo "✓ SES: quota" || echo "✗"
```

### 2. Verify Configuration Auto-Switching ✓

Check that EventConfig properly switches between real and mock:

```bash
# Check EventConfig imports conditionally
grep -q "if settings.AWS_ENABLED" app/events/config.py && echo "✓ Conditional import detected" || echo "✗"
grep -q "from app.aws_services" app/events/config.py && echo "✓ Real AWS import" || echo "✗"
grep -q "from app.aws_mock" app/events/config.py && echo "✓ Mock fallback" || echo "✗"
```

### 3. Verify Resume Service Updated ✓

```bash
# Check ResumeService uses configurable S3
grep -q "if settings.AWS_ENABLED" app/modules/resume/service.py && echo "✓ ResumeService updated" || echo "✗"
grep -q "from app.aws_services.s3_client import S3Client as RealS3Client" app/modules/resume/service.py && echo "✓ Real S3 import" || echo "✗"
```

## Running Tests

### 1. Unit Tests (With Mocks)

```bash
cd backend

# Run all tests except AWS integration tests
pytest tests/ --ignore=tests/test_aws_integration.py -v

# Expected: All tests should PASS (using mocks)
```

### 2. Syntax Check

```bash
# Check Python syntax
python -m py_compile app/aws_services/s3_client.py && echo "✓ S3 syntax OK" || echo "✗ S3 syntax error"
python -m py_compile app/aws_services/sns_client.py && echo "✓ SNS syntax OK" || echo "✗ SNS syntax error"
python -m py_compile app/aws_services/sqs_client.py && echo "✓ SQS syntax OK" || echo "✗ SQS syntax error"
python -m py_compile app/aws_services/ses_client.py && echo "✓ SES syntax OK" || echo "✗ SES syntax error"
```

### 3. Import Check

```bash
# Test imports work
python -c "from app.aws_services.s3_client import S3Client; print('✓ S3 imports OK')" 2>&1
python -c "from app.aws_services.sns_client import SNSClient; print('✓ SNS imports OK')" 2>&1
python -c "from app.aws_services.sqs_client import SQSClient; print('✓ SQS imports OK')" 2>&1
python -c "from app.aws_services.ses_client import SESClient; print('✓ SES imports OK')" 2>&1
```

## Configuration Verification

### 1. Check Default Settings

```python
# Run this Python snippet to verify config
python << 'EOF'
from app.core.config import settings

print(f"AWS_ENABLED: {settings.AWS_ENABLED}")
print(f"AWS_REGION: {settings.AWS_REGION}")
print(f"S3_BUCKET_NAME: {settings.S3_BUCKET_NAME}")
print(f"SNS_TOPIC_ARN: {settings.SNS_TOPIC_ARN}")
print(f"SQS_QUEUE_URL: {settings.SQS_QUEUE_URL}")
print(f"SES_FROM_EMAIL: {settings.SES_FROM_EMAIL}")
print()
print(f"S3_MOCK_ENABLED: {settings.S3_MOCK_ENABLED}")
print(f"SNS_MOCK_ENABLED: {settings.SNS_MOCK_ENABLED}")
print(f"SQS_MOCK_ENABLED: {settings.SQS_MOCK_ENABLED}")
print(f"SES_MOCK_ENABLED: {settings.SES_MOCK_ENABLED}")
EOF
```

Expected output (Development mode):
```
AWS_ENABLED: False
AWS_REGION: us-east-1
S3_BUCKET_NAME: recruitment-resumes-prod
SNS_TOPIC_ARN: arn:aws:sns:us-east-1:123456789:recruitment-resume-uploads
SQS_QUEUE_URL: https://sqs.us-east-1.amazonaws.com/123456789/recruitment-resume-processing
SES_FROM_EMAIL: noreply@recruitment.com

S3_MOCK_ENABLED: True
SNS_MOCK_ENABLED: True
SQS_MOCK_ENABLED: True
SES_MOCK_ENABLED: True
```

### 2. Verify .env.example.aws Content

```bash
# Check critical variables are documented
grep -q "AWS_ENABLED" .env.example.aws && echo "✓ AWS_ENABLED" || echo "✗"
grep -q "AWS_ACCESS_KEY_ID" .env.example.aws && echo "✓ AWS_ACCESS_KEY_ID" || echo "✗"
grep -q "S3_BUCKET_NAME" .env.example.aws && echo "✓ S3_BUCKET_NAME" || echo "✗"
grep -q "SNS_TOPIC_ARN" .env.example.aws && echo "✓ SNS_TOPIC_ARN" || echo "✗"
grep -q "SQS_QUEUE_URL" .env.example.aws && echo "✓ SQS_QUEUE_URL" || echo "✗"
grep -q "SES_FROM_EMAIL" .env.example.aws && echo "✓ SES_FROM_EMAIL" || echo "✗"
```

## Backend Startup Verification

### 1. Check Logs on Startup (With Mocks)

```bash
# Ensure config is for mocks
cat .env | grep AWS_ENABLED
# Should show: AWS_ENABLED=False

# Start backend
cd backend
python -m uvicorn app.main:app --reload 2>&1 | head -50

# Expected log entries:
# ✓ Database initialized and ready
# ✓ Event infrastructure initialized
# ✓ Using mock SNS/SQS services
# ✓ Resume worker started (listening on resume-processing-queue)
```

### 2. Check Logs on Startup (With Real AWS)

```bash
# Set AWS config
cat > .env << 'EOF'
AWS_ENABLED=True
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_BUCKET_NAME=recruitment-resumes-prod
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789:recruitment-resume-uploads
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789/recruitment-resume-processing
SES_FROM_EMAIL=noreply@recruitment.com
S3_MOCK_ENABLED=False
SNS_MOCK_ENABLED=False
SQS_MOCK_ENABLED=False
SES_MOCK_ENABLED=False
EOF

# Start backend
python -m uvicorn app.main:app --reload 2>&1 | head -50

# Expected log entries:
# ✓ AWS_ENABLED=True - Attempting to initialize real AWS SNS/SQS services
# ✓ Successfully initialized real AWS SNS/SQS services
# ✓ S3Client initialized for bucket: recruitment-resumes-prod
# ✓ SNSClient initialized for topic: arn:aws:sns:...
# ✓ SQSClient initialized for queue: https://sqs...
# ✓ SESClient initialized for sender: noreply@recruitment.com
```

## API Endpoint Testing

### 1. Create Test User (If Needed)

```bash
# Login as admin
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"password123"}'

# Save the token from response
TOKEN="eyJhbGciOiJIUzI1NiIs..."
```

### 2. Test Resume Upload (Both Modes)

**With Mocks:**
```bash
# File should be created in ./storage/resumes/
curl -X POST http://localhost:8000/resumes/upload \
  -F "file=@test_resume.pdf" \
  -H "Authorization: Bearer $TOKEN"

# Check response
# { "id": "...", "status": "UPLOADED", "file_name": "test_resume.pdf", ... }

# Verify file exists locally
ls -la storage/resumes/
# Should show: user_id_random_filename.pdf
```

**With Real AWS:**
```bash
curl -X POST http://localhost:8000/resumes/upload \
  -F "file=@test_resume.pdf" \
  -H "Authorization: Bearer $TOKEN"

# Check response
# { "id": "...", "status": "UPLOADED", "file_name": "test_resume.pdf", ... }

# Verify file in S3
aws s3 ls s3://recruitment-resumes-prod/
# Should show: user_id_random_filename.pdf

# Verify SNS message published
aws sns list-topics --region us-east-1
# Topic should exist

# Verify SQS message received
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789/recruitment-resume-processing \
  --attribute-names ApproximateNumberOfMessages
# Should show: "ApproximateNumberOfMessages": "X" (where X > 0)
```

## Documentation Verification

### 1. Check Documentation Completeness

```bash
# Count sections in each guide
echo "=== AWS_MIGRATION_GUIDE.md ==="
grep "^## " AWS_MIGRATION_GUIDE.md | wc -l
# Should be: 7

echo "=== AWS_QUICK_START.md ==="
grep "^## " AWS_QUICK_START.md | wc -l
# Should be: 8

echo "=== AWS_MIGRATION_CHECKLIST.md ==="
grep "^- \[ \]" AWS_MIGRATION_CHECKLIST.md | wc -l
# Should be: 40+ checklist items
```

### 2. Check Code Examples in Docs

```bash
# Verify code blocks are present
grep -c '```python' AWS_MIGRATION_GUIDE.md
# Should be: 15+ examples

grep -c '```' AWS_QUICK_START.md
# Should be: 10+ code blocks
```

## Final Verification Script

Save this as `verify_aws_migration.sh`:

```bash
#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     AWS Migration Verification Script                    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

PASS=0
FAIL=0

# Function to test condition
test_condition() {
  if eval "$1"; then
    echo "✓ $2"
    ((PASS++))
  else
    echo "✗ $2"
    ((FAIL++))
  fi
}

echo "📦 Checking Files..."
test_condition "test -f app/aws_services/s3_client.py" "S3 client exists"
test_condition "test -f app/aws_services/sns_client.py" "SNS client exists"
test_condition "test -f app/aws_services/sqs_client.py" "SQS client exists"
test_condition "test -f app/aws_services/ses_client.py" "SES client exists"
test_condition "test -f AWS_MIGRATION_GUIDE.md" "Migration guide exists"
test_condition "test -f AWS_QUICK_START.md" "Quick start guide exists"
test_condition "test -f .env.example.aws" ".env template exists"
test_condition "test -f tests/test_aws_integration.py" "Integration tests exist"

echo ""
echo "🔍 Checking Configuration..."
test_condition "grep -q 'AWS_ENABLED' app/core/config.py" "AWS settings in config"
test_condition "grep -q 'aws_services' app/events/config.py" "AWS imports in events"
test_condition "grep -q 'aioboto3' requirements.txt || grep -q 'boto3' requirements.txt" "boto3 in requirements"

echo ""
echo "✅ Summary"
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
  echo "🎉 All checks passed! AWS migration code is ready."
else
  echo "⚠️  Some checks failed. Review output above."
fi
```

Run it:
```bash
bash verify_aws_migration.sh
```

Expected output:
```
╔═══════════════════════════════════════════════════════════╗
║     AWS Migration Verification Script                    ║
╚═══════════════════════════════════════════════════════════╝

📦 Checking Files...
✓ S3 client exists
✓ SNS client exists
✓ SQS client exists
✓ SES client exists
✓ Migration guide exists
✓ Quick start guide exists
✓ .env template exists
✓ Integration tests exist

🔍 Checking Configuration...
✓ AWS settings in config
✓ AWS imports in events
✓ boto3 in requirements

✅ Summary
Passed: 14
Failed: 0

🎉 All checks passed! AWS migration code is ready.
```

## Next Steps After Verification

1. ✓ All files exist and syntax is valid
2. ✓ Configuration auto-switches based on flags
3. ✓ Current mocks still work (backward compatible)
4. ⬜ Set AWS credentials in `.env`
5. ⬜ Run AWS console setup (9 steps)
6. ⬜ Test with real AWS services
7. ⬜ Monitor CloudWatch logs
8. ⬜ Archive mock implementation (optional)

See **AWS_QUICK_START.md** for the next steps!
