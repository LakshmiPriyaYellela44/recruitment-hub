"""Real SNS client using boto3."""
import logging
import json
from typing import Dict, Any
import aioboto3
from botocore.exceptions import ClientError
from app.core.config import settings

logger = logging.getLogger(__name__)


class SNSClient:
    """Real SNS client using boto3."""
    
    def __init__(self):
        """Initialize SNS client."""
        self.topic_arn = settings.SNS_TOPIC_ARN
        self.region = settings.AWS_REGION
        
        # Create session
        self.session = aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=self.region
        )
        logger.info(f"SNSClient initialized for topic: {self.topic_arn}")
    
    async def publish(self, topic: str, message: Dict[str, Any]) -> str:
        """
        Publish message to SNS topic.
        
        Args:
            topic: Topic name (parameter for interface compatibility, uses configured ARN)
            message: Message dictionary
        
        Returns:
            SNS MessageId
        """
        try:
            async with self.session.client('sns') as sns:
                response = await sns.publish(
                    TopicArn=self.topic_arn,
                    Message=json.dumps(message),
                    Subject=f"Resume Upload Event"  # SNS subject for email subscribers
                )
            
            message_id = response['MessageId']
            logger.info(
                f"Message published to SNS topic",
                extra={
                    "topic_arn": self.topic_arn,
                    "message_id": message_id,
                }
            )
            return message_id
        
        except ClientError as e:
            logger.error(f"SNS publish error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error publishing to SNS: {e}", exc_info=True)
            raise
    
    def subscribe(self, topic: str, callback: callable):
        """
        Subscribe to topic.
        
        Note: Real SNS uses subscriptions created in AWS Console or via subscriptions().
        This method is kept for interface compatibility.
        """
        logger.warning(
            "subscribe() called on real SNS client. "
            "Subscriptions should be configured in AWS Console (SNS → Topics → Subscriptions)"
        )
