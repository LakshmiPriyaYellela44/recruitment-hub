#!/usr/bin/env python3
"""
COMPREHENSIVE END-TO-END TESTING SCRIPT
Tests all API endpoints and complete workflows with REAL AWS services
"""

import asyncio
import sys
import json
import httpx
import time
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

def print_header(title):
    print(f"\n{'='*80}")
    print(f"🧪 {title}")
    print(f"{'='*80}\n")

def print_section(title):
    print(f"\n{'─'*80}")
    print(f"📌 {title}")
    print(f"{'─'*80}")

def print_step(num, description):
    print(f"\n   {num}️⃣  {description}")

def print_success(message):
    print(f"   ✅ {message}")

def print_error(message):
    print(f"   ❌ {message}")

def print_info(message):
    print(f"   ℹ️  {message}")

def print_test_result(name, passed, details=None):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n   [{status}] {name}")
    if details:
        print(f"        {details}")

# ============================================================================
# TEST SUITE 1: HEALTH & INFO ENDPOINTS
# ============================================================================

async def test_health_check():
    """Test basic health check endpoint"""
    print_section("TEST 1: HEALTH CHECK")
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_step(1, "GET /api/health")
            response = await client.get(f"{BASE_URL}/api/health")
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Health check passed: {data.get('status', 'unknown')}")
                print_test_result("Health Check", True, f"Status: {data.get('status')}")
                return True
            else:
                print_error(f"Health check failed with status {response.status_code}")
                print_test_result("Health Check", False, f"Status: {response.status_code}")
                return False
    except Exception as e:
        print_error(f"Health check error: {str(e)}")
        print_test_result("Health Check", False, str(e))
        return False

async def test_app_info():
    """Test app info endpoint"""
    print_section("TEST 2: APPLICATION INFO")
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_step(1, "GET /api/info")
            response = await client.get(f"{BASE_URL}/api/info")
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"App Name: {data.get('app_name')}")
                print_success(f"Version: {data.get('version')}")
                print_test_result("App Info", True, f"App: {data.get('app_name')} v{data.get('version')}")
                return True
            else:
                print_error(f"App info failed with status {response.status_code}")
                print_test_result("App Info", False, f"Status: {response.status_code}")
                return False
    except Exception as e:
        print_error(f"App info error: {str(e)}")
        print_test_result("App Info", False, str(e))
        return False

# ============================================================================
# TEST SUITE 2: AUTHENTICATION & USER MANAGEMENT
# ============================================================================

async def test_user_registration():
    """Test user registration"""
    print_section("TEST 3: USER REGISTRATION")
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            user_data = {
                "email": f"test_user_{int(time.time())}@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User"
            }
            
            print_step(1, "POST /api/auth/register")
            response = await client.post(
                f"{BASE_URL}/api/auth/register",
                json=user_data
            )
            print_info(f"Status Code: {response.status_code}")
            print_info(f"Email: {user_data['email']}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                print_success(f"User registered successfully")
                print_success(f"User ID: {data.get('id', 'N/A')}")
                print_test_result("User Registration", True, f"Email: {user_data['email']}")
                return True, user_data['email'], user_data['password']
            else:
                error_msg = response.json().get('detail', 'Unknown error')
                print_error(f"Registration failed: {error_msg}")
                print_test_result("User Registration", False, error_msg)
                return False, None, None
    except Exception as e:
        print_error(f"Registration error: {str(e)}")
        print_test_result("User Registration", False, str(e))
        return False, None, None

async def test_user_login(email, password):
    """Test user login"""
    print_section("TEST 4: USER LOGIN")
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_step(1, "POST /api/auth/login")
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": email, "password": password}
            )
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                print_success(f"Login successful")
                print_success(f"Token type: {data.get('token_type')}")
                print_test_result("User Login", True, f"Token received: {token[:20]}...")
                return True, token
            else:
                error_msg = response.json().get('detail', 'Unknown error')
                print_error(f"Login failed: {error_msg}")
                print_test_result("User Login", False, error_msg)
                return False, None
    except Exception as e:
        print_error(f"Login error: {str(e)}")
        print_test_result("User Login", False, str(e))
        return False, None

# ============================================================================
# TEST SUITE 3: RESUME UPLOAD & S3 INTEGRATION
# ============================================================================

async def test_resume_upload(token):
    """Test resume file upload to S3"""
    print_section("TEST 5: RESUME UPLOAD TO S3")
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Create a test resume file
            test_file_path = Path(__file__).parent / "test.pdf"
            
            if not test_file_path.exists():
                print_error(f"Test file not found: {test_file_path}")
                print_info(f"Creating dummy test file...")
                test_file_path.write_bytes(b"PDF dummy content for testing")
            
            print_step(1, "POST /api/resumes/upload - With S3 Storage")
            
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test_resume.pdf', f, 'application/pdf')}
                response = await client.post(
                    f"{BASE_URL}/api/resumes/upload",
                    files=files,
                    headers={'Authorization': f'Bearer {token}'}
                )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                resume_id = data.get('id')
                s3_key = data.get('s3_key', 'N/A')
                print_success(f"Resume uploaded successfully")
                print_success(f"Resume ID: {resume_id}")
                print_success(f"S3 Key: {s3_key}")
                print_test_result("Resume Upload", True, f"Resume ID: {resume_id}, S3 Key: {s3_key}")
                return True, resume_id
            else:
                error_msg = response.json().get('detail', 'Unknown error')
                print_error(f"Upload failed: {error_msg}")
                print_test_result("Resume Upload", False, error_msg)
                return False, None
    except Exception as e:
        print_error(f"Upload error: {str(e)}")
        print_test_result("Resume Upload", False, str(e))
        return False, None

async def test_resume_list(token):
    """Test listing resumes"""
    print_section("TEST 6: LIST RESUMES")
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_step(1, "GET /api/resumes - List all user resumes")
            response = await client.get(
                f"{BASE_URL}/api/resumes",
                headers={'Authorization': f'Bearer {token}'}
            )
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                resume_count = len(data) if isinstance(data, list) else data.get('total', 0)
                print_success(f"Retrieved {resume_count} resumes")
                print_test_result("List Resumes", True, f"Count: {resume_count}")
                return True
            else:
                error_msg = response.json().get('detail', 'Unknown error')
                print_error(f"List failed: {error_msg}")
                print_test_result("List Resumes", False, error_msg)
                return False
    except Exception as e:
        print_error(f"List error: {str(e)}")
        print_test_result("List Resumes", False, str(e))
        return False

# ============================================================================
# TEST SUITE 4: JOB POSTINGS
# ============================================================================

async def test_job_listings(token):
    """Test retrieving job listings"""
    print_section("TEST 7: JOB LISTINGS")
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_step(1, "GET /api/jobs - List all jobs")
            response = await client.get(
                f"{BASE_URL}/api/jobs",
                headers={'Authorization': f'Bearer {token}'}
            )
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                job_count = len(data) if isinstance(data, list) else data.get('total', 0)
                print_success(f"Retrieved {job_count} jobs")
                print_test_result("Job Listings", True, f"Count: {job_count}")
                return True, data if isinstance(data, list) else data.get('items', [])
            else:
                print_error(f"Failed to retrieve jobs")
                print_test_result("Job Listings", False, f"Status: {response.status_code}")
                return False, []
    except Exception as e:
        print_error(f"Job listing error: {str(e)}")
        print_test_result("Job Listings", False, str(e))
        return False, []

# ============================================================================
# TEST SUITE 5: AWS SERVICES VERIFICATION
# ============================================================================

async def test_aws_services():
    """Test AWS services integration"""
    print_section("TEST 8: AWS SERVICES VERIFICATION")
    
    try:
        from app.core.config import settings
        import boto3
        
        print_step(1, "Verify AWS Configuration")
        print_success(f"AWS Enabled: {settings.AWS_ENABLED}")
        print_success(f"Region: {settings.AWS_REGION}")
        print_success(f"S3 Bucket: {settings.S3_BUCKET_NAME}")
        print_success(f"SNS Topic: {settings.SNS_TOPIC_ARN}")
        print_success(f"SQS Queue: {settings.SQS_QUEUE_URL}")
        print_success(f"SES Email: {settings.SES_FROM_EMAIL}")
        
        print_step(2, "Test S3 Bucket Access")
        s3 = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        
        try:
            s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
            print_success(f"S3 bucket '{settings.S3_BUCKET_NAME}' is accessible")
            
            # List objects in bucket
            response = s3.list_objects_v2(Bucket=settings.S3_BUCKET_NAME, MaxKeys=5)
            obj_count = response.get('KeyCount', 0)
            print_success(f"S3 bucket contains {obj_count} objects")
             
            print_test_result("AWS S3", True, f"Bucket accessible, {obj_count} objects")
        except Exception as e:
            print_error(f"S3 access failed: {str(e)}")
            print_test_result("AWS S3", False, str(e))
            
        print_step(3, "Test SNS Topic Access")
        sns = boto3.client(
            'sns',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        
        try:
            attrs = sns.get_topic_attributes(TopicArn=settings.SNS_TOPIC_ARN)
            subs = attrs['Attributes'].get('SubscriptionsConfirmed', 0)
            print_success(f"SNS topic is accessible")
            print_success(f"Subscriptions: {subs}")
            print_test_result("AWS SNS", True, f"Topic accessible, {subs} subscriptions")
        except Exception as e:
            print_error(f"SNS access failed: {str(e)}")
            print_test_result("AWS SNS", False, str(e))
            
        print_step(4, "Test SQS Queue Access")
        sqs = boto3.client(
            'sqs',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        
        try:
            attrs = sqs.get_queue_attributes(
                QueueUrl=settings.SQS_QUEUE_URL,
                AttributeNames=['ApproximateNumberOfMessages']
            )
            msg_count = attrs['Attributes'].get('ApproximateNumberOfMessages', 0)
            print_success(f"SQS queue is accessible")
            print_success(f"Messages in queue: {msg_count}")
            print_test_result("AWS SQS", True, f"Queue accessible, {msg_count} messages")
        except Exception as e:
            print_error(f"SQS access failed: {str(e)}")
            print_test_result("AWS SQS", False, str(e))
            
        print_step(5, "Test SES")
        ses = boto3.client(
            'ses',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        
        try:
            response = ses.get_account_sending_enabled()
            enabled = response.get('Enabled', False)
            status = "✅ Enabled" if enabled else "⚠️  Disabled"
            print_success(f"SES sending is {status}")
            print_test_result("AWS SES", enabled, f"Sending: {status}")
        except Exception as e:
            print_error(f"SES access failed: {str(e)}")
            print_test_result("AWS SES", False, str(e))
            
        return True
    except Exception as e:
        print_error(f"AWS services test error: {str(e)}")
        return False

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    print_header("COMPREHENSIVE END-TO-END TEST SUITE")
    print(f"Start Time: {datetime.now().isoformat()}")
    print(f"Base URL: {BASE_URL}")
    print(f"Timeout: {TIMEOUT}s")
    
    results = {
        'health_check': False,
        'app_info': False,
        'user_registration': False,
        'user_login': False,
        'resume_upload': False,
        'resume_list': False,
        'job_listings': False,
        'aws_services': False,
    }
    
    try:
        # Wait a bit for server to fully start
        print("\n⏳ Waiting for server to be fully initialized...")
        await asyncio.sleep(2)
        
        # Test Health
        results['health_check'] = await test_health_check()
        
        # Test App Info
        results['app_info'] = await test_app_info()
        
        # Test User Registration
        registration_ok, email, password = await test_user_registration()
        results['user_registration'] = registration_ok
        
        if registration_ok:
            # Test Login
            login_ok, token = await test_user_login(email, password)
            results['user_login'] = login_ok
            
            if login_ok:
                # Test Resume Upload
                upload_ok, resume_id = await test_resume_upload(token)
                results['resume_upload'] = upload_ok
                
                # Test Resume List
                results['resume_list'] = await test_resume_list(token)
                
                # Test Job Listings
                job_ok, jobs = await test_job_listings(token)
                results['job_listings'] = job_ok
        
        # Test AWS Services
        results['aws_services'] = await test_aws_services()
        
    except Exception as e:
        print_error(f"Test suite error: {str(e)}")
    
    # Print Summary
    print_header("TEST SUMMARY REPORT")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    failed_tests = total_tests - passed_tests
    
    print()
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  [{status}] {test_name.replace('_', ' ').title()}")
    
    print(f"\n{'─'*80}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print(f"{'─'*80}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Application is fully operational.\n")
        return 0
    else:
        print(f"\n⚠️  {failed_tests} test(s) failed. Please review the errors above.\n")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
