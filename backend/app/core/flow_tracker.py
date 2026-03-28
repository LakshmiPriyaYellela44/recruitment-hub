"""
Comprehensive AWS Service Flow Tracker
Logs every step of the application-AWS integration
"""

import logging
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict

class ServiceEvent(Enum):
    """AWS service event types"""
    # S3 events
    S3_UPLOAD_START = "s3.upload.start"
    S3_UPLOAD_SUCCESS = "s3.upload.success"
    S3_UPLOAD_ERROR = "s3.upload.error"
    
    # SNS events
    SNS_PUBLISH_START = "sns.publish.start"
    SNS_PUBLISH_SUCCESS = "sns.publish.success"
    SNS_PUBLISH_ERROR = "sns.publish.error"
    
    # SQS events
    SQS_SEND_START = "sqs.send.start"
    SQS_SEND_SUCCESS = "sqs.send.success"
    SQS_SEND_ERROR = "sqs.send.error"
    SQS_RECEIVE_START = "sqs.receive.start"
    SQS_RECEIVE_SUCCESS = "sqs.receive.success"
    
    # SES events
    SES_SEND_START = "ses.send.start"
    SES_SEND_SUCCESS = "ses.send.success"
    SES_SEND_ERROR = "ses.send.error"
    
    # Database events
    DB_INSERT_START = "db.insert.start"
    DB_INSERT_SUCCESS = "db.insert.success"
    DB_INSERT_ERROR = "db.insert.error"
    
    # Flow events
    FLOW_UPLOAD_START = "flow.upload.start"
    FLOW_UPLOAD_COMPLETE = "flow.upload.complete"
    FLOW_PROCESS_START = "flow.process.start"
    FLOW_PROCESS_COMPLETE = "flow.process.complete"

class AWSFlowTracker:
    """Track and log AWS service interactions"""
    
    def __init__(self):
        self.logger = logging.getLogger('aws_flow_tracker')
        self.logger.setLevel(logging.DEBUG)
        
        # Create flow log file
        from pathlib import Path
        logs_dir = Path(__file__).parent.parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        handler = logging.FileHandler(logs_dir / "aws_flow.log", encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Track flow events
        self.flow_events = []
    
    def log_event(self, event: ServiceEvent, details: Dict[str, Any] = None, **kwargs):
        """Log a service event"""
        details = details or kwargs
        details['timestamp'] = datetime.now().isoformat()
        details['event'] = event.value
        
        # Format message
        msg = f"[{event.value}] {json.dumps(details, indent=0, default=str)}"
        
        if 'error' in event.value or 'Error' in str(details.get('status', '')):
            self.logger.error(msg)
        else:
            self.logger.info(msg)
        
        self.flow_events.append(details)
    
    def log_s3_upload(self, key: str, size: int, status: str = "success", error: str = None):
        """Log S3 upload event"""
        if status == "start":
            self.log_event(ServiceEvent.S3_UPLOAD_START, 
                          key=key, size=size, service="S3")
        elif status == "success":
            self.log_event(ServiceEvent.S3_UPLOAD_SUCCESS,
                          key=key, size=size, service="S3", message="File uploaded to S3")
        else:
            self.log_event(ServiceEvent.S3_UPLOAD_ERROR,
                          key=key, service="S3", error=error)
    
    def log_sns_publish(self, topic_arn: str, message_id: str = None, status: str = "success", error: str = None):
        """Log SNS publish event"""
        if status == "start":
            self.log_event(ServiceEvent.SNS_PUBLISH_START,
                          topic=topic_arn, service="SNS")
        elif status == "success":
            self.log_event(ServiceEvent.SNS_PUBLISH_SUCCESS,
                          topic=topic_arn, message_id=message_id, service="SNS", message="Event published to SNS")
        else:
            self.log_event(ServiceEvent.SNS_PUBLISH_ERROR,
                          topic=topic_arn, service="SNS", error=error)
    
    def log_sqs_send(self, queue_url: str, message_id: str = None, status: str = "success", error: str = None):
        """Log SQS send event"""
        if status == "start":
            self.log_event(ServiceEvent.SQS_SEND_START,
                          queue=queue_url, service="SQS")
        elif status == "success":
            self.log_event(ServiceEvent.SQS_SEND_SUCCESS,
                          queue=queue_url, message_id=message_id, service="SQS", message="Message sent to SQS")
        else:
            self.log_event(ServiceEvent.SQS_SEND_ERROR,
                          queue=queue_url, service="SQS", error=error)
    
    def log_sqs_receive(self, queue_url: str, message_count: int = 0):
        """Log SQS receive event"""
        self.log_event(ServiceEvent.SQS_RECEIVE_SUCCESS,
                      queue=queue_url, message_count=message_count, service="SQS",
                      message=f"Received {message_count} messages from SQS")
    
    def log_ses_send(self, recipient: str, subject: str = "", status: str = "success", error: str = None):
        """Log SES email send event"""
        if status == "start":
            self.log_event(ServiceEvent.SES_SEND_START,
                          recipient=recipient, subject=subject, service="SES")
        elif status == "success":
            self.log_event(ServiceEvent.SES_SEND_SUCCESS,
                          recipient=recipient, subject=subject, service="SES",
                          message=f"Email sent to {recipient}")
        else:
            self.log_event(ServiceEvent.SES_SEND_ERROR,
                          recipient=recipient, service="SES", error=error)
    
    def log_db_operation(self, operation: str, table: str, status: str = "success", error: str = None):
        """Log database operation"""
        if status == "start":
            self.log_event(ServiceEvent.DB_INSERT_START,
                          operation=operation, table=table, service="Database")
        elif status == "success":
            self.log_event(ServiceEvent.DB_INSERT_SUCCESS,
                          operation=operation, table=table, service="Database",
                          message=f"Inserted data into {table}")
        else:
            self.log_event(ServiceEvent.DB_INSERT_ERROR,
                          operation=operation, table=table, service="Database", error=error)
    
    def log_flow_event(self, stage: str, status: str, details: Dict = None):
        """Log application flow event"""
        if stage == "upload":
            if status == "start":
                self.log_event(ServiceEvent.FLOW_UPLOAD_START,
                             message="Resume upload flow initiated")
            else:
                self.log_event(ServiceEvent.FLOW_UPLOAD_COMPLETE,
                             message="Resume upload flow completed", **details or {})
        elif stage == "process":
            if status == "start":
                self.log_event(ServiceEvent.FLOW_PROCESS_START,
                             message="Resume processing flow initiated")
            else:
                self.log_event(ServiceEvent.FLOW_PROCESS_COMPLETE,
                             message="Resume processing completed", **details or {})
    
    def get_flow_summary(self):
        """Get summary of all logged events"""
        summary = {
            'total_events': len(self.flow_events),
            'services_involved': set(),
            'status': 'success',
            'events': self.flow_events
        }
        
        for event in self.flow_events:
            service = event.get('service')
            if service:
                summary['services_involved'].add(service)
            
            if 'error' in event.get('event', ''):
                summary['status'] = 'error'
        
        summary['services_involved'] = list(summary['services_involved'])
        return summary

# Global tracker instance
flow_tracker = AWSFlowTracker()

def get_flow_tracker():
    """Get the global flow tracker instance"""
    return flow_tracker
