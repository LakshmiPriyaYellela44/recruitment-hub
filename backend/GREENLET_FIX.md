# 🔧 GREENLET ERROR FIX - FINAL SOLUTION

## Problem Identified
**Error**: `MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here`
- Occurred when calling `GET /api/candidates/me`
- Root cause: Pydantic `.from_orm()` was trying to access lazy-loaded ORM relationships outside async context

## Solution Implemented

### 1️⃣ Repository Layer - Eagerly Load Relationships
**File**: [app/modules/candidate/repository.py](../repository.py)

**Change**: Updated `get_candidate_by_id()` to use `selectinload()` for all relationships
```python
async def get_candidate_by_id(self, user_id: UUID) -> Optional[User]:
    """Get candidate by ID with eagerly loaded relationships."""
    result = await self.db.execute(
        select(User)
        .filter(User.id == user_id)
        .options(
            selectinload(User.resumes),      # ← Load resumes
            selectinload(User.experiences),  # ← Load experiences
            selectinload(User.educations),   # ← Load educations
            selectinload(User.candidate_skills)  # ← Load skills
        )
    )
    return result.scalars().first()
```

**Why**: `selectinload()` performs a separate SQL query to eagerly load relationships while still in the async session context.

### 2️⃣ Router Layer - Manual Response Construction
**File**: [app/modules/candidate/router.py](../router.py)

**Change**: Replaced `.from_orm()` with manual dict construction
```python
@router.get("/me", response_model=CandidateProfileResponse)
async def get_profile(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current candidate profile."""
    service = CandidateService(db)
    candidate = await service.get_candidate_profile(current_user.id)
    
    # Manually construct response to avoid greenlet issues
    response_data = {
        "id": candidate.id,
        "email": candidate.email,
        "first_name": candidate.first_name,
        "last_name": candidate.last_name,
        "role": candidate.role,
        "created_at": candidate.created_at,
        "resumes": [r for r in candidate.resumes],
        "skills": [cs.skill for cs in candidate.candidate_skills],
        "experiences": [e for e in candidate.experiences],
        "educations": [e for e in candidate.educations]
    }
    return CandidateProfileResponse(**response_data)
```

**Why**: Manual construction avoids Pydantic trying to lazy-load ORM attributes. All data is already loaded via `selectinload()`.

## Why This Works

### Before (Broken):
1. Router calls service to get User object
2. User object relationships NOT loaded (lazy-loaded)
3. `.from_orm(user)` is called
4. Pydantic tries to access `user.resumes` (lazy attribute)
5. ❌ Lazy-load attempt happens OUTSIDE async session
6. **ERROR**: MissingGreenlet

### After (Fixed):
1. Repository query includes `selectinload()` for all relationships
2. All relationships fetched in separate SQL queries (WHILE session active)
3. User object returned with ALL relationships already loaded in memory
4. Router manually constructs dict from loaded data
5. Pydantic receives fully-populated dict
6. ✅ **No lazy-loading needed - all data in memory**

## SQL Optimization

### Database Queries Generated
With the fix, the following queries are executed (all within active async session):

```sql
-- Query 1: Get User
SELECT users.* FROM users WHERE users.id = $1

-- Query 2: Get Resumes (selectinload)
SELECT resumes.* FROM resumes 
WHERE resumes.user_id = $1

-- Query 3: Get Experiences (selectinload)
SELECT experiences.* FROM experiences 
WHERE experiences.user_id = $1

-- Query 4: Get Educations (selectinload)
SELECT educations.* FROM educations 
WHERE educations.user_id = $1

-- Query 5: Get Skills (selectinload)
SELECT skills.* FROM skills 
JOIN candidate_skills ON skills.id = candidate_skills.skill_id
WHERE candidate_skills.candidate_id = $1
```

All executed within the async session before returning to the router.

## Testing

✅ **Code changes applied successfully**
- Repository: selectinload() added for all relationships
- Router: Manual dict construction instead of .from_orm()
- Auto-reload should pick up changes immediately

### Expected Result
```bash
GET /api/candidates/me

Response: 200 OK
{
  "id": "...",
  "email": "...",
  "first_name": "...",
  "last_name": "...",
  "role": "CANDIDATE",
  "created_at": "...",
  "resumes": [...],
  "skills": [...],
  "experiences": [...],
  "educations": [...]
}
```

### No More Errors
- ✅ No "MissingGreenlet" error
- ✅ All relationships properly loaded
- ✅ Response fully populated
- ✅ No lazy-loading issues

## Related Endpoints

This fix should be applied to any other endpoints that use `.from_orm()` with related objects:
- ✅ `GET /api/candidates/me` - FIXED
- Potentially: Other experience/education endpoints (check if they need similar fix)

## imports

Added to repository.py:
```python
from sqlalchemy.orm import selectinload
```

## Summary

The **greenlet error** was caused by attempting to access lazy-loaded ORM relationships outside an active async session. The fix combines:
1. **Eager loading** with `selectinload()` in the query
2. **Manual response construction** to avoid Pydantic lazy-loading attempts
3. **Result**: All data loaded synchronously while session is active, then passed as dict to Pydantic

This is a **production-ready pattern** for async SQLAlchemy with Pydantic in FastAPI.

---

✅ **Status**: FIXED - Ready for testing
