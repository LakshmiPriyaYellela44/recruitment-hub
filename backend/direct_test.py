#!/usr/bin/env python3
"""
Direct API Testing - Test all endpoints and AWS flows
"""
import subprocess
import time
import sys

# Test endpoints with curl
tests = [
    ("Health Check", "curl -s http://localhost:8000/health || echo 'FAILED'"),
    ("API Health", "curl -s http://localhost:8000/api/health || echo 'FAILED'"),
    ("API Info", "curl -s http://localhost:8000/api/info || echo 'FAILED'"),
    ("Docs", "curl -s -I http://localhost:8000/docs 2>&1 | head -1"),
]

print("\n" + "="*80)
print("DIRECT ENDPOINT TESTING")
print("="*80)

for name, cmd in tests:
    print(f"\n🔍 Testing: {name}")
    print(f"   Command: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        output = result.stdout.strip() or result.stderr.strip()
        if "FAILED" not in output and "Connection refused" not in output:
            print(f"   ✅ {output[:100]}")
        else:
            print(f"   ❌ {output[:100]}")
    except subprocess.TimeoutExpired:
        print(f"   ⏱️  Timeout")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

print("\n" + "="*80)
print("AWS SERVICES CHECK")
print("="*80)

try:
    print("\n✅ Checking AWS Services Configuration...")
    sys.path.insert(0, '.')
    
    from app.core.config import settings
    import boto3
    
    print(f"\n1. Configuration:")
    print(f"   AWS_ENABLED: {settings.AWS_ENABLED}")
    print(f"   S3_MOCK_ENABLED: {settings.S3_MOCK_ENABLED}")
    print(f"   SNS_MOCK_ENABLED: {settings.SNS_MOCK_ENABLED}")
    print(f"   SQS_MOCK_ENABLED: {settings.SQS_MOCK_ENABLED}")
    print(f"   SES_MOCK_ENABLED: {settings.SES_MOCK_ENABLED}")
    
    print(f"\n2. S3 Status:")
    try:
        s3 = boto3.client('s3', region_name=settings.AWS_REGION)
        buckets = s3.list_buckets()
        print(f"   ✅ Connected - {len(buckets.get('Buckets', []))} buckets")
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:50]}")
    
    print(f"\n3. SNS Status:")
    try:
        sns = boto3.client('sns', region_name=settings.AWS_REGION)
        sns.get_topic_attributes(TopicArn=settings.SNS_TOPIC_ARN)
        print(f"   ✅ Connected to topic")
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:50]}")
    
    print(f"\n4. SQS Status:")
    try:
        sqs = boto3.client('sqs', region_name=settings.AWS_REGION)
        attrs = sqs.get_queue_attributes(
            QueueUrl=settings.SQS_QUEUE_URL,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        msg_count = attrs['Attributes'].get('ApproximateNumberOfMessages', 0)
        print(f"   ✅ Connected - {msg_count} messages in queue")
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:50]}")
    
    print(f"\n5. SES Status:")
    try:
        ses = boto3.client('ses', region_name=settings.AWS_REGION)
        ses.get_account_sending_enabled()
        print(f"   ✅ Connected - SES ready")
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:50]}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n" + "="*80)
