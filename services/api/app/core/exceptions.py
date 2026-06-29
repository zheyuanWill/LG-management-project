"""
Custom Business Exceptions

Provides a hierarchy of business exceptions that are automatically
converted to structured JSON error responses by the global exception handler.
"""
from typing import Optional, Any


class BusinessError(Exception):
    """Base class for all business exceptions."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        detail: Optional[str] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class NotFoundError(BusinessError):
    """Resource not found."""

    def __init__(self, resource: str, identifier: Any = None):
        detail = f"{resource} (id={identifier})" if identifier else resource
        super().__init__(
            code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource}不存在",
            status_code=404,
            detail=detail,
        )


class ForbiddenError(BusinessError):
    """Permission denied."""

    def __init__(self, message: str = "无权执行此操作"):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=403,
        )


class ConflictError(BusinessError):
    """Business rule violation or state conflict."""

    def __init__(self, message: str, code: str = "CONFLICT"):
        super().__init__(
            code=code,
            message=message,
            status_code=409,
        )


class InvalidStateTransitionError(BusinessError):
    """Invalid status transition."""

    def __init__(self, resource: str, from_status: str, to_status: str):
        super().__init__(
            code="INVALID_STATE_TRANSITION",
            message=f"不允许从 {from_status} 转换到 {to_status}",
            status_code=400,
            detail=f"{resource}: {from_status} -> {to_status}",
        )


class ValidationError(BusinessError):
    """Input validation error."""

    def __init__(self, message: str, field: Optional[str] = None):
        code = f"VALIDATION_{field.upper()}" if field else "VALIDATION_ERROR"
        super().__init__(
            code=code,
            message=message,
            status_code=422,
        )
