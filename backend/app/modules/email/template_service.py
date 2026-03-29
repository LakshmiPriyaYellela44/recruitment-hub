from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import EmailTemplate, EmailSent, User
from app.core.exceptions import NotFoundException, ValidationException, AuthorizationException
from app.core.models import SubscriptionType
from app.aws_services.ses_client import SESClient
from typing import Dict, Optional
from uuid import UUID
import logging
import re
from sqlalchemy import select

logger = logging.getLogger(__name__)


class EmailTemplateService:
    """Service for email template operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ses_client = SESClient()
    
    async def get_recruiter_templates(self, recruiter_id: UUID) -> list:
        """Get available templates for recruiters (PRO only)."""
        from sqlalchemy import select
        
        result = await self.db.execute(
            select(EmailTemplate).filter(EmailTemplate.is_active == True)
        )
        return result.scalars().all()
    
    def render_template(self, template: EmailTemplate, dynamic_data: Dict[str, str]) -> tuple[str, str]:
        """Render template with dynamic data and return (subject, body)."""
        import json
        
        # Parse placeholders if they're stored as JSON string
        placeholders_data = template.placeholders
        if isinstance(placeholders_data, str):
            try:
                placeholders_dict = json.loads(placeholders_data)
            except (json.JSONDecodeError, TypeError):
                # If it's not valid JSON, treat it as empty
                placeholders_dict = {}
        elif isinstance(placeholders_data, list):
            # If it's a list, convert to dict with all required
            placeholders_dict = {name: {"required": True} for name in placeholders_data}
        else:
            # Assume it's already a dict
            placeholders_dict = placeholders_data or {}
        
        # Get list of required placeholder names
        # A placeholder is required if:
        # 1. It's a key in the placeholders dict (all are considered required by default)
        # 2. Or explicitly marked as required in its config
        required_placeholders = []
        for name, config in placeholders_dict.items():
            if isinstance(config, dict):
                # If it's a config dict, check the "required" field (default True)
                if config.get("required", True):
                    required_placeholders.append(name)
            else:
                # If it's not a dict, treat the key itself as a required placeholder
                required_placeholders.append(name)
        
        # Also consider any placeholder name found in subject/body that's in dynamic_data
        # This ensures backward compatibility
        import re
        placeholder_pattern = r'\{\{([^}]+)\}\}'
        subject_placeholders = set(re.findall(placeholder_pattern, template.subject))
        body_placeholders = set(re.findall(placeholder_pattern, template.body))
        all_template_placeholders = subject_placeholders | body_placeholders
        
        # Required are those that appear in template but aren't in dynamic_data
        missing = [p for p in all_template_placeholders if p not in dynamic_data or (dynamic_data[p] is None or dynamic_data[p] == '')]
        if missing:
            raise ValidationException(
                f"Missing required fields: {', '.join(missing)}",
                {"missing_fields": missing}
            )
        
        # Render subject
        subject = template.subject
        for placeholder, value in dynamic_data.items():
            subject = subject.replace(f"{{{{{placeholder}}}}}", str(value) if value is not None else "")
        
        # Render body
        body = template.body
        for placeholder, value in dynamic_data.items():
            body = body.replace(f"{{{{{placeholder}}}}}", str(value) if value is not None else "")
        
        return subject, body
    
    async def send_email_with_template(
        self,
        recruiter_id: UUID,
        recruiter_subscription: SubscriptionType,
        template_id: UUID,
        candidate_id: UUID,
        candidate_email: str,
        dynamic_data: Dict[str, str]
    ) -> dict:
        """Send email to candidate using template with dynamic data."""
        # Check subscription
        if recruiter_subscription != SubscriptionType.PRO:
            raise AuthorizationException(
                "Sending templated emails requires PRO subscription"
            )
        
        # Get template
        result = await self.db.execute(
            select(EmailTemplate).filter(EmailTemplate.id == template_id)
        )
        template = result.scalars().first()
        if not template:
            raise NotFoundException("EmailTemplate", str(template_id))
        
        # Get parsed resume email if available (prefer parsed resume email over provided email)
        from app.core.models import Resume
        resume_result = await self.db.execute(
            select(Resume)
            .filter(Resume.user_id == candidate_id)
            .filter(Resume.status == "PARSED")
            .order_by(Resume.created_at.desc())
            .limit(1)
        )
        resume = resume_result.scalars().first()
        
        # Extract email from parsed resume data if available
        parsed_email = None
        if resume and resume.parsed_data:
            parsed_email = resume.parsed_data.get("email") if isinstance(resume.parsed_data, dict) else None
        
        # Use parsed email if available, otherwise fall back to provided candidate_email
        email_to_send = parsed_email if parsed_email else candidate_email
        
        if not email_to_send:
            raise ValidationException(
                f"No email found for candidate. Please provide a valid email address.",
                {"candidate_id": str(candidate_id)}
            )
        
        # Render template
        subject, body = self.render_template(template, dynamic_data)
        
        # Send via SES
        try:
            email_id = await self.ses_client.send_email(
                to_addresses=[email_to_send],
                subject=subject,
                body=body
            )
        except Exception as e:
            # Catch SES errors and re-raise as validation error with user-friendly message
            error_msg = str(e)
            
            if "UnverifiedEmailAddress" in error_msg or "not verified" in error_msg:
                logger.warning(
                    f"Email not sent - recipient address not verified in AWS SES",
                    extra={
                        "candidate_email": email_to_send,
                        "candidate_id": str(candidate_id),
                        "recruiter_id": str(recruiter_id),
                    }
                )
                raise ValidationException(
                    f"Cannot send email to {email_to_send} - this email address is not verified in AWS SES. "
                    f"Please verify this email address in the AWS SES console before sending emails.",
                    {"unverified_email": email_to_send, "aws_console": "https://console.aws.amazon.com/sesu/"}
                )
            else:
                logger.error(
                    f"Failed to send email via SES",
                    extra={
                        "candidate_email": email_to_send,
                        "candidate_id": str(candidate_id),
                        "error": error_msg
                    }
                )
                raise ValidationException(
                    f"Failed to send email: {error_msg}",
                    {"error_details": error_msg}
                )
        
        # Log email
        email_sent = EmailSent(
            from_user_id=recruiter_id,
            to_email=email_to_send,
            to_candidate_id=candidate_id,
            template_id=template_id,
            subject=subject,
            body=body,
            dynamic_data=dynamic_data,
            status="SENT"
        )
        
        self.db.add(email_sent)
        await self.db.commit()
        await self.db.refresh(email_sent)
        
        logger.info(
            f"Email sent successfully",
            extra={
                "email_id": email_id,
                "recruiter_id": str(recruiter_id),
                "candidate_id": str(candidate_id),
                "template_id": str(template_id)
            }
        )
        
        return {
            "message": "Email sent successfully",
            "email_id": email_id,
            "message_id": email_id,  # For backward compatibility
            "recipient": email_to_send,
            "template_name": template.name
        }
