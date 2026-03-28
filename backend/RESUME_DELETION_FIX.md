# Resume Deletion Data Consistency Fix

## Problem
When a candidate deletes a resume, the parsed data (skills, experiences, education) still appears in the UI. This creates stale/inconsistent data.

## Root Cause
- Parsed data is stored independently with NO link to the originating resume
- No foreign key relationship between Resume ↔ CandidateSkill, Experience, Education
- When resume is deleted, parsed data orphan records remain in DB

## Solution Overview

### 1. Database Schema Changes
Add `resume_id` FK and `is_derived_from_resume` flag to:
- `candidate_skills` table
- `experiences` table
- `educations` table

### 2. Service Logic Updates
- Update `sync_parsed_resume_data()` to pass `resume_id` when creating derived data
- Update `delete_resume()` to cascade-delete all related parsed data
- Use transactions for atomic deletes

### 3. Migration Path
- Back-fill existing records with `is_derived_from_resume=false`
- Going forward, set flag to `true` for parsed data

---

## Implementation Files & Changes

### File 1: `app/core/models.py`

#### CandidateSkill
```python
class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    skill_id = Column(PGUUID(as_uuid=True), ForeignKey("skills.id"), nullable=False, index=True)
    resume_id = Column(PGUUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True, index=True)  # NEW
    proficiency = Column(String(50), nullable=True)
    is_derived_from_resume = Column(Boolean, default=False, nullable=False)  # NEW
    
    # Audit columns...
```

#### Experience
```python
class Experience(Base):
    __tablename__ = "experiences"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    resume_id = Column(PGUUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True, index=True)  # NEW
    job_title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    # ... other columns
    is_derived_from_resume = Column(Boolean, default=False, nullable=False)  # NEW
    
    # Audit columns...
```

#### Education
```python
class Education(Base):
    __tablename__ = "educations"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    resume_id = Column(PGUUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True, index=True)  # NEW
    institution = Column(String(255), nullable=False)
    degree = Column(String(100), nullable=False, index=True)
    # ... other columns
    is_derived_from_resume = Column(Boolean, default=False, nullable=False)  # NEW
    
    # Audit columns...
```

---

### File 2: `app/modules/candidate/service.py`

Update `sync_parsed_resume_data()` to accept and pass `resume_id`:

```python
async def sync_parsed_resume_data(self, user_id: UUID, parsed_data: dict, resume_id: UUID):
    """Sync extracted resume data with resume_id tracking."""
    logger.info(f"[sync_parsed_resume_data] Starting sync for user_id: {user_id}, resume_id: {resume_id}")
    
    try:
        # Extract and add skills
        skills_list = parsed_data.get("skills", [])
        if skills_list:
            for skill_name in skills_list:
                try:
                    await self.add_skill_to_candidate(
                        user_id, 
                        skill_name, 
                        proficiency="INTERMEDIATE",
                        resume_id=resume_id,  # PASS RESUME ID
                        is_derived=True  # MARK AS PARSED
                    )
                except Exception as e:
                    logger.warning(f"Failed to add skill: {str(e)}")
        
        # Extract and add experiences
        experiences_list = parsed_data.get("experiences", [])
        if experiences_list:
            for exp_data in experiences_list:
                try:
                    exp = ExperienceCreate(
                        job_title=exp_data.get("title", "Unknown"),
                        company_name=exp_data.get("company", "Unknown"),
                        resume_id=resume_id,  # PASS RESUME ID
                        is_derived_from_resume=True  # MARK AS PARSED
                    )
                    await self.add_experience(user_id, exp)
                except Exception as e:
                    logger.warning(f"Failed to add experience: {str(e)}")
        
        # Extract and add educations
        educations_list = parsed_data.get("educations", [])
        if educations_list:
            for edu_data in educations_list:
                try:
                    edu = EducationCreate(
                        institution=edu_data.get("institution", "Unknown"),
                        degree=edu_data.get("degree", "Unknown"),
                        resume_id=resume_id,  # PASS RESUME ID
                        is_derived_from_resume=True  # MARK AS PARSED
                    )
                    await self.add_education(user_id, edu)
                except Exception as e:
                    logger.warning(f"Failed to add education: {str(e)}")
        
        logger.info(f"[sync_parsed_resume_data] Completed sync")
        
    except Exception as e:
        logger.error(f"[sync_parsed_resume_data] Error: {str(e)}", exc_info=True)
        raise
```

Update method signatures to accept `resume_id` and `is_derived`:

```python
async def add_skill_to_candidate(
    self, 
    user_id: UUID, 
    skill_name: str, 
    proficiency: Optional[str] = None,
    resume_id: Optional[UUID] = None,  # NEW
    is_derived: bool = False  # NEW
):
    """Add skill to candidate with resume origin tracking."""
    # ... existing code ...
    candidate_skill = await self.repository.add_candidate_skill(
        user_id, 
        skill.id, 
        proficiency,
        resume_id=resume_id,  # PASS
        is_derived_from_resume=is_derived  # PASS
    )
```

---

### File 3: `app/modules/resume/service.py`

Update `process_resume()` to pass resume_id:

```python
async def process_resume(self, resume_id: UUID) -> Resume:
    """Process uploaded resume (called by worker)."""
    resume = await self.repository.get_resume_by_id(resume_id)
    if not resume:
        raise NotFoundException("Resume", str(resume_id))
    
    try:
        # Parse resume
        if resume.file_type == "pdf":
            parsed_data = ResumeParser.parse_pdf(resume.file_path)
        else:
            parsed_data = ResumeParser.parse_docx(resume.file_path)
        
        # Update resume with parsed data
        resume.parsed_data = parsed_data
        resume.status = "PARSED"
        updated_resume = await self.repository.update_resume(resume)
        
        # Sync extracted data to candidate profile WITH RESUME_ID
        try:
            candidate_service = CandidateService(self.db)
            await candidate_service.sync_parsed_resume_data(
                resume.user_id, 
                parsed_data,
                resume_id  # PASS RESUME_ID
            )
            logger.info(f"Successfully synced parsed resume data for resume_id: {resume_id}")
        except Exception as e:
            logger.warning(f"Failed to sync parsed resume data: {str(e)}", exc_info=True)
        
        return updated_resume
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}", exc_info=True)
        resume.status = "FAILED"
        await self.repository.update_resume(resume)
        raise


async def delete_resume(self, resume_id: UUID, user_id: UUID):
    """Delete resume and ALL derived data."""
    logger.info(f"Deleting resume_id: {resume_id} for user_id: {user_id}")
    
    resume = await self.repository.get_resume_by_id(resume_id)
    if not resume or resume.user_id != user_id:
        raise NotFoundException("Resume", str(resume_id))
    
    try:
        # Start transaction
        async with self.db.begin():
            # 1. Delete all candidate skills derived from this resume
            await self.repository.delete_resume_skills(resume_id)
            logger.info(f"Deleted skills for resume_id: {resume_id}")
            
            # 2. Delete all experiences derived from this resume
            await self.repository.delete_resume_experiences(resume_id)
            logger.info(f"Deleted experiences for resume_id: {resume_id}")
            
            # 3. Delete all educations derived from this resume
            await self.repository.delete_resume_educations(resume_id)
            logger.info(f"Deleted educations for resume_id: {resume_id}")
            
            # 4. Delete from S3
            await self.s3_client.delete_file(resume.s3_key)
            logger.info(f"Deleted file from S3 for resume_id: {resume_id}")
            
            # 5. Delete resume record
            await self.repository.delete_resume(resume_id)
            logger.info(f"Deleted resume record for resume_id: {resume_id}")
        
        # Log audit
        await log_audit(
            self.db,
            user_id,
            "RESUME_DELETED_WITH_DATA",
            "Resume",
            str(resume_id),
            {"details": "Cascaded delete of all derived data"}
        )
        
    except Exception as e:
        logger.error(f"Error deleting resume: {str(e)}", exc_info=True)
        raise
```

---

### File 4: `app/modules/resume/repository.py`

Add new delete methods:

```python
async def delete_resume_skills(self, resume_id: UUID) -> int:
    """Delete all candidate skills derived from this resume."""
    result = await self.db.execute(
        delete(CandidateSkill).where(
            CandidateSkill.resume_id == resume_id,
            CandidateSkill.is_derived_from_resume == True
        )
    )
    await self.db.commit()
    return result.rowcount


async def delete_resume_experiences(self, resume_id: UUID) -> int:
    """Delete all experiences derived from this resume."""
    result = await self.db.execute(
        delete(Experience).where(
            Experience.resume_id == resume_id,
            Experience.is_derived_from_resume == True
        )
    )
    await self.db.commit()
    return result.rowcount


async def delete_resume_educations(self, resume_id: UUID) -> int:
    """Delete all educations derived from this resume."""
    result = await self.db.execute(
        delete(Education).where(
            Education.resume_id == resume_id,
            Education.is_derived_from_resume == True
        )
    )
    await self.db.commit()
    return result.rowcount
```

---

### File 5: `app/modules/candidate/repository.py`

Update to support resume_id in add methods:

```python
async def add_candidate_skill(
    self, 
    user_id: UUID, 
    skill_id: UUID, 
    proficiency: Optional[str] = None,
    resume_id: Optional[UUID] = None,  # NEW
    is_derived_from_resume: bool = False  # NEW
) -> CandidateSkill:
    """Add skill to candidate."""
    candidate_skill = CandidateSkill(
        candidate_id=user_id,
        skill_id=skill_id,
        proficiency=proficiency,
        resume_id=resume_id,  # STORE
        is_derived_from_resume=is_derived_from_resume  # STORE
    )
    self.db.add(candidate_skill)
    await self.db.commit()
    await self.db.refresh(candidate_skill)
    return candidate_skill


async def create_experience(
    self, 
    user_id: UUID, 
    experience_data: dict,
    resume_id: Optional[UUID] = None,  # NEW
    is_derived_from_resume: bool = False  # NEW
) -> Experience:
    """Create experience."""
    experience = Experience(
        user_id=user_id,
        **experience_data,
        resume_id=resume_id,  # STORE
        is_derived_from_resume=is_derived_from_resume  # STORE
    )
    self.db.add(experience)
    await self.db.commit()
    await self.db.refresh(experience)
    return experience


async def create_education(
    self, 
    user_id: UUID, 
    education_data: dict,
    resume_id: Optional[UUID] = None,  # NEW
    is_derived_from_resume: bool = False  # NEW
) -> Education:
    """Create education."""
    education = Education(
        user_id=user_id,
        **education_data,
        resume_id=resume_id,  # STORE
        is_derived_from_resume=is_derived_from_resume  # STORE
    )
    self.db.add(education)
    await self.db.commit()
    await self.db.refresh(education)
    return education
```

---

## Migration Script

Create `backend/migrations/0002_add_resume_traceability.sql`:

```sql
-- Add resume_id column to candidate_skills
ALTER TABLE candidate_skills ADD COLUMN resume_id UUID NULL REFERENCES resumes(id) ON DELETE CASCADE;
ALTER TABLE candidate_skills ADD COLUMN is_derived_from_resume BOOLEAN NOT NULL DEFAULT false;
CREATE INDEX idx_candidate_skills_resume_id ON candidate_skills(resume_id);

-- Add resume_id column to experiences
ALTER TABLE experiences ADD COLUMN resume_id UUID NULL REFERENCES resumes(id) ON DELETE CASCADE;
ALTER TABLE experiences ADD COLUMN is_derived_from_resume BOOLEAN NOT NULL DEFAULT false;
CREATE INDEX idx_experiences_resume_id ON experiences(resume_id);

-- Add resume_id column to educations
ALTER TABLE educations ADD COLUMN resume_id UUID NULL REFERENCES resumes(id) ON DELETE CASCADE;
ALTER TABLE educations ADD COLUMN is_derived_from_resume BOOLEAN NOT NULL DEFAULT false;
CREATE INDEX idx_educations_resume_id ON educations(resume_id);
```

---

## Expected Behavior After Fix

### Scenario: User uploads resume, it gets parsed, then deletes it

**Before:**
- Resume deleted ✓
- Skills still visible ✗
- Experiences still visible ✗
- Education still visible ✗

**After:**
- Resume deleted ✓
- All skills linked to that resume deleted ✓
- All experiences linked to that resume deleted ✓
- All educations linked to that resume deleted ✓
- UI immediately reflects accurate state ✓

### Scenario: User has 2 resumes, deletes one

- Only data from resume_id=X is deleted
- Data from resume_id=Y remains
- UI shows only resume_Y's data

---

## Testing Checklist

- [ ] Upload resume → verify resume_id stored in skills/experiences/educations
- [ ] Delete resume → verify all linked data deleted from DB
- [ ] Delete resume → verify UI immediately shows empty profile
- [ ] Upload 2 resumes → delete one → verify other data remains
- [ ] Test with manual skill entry + parsed data mixed
- [ ] Verify orphaned data (old records) handled correctly

---

## Rollback Plan

If needed, set `is_derived_from_resume=false` for all records to treat them as manual entries:

```sql
UPDATE candidate_skills SET is_derived_from_resume = false WHERE is_derived_from_resume IS NULL;
UPDATE experiences SET is_derived_from_resume = false WHERE is_derived_from_resume IS NULL;
UPDATE educations SET is_derived_from_resume = false WHERE is_derived_from_resume IS NULL;
```

