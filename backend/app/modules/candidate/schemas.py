from pydantic import BaseModel, Field
from typing import Optional, List, Union, Dict
from datetime import datetime
from uuid import UUID


# Skill Schemas
class SkillBase(BaseModel):
    name: str
    category: Optional[str] = None


class SkillCreate(SkillBase):
    pass


class SkillResponse(SkillBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


# Experience Schemas
class ExperienceBase(BaseModel):
    job_title: str
    company_name: str
    location: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_current: bool = False


class ExperienceCreate(ExperienceBase):
    pass


class ExperienceUpdate(ExperienceBase):
    pass


class ExperienceResponse(ExperienceBase):
    id: UUID
    user_id: UUID
    years: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Education Schemas
class EducationBase(BaseModel):
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: Optional[str] = None


class EducationCreate(EducationBase):
    pass


class EducationUpdate(EducationBase):
    pass


class EducationResponse(EducationBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Resume Schemas
class ResumeResponse(BaseModel):
    id: UUID
    file_name: str
    file_type: str
    status: str
    parsed_data: Optional[dict] = None
    s3_key: Optional[str] = None
    created_at: datetime
    is_latest: bool = False  # Flag indicating if this is the latest resume
    
    class Config:
        from_attributes = True


# Candidate Profile
class CandidateProfileResponse(BaseModel):
    id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    created_at: datetime
    resumes: List[ResumeResponse] = []
    skills: Union[Dict[str, List[SkillResponse]], List[SkillResponse]] = Field(default_factory=dict)  # Default to empty dict
    experiences: List[ExperienceResponse] = []
    educations: List[EducationResponse] = []
    
    class Config:
        from_attributes = True
