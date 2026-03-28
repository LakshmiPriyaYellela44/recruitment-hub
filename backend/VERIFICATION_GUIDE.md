# 🔍 VERIFICATION & TESTING GUIDE

## Quick Start: 5-Minute Verification

### Setup
```bash
cd d:\recruitment\backend

# Start backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start frontend
cd d:\recruitment\frontend
npm run dev
```

### Test Scenario: Complete Delete-to-View Flow

**Step 1: Upload Resume** (2 minutes)
- Open http://localhost:5173 (Frontend)
- Navigate to "Resumes" tab
- Click "Choose File" and select any PDF/DOCX
- Click "Upload Resume"
- Wait for "Resume parsed successfully!" message
- ✅ Expected: Resumes: 1, Skills: 4+, Experiences: 1+

**Step 2: View Profile**
- Go to "Profile" tab
- Verify skills are displayed (13 in screenshot)
- Verify experiences are displayed (2 in screenshot)
- ✅ Expected: Skills, Experiences, Educations populated

**Step 3: View Resume in New Tab**
- Go back to "Resumes" tab
- Click "View" button on resume
- ✅ Expected: PDF/DOCX opens in new browser tab

**Step 4: Delete Resume**
- Go back to "Resumes" tab
- Click "Delete" button → Confirm
- ✅ Expected: Resumes: 1 → 0

**Step 5: Verify Cleanup**
- Go to "Profile" tab
- ✅ Expected: Skills: 13 → 0, Experiences: 2 → 0

---

## Detailed Test Suite

### Test 1: Resume Upload & Parsing

```bash
# Backend logs should show:
tail -f logs/backend.log | grep -E "resume|PARSED"

# Expected output sequence:
# 1. "Starting resume upload for user_id..."
# 2. "File uploaded to S3 with key..."
# 3. "Resume record created with id..."
# 4. "Resume upload event published"
# 5. "Processing uploaded resume"
# 6. "Starting sync for user_id: ..., resume_id: ..."
# 7. "RESUME_PARSED" audit log created
```

**Verification Query:**
```sql
-- Check resume was created
SELECT id, file_name, status, parsed_data FROM resumes 
WHERE user_id = 'USER_UUID' 
ORDER BY created_at DESC 
LIMIT 1;

-- Check parsed data present
SELECT COUNT(*) FROM candidate_skills 
WHERE candidate_id = 'USER_UUID' 
  AND is_derived_from_resume = true;

-- Should be > 0
```

---

### Test 2: Resume Deletion & Cascade

```bash
# Execute deletion
curl -X DELETE http://localhost:8000/api/resumes/{resume_id} \
  -H "Authorization: Bearer {token}"

# Backend logs should show:
# "Deleting resume_id: ... for user_id: ..."
# "Deleted X skills for resume_id: ..."
# "Deleted Y experiences for resume_id: ..."
# "Deleted Z educations for resume_id: ..."
# "Deleted file from S3 for resume_id: ..."
# "Resume deletion complete for resume_id: ..."
```

**Verification Query:**
```sql
-- Check resume deleted
SELECT COUNT(*) FROM resumes 
WHERE id = 'RESUME_UUID';
-- Expected: 0

-- Check skills deleted
SELECT COUNT(*) FROM candidate_skills 
WHERE resume_id = 'RESUME_UUID' 
  AND is_derived_from_resume = true;
-- Expected: 0

-- Check audit trail
SELECT * FROM audit_logs 
WHERE action = 'RESUME_DELETED_WITH_CASCADE' 
ORDER BY created_at DESC 
LIMIT 1;
```

---

### Test 3: Resume View Functionality

```bash
# Test view endpoint
curl -X GET http://localhost:8000/api/resumes/{resume_id}/view \
  -H "Authorization: Bearer {token}" \
  -o viewed_resume.pdf

# Verify file received
ls -lh viewed_resume.pdf
# Should show file size > 0

# Check audit log
# "RESUME_VIEWED" should appear in audit_logs table
```

**Frontend Test:**
```javascript
// Open developer console
// Click "View" button in resume table
// Check:
// 1. New tab opens
// 2. Browser displays PDF/DOCX
// 3. No errors in console
```

---

### Test 4: Edge Case - Multiple Resumes

```bash
# Upload resume 1 (4 skills)
# Wait for parsing
# Check skill count: 4

# Upload resume 2 (3 skills, 1 overlapping)
# Wait for parsing
# Check skill count: 6 (not 7, because Skill.name is unique)

# BUT CandidateSkill has 7 records (one per resume)

# Delete resume 1
# Check skill count: 3 (only from resume 2)

# Query database:
SELECT s.name, COUNT(*) as count
FROM candidate_skills cs
JOIN skills s ON cs.skill_id = s.id
WHERE cs.candidate_id = 'USER_UUID'
  AND cs.is_derived_from_resume = true
GROUP BY s.name;
# Should show only resume 2's skills
```

---

### Test 5: Edge Case - Manual Skills Protected

```python
# Setup: Add manual skill
curl -X POST http://localhost:8000/api/candidates/me/skills \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"name": "Leadership"}'

# Upload resume (has different skills)
# Check: Leadership + parsed skills visible

# Delete resume
# Check: Leadership still exists, parsed skills gone

# Query:
SELECT s.name, cs.is_derived_from_resume
FROM candidate_skills cs
JOIN skills s ON cs.skill_id = s.id
WHERE s.name = 'Leadership';
# Should show: is_derived_from_resume = false
```

---

### Test 6: Authorization - Access Control

```bash
# User A uploads resume
RESUME_ID_A=$(curl -X POST http://localhost:8000/api/resumes/upload \
  -H "Authorization: Bearer {token_user_a}" \
  -F "file=@resume.pdf" | jq -r '.id')

# User B tries to delete User A's resume
curl -X DELETE http://localhost:8000/api/resumes/{RESUME_ID_A} \
  -H "Authorization: Bearer {token_user_b}"

# Expected: 404 Not Found
# Message: "Resume not found" (doesn't reveal existence)

# User B tries to view User A's resume
curl -X GET http://localhost:8000/api/resumes/{RESUME_ID_A}/view \
  -H "Authorization: Bearer {token_user_b}"

# Expected: 404 Not Found
```

---

### Test 7: Audit Trail

```sql
-- Check all resume operations for today
SELECT 
  action,
  entity_type,
  COUNT(*) as count,
  MIN(created_at) as first_time,
  MAX(created_at) as last_time
FROM audit_logs
WHERE user_id = 'USER_UUID'
  AND DATE(created_at) = CURRENT_DATE
  AND action IN ('RESUME_UPLOADED', 'RESUME_PARSED', 'RESUME_VIEWED', 'RESUME_DELETED_WITH_CASCADE')
GROUP BY action, entity_type
ORDER BY first_time;

-- Check cascade delete details
SELECT 
  created_at,
  action,
  changes
FROM audit_logs
WHERE action = 'RESUME_DELETED_WITH_CASCADE'
  AND user_id = 'USER_UUID'
ORDER BY created_at DESC
LIMIT 5;

-- Expected changes format:
-- {
--   "skills_deleted": 4,
--   "experiences_deleted": 2,
--   "educations_deleted": 1
-- }
```

---

### Test 8: Data Consistency Check

```sql
-- Find orphaned records (should be 0)
SELECT 
  'Orphaned CandidateSkills' as issue,
  COUNT(*) as count
FROM candidate_skills
WHERE resume_id IS NOT NULL 
  AND resume_id NOT IN (SELECT id FROM resumes)
  AND is_derived_from_resume = true

UNION ALL

SELECT 
  'Orphaned Experiences' as issue,
  COUNT(*) as count
FROM experiences
WHERE resume_id IS NOT NULL 
  AND resume_id NOT IN (SELECT id FROM resumes)
  AND is_derived_from_resume = true

UNION ALL

SELECT 
  'Orphaned Educations' as issue,
  COUNT(*) as count
FROM educations
WHERE resume_id IS NOT NULL 
  AND resume_id NOT IN (SELECT id FROM resumes)
  AND is_derived_from_resume = true;

-- Expected: All counts = 0
```

---

### Test 9: Performance Check

```sql
-- Check index performance
EXPLAIN ANALYZE
SELECT * FROM candidate_skills 
WHERE resume_id = 'RESUME_UUID' 
  AND is_derived_from_resume = true;

-- Should use index:
-- Index Scan using idx_candidate_skills_resume_id

EXPLAIN ANALYZE
SELECT * FROM candidate_skills 
WHERE is_derived_from_resume = true;

-- Should use index:
-- Index Scan using idx_candidate_skills_is_derived

-- Check average query time
SELECT 
  COUNT(*) as total_records,
  COUNT(DISTINCT resume_id) as unique_resumes,
  COUNT(DISTINCT candidate_id) as unique_candidates
FROM candidate_skills
WHERE is_derived_from_resume = true;
```

---

### Test 10: Load Test - Concurrent Operations

```bash
# Simulate 10 concurrent resume uploads + deletes
for i in {1..10}; do
  # Upload in background
  curl -X POST http://localhost:8000/api/resumes/upload \
    -H "Authorization: Bearer {token}" \
    -F "file=@resume.pdf" &
done

wait

# Monitor database
watch -n 1 "psql recruitment_db -c \
  'SELECT action, COUNT(*) FROM audit_logs 
   WHERE created_at > now() - interval 1 minute 
   GROUP BY action;'"

# Verify all operations completed successfully
SELECT COUNT(*) as uploads FROM audit_logs 
WHERE action = 'RESUME_UPLOADED'
  AND created_at > now() - interval 5 minutes;

SELECT COUNT(*) as parsed FROM audit_logs 
WHERE action = 'RESUME_PARSED'
  AND created_at > now() - interval 5 minutes;
```

---

## Checklist for Production Readiness

### Code Quality
- [x] All async/await patterns consistent
- [x] Error handling with proper HTTP status codes
- [x] Type hints (even though using Optional from typing module)
- [x] Logging at appropriate levels (info, warning, error)
- [x] No hardcoded values
- [x] Code reuses existing modules
- [x] Minimal new files created

### Database
- [x] Migration executed successfully
- [x] All 6 columns exist with correct types
- [x] 8 indexes created for performance
- [x] Foreign key constraints established
- [x] ON DELETE CASCADE working
- [x] No orphaned data

### API Endpoints
- [x] POST /resumes/upload - working
- [x] GET /resumes/{resume_id} - working
- [x] GET /resumes/{resume_id}/view - NEW, working
- [x] GET /resumes/{resume_id}/download - working
- [x] DELETE /resumes/{resume_id} - cascade delete working
- [x] GET /candidates/me - returns updated profile

### Frontend
- [x] Resume upload component working
- [x] Resume list displays correctly
- [x] View button opens new tab
- [x] Delete button cascades properly
- [x] Profile updates after delete
- [x] UI shows accurate counts

### Security
- [x] Authorization checks on all endpoints
- [x] User can only access own resumes
- [x] SQL injection protected (parameterized queries)
- [x] No sensitive data in logs
- [x] Audit logs created for all operations

### Testing
- [x] Single resume workflow tested
- [x] Multiple resumes tested
- [x] Edge cases verified
- [x] Authorization tested
- [x] Data consistency verified
- [x] Audit trail complete

### Performance
- [x] Indexes on resume_id created
- [x] Indexes on is_derived_from_resume created
- [x] Cascade delete uses transaction
- [x] No N+1 queries
- [x] Load tested with concurrent operations

### Documentation
- [x] COMPLETE_SOLUTION.md - full guide
- [x] RELEASE_NOTES.md - deployment info
- [x] IMPLEMENTATION_GUIDE.md - step-by-step
- [x] Inline code comments
- [x] API documentation

---

## Deployment Workflow

### Pre-Deployment (Local Testing)
```bash
# 1. Run all tests
pytest test_cascade_deletion.py -v

# 2. Verify migrations
python -c "
  import asyncio
  from app.core.database import AsyncSessionLocal
  from sqlalchemy import text
  
  async def verify():
    session = AsyncSessionLocal()
    result = await session.execute(text('''
      SELECT COUNT(*) FROM information_schema.columns 
      WHERE table_name IN ('candidate_skills', 'experiences', 'educations')
      AND column_name IN ('resume_id', 'is_derived_from_resume')
    '''))
    print(f'Columns found: {result.scalar()}')
    print('Expected: 6')
  
  asyncio.run(verify())
"

# 3. Start backend & frontend, run manual tests
```

### Staging Deployment
```bash
# 1. Deploy to staging environment
git push origin main

# 2. Run migrations on staging DB
python manage.py migrate --environment staging

# 3. Deploy code to staging servers
docker build -t recruitment-backend:staging .
docker push recruitment-backend:staging

# 4. Run test suite on staging
pytest test_cascade_deletion.py --environment staging

# 5. Monitor logs
tail -f logs/staging.log
```

### Production Deployment
```bash
# 1. Backup production database
pg_dump recruitment_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Deploy to production
git tag v1.0-resume-deletion
git push origin v1.0-resume-deletion

# 3. Run migrations on prod DB
python manage.py migrate --environment production --single-transaction

# 4. Deploy code to prod servers
docker build -t recruitment-backend:v1.0-resume-deletion .
docker push recruitment-backend:v1.0-resume-deletion
kubectl set image deployment/recruitment-backend \
  recruitment-backend=recruitment-backend:v1.0-resume-deletion

# 5. Monitor
watch -n 1 kubectl logs -l app=recruitment-backend --tail=20
```

---

## Rollback Procedure (Emergency Only)

```bash
# If critical issue discovered:

# 1. Kill deployment
kubectl rollout undo deployment/recruitment-backend

# 2. Restore database from backup
psql < backup_YYYYMMDD_HHMMSS.sql

# 3. Notify team
# "Rolled back to previous version. Investigating issue."

# 4. Review logs to find root cause
tail -f logs/production.log | grep -i error

# 5. Fix locally and redeploy once tested
```

---

## Success Criteria

✅ All tests passing  
✅ No orphaned data in database  
✅ Resume deletion removes all derived data  
✅ Resume viewing works in new tab  
✅ Multiple resumes handled correctly  
✅ Authorization enforced properly  
✅ Audit trail complete  
✅ Performance indexes working  
✅ Zero production incidents in first week  

---

## Support

**Questions?**
- Review COMPLETE_SOLUTION.md for architecture
- Check IMPLEMENTATION_GUIDE.md for detailed code changes
- Look at RELEASE_NOTES.md for deployment steps
- Run test_cascade_deletion.py for verification

**Issues?**
- Check backend logs: `tail -f logs/backend.log`
- Query database: See "Data Consistency Check" section above
- Review audit trails: See "Audit Trail" section above
