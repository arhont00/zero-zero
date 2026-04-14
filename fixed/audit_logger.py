"""
Audit logging for security events and user actions.
Logs all security-relevant events for compliance and debugging.
"""
import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditLogger:
    """Logs security and audit events."""
    
    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or Path('logs/audit.log')
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create audit logger
        self.audit_logger = logging.getLogger('audit')
        handler = logging.FileHandler(self.log_path, encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.audit_logger.addHandler(handler)
        self.audit_logger.setLevel(logging.INFO)
    
    def log_event(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        action: str = '',
        details: Optional[Dict[str, Any]] = None,
        status: str = 'SUCCESS',
        severity: str = 'INFO'
    ):
        """Log an audit event."""
        event_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'action': action,
            'status': status,
            'severity': severity,
            'details': details or {}
        }
        
        log_message = json.dumps(event_data, ensure_ascii=False)
        
        if severity == 'CRITICAL':
            self.audit_logger.critical(log_message)
        elif severity == 'ERROR':
            self.audit_logger.error(log_message)
        elif severity == 'WARNING':
            self.audit_logger.warning(log_message)
        else:
            self.audit_logger.info(log_message)
    
    def log_authentication(self, user_id: int, success: bool):
        """Log authentication events."""
        self.log_event(
            event_type='AUTHENTICATION',
            user_id=user_id,
            action='login',
            status='SUCCESS' if success else 'FAILED',
            severity='WARNING' if not success else 'INFO'
        )
    
    def log_authorization(self, user_id: int, resource: str, allowed: bool):
        """Log authorization events."""
        self.log_event(
            event_type='AUTHORIZATION',
            user_id=user_id,
            action=f'access_attempt',
            details={'resource': resource},
            status='ALLOWED' if allowed else 'DENIED',
            severity='WARNING' if not allowed else 'INFO'
        )
    
    def log_data_access(self, user_id: int, data_type: str, operation: str):
        """Log data access events."""
        self.log_event(
            event_type='DATA_ACCESS',
            user_id=user_id,
            action=f'{operation}_{data_type}',
            details={'data_type': data_type}
        )
    
    def log_security_incident(
        self,
        incident_type: str,
        user_id: Optional[int],
        details: Dict[str, Any]
    ):
        """Log security incidents."""
        self.log_event(
            event_type='SECURITY_INCIDENT',
            user_id=user_id,
            action=incident_type,
            details=details,
            severity='CRITICAL'
        )
    
    def log_rate_limit_exceeded(self, user_id: int, endpoint: str):
        """Log rate limit exceeded."""
        self.log_event(
            event_type='RATE_LIMIT',
            user_id=user_id,
            action='exceeded',
            details={'endpoint': endpoint},
            severity='WARNING'
        )