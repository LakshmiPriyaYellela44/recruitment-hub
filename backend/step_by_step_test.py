#!/usr/bin/env python3
"""
Step-by-Step Manual Testing Script
Execute each test manually and verify results
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def print_header(title):
    print(f"\n{'='*80}")
    print(f"🧪 {title}")
    print(f"{'='*80}\n")

def print_step(num, description):
    print(f"\n📍 STEP {num}: {description}")
    print("-" * 80)

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

# ============================================================================
# TEST 1: VERIFY CONFIGURATION
# ============================================================================

def test_configuration():
    print_header("TEST 1: VERIFY ALL MOCKS ARE DISABLED")
    
    try:
        from app.core.config import settings
        
        print_step(1, "Check AWS_ENABLED")
        if settings.AWS_ENABLED:
            print_success(f"AWS_ENABLED = True")
        else:
            print_error(f"AWS_ENABLED = False (should be True!)")
            return False
        
        print_step(2, "Check Mock Flags")
        mocks = {
            'S3_MOCK_ENABLED': settings.S3_MOCK_ENABLED,
            'SNS_MOCK_ENABLED': settings.SNS_MOCK_ENABLED,
            'SQS_MOCK_ENABLED': settings.SQS_MOCK_ENABLED,
            'SES_MOCK_ENABLED': settings.SES_MOCK_ENABLED,
            'QUEUE_MOCK_ENABLED': settings.QUEUE_MOCK_ENABLED,
        }
        
        all_disabled = all(not v for v in mocks.values())
        for name, enabled in mocks.items():
            status = "ENABLED ❌" if enabled else "DISABLED ✅"
            print(f"   {name}: {status}")
        
        if not all_disabled:
            print_error("Some mocks are still enabled!")
            return False
        
        print_step(3, "Verify AWS Credentials")
        has_key = bool(settings.AWS_ACCESS_KEY_ID)
        has_secret = bool(settings.AWS_SECRET_ACCESS_KEY)
        
        if has_key:
            key_preview = settings.AWS_ACCESS_KEY_ID[:10] + "***"
            print_success(f"AWS_ACCESS_KEY_ID configured ({key_preview})")
        else:
            print_error("AWS_ACCESS_KEY_ID missing!")
            return False
            
        if has_secret:
            print_success(f"AWS_SECRET_ACCESS_KEY configured")
        else:
            print_error("AWS_SECRET_ACCESS_KEY missing!")
            return False
        
        print_step(4, "Verify AWS Endpoints")
        print_info(f"AWS Region: {settings.AWS_REGION}")
        print_info(f"S3 Bucket: {settings.S3_BUCKET_NAME}")
        print_info(f"SNS Topic: {settings.SNS_TOPIC_ARN[:60]}...")
        print_info(f"SQS Queue: {settings.SQS_QUEUE_URL[:60]}...")
        print_info(f"SES Email: {settings.SES_FROM_EMAIL}")
        
        return True
        
    except Exception as e:
        print_error(f"Configuration test failed: {str(e)}")
        return False

# ============================================================================
# TEST 2: AWS SERVICE CONNECTIVITY
# ============================================================================

def test_aws_connectivity():
    print_header("TEST 2: AWS SERVICE CONNECTIVITY")
    
    try:
        import boto3
        from app.core.config import settings
        
        # Create clients with explicit credentials
        client_kwargs = {
            'region_name': settings.AWS_REGION,
            'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
        }
        
        # Test S3
        print_step(1, "Test S3 Connectivity")
        try:
            s3 = boto3.client('s3', **client_kwargs)
            buckets = s3.list_buckets()
            bucket_names = [b['Name'] for b in buckets.get('Buckets', [])]
            
            if settings.S3_BUCKET_NAME in bucket_names:
                print_success(f"S3 bucket '{settings.S3_BUCKET_NAME}' is accessible")
            else:
                print_error(f"S3 bucket '{settings.S3_BUCKET_NAME}' not found!")
                return False
        except Exception as e:
            print_error(f"S3 connection failed: {str(e)}")
            return False
        
        # Test SNS
        print_step(2, "Test SNS Connectivity")
        try:
            sns = boto3.client('sns', **client_kwargs)
            attrs = sns.get_topic_attributes(TopicArn=settings.SNS_TOPIC_ARN)
            print_success(f"SNS topic is accessible")
            print_info(f"Topic subscriptions: {attrs['Attributes'].get('SubscriptionsConfirmed', 0)}")
        except Exception as e:
            print_error(f"SNS connection failed: {str(e)}")
            return False
        
        # Test SQS
        print_step(3, "Test SQS Connectivity")
        try:
            sqs = boto3.client('sqs', **client_kwargs)
            attrs = sqs.get_queue_attributes(
                QueueUrl=settings.SQS_QUEUE_URL,
                AttributeNames=['ApproximateNumberOfMessages', 'VisibilityTimeout']
            )
            msg_count = attrs['Attributes'].get('ApproximateNumberOfMessages', 0)
            print_success(f"SQS queue is accessible")
            print_info(f"Messages in queue: {msg_count}")
        except Exception as e:
            print_error(f"SQS connection failed: {str(e)}")
            return False
        
        # Test SES
        print_step(4, "Test SES Connectivity")
        try:
            ses = boto3.client('ses', **client_kwargs)
            response = ses.get_account_sending_enabled()
            enabled = response.get('Enabled', False)
            
            if enabled:
                print_success(f"SES is accessible and sending is enabled")
            else:
                print_error(f"SES sending is disabled!")
                return False
        except Exception as e:
            print_error(f"SES connection failed: {str(e)}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"AWS connectivity test failed: {str(e)}")
        return False

# ============================================================================
# TEST 3: DATABASE CONNECTIVITY
# ============================================================================

def test_database():
    print_header("TEST 3: DATABASE CONNECTIVITY")
    
    try:
        print_step(1, "Import database session")
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine
        from app.core.config import settings
        
        print_info(f"Database URL: {settings.DATABASE_URL}")
        
        print_step(2, "Create async engine")
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        
        print_step(3, "Test connection")
        async def test_conn():
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar()
        
        import asyncio
        result = asyncio.run(test_conn())
        
        if result == 1:
            print_success("Database connection successful")
        
        asyncio.run(engine.dispose())
        return True
        
    except Exception as e:
        print_error(f"Database test failed: {str(e)}")
        return False

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE AWS INTEGRATION TEST SUITE")
    print(f"{'='*80}")
    
    tests = [
        ("Configuration Check", test_configuration),
        ("AWS Connectivity", test_aws_connectivity),
        ("Database Connectivity", test_database),
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            success = test_func()
            results[name] = "PASS" if success else "FAIL"
        except Exception as e:
            print_error(f"Test '{name}' crashed: {str(e)}")
            results[name] = "ERROR"
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v == "PASS")
    failed = sum(1 for v in results.values() if v == "FAIL")
    errors = sum(1 for v in results.values() if v == "ERROR")
    
    for name, status in results.items():
        symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{symbol} {name}: {status}")
    
    print(f"\n{'='*80}")
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
    print(f"{'='*80}\n")
    
    if failed > 0 or errors > 0:
        print_error("Some tests failed! Please review errors above.")
        return 1
    else:
        print_success("All tests passed! Application is ready for deployment.")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
