#!/usr/bin/env python
"""Simple E2E test using urllib - no external dependencies."""

import sys
import json
import urllib.request
import urllib.error
import time
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor

BASE_URL = "http://localhost:8000"
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "recruitment_db",
    "user": "postgres",
    "password": "postgres",
}
TOKEN = None
USER_ID = None


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
        print(f"❌ DB Error: {e}")
        return None


def test_api_health():
    """Test if API is online."""
    try:
        resp = urllib.request.urlopen(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Backend health: {resp.status}")
        return True
    except Exception as e:
        print(f"❌ Backend offline: {e}")
        return False


def test_db_connection():
    """Test if database is accessible."""
    result = query_db("SELECT 1")
    if result:
        print(f"✅ Database connected")
        return True
    return False


def check_latest_resume():
    """Check latest resume in database."""
    result = query_db("""
        SELECT id, file_name, status, is_active, created_at 
        FROM resumes 
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    
    if result:
        r = result[0]
        print(f"\n✅ Latest Resume in Database:")
        print(f"   File: {r['file_name']}")
        print(f"   Status: {r['status']}")
        print(f"   Is Active: {r['is_active']}")
        
        # Check parsed data
        resume_id = r['id']
        skills = query_db("SELECT COUNT(*) as c FROM candidate_skills WHERE resume_id = %s", (resume_id,))
        exps = query_db("SELECT COUNT(*) as c FROM experiences WHERE resume_id = %s", (resume_id,))
        edus = query_db("SELECT COUNT(*) as c FROM educations WHERE resume_id = %s", (resume_id,))
        
        skills_count = skills[0]['c'] if skills else 0
        exps_count = exps[0]['c'] if exps else 0
        edus_count = edus[0]['c'] if edus else 0
        
        print(f"\n📊 Parsed Data from Database:")
        print(f"   Skills: {skills_count}")
        print(f"   Experiences: {exps_count}")
        print(f"   Educations: {edus_count}")
        
        return r['status'], skills_count, exps_count, edus_count
    else:
        print(f"❌ No resumes found in database")
        return None, 0, 0, 0


def main():
    print("="*70)
    print("  SIMPLE E2E DIAGNOSTIC TEST")
    print("="*70)
    
    # Test 1: API Health
    print("\n✓ Checking Backend Health...")
    if not test_api_health():
        print("Backend is not running. Start it first.")
        return 1
    
    # Test 2: DB Connection
    print("\n✓ Checking Database Connection...")
    if not test_db_connection():
        print("Cannot connect to database.")
        return 1
    
    # Test 3: Check latest resume
    print("\n✓ Checking Latest Resume...")
    status, skills, exps, edus = check_latest_resume()
    
    if status is None:
        print("No resumes in database yet. Try uploading one from the UI.")
        return 0
    
    print(f"\n{'='*70}")
    print("RESULTS:")
    print(f"  Status: {status}")
    print(f"  Parsed Skills: {skills}")
    print(f"  Parsed Experiences: {exps}")
    print(f"  Parsed Educations: {edus}")
    print(f"{'='*70}")
    
    if status == "PARSED" and (skills > 0 or exps > 0 or edus > 0):
        print("\n✅✅✅ PIPELINE WORKING! Data is being parsed and persisted!")
        return 0
    elif status == "PARSED":
        print("\n⚠️  Resume marked PARSED but no extracted data found")
        print("   This could mean:")
        print("   1. Parser returned empty lists (resume text not detected)")
        print("   2. _persist_* methods not called")
        print("   3. Data not committed to database")
        return 1
    elif status == "FAILED":
        print("\n❌ Resume parsing FAILED")
        print("   Check backend logs for error details")
        return 1
    else:
        print(f"\n⏳ Resume status is {status} (not yet PARSED)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
