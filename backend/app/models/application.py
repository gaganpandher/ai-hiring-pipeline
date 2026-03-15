from sqlalchemy import (
    Column, String, Text, Enum, DateTime,
    ForeignKey, Integer, Boolean
)
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class ApplicationStatus(str, enum.Enum):
    SUBMITTED   = "submitted"    # just came in
    SCREENING   = "screening"    # AI scoring in progress
    REVIEWED    = "reviewed"     # recruiter has seen it
    SHORTLISTED = "shortlisted"  # moved forward
    INTERVIEWING = "interviewing"
    OFFERED     = "offered"
    HIRED       = "hired"
    REJECTED    = "rejected"
    WITHDRAWN   = "withdrawn"    # applicant withdrew


class Application(Base):
    __tablename__ = "applications"

    id              = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id          = Column(CHAR(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    applicant_id    = Column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    status          = Column(Enum(ApplicationStatus), default=ApplicationStatus.SUBMITTED, nullable=False, index=True)

    # Resume
    resume_url      = Column(String(500), nullable=True)
    resume_text     = Column(Text, nullable=True)   # extracted plain text for AI scoring

    # Cover letter
    cover_letter    = Column(Text, nullable=True)

    # Applicant-provided demographic data (optional, for bias analysis)
    # Stored separately to allow anonymisation
    gender          = Column(String(50), nullable=True)
    age_range       = Column(String(20), nullable=True)   # e.g. "25-34"
    ethnicity       = Column(String(100), nullable=True)

    # Recruiter notes
    recruiter_notes = Column(Text, nullable=True)
    rejection_reason = Column(String(255), nullable=True)

    # Flags
    is_flagged      = Column(Boolean, default=False)  # manually flagged by recruiter
    kafka_sent      = Column(Boolean, default=False)  # has been sent to Kafka topic

    # Timestamps
    submitted_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at     = Column(DateTime(timezone=True), nullable=True)
    decided_at      = Column(DateTime(timezone=True), nullable=True)
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    job             = relationship("Job", back_populates="applications")
    applicant       = relationship("User", back_populates="applications", foreign_keys=[applicant_id])
    score           = relationship("Score", back_populates="application", uselist=False, cascade="all, delete-orphan")
    bias_flags      = relationship("BiasFlag", back_populates="application", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Application {self.id[:8]} job={self.job_id[:8]} [{self.status}]>"
