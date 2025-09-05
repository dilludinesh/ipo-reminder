"""
Custom exceptions for the IPO Reminder system.

This module defines a hierarchy of custom exceptions for better error handling
and more specific error reporting throughout the application.
"""
from typing import Optional, Dict, Any, Type, Union, List

class IPOReminderError(Exception):
    """Base exception class for all IPO Reminder specific exceptions."""
    
    def __init__(
        self,
        message: str = "An error occurred in the IPO Reminder system",
        status_code: int = 500,
        error_code: str = "internal_server_error",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize the exception.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code (default: 500)
            error_code: Machine-readable error code (default: 'internal_server_error')
            details: Additional error details
            cause: The underlying exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
        
        # Add cause details if available
        if cause:
            self.details['cause'] = str(cause)
            if hasattr(cause, '__traceback__'):
                self.details['traceback'] = self._format_traceback(cause.__traceback__)
    
    def _format_traceback(self, traceback) -> List[Dict[str, Any]]:
        """Format traceback for JSON serialization."""
        import traceback
        return [
            {
                'filename': frame.filename,
                'lineno': frame.lineno,
                'name': frame.name,
                'line': line.strip() if (line := frame.line) else None,
            }
            for frame in traceback.extract_tb(traceback)
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for serialization."""
        return {
            'error': {
                'code': self.error_code,
                'message': self.message,
                'status': self.status_code,
                'details': self.details,
            }
        }

# Configuration Errors (4xx)
class ConfigurationError(IPOReminderError):
    """Base class for configuration-related errors."""
    def __init__(self, message: str = "Configuration error", **kwargs):
        super().__init__(message, status_code=400, error_code="configuration_error", **kwargs)

class MissingConfigurationError(ConfigurationError):
    """Raised when a required configuration is missing."""
    def __init__(self, key: str, **kwargs):
        super().__init__(
            message=f"Missing required configuration: {key}",
            error_code="missing_configuration",
            details={"missing_key": key},
            **kwargs
        )

class InvalidConfigurationError(ConfigurationError):
    """Raised when a configuration value is invalid."""
    def __init__(self, key: str, value: Any, reason: str, **kwargs):
        super().__init__(
            message=f"Invalid configuration for {key}: {reason}",
            error_code="invalid_configuration",
            details={"key": key, "value": value, "reason": reason},
            **kwargs
        )

# Authentication & Authorization Errors (401, 403)
class AuthenticationError(IPOReminderError):
    """Base class for authentication errors."""
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, status_code=401, error_code="authentication_failed", **kwargs)

class AuthorizationError(IPOReminderError):
    """Raised when a user is not authorized to perform an action."""
    def __init__(self, message: str = "Not authorized", **kwargs):
        super().__init__(message, status_code=403, error_code="forbidden", **kwargs)

# Data Validation Errors (400)
class ValidationError(IPOReminderError):
    """Raised when data validation fails."""
    def __init__(self, message: str = "Validation failed", errors: Optional[Dict[str, Any]] = None, **kwargs):
        details = kwargs.pop('details', {})
        if errors:
            details['errors'] = errors
        super().__init__(
            message=message,
            status_code=400,
            error_code="validation_error",
            details=details,
            **kwargs
        )

# Not Found Errors (404)
class NotFoundError(IPOReminderError):
    """Raised when a requested resource is not found."""
    def __init__(self, resource_type: str, resource_id: Any, **kwargs):
        super().__init__(
            message=f"{resource_type} with ID {resource_id} not found",
            status_code=404,
            error_code="not_found",
            details={"resource_type": resource_type, "resource_id": resource_id},
            **kwargs
        )

# Database Errors (500)
class DatabaseError(IPOReminderError):
    """Base class for database-related errors."""
    def __init__(self, message: str = "Database error", **kwargs):
        super().__init__(message, status_code=500, error_code="database_error", **kwargs)

class ConnectionError(DatabaseError):
    """Raised when a database connection cannot be established."""
    def __init__(self, message: str = "Database connection failed", **kwargs):
        super().__init__(message, error_code="database_connection_error", **kwargs)

class TimeoutError(DatabaseError):
    """Raised when a database operation times out."""
    def __init__(self, message: str = "Database operation timed out", **kwargs):
        super().__init__(message, error_code="database_timeout", **kwargs)

class ConstraintViolationError(DatabaseError):
    """Raised when a database constraint is violated."""
    def __init__(self, constraint: str, table: str, **kwargs):
        super().__init__(
            message=f"Database constraint '{constraint}' violation in table '{table}'",
            error_code="constraint_violation",
            details={"constraint": constraint, "table": table},
            **kwargs
        )

# API Errors (5xx)
class APIError(IPOReminderError):
    """Base class for API-related errors."""
    def __init__(self, message: str = "API error", status_code: int = 500, **kwargs):
        super().__init__(message, status_code=status_code, error_code="api_error", **kwargs)

class RateLimitExceededError(APIError):
    """Raised when an API rate limit is exceeded."""
    def __init__(self, message: str = "API rate limit exceeded", retry_after: Optional[int] = None, **kwargs):
        details = kwargs.pop('details', {})
        if retry_after is not None:
            details['retry_after'] = retry_after
        super().__init__(
            message=message,
            status_code=429,
            error_code="rate_limit_exceeded",
            details=details,
            **kwargs
        )

class ServiceUnavailableError(APIError):
    """Raised when an external service is unavailable."""
    def __init__(self, service_name: str, **kwargs):
        super().__init__(
            message=f"Service '{service_name}' is currently unavailable",
            status_code=503,
            error_code="service_unavailable",
            details={"service": service_name},
            **kwargs
        )

# Email Errors
class EmailError(IPOReminderError):
    """Base class for email-related errors."""
    def __init__(self, message: str = "Email error", **kwargs):
        super().__init__(message, status_code=500, error_code="email_error", **kwargs)

class EmailSendError(EmailError):
    """Raised when an email fails to send."""
    def __init__(self, recipient: str, reason: str, **kwargs):
        super().__init__(
            message=f"Failed to send email to {recipient}: {reason}",
            error_code="email_send_failed",
            details={"recipient": recipient, "reason": reason},
            **kwargs
        )

# Circuit Breaker Errors
class CircuitBreakerError(IPOReminderError):
    """Raised when a circuit breaker is open."""
    def __init__(self, service: str, state: str, retry_after: Optional[float] = None, **kwargs):
        details = {"service": service, "state": state}
        if retry_after is not None:
            details['retry_after'] = retry_after
        super().__init__(
            message=f"Circuit breaker for service '{service}' is {state}",
            status_code=503,
            error_code="circuit_breaker_open",
            details=details,
            **kwargs
        )
