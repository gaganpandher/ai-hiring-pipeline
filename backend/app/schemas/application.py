"""
schemas/application.py
──────────────────────
Pydantic schemas for the Application resource.
"""

from pydantic import Field, HttpUrl
from typing import Optional
from datetime import datetime
from app.models.application import ApplicationStatus
from app.schemas.base import Base, TimestampMixin
from app.schemas.user import UserSummary
from app.schemas.job import JobSummary


class ApplicationCreate(Base):
    """
    Body of POST /applications
    resume_path is set server-side after file upload —
    the frontend sends the file separately via multipart form.
    """
    job_id:        str
    cover_letter:  Optional[str]  = Field(None, max_length=5000)
    linkedin_url:  Optional[str]  = Field(None, max_length=300)
    portfolio_url: Optional[str]  = Field(None, max_length=300)


class ApplicationDecision(Base):
    """
    Body of PATCH /applications/{id}/decision
    Only recruiters can call this endpoint (enforced by RBAC).
    """
    status:           ApplicationStatus
    recruiter_notes:  Optional[str] = Field(None, max_length=2000)


class ScoreSummary(Base):
    """Nested score shown inside ApplicationResponse."""
    overall_score:    int
    skills_score:     Optional[float]
    experience_score: Optional[float]
    education_score:  Optional[float]
    keyword_score:    Optional[float]
    scored_at:        datetime


class ApplicationResponse(TimestampMixin):
    """Full application details."""
    id:               str
    job_id:           str
    applicant_id:     str
    resume_path:      str
    cover_letter:     Optional[str]
    linkedin_url:     Optional[str]
    portfolio_url:    Optional[str]
    status:           ApplicationStatus
    submitted_at:     datetime
    reviewed_at:      Optional[datetime]
    decided_at:       Optional[datetime]
    # Nested objects — recruiter sees who applied and for what
    job:              Optional[JobSummary]   = None
    applicant:        Optional[UserSummary]  = None
    score:            Optional[ScoreSummary] = None
    # recruiter_notes intentionally excluded from applicant-facing response
    # The API layer will strip this based on the caller's role


class ApplicationSummary(Base):
    """Lightweight version for list views."""
    id:          str
    job_id:      str
    status:      ApplicationStatus
    submitted_at: datetime
    score:        Optional[ScoreSummary] = None
    job:          Optional[JobSummary]   = None
