"""
Enhanced logging configuration for AWS service tracking
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Log file paths
APP_LOG = LOGS_DIR / "app.log"
AWS_LOG = LOGS_DIR / "aws_services.log"
FLOW_LOG = LOGS_DIR / "application_flow.log"

# Logging format
DETAILED_FORMAT = '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s'
AWS_FORMAT = '%(asctime)s | [AWS] %(name)s | %(levelname)-8s | %(message)s'
FLOW_FORMAT = '%(asctime)s | [FLOW] %(name)s | %(levelname)-8s | %(message)s'

def setup_logger(name, log_file, format_string, level=logging.INFO):
    """Setup logger with file and console handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(format_string)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger

# Main application logger
app_logger = setup_logger('app', APP_LOG, DETAILED_FORMAT)

# AWS services logger
aws_logger = setup_logger('aws_services', AWS_LOG, AWS_FORMAT)

# Application flow logger
flow_logger = setup_logger('flow', FLOW_LOG, FLOW_FORMAT)

# Get AWS service loggers
def get_aws_logger(service_name):
    """Get logger for specific AWS service"""
    logger = logging.getLogger(f'aws.{service_name}')
    logger.setLevel(logging.DEBUG)
    
    # AWs log file
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    handler = logging.FileHandler(AWS_LOG, encoding='utf-8')
    handler.setFormatter(logging.Formatter(AWS_FORMAT))
    logger.addHandler(handler)
    
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(AWS_FORMAT))
    logger.addHandler(console)
    
    return logger

# Get flow logger
def get_flow_logger(component):
    """Get logger for specific application component"""
    logger = logging.getLogger(f'flow.{component}')
    logger.setLevel(logging.DEBUG)
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    handler = logging.FileHandler(FLOW_LOG, encoding='utf-8')
    handler.setFormatter(logging.Formatter(FLOW_FORMAT))
    logger.addHandler(handler)
    
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(FLOW_FORMAT))
    logger.addHandler(console)
    
    return logger

# Loggers for each component
s3_logger = get_aws_logger('S3')
sns_logger = get_aws_logger('SNS')
sqs_logger = get_aws_logger('SQS')
ses_logger = get_aws_logger('SES')

upload_logger = get_flow_logger('upload')
processing_logger = get_flow_logger('processing')
email_logger = get_flow_logger('email')
