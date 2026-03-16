import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, DateTime,
    Enum as SAEnum, ForeignKey,
    UniqueConstraint, Index, text
)
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class ApplicationStatus(str, enum.Enum):
    PENDING   = "pending"
    SCORED    = "scored"
    REVIEWED  = "reviewed"
    SHORTLIST = "shortlist"
    REJECTED  = "rejected"
    HIRED     = "hired"


class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    applicant_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    resume_path = Column(String(500), nullable=False)
    cover_letter = Column(Text, nullable=True)
    linkedin_url = Column(String(300), nullable=True)
    portfolio_url = Column(String(300), nullable=True)
    status = Column(SAEnum(ApplicationStatus), nullable=False, default=ApplicationStatus.PENDING, index=True)
    recruiter_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                          server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc),
                        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                        nullable=False)

    job       = relationship("Job",   back_populates="applications")
    applicant = relationship("User",  back_populates="applications")
    score     = relationship("Score", back_populates="application",
                             uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("job_id", "applicant_id", name="uq_application_job_applicant"),
        Index("ix_applications_job_status",        "job_id",       "status"),
        Index("ix_applications_applicant_status",  "applicant_id", "status"),
        {"comment": "Job applications"},
    )

    def __repr__(self):
        return f"<Application id={self.id} status={self.status}>"