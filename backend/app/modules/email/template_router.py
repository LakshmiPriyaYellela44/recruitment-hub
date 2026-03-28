from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.utils.auth_utils import get_current_user, require_admin
from pydantic import BaseModel
from typing import Dict, List, Optional
from uuid import UUID
from app.core.models import EmailTemplate

router = APIRouter(prefix="/admin/email-templates", tags=["admin-templates"])


class PlaceholderDef(BaseModel):
    name: str
    type: str  # string, number, date, email, etc.
    required: bool = True
    description: Optional[str] = None


class CreateEmailTemplateRequest(BaseModel):
    name: str
    subject: str
    body: str  # Template with {{placeholder}} syntax
    description: Optional[str] = None
    placeholders: List[PlaceholderDef] = []


class EmailTemplateResponse(BaseModel):
    id: UUID
    name: str
    subject: str
    body: str
    description: Optional[str]
    placeholders: Dict
    is_active: bool
    created_at: str
    
    class Config:
        from_attributes = True


@router.post("/", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_email_template(
    request: CreateEmailTemplateRequest,
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Create new email template."""
    # Convert placeholders list to dict
    placeholders_dict = {p.name: {"type": p.type, "required": p.required, "description": p.description} for p in request.placeholders}
    
    template = EmailTemplate(
        name=request.name,
        subject=request.subject,
        body=request.body,
        description=request.description,
        placeholders=placeholders_dict,
        created_by=current_user.id
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return template


@router.get("/", response_model=List[EmailTemplateResponse])
async def list_email_templates(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin: List all email templates."""
    from sqlalchemy import select
    
    query = select(EmailTemplate).filter(
        EmailTemplate.is_active == True
    ).offset(offset).limit(limit)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return templates


@router.get("/{template_id}", response_model=EmailTemplateResponse)
async def get_email_template(
    template_id: UUID,
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Get specific email template."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(EmailTemplate).filter(EmailTemplate.id == template_id)
    )
    template = result.scalars().first()
    
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    return template
