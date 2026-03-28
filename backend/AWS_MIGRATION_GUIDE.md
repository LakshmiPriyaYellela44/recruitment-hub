# AWS Migration Guide: Mock to Real AWS Services

Complete guide to migrate your FastAPI recruitment platform from mock AWS services to real AWS services (S3, SNS, SQS, SES).

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [AWS Console Setup](#aws-console-setup)
3. [Code Migration](#code-migration)
4. [Configuration](#configuration)
5. [Testing & Validation](#testing--validation)
6. [Deployment Strategies](#deployment-strategies)

---

## Architecture Overview

### Current Flow (Mocked)
```
Resume Upload → S3 Mock (Local FS) → SNS Mock → SQS Mock → Worker (In-memory) → Parse Resume
                                        ↓
                                    Email Queue (SES Mock → Logs file)
```

### Target Flow (Real AWS)
```
Resume Upload → S3 (Real Bucket) → SNS Topic → SQS Queue → Worker (Real Polling) → Parse Resume
                     ↓                                              ↓
              Presigned URLs                           CloudWatch Logs (Optional)
                                                        ↓
                                    Email Queue (SES Real) → Production Email
```

### Event Flow
1. **Resume Upload** → User uploads file to `/resumes/upload`
2. **S3 Storage** → File stored in AWS S3 bucket
3. **SNS Publish** → Upload event published to SNS topic
4. **SQS Message** → SNS automatically sends to SQS queue subscription
5. **SQS Polling** → Worker polls SQS queue continuously
6. **Resume Processing** → Worker processes resume (extract text, parse)
7. **Message Deletion** → Successfully processed messages deleted from queue
8. **Email Sending** → System sends emails via AWS SES
9. **Presigned URLs** → Frontend gets signed URLs to download resumes from S3

---

## AWS Console Setup

### Prerequisites
- AWS Account with appropriate permissions
- AWS CLI configured locally (optional but recommended)
- IAM User with programmatic access

### Step 1: Create IAM User (Recommended)

**Why:** Use least privilege principle - don't use root account

1. Go to **AWS Console** → **IAM** → **Users** → **Create user**
2. Name: `recruitment-api-user`
3. Select: **Provide user access to the AWS Management Console** (optional, for testing)
4. Create access key for this user
5. **Save Access Key ID and Secret Access Key** (you'll need these)

### Step 2: Create S3 Bucket for Resume Storage

1. **AWS Console** → **S3** → **Create bucket**
   - **Bucket name**: `recruitment-resumes-prod` (must be globally unique)
   - **Region**: `us-east-1` (match your region)
   - **Block Public Access**: Leave all enabled (✓ Block all)
   - Create bucket

2. **Configuration - Versioning** (Optional but Recommended)
   - Select bucket → **Properties** → **Versioning** → **Enable**
   - Keeps historical versions of files for recovery

3. **Configuration - Lifecycle Policy** (Optional - Cost Optimization)
   - Select bucket → **Management** → **Lifecycle rules** → **Create rule**
   - Rule name: `delete-old-resumes`
   - Apply to: All objects in bucket
   - Expiration: Delete after 90 days
   - Create rule

4. **Configuration - Server-side Encryption** (Recommended)
   - Select bucket → **Properties** → **Default encryption**
   - Enable: **Server-side encryption with Amazon S3-managed keys (SSE-S3)**

### Step 3: Create SNS Topic for Resume Upload Events

1. **AWS Console** → **SNS** → **Topics** → **Create topic**
   - **Type**: Standard
   - **Name**: `recruitment-resume-uploads`
   - Create topic

2. **Note the Topic ARN**: You'll need this value
   - Format: `arn:aws:sns:us-east-1:123456789:recruitment-resume-uploads`

### Step 4: Create SQS Queue for Resume Processing

1. **AWS Console** → **SQS** → **Queues** → **Create queue**

   **Queue Settings:**
   - **Name**: `recruitment-resume-processing`
   - **Type**: Standard
   - **Visibility timeout**: 30 seconds (time to process before retry)
   - **Message retention period**: 4 days
   - **Delivery delay**: 0 seconds
   - Leave other defaults
   - Create queue

2. **Note the Queue URL**: You'll need this value
   - Format: `https://sqs.us-east-1.amazonaws.com/123456789/recruitment-resume-processing`

3. **Create Dead Letter Queue (DLQ)** (Optional but Recommended)
   - Repeat Step 4 but name it: `recruitment-resume-processing-dlq`
   - Set Message retention: 14 days

### Step 5: Subscribe SQS Queue to SNS Topic

This means messages published to SNS will automatically go to SQS.

1. **SNS Console** → **Topics** → `recruitment-resume-uploads` → **Subscriptions** → **Create subscription**

   **Subscription Settings:**
   - **Topic ARN**: `recruitment-resume-uploads` (pre-selected)
   - **Protocol**: `Amazon SQS`
   - **Endpoint**: Paste the SQS Queue ARN
     - Go to SQS → Select queue → Copy ARN
     - Format: `arn:aws:sqs:us-east-1:123456789:recruitment-resume-processing`
   - Create subscription

2. **Configure Dead Letter Queue** (Optional - if you created a DLQ)
   - Go to **SQS** → Select `recruitment-resume-processing` queue
   - **Configure queue** → **Redrive policy**
   - **Dead-letter queue**: Select `recruitment-resume-processing-dlq`
   - **Number of receives**: 3 (retry 3 times before sending to DLQ)

### Step 6: Configure SES for Email Sending

#### Option A: Sandbox Mode (Testing Only)
Good for development - no sending delays, but can only send to verified addresses.

1. **AWS Console** → **SES** → **Email addresses** → **Verify a New Email Address**
   - Enter: `noreply@yourcompany.com` (should be your email for testing)
   - Verify email by clicking link in sent verification email

#### Option B: Production Mode (Recommended for Staging/Prod)
Better for production but requires domain verification and increases sending limits.

1. **AWS Console** → **SES** → **Domains** → **Verify a New Domain**
   - Enter: `yourcompany.com`
   - Add DKIM records to your domain DNS
   - Wait for verification (can take 24 hours)

2. **Request Production Access**
   - **AWS Console** → **SES** → **Account Dashboard**
   - Click **Request Production Access**
   - Fill out form (usually approved within 24 hours)

### Step 7: Create IAM Policy for Least Privilege Access

1. **AWS Console** → **IAM** → **Policies** → **Create policy**

2. **JSON Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3ResumeAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "arn:aws:s3:::recruitment-resumes-prod/*"
    },
    {
      "Sid": "SNSPublish",
      "Effect": "Allow",
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:us-east-1:123456789:recruitment-resume-uploads"
    },
    {
      "Sid": "SQSConsume",
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:ChangeMessageVisibility"
      ],
      "Resource": "arn:aws:sqs:us-east-1:123456789:recruitment-resume-processing"
    },
    {
      "Sid": "SESEmail",
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:123456789:log-group:/aws/recruitment/*"
    }
  ]
}
```

3. Name: `recruitment-api-policy`
4. Create policy

### Step 8: Attach Policy to IAM User

1. **IAM** → **Users** → Select `recruitment-api-user`
2. **Add permissions** → **Attach policies directly**
3. Select `recruitment-api-policy`
4. Save

### Step 9: Create CloudWatch Log Group (Optional)

For centralized logging from your application:

1. **AWS Console** → **CloudWatch** → **Log Groups** → **Create log group**
2. Name: `/aws/recruitment/api`
3. Set retention: 7 days (or your preference)

---

## Code Migration

### Step 1: Update Requirements

Add boto3 to your dependencies:

```bash
pip install boto3>=1.26.0
pip install aioboto3>=12.0.0  # For async boto3
```

Update `requirements.txt`:
```
boto3>=1.26.0
aioboto3>=12.0.0
```

### Step 2: Create Real AWS Clients

Create `app/aws_services/` directory:

```bash
mkdir -p app/aws_services
```

#### File: `app/aws_services/__init__.py`
```python
"""AWS services module."""
```

#### File: `app/aws_services/s3_client.py`
```python
"""Real S3 client using boto3."""
import logging
from typing import Optional
import aioboto3
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
        logger.info(f"S3Client initialized for bucket: {self.bucket_name}")
    
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
            
            logger.info(f"File uploaded to S3: s3://{self.bucket_name}/{key}")
            return key
        
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading to S3: {e}")
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
                logger.info(f"File downloaded from S3: {key}")
                return content
        
        except s3.exceptions.NoSuchKey:
            logger.warning(f"File not found in S3: {key}")
            return None
        except ClientError as e:
            logger.error(f"S3 download error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading from S3: {e}")
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
            logger.error(f"Unexpected error deleting from S3: {e}")
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
            
            logger.info(f"Presigned URL generated for: {key}")
            return url
        
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL: {e}")
            raise
```

#### File: `app/aws_services/sns_client.py`
```python
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
            topic: Topic name (not used, uses configured ARN)
            message: Message dictionary
        
        Returns:
            SNS MessageId
        """
        try:
            async with self.session.client('sns') as sns:
                response = await sns.publish(
                    TopicArn=self.topic_arn,
                    Message=json.dumps(message),
                    MessageStructure='raw'
                )
            
            message_id = response['MessageId']
            logger.info(
                f"Message published to SNS topic",
                extra={
                    "topic_arn": self.topic_arn,
                    "message_id": message_id,
                    "message": message
                }
            )
            return message_id
        
        except ClientError as e:
            logger.error(f"SNS publish error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error publishing to SNS: {e}")
            raise
    
    def subscribe(self, topic: str, callback: callable):
        """
        Subscribe to topic.
        
        Note: Real SNS uses subscriptions created in AWS Console.
        This method is for interface compatibility.
        """
        logger.warning(
            "subscribe() called on real SNS client. "
            "Subscriptions should be configured in AWS Console or via boto3 resource."
        )
```

#### File: `app/aws_services/sqs_client.py`
```python
"""Real SQS client using boto3."""
import logging
import json
from typing import List, Dict, Any, Optional
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
            queue_name: Queue name (not used, uses configured URL)
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
                    "queue_url": self.queue_url,
                    "message_id": message_id,
                    "retry_count": retry_count
                }
            )
            return message_id
        
        except ClientError as e:
            logger.error(f"SQS send error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending to SQS: {e}")
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
            queue_name: Queue name (not used, uses configured URL)
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
                    MessageAttributeNames=['All']
                )
            
            messages = []
            if 'Messages' in response:
                for msg in response['Messages']:
                    try:
                        body = json.loads(msg['Body'])
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
            
            logger.info(
                f"Received messages from SQS",
                extra={
                    "queue_url": self.queue_url,
                    "message_count": len(messages),
                    "wait_time": wait_time_seconds
                }
            )
            return messages
        
        except ClientError as e:
            logger.error(f"SQS receive error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error receiving from SQS: {e}")
            raise
    
    async def delete_message(self, queue_name: str, receipt_handle: str) -> bool:
        """
        Delete message from SQS queue.
        
        Args:
            queue_name: Queue name (not used, uses configured URL)
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
            
            logger.info(
                f"Message deleted from SQS",
                extra={"queue_url": self.queue_url}
            )
            return True
        
        except ClientError as e:
            logger.error(f"SQS delete error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting from SQS: {e}")
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
            
            return response.get('Attributes', {})
        
        except ClientError as e:
            logger.error(f"Error getting queue attributes: {e}")
            raise
```

#### File: `app/aws_services/ses_client.py`
```python
"""Real SES client using boto3."""
import logging
from typing import Optional, List
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
        logger.info(f"SESClient initialized for sender: {self.from_address}")
    
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
                    "to_addresses": to_addresses,
                    "subject": subject,
                    "from_address": from_address
                }
            )
            return message_id
        
        except ClientError as e:
            logger.error(f"SES send error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            raise
    
    async def get_send_quota(self) -> Dict[str, Any]:
        """
        Get SES sending quota/statistics.
        
        Returns:
            Dictionary with quota information
        """
        try:
            async with self.session.client('ses') as ses:
                response = await ses.get_send_statistics()
                quota = await ses.get_account_sending_enabled()
            
            return {
                'send_quota': response,
                'account_enabled': quota.get('Enabled', False)
            }
        
        except ClientError as e:
            logger.error(f"Error getting SES quota: {e}")
            raise
```

### Step 3: Update Configuration

Update `app/core/config.py`:

```python
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Recruitment Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres@localhost:5432/recruitment_db"
    DB_CONNECTION_RETRIES: int = 5
    DB_CONNECTION_RETRY_DELAY: float = 1.0
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AWS Configuration
    AWS_ENABLED: bool = True  # Set to False to use mocks
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    
    # S3 Configuration
    S3_BUCKET_NAME: str = "recruitment-resumes-prod"
    S3_MOCK_ENABLED: bool = False  # Set to True for local development
    S3_MOCK_STORAGE_PATH: str = "./storage/resumes"
    
    # SNS Configuration
    SNS_TOPIC_ARN: str = "arn:aws:sns:us-east-1:123456789:recruitment-resume-uploads"
    SNS_MOCK_ENABLED: bool = False
    
    # SQS Configuration
    SQS_QUEUE_URL: str = "https://sqs.us-east-1.amazonaws.com/123456789/recruitment-resume-processing"
    SQS_MOCK_ENABLED: bool = False
    
    # SES Configuration
    SES_FROM_EMAIL: str = "noreply@recruitment.com"
    SES_MOCK_ENABLED: bool = False
    EMAIL_LOG_PATH: str = "./logs/emails.log"  # Only used with mocks
    
    # Event Configuration
    QUEUE_MOCK_ENABLED: bool = False
    SQS_POLL_INTERVAL_SECONDS: int = 2
    SQS_MAX_MESSAGES_PER_POLL: int = 10
    SQS_VISIBILITY_TIMEOUT_SECONDS: int = 30
    SQS_MAX_RETRIES: int = 3
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

### Step 4: Update Events Configuration

Update `app/events/config.py` to support both real and mock implementations:

```python
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
        """Initialize event infrastructure (real or mock)."""
        if cls._initialized:
            logger.info("Event infrastructure already initialized")
            return
        
        # Use real AWS services if enabled
        if settings.AWS_ENABLED and not settings.SNS_MOCK_ENABLED:
            from app.aws_services.sns_client import SNSClient as RealSNSClient
            from app.aws_services.sqs_client import SQSClient as RealSQSClient
            
            cls._sqs_client = RealSQSClient()
            cls._sns_client = RealSNSClient()
            logger.info("✓ Using real AWS SNS/SQS services")
        else:
            # Fall back to mock implementations
            from app.aws_mock.sns_client import SNSClient as MockSNSClient
            from app.aws_mock.sns_client import SQSClient as MockSQSClient
            
            cls._sqs_client = MockSQSClient()
            cls._sns_client = MockSNSClient()
            MockSNSClient.set_sqs_client(cls._sqs_client)
            logger.info("✓ Using mock SNS/SQS services")
        
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
```

### Step 5: Update Resume Service

Update `app/modules/resume/service.py` to use configurable S3 client:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import Resume
from app.core.exceptions import NotFoundException, ValidationException
from app.modules.resume.repository import ResumeRepository
from app.modules.resume.parser import ResumeParser
from app.modules.candidate.service import CandidateService
from app.events.config import EventConfig
from app.utils.audit import log_audit
from fastapi import UploadFile
from uuid import UUID, uuid4
from datetime import datetime
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ResumeService:
    """Service for resume operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ResumeRepository(db)
        
        # Use real or mock S3 client based on config
        if settings.AWS_ENABLED and not settings.S3_MOCK_ENABLED:
            from app.aws_services.s3_client import S3Client as RealS3Client
            self.s3_client = RealS3Client()
            logger.info("Using real S3 client")
        else:
            from app.aws_mock.s3_client import S3Client as MockS3Client
            self.s3_client = MockS3Client()
            logger.info("Using mock S3 client")
        
        # Use SNS client from event configuration
        self.sns_client = EventConfig.get_sns_client()
    
    async def upload_resume(self, user_id: UUID, file: UploadFile) -> Resume:
        """Upload and process resume."""
        logger.info(f"Starting resume upload for user_id: {user_id}, filename: {file.filename}")
        
        try:
            # Validate file type
            file_ext = file.filename.split(".")[-1].lower()
            if file_ext not in ["pdf", "docx"]:
                logger.error(f"Invalid file type: {file_ext}")
                raise ValidationException("Only PDF and DOCX files are supported")
            
            # Check file size (max 10MB)
            content = await file.read()
            if len(content) > 10 * 1024 * 1024:
                logger.error(f"File too large: {len(content)} bytes")
                raise ValidationException("File size must be less than 10MB")
            
            # Generate unique file name
            unique_filename = f"{user_id}_{uuid4().hex}_{file.filename}"
            logger.info(f"Generated unique filename: {unique_filename}")
            
            # Upload to S3 (real or mock)
            s3_key = await self.s3_client.upload_file(unique_filename, content)
            logger.info(f"File uploaded to S3 with key: {s3_key}")
            
            # Create resume record
            resume = Resume(
                user_id=user_id,
                file_name=file.filename,
                file_path=s3_key,
                file_type=file_ext,
                s3_key=s3_key,
                status="UPLOADED"
            )
            
            created_resume = await self.repository.create_resume(resume)
            logger.info(f"Resume record created with id: {created_resume.id}")
            
            # Publish event to SNS for processing
            await self.sns_client.publish(
                topic="resume-upload",
                message={
                    "resume_id": str(created_resume.id),
                    "user_id": str(user_id),
                    "s3_key": s3_key,
                    "file_type": file_ext
                }
            )
            logger.info(f"Resume upload event published for resume_id: {created_resume.id}")
            
            # Log audit
            await log_audit(
                self.db,
                entity_type="Resume",
                entity_id=str(created_resume.id),
                action="upload",
                changes={"status": "UPLOADED", "file_name": file.filename}
            )
            
            return created_resume
        
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error uploading resume: {e}", exc_info=True)
            raise
    
    # ... rest of methods remain the same ...
```

### Step 6: Update Email Template Service

Update `app/modules/email/template_service.py` to use configurable SES client:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import EmailTemplate
from app.modules.email.schemas import EmailSendRequest
from app.core.exceptions import NotFoundException, ValidationException
from app.core.config import settings
from uuid import UUID
import logging
import re

logger = logging.getLogger(__name__)


class EmailTemplateService:
    """Service for email template operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Use real or mock SES client based on config
        if settings.AWS_ENABLED and not settings.SES_MOCK_ENABLED:
            from app.aws_services.ses_client import SESClient as RealSESClient
            self.ses_client = RealSESClient()
            logger.info("Using real SES client")
        else:
            from app.aws_mock.ses_client import SESClient as MockSESClient
            self.ses_client = MockSESClient()
            logger.info("Using mock SES client")
    
    async def send_email_with_template(
        self,
        template_id: UUID,
        to_addresses: list,
        placeholders: dict = None
    ) -> str:
        """
        Send email using template with placeholder substitution.
        
        Args:
            template_id: Template ID
            to_addresses: List of recipient emails
            placeholders: Dictionary of placeholder values
        
        Returns:
            SES MessageId
        """
        from sqlalchemy import select
        
        placeholders = placeholders or {}
        
        # Get template from database
        from app.core.models import EmailTemplate
        result = await self.db.execute(
            select(EmailTemplate).where(EmailTemplate.id == template_id)
        )
        template = result.scalars().first()
        
        if not template:
            raise NotFoundException(f"Template not found: {template_id}")
        
        # Validate required placeholders
        if template.required_fields:
            missing = set(template.required_fields) - set(placeholders.keys())
            if missing:
                raise ValidationException(
                    f"Missing required placeholders: {', '.join(missing)}"
                )
        
        # Substitute placeholders in subject and body
        subject = self._substitute_placeholders(template.subject, placeholders)
        body = self._substitute_placeholders(template.body, placeholders)
        html_body = (
            self._substitute_placeholders(template.html_body, placeholders)
            if template.html_body
            else None
        )
        
        # Send email
        message_id = await self.ses_client.send_email(
            to_addresses=to_addresses,
            subject=subject,
            body=body,
            html_body=html_body,
            from_address=settings.SES_FROM_EMAIL
        )
        
        logger.info(
            f"Email sent successfully",
            extra={
                "template_id": str(template_id),
                "message_id": message_id,
                "recipients": to_addresses
            }
        )
        
        return message_id
    
    @staticmethod
    def _substitute_placeholders(text: str, placeholders: dict) -> str:
        """Substitute {{placeholder}} values in text."""
        for key, value in placeholders.items():
            text = text.replace(f"{{{{{key}}}}}", str(value))
        return text
```

### Step 7: Update Workers

Update `app/workers/resume_worker.py` to support real SQS polling:

```python
"""Resume worker for processing resume uploads via SQS queue."""
import asyncio
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.modules.resume.service import ResumeService
from app.events.config import EventConfig
from app.core.exceptions import NotFoundException
from app.core.config import settings

logger = logging.getLogger(__name__)


class SQSResumeWorker:
    """Worker for processing resumes from SQS queue."""
    
    QUEUE_NAME = "resume-processing-queue"
    MAX_RETRIES = settings.SQS_MAX_RETRIES
    POLL_INTERVAL_SECONDS = settings.SQS_POLL_INTERVAL_SECONDS
    MAX_MESSAGES_PER_POLL = settings.SQS_MAX_MESSAGES_PER_POLL
    VISIBILITY_TIMEOUT = settings.SQS_VISIBILITY_TIMEOUT_SECONDS
    
    def __init__(self, sqs_client):
        """Initialize resume worker."""
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
        resume_id_str = message_body.get("data", {}).get("resume_id")
        
        if not resume_id_str:
            logger.error(
                f"Invalid message format - missing resume_id",
                extra={
                    "queue": self.QUEUE_NAME,
                    "message_id": message.get("id"),
                    "retry_count": retry_count,
                }
            )
            return False
        
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
            logger.error(
                f"Resume not found during processing",
                extra={
                    "resume_id": resume_id_str,
                    "message_id": message.get("id"),
                    "error": str(e),
                }
            )
            # Don't retry if resume doesn't exist
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
                retry_count += 1
                logger.warning(
                    f"Will retry message processing",
                    extra={
                        "resume_id": resume_id_str,
                        "message_id": message.get("id"),
                        "retry_count": retry_count,
                        "max_retries": self.MAX_RETRIES,
                    }
                )
                # Re-queue message with incremented retry count
                # (message visibility timeout handles the delay)
                return False  # Keep message in queue
            
            # Max retries exceeded - send to DLQ (not needed for real SQS,
            # SQS handles DLQ redrive policy automatically)
            logger.error(
                f"Message processing failed after {self.MAX_RETRIES} retries",
                extra={
                    "resume_id": resume_id_str,
                    "message_id": message.get("id"),
                }
            )
            # Delete from main queue (SQS redrive policy will handle DLQ)
            await self.sqs_client.delete_message(self.QUEUE_NAME, receipt_handle)
            return False
    
    async def start(self):
        """Start polling SQS queue for messages."""
        self.is_running = True
        logger.info("Resume worker started - polling SQS queue")
        
        while self.is_running:
            try:
                # Receive messages from queue
                messages = await self.sqs_client.receive_messages(
                    queue_name=self.QUEUE_NAME,
                    max_messages=self.MAX_MESSAGES_PER_POLL,
                    wait_time_seconds=20  # Long polling for efficiency
                )
                
                if messages:
                    logger.info(
                        f"Received {len(messages)} messages from SQS",
                        extra={"count": len(messages)}
                    )
                    
                    # Process messages concurrently
                    tasks = [self.process_message(msg) for msg in messages]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Log results
                    success_count = sum(1 for r in results if r is True)
                    logger.info(
                        f"Batch processing complete",
                        extra={
                            "total": len(messages),
                            "successful": success_count,
                            "failed": len(messages) - success_count
                        }
                    )
                else:
                    logger.debug("No messages received from SQS queue")
                    # Still sleep briefly to avoid busy-wait
                    await asyncio.sleep(self.POLL_INTERVAL_SECONDS)
            
            except asyncio.CancelledError:
                logger.info("Worker received cancellation signal")
                self.is_running = False
                break
            
            except Exception as e:
                logger.error(
                    f"Error in worker polling loop: {e}",
                    exc_info=True
                )
                # Sleep before retrying to avoid thundering herd
                await asyncio.sleep(5)
    
    async def stop(self):
        """Stop polling SQS queue."""
        self.is_running = False
        logger.info("Resume worker stopped")


async def start_resume_worker(sqs_client):
    """Start resume worker in background."""
    worker = SQSResumeWorker(sqs_client)
    try:
        await worker.start()
    except Exception as e:
        logger.error(f"Resume worker failed: {e}", exc_info=True)
        worker.is_running = False
```

---

## Configuration

### Create .env File

Create `.env` file in your backend root directory:

```env
# App
APP_NAME=Recruitment Platform
DEBUG=False

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/recruitment_db

# AWS Configuration
AWS_ENABLED=True
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1

# S3 Configuration
S3_BUCKET_NAME=recruitment-resumes-prod
S3_MOCK_ENABLED=False

# SNS Configuration
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789:recruitment-resume-uploads
SNS_MOCK_ENABLED=False

# SQS Configuration
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789/recruitment-resume-processing
SQS_MOCK_ENABLED=False
SQS_POLL_INTERVAL_SECONDS=2
SQS_MAX_MESSAGES_PER_POLL=10
SQS_VISIBILITY_TIMEOUT_SECONDS=30
SQS_MAX_RETRIES=3

# SES Configuration
SES_FROM_EMAIL=noreply@recruitment.com
SES_MOCK_ENABLED=False

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"]
```

---

## Testing & Validation

### Manual Testing Steps

1. **Start Backend with Real AWS**
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Upload Resume**
   ```bash
   curl -X POST http://localhost:8000/resumes/upload \
     -F "file=@test_resume.pdf" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

3. **Monitor SQS Queue**
   - AWS Console → SQS → Select queue → Monitor
   - Should see message count increase when resume is uploaded
   - Should see message count decrease as worker processes

4. **Check S3 Bucket**
   - AWS Console → S3 → Select bucket
   - Should see file with key like: `user_id_random_filename.pdf`

5. **Monitor CloudWatch Logs** (Optional)
   - AWS Console → CloudWatch → Log Groups → `/aws/recruitment/api`

### Integration Test Example

Create `test_aws_integration.py`:

```python
import pytest
import asyncio
from uuid import UUID
from app.modules.resume.service import ResumeService
from app.core.database import AsyncSessionLocal
from app.events.config import EventConfig
from fastapi import UploadFile
from io import BytesIO


@pytest.mark.asyncio
async def test_resume_upload_to_s3():
    """Test resume upload to real S3."""
    
    # Create test file
    test_file = UploadFile(
        file=BytesIO(b"PDF mock content"),
        filename="test_resume.pdf"
    )
    
    # Create service with real AWS clients
    async with AsyncSessionLocal() as db:
        service = ResumeService(db)
        
        # Create test user
        from app.core.models import User
        test_user = User(
            id=UUID('00000000-0000-0000-0000-000000000001'),
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        db.add(test_user)
        await db.commit()
        
        # Upload resume
        resume = await service.upload_resume(test_user.id, test_file)
        
        # Verify resume record created
        assert resume.id is not None
        assert resume.status == "UPLOADED"
        
        # Verify file in S3 (you can add explicit verification here)
        # For real S3, file is actually stored


@pytest.mark.asyncio
async def test_sqs_message_flow():
    """Test message flow through SNS/SQS."""
    
    sqs = EventConfig.get_sqs_client()
    
    # Receive messages (should have one from upload test)
    messages = await sqs.receive_messages("resume-processing-queue", max_messages=1)
    
    if messages:
        msg = messages[0]
        print(f"Received message: {msg}")
        
        # Verify message structure
        assert 'body' in msg
        assert 'receipt_handle' in msg
        
        # Delete message (simulate processing)
        result = await sqs.delete_message("resume-processing-queue", msg['receipt_handle'])
        assert result is True


@pytest.mark.asyncio
async def test_ses_email_sending():
    """Test email sending via SES."""
    
    from app.modules.email.template_service import EmailTemplateService
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        service = EmailTemplateService(db)
        
        # Send test email
        message_id = await service.ses_client.send_email(
            to_addresses=["test@example.com"],
            subject="Test Email",
            body="This is a test email from AWS SES"
        )
        
        assert message_id is not None
        print(f"Email sent with MessageId: {message_id}")
```

---

## Deployment Strategies

### Strategy 1: Gradual Rollout (Recommended)

```env
# Development
AWS_ENABLED=False  # Use mocks
S3_MOCK_ENABLED=True
SNS_MOCK_ENABLED=True
SQS_MOCK_ENABLED=True
SES_MOCK_ENABLED=True

# Staging
AWS_ENABLED=True
S3_MOCK_ENABLED=False
SNS_MOCK_ENABLED=False
SQS_MOCK_ENABLED=False
SES_MOCK_ENABLED=False  # Use sandbox for testing

# Production
AWS_ENABLED=True
# (All mock settings false)
# SES upgraded to production mode
```

### Strategy 2: Feature Flag Approach

Add feature flag in config:

```python
# app/core/config.py
USE_REAL_AWS_S3: bool = True  # Can be flipped per environment
USE_REAL_AWS_SNS: bool = True
USE_REAL_AWS_SQS: bool = True
USE_REAL_AWS_SES: bool = True
```

Update EventConfig and services to check these flags.

### Strategy 3: Blue-Green Deployment

1. **Blue Environment** (Current) - Uses mocks
2. **Green Environment** (New) - Uses real AWS
3. Switch traffic after validation

---

## Best Practices for Production

1. **IAM Least Privilege**
   - Use specific bucket/topic/queue ARNs
   - Don't use wildcards (*) in production

2. **Error Handling & Retries**
   - Implement exponential backoff
   - Max 3 retries for SQS messages
   - Send failed messages to DLQ

3. **Monitoring**
   - CloudWatch Metrics
   - CloudWatch Logs (configured in workers)
   - SNS alarms for failures

4. **Security**
   - Encrypt data in transit (HTTPS/TLS)
   - Encrypt data at rest (S3 SSE-S3 or SSE-KMS)
   - Rotate credentials regularly
   - Use IAM roles for EC2/ECS instead of IAM user keys

5. **Cost Optimization**
   - S3 lifecycle policies (delete after 90 days)
   - SQS long polling (20 seconds default)
   - SES sending preferences (only necessary recipients)

6. **Logging**
   - Use structured logging (JSON format)
   - Include correlation IDs for tracing
   - Log to CloudWatch for centralization

---

## Rollback Plan

If issues occur with real AWS:

1. **Quick Rollback** - Set mock flags back to True in `.env`:
   ```env
   AWS_ENABLED=False
   S3_MOCK_ENABLED=True
   SNS_MOCK_ENABLED=True
   SQS_MOCK_ENABLED=True
   SES_MOCK_ENABLED=True
   ```

2. **Restart Backend**
   ```bash
   # Kill current process and restart
   python -m uvicorn app.main:app --reload
   ```

3. **All new requests will use mocks** - existing data remains in AWS (can be migrated back if needed)

---

## Next Steps

1. Complete AWS Console setup (all 9 steps)
2. Create `.env` file with actual AWS credentials
3. Deploy new code with boto3 clients
4. Test with integration tests
5. Monitor CloudWatch logs during first 24 hours
6. Gradually increase traffic to real AWS services
7. Archive or delete mock implementation once confident

