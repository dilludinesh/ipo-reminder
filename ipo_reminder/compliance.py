"""Compliance and audit logging system for regulatory requirements."""
import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from ..database import DatabaseManager, AuditLog

logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    """Types of audit events."""
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    IPO_DATA_FETCH = "ipo_data_fetch"
    EMAIL_SEND = "email_send"
    EMAIL_FAILURE = "email_failure"
    CACHE_OPERATION = "cache_operation"
    API_CALL = "api_call"
    API_FAILURE = "api_failure"
    CONFIG_CHANGE = "config_change"
    SECURITY_EVENT = "security_event"
    DATA_PROCESSING = "data_processing"
    ERROR_OCCURRED = "error_occurred"
    USER_ACTION = "user_action"

class ComplianceLevel(Enum):
    """Compliance levels for different operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """Audit event data structure."""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    resource: str
    action: str
    status: str  # SUCCESS, FAILURE, WARNING
    details: Dict[str, Any]
    compliance_level: ComplianceLevel
    ip_address: Optional[str]
    user_agent: Optional[str]
    checksum: Optional[str]

    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.checksum:
            self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate SHA256 checksum of the event data."""
        event_data = {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'session_id': self.session_id,
            'resource': self.resource,
            'action': self.action,
            'status': self.status,
            'details': json.dumps(self.details, sort_keys=True, default=str),
            'compliance_level': self.compliance_level.value,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }

        data_str = json.dumps(event_data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['compliance_level'] = self.compliance_level.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

class ComplianceLogger:
    """Compliance and audit logging system."""

    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.retention_days = 365  # Keep logs for 1 year
        self.max_log_size_mb = 100  # Max size per log file
        self.encryption_enabled = True

    def log_event(self, event: AuditEvent):
        """Log an audit event."""
        try:
            # Persist to database
            with DatabaseManager.get_session() as session:
                db_log = AuditLog(
                    event_id=event.event_id,
                    event_type=event.event_type.value,
                    timestamp=event.timestamp,
                    user_id=event.user_id,
                    session_id=event.session_id,
                    resource=event.resource,
                    action=event.action,
                    status=event.status,
                    details=json.dumps(event.details),
                    compliance_level=event.compliance_level.value,
                    ip_address=event.ip_address,
                    user_agent=event.user_agent,
                    checksum=event.checksum
                )
                session.add(db_log)

            # Log to file for immediate access
            logger.info(f"AUDIT: {event.event_type.value} - {event.resource} - {event.status}")

            # Handle high-compliance events
            if event.compliance_level in [ComplianceLevel.HIGH, ComplianceLevel.CRITICAL]:
                self._handle_high_compliance_event(event)

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            # Fallback to file-only logging
            self._log_to_file(event)

    def _log_to_file(self, event: AuditEvent):
        """Fallback logging to file."""
        try:
            log_entry = json.dumps(event.to_dict(), default=str)
            logger.error(f"AUDIT_FALLBACK: {log_entry}")
        except Exception as e:
            logger.critical(f"Complete audit logging failure: {e}")

    def _handle_high_compliance_event(self, event: AuditEvent):
        """Handle high-compliance level events."""
        # Could send notifications, trigger alerts, etc.
        logger.warning(f"HIGH COMPLIANCE EVENT: {event.event_type.value} - {event.resource}")

    def log_system_startup(self, details: Dict[str, Any] = None):
        """Log system startup event."""
        event = AuditEvent(
            event_id="",
            event_type=AuditEventType.SYSTEM_STARTUP,
            timestamp=datetime.utcnow(),
            user_id=None,
            session_id=self.session_id,
            resource="system",
            action="startup",
            status="SUCCESS",
            details=details or {},
            compliance_level=ComplianceLevel.MEDIUM,
            ip_address=None,
            user_agent=None,
            checksum=None
        )
        self.log_event(event)

    def log_system_shutdown(self, details: Dict[str, Any] = None):
        """Log system shutdown event."""
        event = AuditEvent(
            event_id="",
            event_type=AuditEventType.SYSTEM_SHUTDOWN,
            timestamp=datetime.utcnow(),
            user_id=None,
            session_id=self.session_id,
            resource="system",
            action="shutdown",
            status="SUCCESS",
            details=details or {},
            compliance_level=ComplianceLevel.MEDIUM,
            ip_address=None,
            user_agent=None,
            checksum=None
        )
        self.log_event(event)

    def log_ipo_data_fetch(self, source: str, count: int, status: str, details: Dict[str, Any] = None):
        """Log IPO data fetching event."""
        event = AuditEvent(
            event_id="",
            event_type=AuditEventType.IPO_DATA_FETCH,
            timestamp=datetime.utcnow(),
            user_id=None,
            session_id=self.session_id,
            resource=f"ipo_data:{source}",
            action="fetch",
            status=status,
            details={
                'source': source,
                'record_count': count,
                **(details or {})
            },
            compliance_level=ComplianceLevel.MEDIUM,
            ip_address=None,
            user_agent=None,
            checksum=None
        )
        self.log_event(event)

    def log_email_send(self, recipient: str, subject: str, status: str, details: Dict[str, Any] = None):
        """Log email sending event."""
        event = AuditEvent(
            event_id="",
            event_type=AuditEventType.EMAIL_SEND,
            timestamp=datetime.utcnow(),
            user_id=None,
            session_id=self.session_id,
            resource=f"email:{recipient}",
            action="send",
            status=status,
            details={
                'recipient': recipient,
                'subject': subject,
                **(details or {})
            },
            compliance_level=ComplianceLevel.HIGH,
            ip_address=None,
            user_agent=None,
            checksum=None
        )
        self.log_event(event)

    def log_api_call(self, api_name: str, endpoint: str, status: str, details: Dict[str, Any] = None):
        """Log API call event."""
        event = AuditEvent(
            event_id="",
            event_type=AuditEventType.API_CALL,
            timestamp=datetime.utcnow(),
            user_id=None,
            session_id=self.session_id,
            resource=f"api:{api_name}:{endpoint}",
            action="call",
            status=status,
            details={
                'api_name': api_name,
                'endpoint': endpoint,
                **(details or {})
            },
            compliance_level=ComplianceLevel.MEDIUM,
            ip_address=None,
            user_agent=None,
            checksum=None
        )
        self.log_event(event)

    def log_error(self, error_type: str, error_message: str, details: Dict[str, Any] = None):
        """Log error event."""
        event = AuditEvent(
            event_id="",
            event_type=AuditEventType.ERROR_OCCURRED,
            timestamp=datetime.utcnow(),
            user_id=None,
            session_id=self.session_id,
            resource=f"error:{error_type}",
            action="occurred",
            status="FAILURE",
            details={
                'error_type': error_type,
                'error_message': error_message,
                **(details or {})
            },
            compliance_level=ComplianceLevel.HIGH,
            ip_address=None,
            user_agent=None,
            checksum=None
        )
        self.log_event(event)

    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related event."""
        event = AuditEvent(
            event_id="",
            event_type=AuditEventType.SECURITY_EVENT,
            timestamp=datetime.utcnow(),
            user_id=None,
            session_id=self.session_id,
            resource=f"security:{event_type}",
            action="detected",
            status="WARNING",
            details=details,
            compliance_level=ComplianceLevel.CRITICAL,
            ip_address=None,
            user_agent=None,
            checksum=None
        )
        self.log_event(event)

    def get_audit_trail(self, resource: str = None, event_type: AuditEventType = None,
                       start_date: datetime = None, end_date: datetime = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve audit trail with filtering."""
        try:
            with DatabaseManager.get_session() as session:
                query = session.query(AuditLog)

                if resource:
                    query = query.filter(AuditLog.resource.like(f"%{resource}%"))
                if event_type:
                    query = query.filter(AuditLog.event_type == event_type.value)
                if start_date:
                    query = query.filter(AuditLog.timestamp >= start_date)
                if end_date:
                    query = query.filter(AuditLog.timestamp <= end_date)

                query = query.order_by(AuditLog.timestamp.desc()).limit(limit)

                logs = query.all()
                return [log.to_dict() for log in logs]

        except Exception as e:
            logger.error(f"Failed to retrieve audit trail: {e}")
            return []

    def generate_compliance_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate compliance report for a date range."""
        try:
            audit_trail = self.get_audit_trail(
                start_date=start_date,
                end_date=end_date,
                limit=10000  # Large limit for reporting
            )

            report = {
                'report_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_events': len(audit_trail),
                    'events_by_type': {},
                    'events_by_status': {},
                    'compliance_violations': 0,
                    'security_events': 0
                },
                'details': audit_trail
            }

            # Analyze events
            for event in audit_trail:
                event_type = event['event_type']
                status = event['status']

                # Count by type
                if event_type not in report['summary']['events_by_type']:
                    report['summary']['events_by_type'][event_type] = 0
                report['summary']['events_by_type'][event_type] += 1

                # Count by status
                if status not in report['summary']['events_by_status']:
                    report['summary']['events_by_status'][status] = 0
                report['summary']['events_by_status'][status] += 1

                # Count violations and security events
                if status == 'FAILURE':
                    report['summary']['compliance_violations'] += 1
                if event_type == 'security_event':
                    report['summary']['security_events'] += 1

            return report

        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {'error': str(e)}

    def cleanup_old_logs(self, days_to_keep: int = None):
        """Clean up old audit logs beyond retention period."""
        if days_to_keep is None:
            days_to_keep = self.retention_days

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        try:
            with DatabaseManager.get_session() as session:
                deleted_count = session.query(AuditLog).filter(
                    AuditLog.timestamp < cutoff_date
                ).delete()

                logger.info(f"Cleaned up {deleted_count} old audit log entries")

        except Exception as e:
            logger.error(f"Failed to cleanup old audit logs: {e}")

# Global compliance logger instance
compliance_logger = ComplianceLogger()

# Convenience functions
def log_event(event: AuditEvent):
    """Log an audit event."""
    compliance_logger.log_event(event)

def log_system_startup(details: Dict[str, Any] = None):
    """Log system startup."""
    compliance_logger.log_system_startup(details)

def log_ipo_data_fetch(source: str, count: int, status: str, details: Dict[str, Any] = None):
    """Log IPO data fetch."""
    compliance_logger.log_ipo_data_fetch(source, count, status, details)

def log_email_send(recipient: str, subject: str, status: str, details: Dict[str, Any] = None):
    """Log email send."""
    compliance_logger.log_email_send(recipient, subject, status, details)

def get_audit_trail(**kwargs) -> List[Dict[str, Any]]:
    """Get audit trail."""
    return compliance_logger.get_audit_trail(**kwargs)

def generate_compliance_report(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate compliance report."""
    return compliance_logger.generate_compliance_report(start_date, end_date)
