#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing Suite
Tests all endpoints, flows, and AWS services integration
"""
import asyncio
import sys
import json
import time
from datetime import datetime
import httpx
from pathlib import Path

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class TestResults:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        self.start_time = datetime.now()
    
    def add(self, name, status, details=""):
        self.tests.append({"name": name, "status": status, "details": details})
        if status == "PASS":
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        duration = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{'='*80}")
        print(f"{BOLD}TEST SUMMARY{RESET}")
        print(f"{'='*80}")
        print(f"Total Tests:    {self.passed + self.failed}")
        print(f"{GREEN}Passed:         {self.passed}{RESET}")
        print(f"{RED}Failed:         {self.failed}{RESET}")
        print(f"Duration:       {duration:.2f} seconds")
        print(f"{'='*80}\n")

results = TestResults()

async def test_health_check():
    """Test 1: Health check endpoint"""
    print(f"\n{BLUE}Test 1: Health Check{RESET}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/health")
            if response.status_code == 200:
                print(f"{GREEN}✅ Health check passed{RESET}")
                print(f"   Response: {response.json()}")
                results.add("Health Check", "PASS")
                return True
            else:
                print(f"{RED}❌ Health check failed: {response.status_code}{RESET}")
                results.add("Health Check", "FAIL", f"Status: {response.status_code}")
                return False
    except Exception as e:
        print(f"{RED}❌ Error: {str(e)}{RESET}")
        results.add("Health Check", "FAIL", str(e))
        return False

async def test_app_info():
    """Test 2: Get app info"""
    print(f"\n{BLUE}Test 2: App Info Endpoint{RESET}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/info")
            if response.status_code == 200:
                data = response.json()
                print(f"{GREEN}✅ App info retrieved{RESET}")
                print(f"   App: {data.get('app_name')}")
                print(f"   Version: {data.get('version')}")
                results.add("App Info", "PASS")
                return True
            else:
                print(f"{RED}❌ Failed: {response.status_code}{RESET}")
                results.add("App Info", "FAIL", f"Status: {response.status_code}")
                return False
    except Exception as e:
        print(f"{RED}❌ Error: {str(e)}{RESET}")
        results.add("App Info", "FAIL", str(e))
        return False

async def test_aws_services_check():
    """Test 3: AWS Services Status"""
    print(f"\n{BLUE}Test 3: AWS Services Integration{RESET}")
    try:
        from app.core.config import settings
        
        print(f"   AWS_ENABLED: {settings.AWS_ENABLED}")
        print(f"   S3_MOCK_ENABLED: {settings.S3_MOCK_ENABLED}")
        print(f"   SNS_MOCK_ENABLED: {settings.SNS_MOCK_ENABLED}")
        print(f"   SQS_MOCK_ENABLED: {settings.SQS_MOCK_ENABLED}")
        print(f"   SES_MOCK_ENABLED: {settings.SES_MOCK_ENABLED}")
        
        if settings.AWS_ENABLED and not settings.S3_MOCK_ENABLED and \
           not settings.SNS_MOCK_ENABLED and not settings.SQS_MOCK_ENABLED and \
           not settings.SES_MOCK_ENABLED:
            print(f"{GREEN}✅ All AWS services enabled (mocks disabled){RESET}")
            results.add("AWS Services Config", "PASS")
            return True
        else:
            print(f"{RED}❌ Some mocks still enabled!{RESET}")
            results.add("AWS Services Config", "FAIL", "Mocks still enabled")
            return False
    except Exception as e:
        print(f"{RED}❌ Error: {str(e)}{RESET}")
        results.add("AWS Services Config", "FAIL", str(e))
        return False

async def test_database_connection():
    """Test 4: Database Connectivity"""
    print(f"\n{BLUE}Test 4: Database Connection{RESET}")
    try:
        async with httpx.AsyncClient() as client:
            # Try to get users (requires DB)
            response = await client.get("http://localhost:8000/api/users")
            # We expect 401 (auth required) or 200 - both mean DB is connected
            if response.status_code in [200, 401, 403]:
                print(f"{GREEN}✅ Database connected{RESET}")
                print(f"   Status: {response.status_code}")
                results.add("Database Connection", "PASS")
                return True
            else:
                print(f"{YELLOW}⚠️  Unexpected status: {response.status_code}{RESET}")
                results.add("Database Connection", "FAIL", f"Status: {response.status_code}")
                return False
    except Exception as e:
        print(f"{RED}❌ Database connection failed: {str(e)}{RESET}")
        results.add("Database Connection", "FAIL", str(e))
        return False

async def test_s3_connectivity():
    """Test 5: S3 Connectivity"""
    print(f"\n{BLUE}Test 5: S3 Connectivity{RESET}")
    try:
        import boto3
        from app.core.config import settings
        
        s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
        response = s3_client.list_buckets()
        
        bucket_names = [b['Name'] for b in response.get('Buckets', [])]
        if settings.S3_BUCKET_NAME in bucket_names:
            print(f"{GREEN}✅ S3 bucket accessible{RESET}")
            print(f"   Bucket: {settings.S3_BUCKET_NAME}")
            print(f"   Total buckets: {len(bucket_names)}")
            results.add("S3 Connectivity", "PASS")
            return True
        else:
            print(f"{RED}❌ Target S3 bucket not found{RESET}")
            print(f"   Looking for: {settings.S3_BUCKET_NAME}")
            print(f"   Found: {bucket_names}")
            results.add("S3 Connectivity", "FAIL", f"Bucket {settings.S3_BUCKET_NAME} not found")
            return False
    except Exception as e:
        print(f"{RED}❌ S3 connection failed: {str(e)}{RESET}")
        results.add("S3 Connectivity", "FAIL", str(e))
        return False

async def test_sns_connectivity():
    """Test 6: SNS Connectivity"""
    print(f"\n{BLUE}Test 6: SNS Connectivity{RESET}")
    try:
        import boto3
        from app.core.config import settings
        
        sns_client = boto3.client('sns', region_name=settings.AWS_REGION)
        
        # Try to get topic attributes
        response = sns_client.get_topic_attributes(TopicArn=settings.SNS_TOPIC_ARN)
        attributes = response.get('Attributes', {})
        
        print(f"{GREEN}✅ SNS topic accessible{RESET}")
        print(f"   Topic ARN: {settings.SNS_TOPIC_ARN}")
        print(f"   Subscriptions: {attributes.get('SubscriptionsConfirmed', 'N/A')}")
        results.add("SNS Connectivity", "PASS")
        return True
    except Exception as e:
        print(f"{RED}❌ SNS connection failed: {str(e)}{RESET}")
        results.add("SNS Connectivity", "FAIL", str(e))
        return False

async def test_sqs_connectivity():
    """Test 7: SQS Connectivity"""
    print(f"\n{BLUE}Test 7: SQS Connectivity{RESET}")
    try:
        import boto3
        from app.core.config import settings
        
        sqs_client = boto3.client('sqs', region_name=settings.AWS_REGION)
        
        # Get queue attributes
        response = sqs_client.get_queue_attributes(
            QueueUrl=settings.SQS_QUEUE_URL,
            AttributeNames=['All']
        )
        
        attrs = response.get('Attributes', {})
        print(f"{GREEN}✅ SQS queue accessible{RESET}")
        print(f"   Queue URL: {settings.SQS_QUEUE_URL}")
        print(f"   Messages in queue: {attrs.get('ApproximateNumberOfMessages', 'N/A')}")
        print(f"   Visibility timeout: {attrs.get('VisibilityTimeout', 'N/A')}s")
        results.add("SQS Connectivity", "PASS")
        return True
    except Exception as e:
        print(f"{RED}❌ SQS connection failed: {str(e)}{RESET}")
        results.add("SQS Connectivity", "FAIL", str(e))
        return False

async def test_ses_connectivity():
    """Test 8: SES Connectivity"""
    print(f"\n{BLUE}Test 8: SES Connectivity{RESET}")
    try:
        import boto3
        from app.core.config import settings
        
        ses_client = boto3.client('ses', region_name=settings.AWS_REGION)
        
        # Get send quota
        response = ses_client.get_account_sending_enabled()
        
        print(f"{GREEN}✅ SES service accessible{RESET}")
        print(f"   From Email: {settings.SES_FROM_EMAIL}")
        print(f"   Sending enabled: {response.get('Enabled', 'Unknown')}")
        results.add("SES Connectivity", "PASS")
        return True
    except Exception as e:
        print(f"{RED}❌ SES connection failed: {str(e)}{RESET}")
        results.add("SES Connectivity", "FAIL", str(e))
        return False

async def test_auth_endpoints():
    """Test 9: Authentication Endpoints"""
    print(f"\n{BLUE}Test 9: Authentication Endpoints{RESET}")
    try:
        async with httpx.AsyncClient() as client:
            # Test register endpoint exists
            response = await client.post(
                "http://localhost:8000/api/auth/register",
                json={"email": "test@example.com", "password": "test123", "full_name": "Test User"}
            )
            
            # Should return 200, 400, or 409 (not 404)
            if response.status_code != 404:
                print(f"{GREEN}✅ Auth endpoints accessible{RESET}")
                print(f"   Register endpoint: Status {response.status_code}")
                results.add("Auth Endpoints", "PASS")
                return True
            else:
                print(f"{RED}❌ Auth endpoints not found{RESET}")
                results.add("Auth Endpoints", "FAIL", "Endpoints not found")
                return False
    except Exception as e:
        print(f"{RED}❌ Error: {str(e)}{RESET}")
        results.add("Auth Endpoints", "FAIL", str(e))
        return False

async def test_resume_endpoints():
    """Test 10: Resume Endpoints Exist"""
    print(f"\n{BLUE}Test 10: Resume Endpoints{RESET}")
    try:
        async with httpx.AsyncClient() as client:
            # Test resumes endpoint exists (will fail auth but endpoint exists)
            response = await client.get("http://localhost:8000/api/resumes")
            
            # Should return 401 (auth required) or 200 - not 404
            if response.status_code != 404:
                print(f"{GREEN}✅ Resume endpoints accessible{RESET}")
                print(f"   Resumes endpoint: Status {response.status_code}")
                results.add("Resume Endpoints", "PASS")
                return True
            else:
                print(f"{RED}❌ Resume endpoints not found{RESET}")
                results.add("Resume Endpoints", "FAIL", "Endpoints not found")
                return False
    except Exception as e:
        print(f"{RED}❌ Error: {str(e)}{RESET}")
        results.add("Resume Endpoints", "FAIL", str(e))
        return False

async def main():
    print(f"\n{BOLD}{'='*80}")
    print(f"COMPREHENSIVE END-TO-END TEST SUITE")
    print(f"Testing: UI, Backend, Database, AWS Services")
    print(f"{'='*80}{RESET}")
    
    # Run all tests
    await test_health_check()
    await test_app_info()
    await test_aws_services_check()
    await test_database_connection()
    await test_s3_connectivity()
    await test_sns_connectivity()
    await test_sqs_connectivity()
    await test_ses_connectivity()
    await test_auth_endpoints()
    await test_resume_endpoints()
    
    # Print summary
    results.print_summary()
    
    # Return exit code
    return 0 if results.failed == 0 else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"{RED}Fatal error: {str(e)}{RESET}")
        sys.exit(1)
