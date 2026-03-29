"""Seed data for database initialization."""
import logging
from app.core.models import EmailTemplate
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def seed_email_templates(session: AsyncSession):
    """Seed default email templates."""
    try:
        # Check if templates already exist
        result = await session.execute(select(func.count(EmailTemplate.id)))
        template_count = result.scalar() or 0
        
        if template_count > 0:
            logger.info(f"✓ Email templates already exist ({template_count} templates)")
            return
        
        logger.info("Seeding email templates...")
        
        # Template 1: Job Interview Invitation
        template1 = EmailTemplate(
            name="Interview Invitation",
            subject="You're Invited to Interview at {{company_name}}",
            body="""Dear {{candidate_name}},

We are pleased to invite you to interview for the {{position}} role at {{company_name}}.

Interview Details:
- Date & Time: {{interview_date}} at {{interview_time}}
- Duration: {{duration}} minutes
- Location/Format: {{interview_location}}
- Interviewer: {{interviewer_name}}

Please confirm your availability by replying to this email. If you have any questions, feel free to reach out.

Looking forward to meeting you!

Best regards,
{{recruiter_name}}
Recruitment Team""",
            description="Invitation email for scheduled interviews",
            placeholders={
                "candidate_name": {"type": "string", "required": True, "description": "Full name of the candidate"},
                "company_name": {"type": "string", "required": True, "description": "Name of the company"},
                "position": {"type": "string", "required": True, "description": "Job position title"},
                "interview_date": {"type": "date", "required": True, "description": "Interview date"},
                "interview_time": {"type": "string", "required": True, "description": "Interview time"},
                "duration": {"type": "number", "required": False, "description": "Interview duration in minutes"},
                "interview_location": {"type": "string", "required": True, "description": "Office location or video call link"},
                "interviewer_name": {"type": "string", "required": False, "description": "Name of interviewer"},
                "recruiter_name": {"type": "string", "required": False, "description": "Recruiter's name"}
            },
            is_active=True
        )
        
        # Template 2: Job Offer Letter
        template2 = EmailTemplate(
            name="Job Offer",
            subject="Job Offer - {{position}} at {{company_name}}",
            body="""Dear {{candidate_name}},

Congratulations! We are pleased to extend an offer for the {{position}} position at {{company_name}}.

Position Details:
- Position: {{position}}
- Department: {{department}}
- Salary: {{salary}}
- Start Date: {{start_date}}
- Location: {{work_location}}

Benefits:
{{benefits}}

Please review the attached offer letter and confirm your acceptance by {{response_deadline}}.

If you have any questions, please don't hesitate to contact me.

Best regards,
{{recruiter_name}}
{{company_name}} Recruitment Team""",
            description="Job offer letter",
            placeholders={
                "candidate_name": {"type": "string", "required": True},
                "position": {"type": "string", "required": True},
                "company_name": {"type": "string", "required": True},
                "department": {"type": "string", "required": False},
                "salary": {"type": "string", "required": True},
                "start_date": {"type": "date", "required": True},
                "work_location": {"type": "string", "required": False},
                "benefits": {"type": "string", "required": False},
                "response_deadline": {"type": "date", "required": True},
                "recruiter_name": {"type": "string", "required": False}
            },
            is_active=True
        )
        
        # Template 3: Follow-up After Interview
        template3 = EmailTemplate(
            name="Interview Follow-up",
            subject="Thank You for Your Interview",
            body="""Dear {{candidate_name}},

Thank you for taking the time to interview with us for the {{position}} position. We appreciate your interest in {{company_name}}.

We enjoyed learning about your background and experience in {{key_discussion_point}}.

Our team is currently reviewing all candidates and we will be in touch with an update by {{decision_date}}.

If you have any questions in the meantime, feel free to reach out.

Best regards,
{{recruiter_name}}
{{company_name}} Recruitment Team""",
            description="Follow-up email after interview",
            placeholders={
                "candidate_name": {"type": "string", "required": True},
                "position": {"type": "string", "required": True},
                "company_name": {"type": "string", "required": True},
                "key_discussion_point": {"type": "string", "required": False},
                "decision_date": {"type": "date", "required": True},
                "recruiter_name": {"type": "string", "required": False}
            },
            is_active=True
        )
        
        # Template 4: Rejection Email
        template4 = EmailTemplate(
            name="Rejection Notice",
            subject="Application Status for {{position}} at {{company_name}}",
            body="""Dear {{candidate_name}},

Thank you for your interest in the {{position}} position at {{company_name}} and for taking the time to interview with us.

After careful consideration, we have decided to move forward with other candidates who more closely match our current needs.

We were impressed with your {{impressive_quality}} and would encourage you to apply for future opportunities that align with your background.

We wish you the best in your job search.

Best regards,
{{recruiter_name}}
{{company_name}} Recruitment Team""",
            description="Rejection email to candidates",
            placeholders={
                "candidate_name": {"type": "string", "required": True},
                "position": {"type": "string", "required": True},
                "company_name": {"type": "string", "required": True},
                "impressive_quality": {"type": "string", "required": False},
                "recruiter_name": {"type": "string", "required": False}
            },
            is_active=True
        )
        
        # Template 5: Initial Outreach/Introduction
        template5 = EmailTemplate(
            name="Candidate Outreach",
            subject="Exciting {{position}} Opportunity at {{company_name}}",
            body="""Hi {{candidate_name}},

I hope this email finds you well! I came across your profile and was impressed by your experience in {{field_of_expertise}}.

We currently have an exciting opportunity for a {{position}} role at {{company_name}}. Based on your background, I believe you could be a great fit.

About the Role:
- Position: {{position}}
- Location: {{location}}
- Key Responsibilities: {{key_responsibilities}}

Would you be interested in learning more about this opportunity? I'd love to have a brief conversation to discuss how this role could be a great next step in your career.

Feel free to reach out at your convenience.

Best regards,
{{recruiter_name}}
{{company_name}}
{{contact_info}}""",
            description="Initial outreach email to potential candidates",
            placeholders={
                "candidate_name": {"type": "string", "required": True},
                "field_of_expertise": {"type": "string", "required": False},
                "position": {"type": "string", "required": True},
                "company_name": {"type": "string", "required": True},
                "location": {"type": "string", "required": False},
                "key_responsibilities": {"type": "string", "required": False},
                "recruiter_name": {"type": "string", "required": False},
                "contact_info": {"type": "string", "required": False}
            },
            is_active=True
        )
        
        session.add(template1)
        session.add(template2)
        session.add(template3)
        session.add(template4)
        session.add(template5)
        
        await session.commit()
        
        logger.info("✓ Email templates seeded successfully (5 templates created)")
        logger.info("  - Interview Invitation")
        logger.info("  - Job Offer")
        logger.info("  - Interview Follow-up")
        logger.info("  - Rejection Notice")
        logger.info("  - Candidate Outreach")
        
    except Exception as e:
        logger.error(f"Failed to seed email templates: {str(e)}", exc_info=True)
        raise
