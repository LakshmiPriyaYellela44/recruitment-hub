from pydantic import BaseModel
from typing import Optional


class ResumeUploadResponse(BaseModel):
    id: str
    file_name: str
    file_type: str
    status: str
    message: str
    s3_key: str = None  # S3 storage key


class ResumeParsedData(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: list = []
    experiences: list = []
    educations: list = []
    summary: Optional[str] = None
