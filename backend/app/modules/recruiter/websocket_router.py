"""WebSocket router for recruiter email sending with live status updates."""
import logging
import json
from fastapi import APIRouter, WebSocket, Depends, status, Query
from uuid import UUID
from app.core.database import get_db
from app.utils.auth_utils import get_current_user_ws
from app.modules.email.template_service import EmailTemplateService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recruiters", tags=["recruiters-websocket"])


@router.websocket("/ws/send-email/{candidate_id}")
async def websocket_send_email(
    websocket: WebSocket,
    candidate_id: str,
    template_id: str = Query(...),
    candidate_email: str = Query(...),
    dynamic_data: str = Query("{}"),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for sending email with template and real-time status updates.
    
    Query parameters:
    - template_id: Email template UUID
    - candidate_email: Recipient email address
    - dynamic_data: JSON string with template placeholders (default: "{}")
    - token: JWT token (in query params)
    
    Status messages sent via WebSocket:
    {
        "status": "sending" | "success" | "error",
        "message": "descriptive message",
        "message_id": "ses-message-id" (only on success),
        "error": "error details" (only on error)
    }
    """
    logger.info(f"[WebSocket] New connection attempt for candidate: {candidate_id}")
    logger.info(f"[WebSocket] Query params: {dict(websocket.query_params)}")
    logger.info(f"[WebSocket] Template ID: {template_id}")
    logger.info(f"[WebSocket] Candidate Email: {candidate_email}")
    logger.info(f"[WebSocket] Dynamic Data: {dynamic_data}")
    
    # Get current user
    try:
        logger.info("[WebSocket] Attempting to authenticate user...")
        current_user = await get_current_user_ws(websocket)
        logger.info(f"[WebSocket] User authenticated: {current_user.email}")
    except Exception as e:
        logger.error(f"[WebSocket] Authentication failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(e))
        return
    
    # Check if recruiter
    if current_user.role.value != "RECRUITER":
        logger.error(f"[WebSocket] User is not recruiter: {current_user.role.value}")
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Only recruiters can send emails"
        )
        return
    
    # Check PRO subscription
    if current_user.subscription_type != "PRO":
        logger.error(f"[WebSocket] User does not have PRO subscription: {current_user.subscription_type}")
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="PRO subscription required to send emails"
        )
        return
    
    await websocket.accept()
    logger.info(f"[WebSocket] Connection accepted for recruiter: {current_user.email}")
    
    try:
        # Validate IDs
        try:
            candidate_id_uuid = UUID(candidate_id)
            template_id_uuid = UUID(template_id)
        except ValueError as ve:
            logger.error(f"[WebSocket] Invalid UUID format: {ve}")
            await websocket.send_json({
                "status": "error",
                "message": "Invalid ID format",
                "error": "candidate_id and template_id must be valid UUIDs"
            })
            await websocket.close(code=status.WS_1011_SERVER_ERROR)
            return
        
        # Parse dynamic data
        try:
            import json as json_module
            dynamic_data_dict = json_module.loads(dynamic_data) if dynamic_data else {}
        except json.JSONDecodeError:
            logger.error(f"[WebSocket] Invalid JSON in dynamic_data: {dynamic_data}")
            await websocket.send_json({
                "status": "error",
                "message": "Invalid data format",
                "error": "dynamic_data must be valid JSON"
            })
            await websocket.close(code=status.WS_1011_SERVER_ERROR)
            return
        
        # Send initial status
        logger.info(f"[WebSocket] Sending 'preparing' status")
        await websocket.send_json({
            "status": "preparing",
            "message": f"Preparing to send email using template '{template_id}'..."
        })
        
        # Add small delay to ensure client receives preparing message
        import asyncio
        await asyncio.sleep(0.5)
        
        # Send status update before validation
        logger.info(f"[WebSocket] Validating template and recipient...")
        await websocket.send_json({
            "status": "validating",
            "message": "Validating template and recipient information..."
        })
        
        await asyncio.sleep(0.3)
        
        # Send email using template service
        logger.info(f"[WebSocket] Calling EmailTemplateService to send email")
        await websocket.send_json({
            "status": "sending",
            "message": "Sending email via AWS SES..."
        })
        
        service = EmailTemplateService(db)
        result = await service.send_email_with_template(
            current_user.id,
            current_user.subscription_type,
            template_id_uuid,
            candidate_id_uuid,
            candidate_email,
            dynamic_data_dict
        )
        
        # Send success status
        logger.info(f"[WebSocket] Email sent successfully with result: {result}")
        await websocket.send_json({
            "status": "success",
            "message": "Email sent successfully!",
            "message_id": result.get("message_id"),
            "timestamp": result.get("timestamp")
        })
        
    except Exception as e:
        logger.error(f"[WebSocket] Error sending email: {e}", exc_info=True)
        
        # Determine error message with more specific guidance
        error_msg = str(e)
        user_message = "Failed to send email"
        
        if "not verified" in error_msg.lower():
            user_message = "Email address not verified in AWS SES"
            error_msg = f"The recipient email address needs to be verified in AWS SES. Contact your administrator to verify '{candidate_email}'."
        elif "emailalreadyexists" in error_msg.lower() or "already exists" in error_msg.lower():
            user_message = "Email already sent"
            error_msg = "This email has already been sent to this candidate recently."
        elif "pro" in error_msg.lower() or "subscription" in error_msg.lower():
            user_message = "Upgrade required"
            error_msg = "Your subscription does not support email sending. Please upgrade to PRO subscription."
        elif "not found" in error_msg.lower():
            user_message = "Template or candidate not found"
            error_msg = "The email template or candidate information could not be found. Please refresh and try again."
        elif "invalid data" in error_msg.lower():
            user_message = "Invalid template data"
            error_msg = "One or more required fields are missing or invalid. Please check your form data."
        elif "timeout" in error_msg.lower():
            user_message = "Operation timeout"
            error_msg = "The email sending operation took too long. Please try again."
        elif "connection" in error_msg.lower():
            user_message = "Connection error"
            error_msg = "Failed to connect to email service. Please check your internet connection and try again."
        else:
            # Generic error with first 200 chars
            error_msg = error_msg[:200]
        
        logger.info(f"[WebSocket] Sending error status: {error_msg}")
        await websocket.send_json({
            "status": "error",
            "message": user_message,
            "error": error_msg
        })
    
    finally:
        try:
            await websocket.close()
            logger.info("[WebSocket] Connection closed")
        except Exception as e:
            logger.debug(f"[WebSocket] Error closing websocket: {e}")
