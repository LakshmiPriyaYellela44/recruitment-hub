#!/usr/bin/env python
"""Comprehensive end-to-end test for resume upload and parsing pipeline."""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
import httpx
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration
BASE_URL = "http://localhost:8000"
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "recruitment_db",
    "user": "postgres",
    "password": "postgres",
}

# Test credentials
TEST_EMAIL = "testcandidate@example.com"
TEST_PASSWORD = "test123"
TEST_USER_ID = None
TEST_TOKEN = None


def print_section(title):
    """Print a section divider."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def query_db(query, params=None):
    """Execute a database query."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return None


def check_db_resume():
    """Check if resume exists in database."""
    print_section("STEP 2: Check Database for Resume Record")
    
    result = query_db("""
        SELECT id, user_id, file_name, status, is_active, created_at 
        FROM resumes 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT 1
    """, (TEST_USER_ID,))
    
    if result:
        resume = result[0]
        print(f"✅ Resume found in database:")
        print(f"   ID: {resume['id']}")
        print(f"   Status: {resume['status']}")
        print(f"   Is Active: {resume['is_active']}")
        print(f"   Created: {resume['created_at']}")
        return resume
    else:
        print("❌ No resume found in database!")
        return None


def check_db_parsed_data(resume_id):
    """Check if parsed data exists in database."""
    print_section("STEP 3: Check Database for Parsed Data")
    
    # Check skills
    skills_result = query_db("""
        SELECT COUNT(*) as count FROM candidate_skills 
        WHERE candidate_id = %s AND resume_id = %s
    """, (TEST_USER_ID, resume_id))
    
    # Check experiences
    exp_result = query_db("""
        SELECT COUNT(*) as count FROM experiences 
        WHERE user_id = %s AND resume_id = %s
    """, (TEST_USER_ID, resume_id))
    
    # Check educations
    edu_result = query_db("""
        SELECT COUNT(*) as count FROM educations 
        WHERE user_id = %s AND resume_id = %s
    """, (TEST_USER_ID, resume_id))
    
    skills_count = skills_result[0]['count'] if skills_result else 0
    exp_count = exp_result[0]['count'] if exp_result else 0
    edu_count = edu_result[0]['count'] if edu_result else 0
    
    print(f"📊 Parsed Data Counts:")
    print(f"   Skills: {skills_count}")
    print(f"   Experiences: {exp_count}")
    print(f"   Educations: {edu_count}")
    
    if skills_count == 0 and exp_count == 0 and edu_count == 0:
        print("\n⚠️  WARNING: No parsed data found in database!")
        print("   This indicates the parser failed or didn't persist data.")
    
    return {
        "skills": skills_count,
        "experiences": exp_count,
        "educations": edu_count
    }


async def get_candidate_profile():
    """Call the API to get candidate profile."""
    print_section("STEP 4: Check API Response")
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
            response = await client.get(f"{BASE_URL}/candidates/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API returned profile:")
                print(f"   Skills in response: {len(data.get('skills', []))}")
                print(f"   Experiences in response: {len(data.get('experiences', []))}")
                print(f"   Educations in response: {len(data.get('educations', []))}")
                
                if data.get('skills'):
                    print(f"\n   Skills:")
                    for skill in data['skills'][:3]:  # Show first 3
                        print(f"      - {skill.get('name', 'Unknown')}")
                
                if data.get('experiences'):
                    print(f"\n   Experiences:")
                    for exp in data['experiences'][:3]:
                        print(f"      - {exp.get('job_title', 'Unknown')}")
                
                return data
            else:
                print(f"❌ API returned status {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return None
    except Exception as e:
        print(f"❌ API error: {str(e)}")
        return None


async def register_and_login():
    """Register and login a test user."""
    print_section("STEP 0: Register & Login Test User")
    
    global TEST_USER_ID, TEST_TOKEN
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Register
            print(f"Registering user: {TEST_EMAIL}")
            register_payload = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "first_name": "Test",
                "last_name": "Candidate",
                "role": "CANDIDATE"
            }
            register_response = await client.post(
                f"{BASE_URL}/auth/register",
                json=register_payload
            )
            
            if register_response.status_code not in [200, 201]:
                # User might already exist, try login
                print(f"Registration returned {register_response.status_code}, trying login...")
            else:
                print("✅ User registered")
            
            # Login
            print(f"Logging in...")
            login_payload = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
            login_response = await client.post(
                f"{BASE_URL}/auth/login",
                json=login_payload
            )
            
            if login_response.status_code == 200:
                data = login_response.json()
                TEST_TOKEN = data.get("access_token")
                print(f"✅ Login success, token received")
                
                # Get user ID
                headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
                profile_response = await client.get(f"{BASE_URL}/candidates/me", headers=headers)
                if profile_response.status_code == 200:
                    TEST_USER_ID = profile_response.json()["id"]
                    print(f"✅ User ID: {TEST_USER_ID}")
                    return True
            else:
                print(f"❌ Login failed: {login_response.text}")
                return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


async def upload_resume():
    """Upload a test resume."""
    print_section("STEP 1: Upload Resume")
    
    # Create a minimal test resume
    test_resume_path = Path("/tmp/test_resume.pdf")
    # Create a very simple text PDF-like content
    test_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    test_content += b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    test_content += b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << >> /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
    test_content += b"4 0 obj\n<< /Length 150 >>\nstream\nBT\n/F1 12 Tf\n50 700 Td\n(John Doe) Tj\n0 -20 Td\n(Python, Java, JavaScript) Tj\n0 -20 Td\n(Senior Software Engineer at Google) Tj\n0 -20 Td\n(BS Computer Science) Tj\nET\nendstream\nendobj\nxref\ntrailer\n"
    test_resume_path.write_bytes(test_content)
    
    print(f"Created test resume: {test_resume_path}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
            
            with open(test_resume_path, "rb") as f:
                files = {"file": ("test_resume.pdf", f, "application/pdf")}
                response = await client.post(
                    f"{BASE_URL}/resumes/upload",
                    headers=headers,
                    files=files
                )
            
            if response.status_code in [200, 201]:
                data = response.json()
                print(f"✅ Resume uploaded successfully")
                print(f"   Resume ID: {data.get('id')}")
                print(f"   Status: {data.get('status')}")
                
                # Wait a bit for async processing
                await asyncio.sleep(2)
                print(f"\nWaiting for background parsing...")
                
                return data.get("id")
            else:
                print(f"❌ Upload failed with status {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return None
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return None
    finally:
        test_resume_path.unlink(missing_ok=True)


async def main():
    """Run the complete E2E test."""
    print("\n" + "="*70)
    print("  COMPREHENSIVE E2E TEST: Resume Upload & Parsing Pipeline")
    print("="*70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Backend URL: {BASE_URL}")
    
    # Step 0: Register/Login
    if not await register_and_login():
        print("\n❌ Failed to login, aborting test")
        sys.exit(1)
    
    # Step 1: Upload resume
    resume_id = await upload_resume()
    if not resume_id:
        print("\n❌ Failed to upload resume, aborting test")
        sys.exit(1)
    
    # Step 2: Check database
    resume = check_db_resume()
    if not resume:
        print("\n❌ Resume not in database, aborting test")
        sys.exit(1)
    
    # Step 3: Check parsed data in database
    parsed_data_count = check_db_parsed_data(resume_id)
    
    # Step 4: Check API response
    profile = await get_candidate_profile()
    
    # Summary
    print_section("FINAL SUMMARY")
    print(f"✅ Resume uploaded: {bool(resume)}")
    print(f"✅ Resume status: {resume.get('status') if resume else 'N/A'}")
    print(f"✅ DB Skills persisted: {parsed_data_count.get('skills', 0)}")
    print(f"✅ DB Experiences persisted: {parsed_data_count.get('experiences', 0)}")
    print(f"✅ DB Educations persisted: {parsed_data_count.get('educations', 0)}")
    
    if profile:
        print(f"✅ API Skills returned: {len(profile.get('skills', []))}")
        print(f"✅ API Experiences returned: {len(profile.get('experiences', []))}")
        print(f"✅ API Educations returned: {len(profile.get('educations', []))}")
    
    print("\n" + "="*70)
    
    # Check if everything passes
    success = (
        bool(resume) and
        resume.get('status') == 'PARSED' and
        parsed_data_count.get('skills', 0) > 0 and
        profile and
        len(profile.get('skills', [])) > 0
    )
    
    if success:
        print("✅✅✅ ALL TESTS PASSED! Pipeline is working correctly!")
        print("="*70 + "\n")
        return 0
    else:
        print("❌ Some tests failed. See details above.")
        print("="*70 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
