# Resume Deletion Data Consistency - Implementation Guide

## Complete Solution Package

I've created a complete fix for resume deletion data consistency. Here's exactly what to do:

---

## Files Generated

### 1. **Documentation**
- `RESUME_DELETION_FIX.md` - Complete problem analysis and solution overview

### 2. **Code Files (Ready to Use)**
- `app/modules/resume/service_updated.py` - Updated service with cascade delete
- `app/modules/resume/repository_updated.py` - Repository with delete methods
- `app/modules/candidate/service_updated.py` - Service with resume_id support
- `app/modules/candidate/repository_updated.py` - Repository with resume_id support

### 3. **Database Migration**
- `migrations/0002_add_resume_traceability.sql` - Add columns and indexes

---

## Implementation Steps

### Step 1: Update Database Models

Edit `app/core/models.py` and add to these three classes:

**CandidateSkill class:**
```python
resume_id = Column(PGUUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True, index=True)
is_derived_from_resume = Column(Boolean, default=False, nullable=False)
```

**Experience class:**
```python
resume_id = Column(PGUUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True, index=True)
is_derived_from_resume = Column(Boolean, default=False, nullable=False)
```

**Education class:**
```python
resume_id = Column(PGUUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True, index=True)
is_derived_from_resume = Column(Boolean, default=False, nullable=False)
```

### Step 2: Replace Service Files

Replace file contents:
- `app/modules/resume/service.py` ← Use code from `service_updated.py`
- `app/modules/resume/repository.py` ← Use code from `repository_updated.py`
- `app/modules/candidate/service.py` ← Use code from `service_updated.py`
- `app/modules/candidate/repository.py` ← Use code from `repository_updated.py`

### Step 3: Run Database Migration

```bash
# Using psql
psql -U recruitment_user -d recruitment_db -f migrations/0002_add_resume_traceability.sql

# Or using Python
python -c "
import asyncio
from app.core.database import get_db
from sqlalchemy import text

async def run_migration():
    db = await get_db()
    with open('migrations/0002_add_resume_traceability.sql', 'r') as f:
        await db.execute(text(f.read()))
    await db.commit()

asyncio.run(run_migration())
"
```

### Step 4: Restart Backend

```bash
# If using Docker
docker-compose restart backend

# If running locally
uvicorn app.main:app --reload
```

---

## What Changed

### Data Flow BEFORE Fix
```
Upload Resume → Parse → Create Skills/Experiences
                           ↓
                    NO LINK TO RESUME
                           ↓
Delete Resume → Resume deleted ✓
               Skills still there ✗
               Experiences still there ✗
               Education still there ✗
```

### Data Flow AFTER Fix
```
Upload Resume → Parse → Create Skills/Experiences
                           ↓
                    WITH resume_id & is_derived_from_resume
                           ↓
Delete Resume → Delete all linked data ✓
               Delete skills ✓
               Delete experiences ✓
               Delete education ✓
               Resume deleted ✓
```

---

## Key Changes in Code

### 1. Resume Service (`delete_resume` method)

**BEFORE:**
```python
async def delete_resume(self, resume_id: UUID, user_id: UUID):
    resume = await self.repository.get_resume_by_id(resume_id)
    if not resume or resume.user_id != user_id:
        raise NotFoundException("Resume", str(resume_id))
    
    await self.s3_client.delete_file(resume.s3_key)
    await self.repository.delete_resume(resume_id)
    # ❌ Parsed data still in database!
```

**AFTER:**
```python
async def delete_resume(self, resume_id: UUID, user_id: UUID):
    resume = await self.repository.get_resume_by_id(resume_id)
    if not resume or resume.user_id != user_id:
        raise NotFoundException("Resume", str(resume_id))
    
    try:
        async with self.db.begin():
            # ✅ Delete skills linked to this resume
            await self.repository.delete_resume_skills(resume_id)
            
            # ✅ Delete experiences linked to this resume
            await self.repository.delete_resume_experiences(resume_id)
            
            # ✅ Delete educations linked to this resume
            await self.repository.delete_resume_educations(resume_id)
            
            # Delete S3 file
            await self.s3_client.delete_file(resume.s3_key)
            
            # Delete resume
            await self.repository.delete_resume(resume_id)
    except Exception as e:
        logger.error(f"Error deleting resume: {str(e)}", exc_info=True)
        raise
```

### 2. Candidate Service (`sync_parsed_resume_data`)

**BEFORE:**
```python
async def sync_parsed_resume_data(self, user_id: UUID, parsed_data: dict):
    for skill_name in skills_list:
        await self.add_skill_to_candidate(user_id, skill_name)
        # ❌ No resume_id passed
```

**AFTER:**
```python
async def sync_parsed_resume_data(self, user_id: UUID, parsed_data: dict, resume_id: UUID):
    for skill_name in skills_list:
        await self.add_skill_to_candidate(
            user_id, 
            skill_name,
            resume_id=resume_id,  # ✅ Pass resume_id
            is_derived=True       # ✅ Mark as parsed
        )
```

### 3. Repository Delete Methods (NEW)

```python
async def delete_resume_skills(self, resume_id: UUID) -> int:
    """Delete all skills derived from this resume."""
    result = await self.db.execute(
        delete(CandidateSkill).where(
            (CandidateSkill.resume_id == resume_id) &
            (CandidateSkill.is_derived_from_resume == True)
        )
    )
    await self.db.commit()
    return result.rowcount
```

---

## Testing the Fix

### Test 1: Single Resume Delete
```python
async def test_single_resume_delete():
    # 1. User uploads resume
    resume = await upload_resume(user_id, file)
    
    # 2. Backend parses it
    await process_resume(resume.id)
    
    # 3. Verify skills/experiences exist
    profile = await get_candidate_profile(user_id)
    assert len(profile.skills) > 0
    
    # 4. Delete resume
    await delete_resume(resume.id, user_id)
    
    # 5. Verify all derived data deleted
    profile = await get_candidate_profile(user_id)
    assert len(profile.skills) == 0
    assert len(profile.experiences) == 0
    assert len(profile.educations) == 0
    
    print("✅ Single resume delete test passed")
```

### Test 2: Multiple Resumes
```python
async def test_multiple_resumes():
    # 1. Upload 2 resumes
    resume1 = await upload_resume(user_id, file1)
    resume2 = await upload_resume(user_id, file2)
    
    await process_resume(resume1.id)
    await process_resume(resume2.id)
    
    profile = await get_candidate_profile(user_id)
    initial_skills = len(profile.skills)
    assert initial_skills > 0
    
    # 2. Delete only resume1
    await delete_resume(resume1.id, user_id)
    
    # 3. Verify resume2's data remains
    profile = await get_candidate_profile(user_id)
    remaining_skills = len(profile.skills)
    
    # Should have fewer skills now
    assert remaining_skills < initial_skills
    assert remaining_skills > 0  # But some should remain
    
    print("✅ Multiple resumes test passed")
```

### Test 3: Frontend Refresh
```javascript
// After resume deletion, UI should fetch fresh data
async function testUIRefresh() {
    // 1. Delete resume
    await deleteResume(resumeId);
    
    // 2. UI calls GET /candidates/me
    const profile = await fetch('/api/candidates/me');
    
    // 3. Verify empty profile
    assert(profile.skills.length === 0);
    assert(profile.experiences.length === 0);
    
    console.log('✅ UI refresh test passed');
}
```

---

## Verification Checklist

- [ ] Models updated with resume_id and is_derived_from_resume
- [ ] Migration script run successfully
- [ ] Resume service delete logic updated
- [ ] Candidate service sync_parsed_resume_data accepts resume_id
- [ ] Repository has delete_resume_* methods
- [ ] Backend restarted
- [ ] Test single resume delete: profiles show empty after delete
- [ ] Test multiple resumes: delete one, other data remains
- [ ] Test UI: refresh after delete shows accurate data
- [ ] Check database: verify orphaned records are gone
- [ ] Audit logs: verify delete events recorded with counts

---

## Troubleshooting

### Issue: Columns don't exist after migration
**Solution:**
```sql
-- Check if columns exist
SELECT column_name FROM information_schema.columns 
WHERE table_name='candidate_skills' AND column_name='resume_id';

-- If not, run migration manually
psql -U recruitment_user -d recruitment_db -f migrations/0002_add_resume_traceability.sql
```

### Issue: Delete fails with foreign key constraint
**Solution:**
```sql
-- Check for orphaned records
SELECT * FROM candidate_skills WHERE resume_id IS NOT NULL AND resume_id NOT IN (SELECT id FROM resumes);

-- Can manually delete:
DELETE FROM candidate_skills WHERE resume_id NOT IN (SELECT id FROM resumes);
```

### Issue: UI still shows old data after delete
**Solution:**
```javascript
// Add cache busting to profile fetch
const profile = await fetch(`/api/candidates/me?t=${Date.now()}`);
```

---

## Database Schema After Migration

```sql
--candidate_skills
- resume_id UUID (FK to resumes, nullable)
- is_derived_from_resume BOOLEAN (default: false)

-- experiences
- resume_id UUID (FK to resumes, nullable)
- is_derived_from_resume BOOLEAN (default: false)

-- educations
- resume_id UUID (FK to resumes, nullable)
- is_derived_from_resume BOOLEAN (default: false)
```

---

## Performance Implications

- **Indexes added** on resume_id and is_derived_from_resume
- **Delete operation**: O(1) lookup + cascade delete (indexes help)
- **Query profile**: No change - still loads all candidate data
- **Storage**: +2 columns per record (UUID + Boolean)

---

## Future Enhancements

1. **Soft Delete**: Mark as deleted instead of hard delete
2. **Audit Trail**: Track what data belonged to which resume
3. **Restore**: Ability to restore deleted data within X days
4. **Batch Operations**: Delete multiple resumes atomically
5. **Data Lineage Dashboard**: Show data flow from resume → profile

---

## Questions?

- Review `RESUME_DELETION_FIX.md` for detailed analysis
- Check test cases for expected behavior
- Verify migration script ran without errors
- Check database indexes: `SELECT * FROM pg_indexes WHERE tablename IN ('candidate_skills', 'experiences', 'educations');`

