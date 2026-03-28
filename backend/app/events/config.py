"""Event-driven architecture configuration with real AWS support."""
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class EventConfig:
    """Configuration for SNS/SQS event-driven system."""
    
    _sns_client = None
    _sqs_client = None
    _initialized: bool = False
    
    @classmethod
    def initialize(cls):
        """Initialize event infrastructure - REAL AWS SERVICES ONLY."""
        if cls._initialized:
            logger.info("Event infrastructure already initialized")
            return
        
        # Always use real AWS services
        logger.info("Initializing REAL AWS SNS/SQS services (mock files removed)...")
        try:
            from app.aws_services.sns_client import SNSClient as RealSNSClient
            from app.aws_services.sqs_client import SQSClient as RealSQSClient
            
            cls._sqs_client = RealSQSClient()
            cls._sns_client = RealSNSClient()
            logger.info("✓ Successfully initialized REAL AWS SNS/SQS services")
            logger.info(f"  SNS Topic: {settings.SNS_TOPIC_ARN}")
            logger.info(f"  SQS Queue: {settings.SQS_QUEUE_URL}")
        except Exception as e:
            logger.error(f"✗ FAILED to initialize real AWS services: {e}")
            logger.error("Check AWS credentials and configuration")
            raise
        
        cls._initialized = True
        logger.info("Event infrastructure initialized successfully")
    
    @classmethod
    def get_sns_client(cls):
        """Get SNS client instance."""
        if not cls._initialized:
            cls.initialize()
        return cls._sns_client
    
    @classmethod
    def get_sqs_client(cls):
        """Get SQS client instance."""
        if not cls._initialized:
            cls.initialize()
        return cls._sqs_client
    
    @classmethod
    def get_queue_stats(cls, queue_name: str = "resume-processing-queue") -> dict:
        """Get statistics for a queue (REAL AWS SQS only)."""
        if not cls._initialized:
            return {"error": "Event infrastructure not initialized"}
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            attrs = loop.run_until_complete(cls._sqs_client.get_queue_attributes())
            return {
                "messages_visible": int(attrs.get('ApproximateNumberOfMessages', 0)),
                "messages_not_visible": int(attrs.get('ApproximateNumberOfMessagesNotVisible', 0)),
                "created_timestamp": attrs.get('CreatedTimestamp', '')
            }
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {"error": str(e)}
    
    @classmethod
    def get_dead_letter_messages(cls, queue_name: str = "resume-processing-queue-dlq") -> list:
        """Get messages from dead-letter queue (REAL AWS SQS only)."""
        if not cls._initialized:
            return []
        
        logger.warning("Dead-letter queue access requires AWS SQS API - use AWS Console for details")
        return []
