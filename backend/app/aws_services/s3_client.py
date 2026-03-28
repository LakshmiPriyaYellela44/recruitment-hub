"""S3 client for AWS services."""
import logging
from typing import Optional
import aioboto3
import asyncio
import os
from pathlib import Path
from botocore.exceptions import ClientError
from app.core.config import settings

logger = logging.getLogger(__name__)


class S3Client:
    """Real S3 client using boto3."""
    
    def __init__(self):
        """Initialize S3 client."""
        self.bucket_name = settings.S3_BUCKET_NAME
        self.region = settings.AWS_REGION
        
        # Create session
        self.session = aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=self.region
        )
        logger.info(f"S3Client initialized for bucket: {self.bucket_name} in region: {self.region}")
    
    async def upload_file(self, key: str, content: bytes) -> str:
        """
        Upload file to S3.
        
        Args:
            key: S3 object key (path)
            content: File content (bytes)
        
        Returns:
            S3 key of uploaded file
        """
        try:
            async with self.session.client('s3') as s3:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=content,
                    ServerSideEncryption='AES256'  # Enable encryption
                )
            
            logger.info(f"File uploaded to S3: s3://{self.bucket_name}/{key} (size: {len(content)} bytes)")
            return key
        
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading to S3: {e}", exc_info=True)
            raise
    
    async def download_file(self, key: str) -> Optional[bytes]:
        """
        Download file from S3.
        
        Args:
            key: S3 object key
        
        Returns:
            File content or None if not found
        """
        try:
            async with self.session.client('s3') as s3:
                response = await s3.get_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
                content = await response['Body'].read()
                logger.info(f"File downloaded from S3: {key} (size: {len(content)} bytes)")
                return content
        
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"File not found in S3: {key}")
                return None
            logger.error(f"S3 download error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading from S3: {e}", exc_info=True)
            raise
    
    async def delete_file(self, key: str) -> bool:
        """
        Delete file from S3.
        
        Args:
            key: S3 object key
        
        Returns:
            True if deleted successfully
        """
        try:
            async with self.session.client('s3') as s3:
                await s3.delete_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
            
            logger.info(f"File deleted from S3: {key}")
            return True
        
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting from S3: {e}", exc_info=True)
            return False
    
    async def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """
        Generate presigned URL for S3 object.
        
        Args:
            key: S3 object key
            expiration: URL expiration in seconds (default: 1 hour)
        
        Returns:
            Presigned URL
        """
        try:
            async with self.session.client('s3') as s3:
                url = await s3.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': key
                    },
                    ExpiresIn=expiration
                )
            
            logger.info(f"Presigned URL generated for: {key} (expires in {expiration}s)")
            return url
        
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL: {e}", exc_info=True)
            raise



