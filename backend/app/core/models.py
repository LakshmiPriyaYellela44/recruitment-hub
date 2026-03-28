from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Enum, Integer, Text, JSON, ForeignKey, Index, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import uuid
import enum
from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    CANDIDATE = "CANDIDATE"
    RECRUITER = "RECRUITER"


class SubscriptionType(str, enum.Enum):
    BASIC = "BASIC"
    PRO = "PRO"


class User(Base):
    __tablename__ = "users"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    role = Column(Enum(UserRole), nullable=False, index=True)
    subscription_type = Column(Enum(SubscriptionType), default=SubscriptionType.BASIC, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Audit columns
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    # Relationships
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    skills = relationship("Skill", secondary="candidate_skills", back_populates="candidates")
    experiences = relationship("Experience", back_populates="candidate", cascade="all, delete-orphan")
    educations = relationship("Education", back_populates="candidate", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", foreign_keys="AuditLog.user_id", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx
    s3_key = Column(String(500), nullable=True)
    parsed_data = Column(JSON, nullable=True)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, PARSING, PARSED, FAILED
    is_active = Column(Boolean, default=True, nullable=False, index=True)  # Resume versioning: only show data from active resume
    
    # Audit columns
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    # Relationships
    candidate = relationship("User", back_populates="resumes")


class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=True)
    
    # Audit columns
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    # Relationships
    candidates = relationship("User", secondary="candidate_skills", back_populates="skills")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    skill_id = Column(PGUUID(as_uuid=True), ForeignKey("skills.id"), nullable=False, index=True)
    resume_id = Column(PGUUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True, index=True)
    proficiency = Column(String(50), nullable=True)  # BEGINNER, INTERMEDIATE, ADVANCED, EXPERT
    is_derived_from_resume = Column(Boolean, default=False, nullable=False)
    
    # Audit columns
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)


class Experience(Base):
    __tablename__ = "experiences"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    resume_id = Column(PGUUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True, index=True)
    job_title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_current = Column(Boolean, default=False)
    years = Column(Integer, nullable=True, index=True)
    is_derived_from_resume = Column(Boolean, default=False, nullable=False)
    
    # Audit columns
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    # Relationships
    candidate = relationship("User", back_populates="experiences")


class Education(Base):
    __tablename__ = "educations"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    resume_id = Column(PGUUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True, index=True)
    institution = Column(String(255), nullable=False)
    degree = Column(String(100), nullable=False, index=True)  # Bachelor, Master, PhD, etc.
    field_of_study = Column(String(255), nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    is_derived_from_resume = Column(Boolean, default=False, nullable=False)
    
    # Audit columns
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    # Relationships
    candidate = relationship("User", back_populates="educations")


class EmailTemplate(Base):
    __tablename__ = "email_templates"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)  # Template with {{placeholders}}
    description = Column(Text, nullable=True)
    placeholders = Column(JSON, nullable=False, default={})  # {"company_name": "string", "location": "string", ...}
    required_fields = Column(JSON, nullable=False, default=[])  # List of required field names
    is_active = Column(Boolean, default=True)
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Audit columns
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class EmailSent(Base):
    __tablename__ = "emails_sent"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    to_email = Column(String(255), nullable=False)
    to_candidate_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    template_id = Column(PGUUID(as_uuid=True), ForeignKey("email_templates.id"), nullable=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    dynamic_data = Column(JSON, nullable=True)  # Stores the dynamic values that were used
    status = Column(String(50), default="SENT", nullable=False)  # SENT, FAILED, BOUNCED
    
    # Audit columns
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(500), nullable=False)
    changes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class PasswordReset(Base):
    __tablename__ = "password_resets"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    reset_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User")
