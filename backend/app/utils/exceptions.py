from typing import Any


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed", details: dict[str, Any] | None = None):
        super().__init__(message=message, status_code=401, details=details)


class AuthorizationError(AppException):
    def __init__(self, message: str = "Not authorized", details: dict[str, Any] | None = None):
        super().__init__(message=message, status_code=403, details=details)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None):
        super().__init__(message=message, status_code=404, details=details)


class ValidationError(AppException):
    def __init__(self, message: str = "Validation error", details: dict[str, Any] | None = None):
        super().__init__(message=message, status_code=422, details=details)


class ExternalAPIError(AppException):
    def __init__(
        self,
        message: str = "External API error",
        source: str = "unknown",
        details: dict[str, Any] | None = None
    ):
        details = details or {}
        details["source"] = source
        super().__init__(message=message, status_code=502, details=details)


class RateLimitError(AppException):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        details: dict[str, Any] | None = None
    ):
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message=message, status_code=429, details=details)


class DatabaseError(AppException):
    def __init__(self, message: str = "Database error", details: dict[str, Any] | None = None):
        super().__init__(message=message, status_code=500, details=details)
