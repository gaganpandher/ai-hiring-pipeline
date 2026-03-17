from pydantic import Field
from typing import Optional
from datetime import datetime
from app.models.application import ApplicationStatus
from app.schemas.base import Base


class ApplicationCreate(Base):
    job_id:        str
    cover_letter:  Optional[str] = Field(None, max_length=5000)
    linkedin_url:  Optional[str] = Field(None, max_length=300)
    portfolio_url: Optional[str] = Field(None, max_length=300)


class ApplicationDecision(Base):
    status:          ApplicationStatus
    recruiter_notes: Optional[str] = Field(None, max_length=2000)


class ScoreSummary(Base):
    overall_score:    int
    skills_score:     Optional[float] = None
    experience_score: Optional[float] = None
    education_score:  Optional[float] = None
    keyword_score:    Optional[float] = None
    scored_at:        datetime


class JobSummaryNested(Base):
    id:         str
    title:      str
    department: str


class UserSummaryNested(Base):
    id:        str
    full_name: str
    email:     str


class ApplicationResponse(Base):
    id:               str
    job_id:           str
    applicant_id:     str
    resume_path:      str
    cover_letter:     Optional[str] = None
    linkedin_url:     Optional[str] = None
    portfolio_url:    Optional[str] = None
    status:           ApplicationStatus
    submitted_at:     datetime
    reviewed_at:      Optional[datetime] = None
    decided_at:       Optional[datetime] = None
    updated_at:       datetime
    job:              Optional[JobSummaryNested]  = None
    applicant:        Optional[UserSummaryNested] = None
    score:            Optional[ScoreSummary]      = None


class ApplicationSummary(Base):
    id:           str
    job_id:       str
    status:       ApplicationStatus
    submitted_at: datetime
    score:        Optional[ScoreSummary]      = None
    job:          Optional[JobSummaryNested]  = None