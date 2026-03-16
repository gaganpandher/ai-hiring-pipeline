"""
schemas/user.py
───────────────
Pydantic schemas for the User resource.

Three categories of schemas:
  1. Request schemas  → data coming IN  (what the frontend sends)
  2. Response schemas → data going OUT  (what the API returns)
  3. Internal schemas → used inside services, not exposed via HTTP

Key rule: password_hash NEVER appears in any response schema.
If you forget and put it in UserResponse, every API call
would leak the hashed password. Pydantic prevents this by
only including fields you explicitly declare.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
from app.models.user import UserRole
from app.schemas.base import Base, TimestampMixin


# ── Request Schemas (data coming IN) ─────────────────────────

class UserRegister(Base):
    """
    Body of POST /auth/register
    Pydantic validates all fields before your code even runs.
    If email is invalid or password too short, it auto-returns
    a 422 Unprocessable Entity with a clear error message.
    """
    email: EmailStr = Field(
        ...,                          # ... means required (no default)
        description="Must be a valid email address",
        examples=["jane@example.com"]
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Minimum 8 characters",
        examples=["SecurePass123"]
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Full display name",
        examples=["Jane Smith"]
    )
    role: UserRole = Field(
        default=UserRole.APPLICANT,
        description="User role — defaults to applicant"
    )

    # Custom validator: strip whitespace from name
    @field_validator("full_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class UserLogin(Base):
    """Body of POST /auth/login (JSON version)."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserUpdate(Base):
    """
    Body of PATCH /users/me
    All fields optional — only send what you want to change.
    This is the standard 'partial update' pattern.
    """
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    password:  Optional[str] = Field(None, min_length=8, max_length=100)


# ── Response Schemas (data going OUT) ────────────────────────

class UserResponse(TimestampMixin):
    """
    Returned whenever the API talks about a user.
    Notice: NO password, NO password_hash field.
    Even though the User model has password_hash in the DB,
    it will never appear here because we don't declare it.
    """
    id:            str
    email:         str
    full_name:     str
    role:          UserRole
    is_active:     bool
    last_login_at: Optional[datetime] = None


class UserSummary(Base):
    """
    Lightweight user reference — used inside other responses.
    e.g. JobResponse includes poster: UserSummary (not full UserResponse)
    This avoids deeply nested JSON with too much data.
    """
    id:        str
    full_name: str
    email:     str
    role:      UserRole


# ── Auth Response Schemas ─────────────────────────────────────

class TokenResponse(Base):
    """
    Returned by POST /auth/login and POST /auth/refresh.
    The frontend stores these tokens and sends access_token
    in the Authorization header of every subsequent request.
    """
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int = Field(description="Access token lifetime in seconds")


class LoginResponse(Base):
    """Login returns both the tokens AND the user profile."""
    tokens: TokenResponse
    user:   UserResponse


class RefreshRequest(Base):
    """Body of POST /auth/refresh."""
    refresh_token: str
