"""
schemas/job.py
──────────────
Pydantic schemas for the Job resource.
"""

from pydantic import Field, field_validator, model_validator
from typing import Optional
from datetime import datetime
from app.models.job import JobStatus, ExperienceLevel
from app.schemas.base import Base, TimestampMixin
from app.schemas.user import UserSummary


class JobCreate(Base):
    """Body of POST /jobs — recruiter creating a new job posting."""
    id:               Optional[str]  = Field(None, max_length=36, pattern=r"^[A-Za-z0-9\-_]+$")
    title:            str            = Field(..., min_length=3, max_length=200)
    department:       str            = Field(..., min_length=2, max_length=100)
    location:         Optional[str]  = Field(None, max_length=150)
    description:      str            = Field(..., min_length=50)
    requirements:     Optional[str]  = None
    salary_min:       Optional[int]  = Field(None, ge=0,  description="Min salary USD")
    salary_max:       Optional[int]  = Field(None, ge=0,  description="Max salary USD")
    experience_level: ExperienceLevel = ExperienceLevel.MID
    closes_at:        Optional[datetime] = None

    # Business rule: salary_max must be >= salary_min
    # model_validator runs AFTER all individual fields are validated
    @model_validator(mode="after")
    def check_salary_range(self) -> "JobCreate":
        if self.salary_min and self.salary_max:
            if self.salary_max < self.salary_min:
                raise ValueError("salary_max must be greater than salary_min")
        return self


class JobUpdate(Base):
    """Body of PATCH /jobs/{id} — all fields optional."""
    title:            Optional[str]           = Field(None, min_length=3, max_length=200)
    department:       Optional[str]           = Field(None, min_length=2, max_length=100)
    location:         Optional[str]           = None
    description:      Optional[str]           = Field(None, min_length=50)
    requirements:     Optional[str]           = None
    salary_min:       Optional[int]           = Field(None, ge=0)
    salary_max:       Optional[int]           = Field(None, ge=0)
    experience_level: Optional[ExperienceLevel] = None
    status:           Optional[JobStatus]     = None
    closes_at:        Optional[datetime]      = None


class JobResponse(TimestampMixin):
    """Full job details returned by the API."""
    id:               str
    title:            str
    department:       str
    location:         Optional[str]
    description:      str
    requirements:     Optional[str]
    salary_min:       Optional[int]
    salary_max:       Optional[int]
    experience_level: ExperienceLevel
    status:           JobStatus
    closes_at:        Optional[datetime]
    poster_id:        str
    # Nested summary — frontend gets name/email without extra API call
    poster:           Optional[UserSummary] = None


class JobSummary(Base):
    """
    Lightweight job reference used inside ApplicationResponse.
    Avoids returning the full description in every application list.
    """
    id:         str
    title:      str
    department: str
    status:     JobStatus
