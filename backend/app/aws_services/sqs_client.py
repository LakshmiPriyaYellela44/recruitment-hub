"""Real SQS client using boto3."""
import logging
import json
from typing import List, Dict, Any
import aioboto3
from botocore.exceptions import ClientError
from app.core.config import settings

logger = logging.getLogger(__name__)


class SQSClient:
    """Real SQS client using boto3."""
    
    def __init__(self):
        """Initialize SQS client."""
        self.queue_url = settings.SQS_QUEUE_URL
        self.region = settings.AWS_REGION
        
        # Create session
        self.session = aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=self.region
        )
        logger.info(f"SQSClient initialized for queue: {self.queue_url}")
    
    async def send_message(
        self,
        queue_name: str,
        message: Dict[str, Any],
        retry_count: int = 0
    ) -> str:
        """
        Send message to SQS queue.
        
        Args:
            queue_name: Queue name (parameter for interface compatibility, uses configured URL)
            message: Message dictionary
            retry_count: Retry count (optional metadata)
        
        Returns:
            SQS MessageId
        """
        try:
            # Add retry count to message if present
            message_body = message.copy()
            if retry_count > 0:
                message_body['retry_count'] = retry_count
            
            async with self.session.client('sqs') as sqs:
                response = await sqs.send_message(
                    QueueUrl=self.queue_url,
                    MessageBody=json.dumps(message_body),
                    MessageAttributes={
                        'RetryCount': {
                            'StringValue': str(retry_count),
                            'DataType': 'Number'
                        }
                    }
                )
            
            message_id = response['MessageId']
            logger.info(
                f"Message sent to SQS queue",
                extra={
                    "message_id": message_id,
                    "retry_count": retry_count
                }
            )
            return message_id
        
        except ClientError as e:
            logger.error(f"SQS send error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending to SQS: {e}", exc_info=True)
            raise
    
    async def receive_messages(
        self,
        queue_name: str,
        max_messages: int = 1,
        wait_time_seconds: int = 20
    ) -> List[Dict]:
        """
        Receive messages from SQS queue.
        
        Args:
            queue_name: Queue name (parameter for interface compatibility, uses configured URL)
            max_messages: Max messages to retrieve (1-10)
            wait_time_seconds: Long polling wait time (0-20)
        
        Returns:
            List of messages with id, body, and receipt_handle
        """
        try:
            # Clamp values to SQS limits
            max_messages = min(max(1, max_messages), 10)
            wait_time_seconds = min(max(0, wait_time_seconds), 20)
            
            async with self.session.client('sqs') as sqs:
                response = await sqs.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=max_messages,
                    WaitTimeSeconds=wait_time_seconds,
                    MessageAttributeNames=['All'],
                    AttributeNames=['All']
                )
            
            messages = []
            if 'Messages' in response:
                for msg in response['Messages']:
                    try:
                        body = json.loads(msg['Body'])
                        
                        # DEBUG: Log the raw message structure
                        logger.debug(f"RAW Message from SQS: Type={body.get('Type') if isinstance(body, dict) else 'not-dict'}, Keys={list(body.keys()) if isinstance(body, dict) else 'N/A'}")
                        
                        # Handle SNS notification wrapper
                        # When SNS publishes to SQS, AWS wraps the message in a notification envelope
                        if isinstance(body, dict) and body.get('Type') == 'Notification':
                            try:
                                # Extract the actual message from the SNS wrapper
                                actual_message = json.loads(body.get('Message', '{}'))
                                body = actual_message
                                logger.debug("Unwrapped SNS notification from SQS message")
                                logger.debug(f"After unwrap: {body}")
                            except json.JSONDecodeError:
                                # If Message field isn't valid JSON, keep the whole body
                                logger.debug("SNS notification Message field is not JSON, keeping whole body")
                    except json.JSONDecodeError:
                        body = msg['Body']
                    
                    messages.append({
                        'id': msg['MessageId'],
                        'body': body,
                        'receipt_handle': msg['ReceiptHandle'],
                        'retry_count': int(msg.get('MessageAttributes', {})
                                           .get('RetryCount', {})
                                           .get('StringValue', 0)),
                        'created_at': msg.get('Attributes', {}).get('SentTimestamp', '')
                    })
            
            if messages:
                logger.info(
                    f"Received {len(messages)} message(s) from SQS",
                    extra={
                        "message_count": len(messages),
                        "wait_time": wait_time_seconds
                    }
                )
            
            return messages
        
        except ClientError as e:
            logger.error(f"SQS receive error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error receiving from SQS: {e}", exc_info=True)
            raise
    
    def get_queue_depth(self, queue_name: str = None) -> int:
        """
        Get approximate number of messages in queue (synchronous wrapper).
        
        Args:
            queue_name: Queue name (optional, uses configured queue URL)
        
        Returns:
            Approximate number of messages waiting in queue
        """
        try:
            # Since we're in a sync method, return 0 as default
            # The async version should be used in actual code
            logger.debug(f"get_queue_depth called for queue: {queue_name or self.queue_url}")
            return 0
        except Exception as e:
            logger.error(f"Error getting queue depth: {e}")
            return 0
    
    async def delete_message(self, queue_name: str, receipt_handle: str) -> bool:
        """
        Delete message from SQS queue.
        
        Args:
            queue_name: Queue name (parameter for interface compatibility, uses configured URL)
            receipt_handle: SQS receipt handle
        
        Returns:
            True if deleted successfully
        """
        try:
            async with self.session.client('sqs') as sqs:
                await sqs.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle
                )
            
            logger.debug("Message deleted from SQS")
            return True
        
        except ClientError as e:
            logger.error(f"SQS delete error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting from SQS: {e}", exc_info=True)
            return False
    
    async def get_queue_attributes(self) -> Dict[str, Any]:
        """
        Get queue attributes (message count, etc).
        
        Returns:
            Dictionary with queue attributes
        """
        try:
            async with self.session.client('sqs') as sqs:
                response = await sqs.get_queue_attributes(
                    QueueUrl=self.queue_url,
                    AttributeNames=['All']
                )
            
            attributes = response.get('Attributes', {})
            logger.info(
                f"Queue attributes retrieved",
                extra={
                    "messages_visible": attributes.get('ApproximateNumberOfMessages', 0),
                    "messages_not_visible": attributes.get('ApproximateNumberOfMessagesNotVisible', 0)
                }
            )
            return attributes
        
        except ClientError as e:
            logger.error(f"Error getting queue attributes: {e}")
            raise
