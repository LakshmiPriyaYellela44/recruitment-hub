from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID


class CandidateSearchFilters(BaseModel):
    skills: Optional[List[str]] = None
    keyword: Optional[str] = None
    experience: Optional[str] = None  # Search by job title, company, description
    education: Optional[str] = None  # Search by degree, institution, field of study


class SendEmailRequest(BaseModel):
    candidate_id: UUID
    subject: str
    body: str


class SendEmailWithTemplateRequest(BaseModel):
    template_id: UUID
    candidate_id: UUID
    candidate_email: str
    dynamic_data: Dict[str, str] = Field(..., description="Dynamic values for template placeholders")


class CandidateSearchResult(BaseModel):
    id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    skills: List[str] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmailResponse(BaseModel):
    message: str
    email_sent_log_id: Optional[UUID]
