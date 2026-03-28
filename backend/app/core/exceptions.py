from typing import Any, Dict, Optional


class BaseAppException(Exception):
    """Base exception for the application."""
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }


class ValidationException(BaseAppException):
    """Raised when validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=422,
            details=details
        )


class AuthorizationException(BaseAppException):
    """Raised when user lacks permission."""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=403
        )


class AuthenticationException(BaseAppException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            code="AUTHENTICATION_ERROR",
            message=message,
            status_code=401
        )


class NotFoundException(BaseAppException):
    """Raised when resource not found."""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource} not found: {identifier}",
            status_code=404,
            details={"resource": resource, "identifier": identifier}
        )


class ConflictException(BaseAppException):
    """Raised when resource already exists."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=409,
            details=details
        )
