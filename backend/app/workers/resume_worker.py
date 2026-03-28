"""Resume worker for processing resume uploads via SQS queue."""
import asyncio
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.modules.resume.service import ResumeService
from app.aws_services.sqs_client import SQSClient
from app.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class SQSResumeWorker:
    """
    Worker for processing resumes from SQS queue.
    
    Polls the resume-processing-queue, processes each message, and handles retries
    with exponential backoff and dead-letter queue support.
    """
    
    QUEUE_NAME = "resume-processing-queue"
    MAX_RETRIES = 3
    POLL_INTERVAL_SECONDS = 2
    MAX_MESSAGES_PER_POLL = 10
    
    def __init__(self, sqs_client: SQSClient):
        """
        Initialize resume worker.
        
        Args:
            sqs_client: SQSClient instance for queue operations
        """
        self.sqs_client = sqs_client
        self.is_running = False
        logger.info("SQSResumeWorker initialized")
    
    async def process_message(self, message: dict) -> bool:
        """
        Process a single message from the queue.
        
        Args:
            message: Message from SQS queue containing resume_id
        
        Returns:
            True if processing succeeded, False otherwise
        """
        receipt_handle = message.get("receipt_handle")
        message_body = message.get("body", {})
        retry_count = message.get("retry_count", 0)
        
        # Extract resume_id from message
        # Message body should contain resume_id directly (after SNS unwrapping in SQSClient)
        resume_id_str = message_body.get("resume_id")
        
        if not resume_id_str:
            # Invalid message with null resume_id (old test data) - skip and delete
            logger.warning(
                f"Skipping message with null resume_id (invalid test data)",
                extra={
                    "queue": self.QUEUE_NAME,
                    "message_id": message.get("id"),
                    "retry_count": retry_count,
                    "message_body_keys": list(message_body.keys()) if isinstance(message_body, dict) else "not-dict",
                }
            )
            # Auto-delete this bad message from queue to prevent it from being retried forever
            try:
                await self.sqs_client.delete_message(self.QUEUE_NAME, receipt_handle)
                logger.info(f"Deleted invalid message from queue: {message.get('id')}")
            except Exception as e:
                logger.error(f"Failed to delete invalid message: {e}")
            return True  # Return True so this isn't retried
        
        try:
            # Convert resume_id to UUID
            resume_id = UUID(resume_id_str)
            
            logger.info(
                f"Worker picked up message from queue",
                extra={
                    "queue": self.QUEUE_NAME,
                    "message_id": message.get("id"),
                    "resume_id": resume_id_str,
                    "retry_count": retry_count,
                }
            )
            
            # Create async database session
            async with AsyncSessionLocal() as db:
                service = ResumeService(db)
                
                # Process resume
                resume = await service.process_resume(resume_id)
                
                logger.info(
                    f"Successfully processed resume",
                    extra={
                        "resume_id": str(resume.id),
                        "status": resume.status,
                        "message_id": message.get("id"),
                    }
                )
            
            # Delete message from queue on success
            await self.sqs_client.delete_message(self.QUEUE_NAME, receipt_handle)
            
            logger.info(
                f"Message deleted from queue after successful processing",
                extra={
                    "resume_id": resume_id_str,
                    "message_id": message.get("id"),
                }
            )
            
            return True
        
        except NotFoundException as e:
            # Retry logic for race condition: resume might not be committed yet
            if retry_count < 3:
                logger.warning(
                    f"Resume not found (may be race condition), retrying...",
                    extra={
                        "resume_id": resume_id_str,
                        "message_id": message.get("id"),
                        "retry_count": retry_count,
                        "error": str(e),
                    }
                )
                # Re-queue with retry
                retry_count += 1
                message_body["retry_count"] = retry_count
                backoff_seconds = 5  # Wait 5 seconds before retrying "not found" errors
                await asyncio.sleep(backoff_seconds)
                await self.sqs_client.send_message(
                    self.QUEUE_NAME,
                    body=message_body,
                    delay_seconds=backoff_seconds
                )
                logger.info(
                    f"Message re-queued with delay for 'resume not found' retry",
                    extra={
                        "resume_id": resume_id_str,
                        "delay_seconds": backoff_seconds,
                        "retry_count": retry_count,
                    }
                )
                return True
            else:
                # Max retries exceeded - delete the message
                logger.error(
                    f"Resume not found after {retry_count} retries, deleting message",
                    extra={
                        "resume_id": resume_id_str,
                        "message_id": message.get("id"),
                        "error": str(e),
                    }
                )
                await self.sqs_client.delete_message(self.QUEUE_NAME, receipt_handle)
                return False
        
        except Exception as e:
            logger.error(
                f"Error processing resume message",
                extra={
                    "resume_id": resume_id_str,
                    "message_id": message.get("id"),
                    "retry_count": retry_count,
                    "error": str(e),
                },
                exc_info=True
            )
            
            # Handle retries with exponential backoff
            if retry_count < self.MAX_RETRIES:
                # Re-queue message with incremented retry count
                retry_count += 1
                message_body["retry_count"] = retry_count
                
                # Exponential backoff: 2^retry_count seconds
                backoff_seconds = 2 ** retry_count
                
                logger.warning(
                    f"Will retry message processing",
                    extra={
                        "resume_id": resume_id_str,
                        "message_id": message.get("id"),
                        "retry_count": retry_count,
                        "max_retries": self.MAX_RETRIES,
                        "backoff_seconds": backoff_seconds,
                    }
                )
                
                # Send message back to queue
                await self.sqs_client.send_message(
                    self.QUEUE_NAME,
                    message_body,
                    retry_count=retry_count
                )
                
                # Delete original message
                await self.sqs_client.delete_message(self.QUEUE_NAME, receipt_handle)
            
            else:
                # Max retries exceeded - move to DLQ
                logger.critical(
                    f"Max retries exceeded - moving to dead-letter queue",
                    extra={
                        "resume_id": resume_id_str,
                        "message_id": message.get("id"),
                        "retry_count": retry_count,
                    }
                )
                
                await self.sqs_client.send_message_to_dead_letter_queue(
                    self.QUEUE_NAME,
                    message
                )
                
                # Delete original message
                await self.sqs_client.delete_message(self.QUEUE_NAME, receipt_handle)
            
            return False
    
    async def poll_queue(self):
        """
        Poll SQS queue continuously for messages.
        
        Runs in an infinite loop, fetching messages and processing them.
        """
        logger.info(
            f"Starting queue polling loop",
            extra={
                "queue": self.QUEUE_NAME,
                "poll_interval_seconds": self.POLL_INTERVAL_SECONDS,
                "max_messages_per_poll": self.MAX_MESSAGES_PER_POLL,
            }
        )
        
        self.is_running = True
        
        while self.is_running:
            try:
                # Receive messages from queue
                messages = await self.sqs_client.receive_messages(
                    self.QUEUE_NAME,
                    max_messages=self.MAX_MESSAGES_PER_POLL,
                    wait_time_seconds=0
                )
                
                if messages:
                    logger.debug(
                        f"Received messages from queue",
                        extra={
                            "queue": self.QUEUE_NAME,
                            "message_count": len(messages),
                            "queue_depth": self.sqs_client.get_queue_depth(self.QUEUE_NAME),
                        }
                    )
                    
                    # Process each message concurrently
                    tasks = [self.process_message(msg) for msg in messages]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Log processing results
                    successful = sum(1 for r in results if r is True)
                    failed = sum(1 for r in results if r is False)
                    exceptions = sum(1 for r in results if isinstance(r, Exception))
                    
                    if successful > 0 or failed > 0:
                        logger.info(
                            f"Batch processing completed",
                            extra={
                                "queue": self.QUEUE_NAME,
                                "successful": successful,
                                "failed": failed,
                                "exceptions": exceptions,
                                "queue_depth_after": self.sqs_client.get_queue_depth(self.QUEUE_NAME),
                            }
                        )
                
                # Poll interval
                await asyncio.sleep(self.POLL_INTERVAL_SECONDS)
            
            except Exception as e:
                logger.error(
                    f"Error in queue polling loop",
                    extra={
                        "queue": self.QUEUE_NAME,
                        "error": str(e),
                    },
                    exc_info=True
                )
                # Continue polling even if error occurs
                await asyncio.sleep(self.POLL_INTERVAL_SECONDS)
    
    def stop(self):
        """Stop the polling loop."""
        logger.info("Stopping queue polling loop")
        self.is_running = False


async def start_resume_worker(sqs_client: SQSClient):
    """
    Start the resume worker.
    
    Args:
        sqs_client: SQSClient instance for queue operations
    """
    worker = SQSResumeWorker(sqs_client)
    
    try:
        await worker.poll_queue()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal - stopping worker")
        worker.stop()


async def start_workers(sqs_client: SQSClient):
    """
    Start all background workers.
    
    Args:
        sqs_client: SQSClient instance for queue operations
    """
    logger.info("Starting background workers...")
    
    # Start resume worker with SQS polling
    try:
        await start_resume_worker(sqs_client)
    except KeyboardInterrupt:
        logger.info("All workers stopped")
