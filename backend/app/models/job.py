import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Integer, DateTime,
    Enum as SAEnum, ForeignKey, Index, text
)
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class JobStatus(str, enum.Enum):
    DRAFT  = "draft"
    OPEN   = "open"
    CLOSED = "closed"
    FILLED = "filled"


class ExperienceLevel(str, enum.Enum):
    ENTRY  = "entry"
    MID    = "mid"
    SENIOR = "senior"
    LEAD   = "lead"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    department = Column(String(100), nullable=False, index=True)
    location = Column(String(150), nullable=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    experience_level = Column(SAEnum(ExperienceLevel), nullable=False, default=ExperienceLevel.MID)
    status = Column(SAEnum(JobStatus), nullable=False, default=JobStatus.DRAFT, index=True)
    poster_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc),
                        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                        nullable=False)
    closes_at = Column(DateTime, nullable=True)

    poster       = relationship("User",        back_populates="posted_jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    bias_flags   = relationship("BiasFlag",    back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_jobs_status_dept",    "status",    "department"),
        Index("ix_jobs_poster_status",  "poster_id", "status"),
        {"comment": "Job postings created by recruiters"},
    )

    def __repr__(self):
        return f"<Job id={self.id} title={self.title} status={self.status}>"