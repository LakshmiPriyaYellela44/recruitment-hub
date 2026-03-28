"""Real SES client using boto3."""
import logging
from typing import Optional, List, Dict, Any
import aioboto3
from botocore.exceptions import ClientError
from app.core.config import settings

logger = logging.getLogger(__name__)


class SESClient:
    """Real SES client using boto3."""
    
    def __init__(self):
        """Initialize SES client."""
        self.from_address = settings.SES_FROM_EMAIL
        self.region = settings.AWS_REGION
        
        # Create session
        self.session = aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=self.region
        )
        logger.info(f"SESClient initialized for sender: {self.from_address} in region: {self.region}")
    
    async def send_email(
        self,
        to_addresses: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_address: Optional[str] = None
    ) -> str:
        """
        Send email via SES.
        
        Args:
            to_addresses: List of recipient email addresses
            subject: Email subject
            body: Email body (plain text)
            html_body: Email body (HTML, optional)
            from_address: Sender address (optional, uses default if not provided)
        
        Returns:
            SES MessageId
        
        Raises:
            ClientError: If email sending fails
        """
        if not from_address:
            from_address = self.from_address
        
        try:
            async with self.session.client('ses') as ses:
                response = await ses.send_email(
                    Source=from_address,
                    Destination={'ToAddresses': to_addresses},
                    Message={
                        'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                        'Body': {
                            'Text': {'Data': body, 'Charset': 'UTF-8'},
                            **(
                                {'Html': {'Data': html_body, 'Charset': 'UTF-8'}}
                                if html_body
                                else {}
                            )
                        }
                    }
                )
            
            message_id = response['MessageId']
            logger.info(
                f"Email sent via SES",
                extra={
                    "message_id": message_id,
                    "to_count": len(to_addresses),
                    "subject": subject[:50],
                    "from_address": from_address
                }
            )
            return message_id
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'MessageRejected':
                if 'not verified' in error_message.lower():
                    logger.error(
                        f"SES MessageRejected - Email address not verified",
                        extra={
                            "to_addresses": to_addresses,
                            "from_address": from_address,
                            "error_message": error_message
                        }
                    )
                    # Re-raise with more informative message
                    raise ClientError(
                        {
                            'Error': {
                                'Code': 'UnverifiedEmailAddress',
                                'Message': f"Email address not verified in AWS SES. To send emails, verify the recipient address in AWS SES console. Unverified: {', '.join(to_addresses)}"
                            }
                        },
                        'SendEmail'
                    )
                else:
                    logger.error(f"SES MessageRejected: {error_message}")
            else:
                logger.error(f"SES send error ({error_code}): {error_message}")
            
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}", exc_info=True)
            raise
    
    async def get_send_quota(self) -> Dict[str, Any]:
        """
        Get SES sending quota/statistics.
        
        Returns:
            Dictionary with quota information
        
        Raises:
            ClientError: If retrieving quota fails
        """
        try:
            async with self.session.client('ses') as ses:
                quota = await ses.get_account_sending_enabled()
                stats = await ses.get_send_statistics()
            
            logger.info(
                f"SES quota retrieved",
                extra={
                    "account_enabled": quota.get('Enabled', False),
                    "recent_bounces": len(stats.get('SendDataPoints', []))
                }
            )
            
            return {
                'send_quota': stats,
                'account_enabled': quota.get('Enabled', False)
            }
        
        except ClientError as e:
            logger.error(f"Error getting SES quota: {e}")
            raise
    
    async def verify_email_identity(self, email_address: str) -> bool:
        """
        Verify an email address with SES (for sandbox mode).
        
        Args:
            email_address: Email to verify
        
        Returns:
            True if verification initiated successfully
        """
        try:
            async with self.session.client('ses') as ses:
                await ses.verify_email_identity(EmailAddress=email_address)
            
            logger.info(f"Email verification initiated for: {email_address}")
            return True
        
        except ClientError as e:
            logger.error(f"Error verifying email: {e}")
            return False
