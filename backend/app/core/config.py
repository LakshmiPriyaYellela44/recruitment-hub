import os
from pydantic_settings import BaseSettings
from typing import Optional
from urllib.parse import quote_plus


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Recruitment Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "recruitment_db"
    DATABASE_URL: Optional[str] = None
    DB_CONNECTION_RETRIES: int = 5
    DB_CONNECTION_RETRY_DELAY: float = 1.0

    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL

        encoded_user = quote_plus(self.DB_USER)
        encoded_password = quote_plus(self.DB_PASSWORD)
        return f"postgresql+asyncpg://{encoded_user}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AWS Configuration
    AWS_ENABLED: bool = False  # Set to True to use real AWS
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"

    # S3 Configuration
    S3_BUCKET_NAME: str = "recruitment-resumes-prod"
    S3_MOCK_ENABLED: bool = False  # Use real S3
    S3_MOCK_STORAGE_PATH: str = "./storage/resumes"

    # SNS Configuration
    SNS_TOPIC_ARN: str = "arn:aws:sns:us-east-1:432305066755:recruitment-resume-uploads"
    SNS_MOCK_ENABLED: bool = False  # Use real SNS

    # SQS Configuration
    SQS_QUEUE_URL: str = "https://sqs.us-east-1.amazonaws.com/432305066755/recruitment-resume-processing"
    SQS_MOCK_ENABLED: bool = False  # Use real SQS
    SQS_POLL_INTERVAL_SECONDS: int = 2
    SQS_MAX_MESSAGES_PER_POLL: int = 10
    SQS_VISIBILITY_TIMEOUT_SECONDS: int = 30
    SQS_MAX_RETRIES: int = 3

    # SES Configuration
    SES_FROM_EMAIL: str = "priyachatgpt44@gmail.com"
    SES_MOCK_ENABLED: bool = False  # Use real SES
    EMAIL_LOG_PATH: str = "./logs/emails.log"

    # Event Queue
    QUEUE_MOCK_ENABLED: bool = False  # Use real SQS

    # Resume Processing
    RESUME_SYNC_PARSING: bool = True  # Parse resumes synchronously instead of async (for development)

    # AI Configuration
    GOOGLE_API_KEY: str = ""
    USE_GOOGLE_GEMINI: bool = False
    USE_CHROMA: bool = False

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
 
