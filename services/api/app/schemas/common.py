"""
Common Schemas
"""
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response schema"""
    items: List[T]
    total: int
    page: int
    size: int

    @classmethod
    def create(cls, items: List[T], total: int, page: int, size: int):
        """Helper to create paginated response with calculated pages"""
        return cls(items=items, total=total, page=page, size=size)


# Alias for compatibility
PageResponse = PaginatedResponse


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str
    code: Optional[str] = None
