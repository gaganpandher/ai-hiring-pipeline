"""
schemas/common.py
─────────────────
Reusable response wrappers used across all endpoints.

Instead of returning raw data directly, we wrap everything
in a consistent envelope so the frontend always knows
exactly what shape to expect.

Every API response follows one of these shapes:
  Success:  { "success": true,  "data": {...},  "message": "..." }
  Error:    { "success": false, "error": {...}, "message": "..." }
  List:     { "success": true,  "data": [...],  "total": N, "page": N }
"""

from pydantic import Field
from typing import TypeVar, Generic, Optional, List, Any
from app.schemas.base import Base

T = TypeVar("T")


class SuccessResponse(Base, Generic[T]):
    """
    Standard wrapper for single-object responses.
    Generic[T] means the data field can hold any schema type.

    Usage in a route:
        return SuccessResponse(data=user, message="User created")
    """
    success: bool    = True
    message: str     = "OK"
    data:    T


class PaginatedResponse(Base, Generic[T]):
    """
    Standard wrapper for list/paginated responses.
    Every list endpoint returns this shape so the frontend
    can build consistent pagination controls.
    """
    success:  bool      = True
    data:     List[T]
    total:    int        = Field(description="Total records matching the query")
    page:     int        = Field(description="Current page number (1-based)")
    per_page: int        = Field(description="Items per page")
    pages:    int        = Field(description="Total number of pages")

    @classmethod
    def build(
        cls,
        data: List[T],
        total: int,
        page: int,
        per_page: int
    ) -> "PaginatedResponse[T]":
        """Helper to calculate pages automatically."""
        import math
        return cls(
            data=data,
            total=total,
            page=page,
            per_page=per_page,
            pages=math.ceil(total / per_page) if per_page else 1,
        )


class ErrorDetail(Base):
    """Structured error info returned on 4xx/5xx responses."""
    code:    str            = Field(description="Machine-readable error code")
    message: str            = Field(description="Human-readable description")
    field:   Optional[str]  = Field(None, description="Which field caused the error")


class ErrorResponse(Base):
    """Standard error envelope."""
    success: bool        = False
    error:   ErrorDetail
    message: str


class MessageResponse(Base):
    """Simple response for actions that don't return data."""
    success: bool = True
    message: str
