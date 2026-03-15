from sqlalchemy import (
    Column, String, Text, Boolean, Enum,
    DateTime, Integer, ForeignKey, JSON, Numeric
)
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class JobStatus(str, enum.Enum):
    DRAFT      = "draft"
    OPEN       = "open"
    PAUSED     = "paused"
    CLOSED     = "closed"
    FILLED     = "filled"


class JobType(str, enum.Enum):
    FULL_TIME  = "full_time"
    PART_TIME  = "part_time"
    CONTRACT   = "contract"
    INTERNSHIP = "internship"
    REMOTE     = "remote"


class ExperienceLevel(str, enum.Enum):
    ENTRY      = "entry"
    MID        = "mid"
    SENIOR     = "senior"
    LEAD       = "lead"
    EXECUTIVE  = "executive"


class Job(Base):
    __tablename__ = "jobs"

    id               = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recruiter_id     = Column(CHAR(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    title            = Column(String(255), nullable=False)
    department       = Column(String(100), nullable=True)
    company          = Column(String(255), nullable=False)
    location         = Column(String(255), nullable=True)
    is_remote        = Column(Boolean, default=False)

    job_type         = Column(Enum(JobType), default=JobType.FULL_TIME)
    experience_level = Column(Enum(ExperienceLevel), default=ExperienceLevel.MID)
    status           = Column(Enum(JobStatus), default=JobStatus.DRAFT, index=True)

    description      = Column(Text, nullable=False)
    requirements     = Column(Text, nullable=True)
    benefits         = Column(Text, nullable=True)

    # Salary range
    salary_min       = Column(Numeric(12, 2), nullable=True)
    salary_max       = Column(Numeric(12, 2), nullable=True)
    salary_currency  = Column(String(10), default="USD")

    # Skills stored as JSON array e.g. ["Python", "Kafka", "MySQL"]
    required_skills  = Column(JSON, default=list)
    preferred_skills = Column(JSON, default=list)

    # Application limits
    max_applicants   = Column(Integer, nullable=True)
    deadline         = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at       = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    closed_at        = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    recruiter        = relationship("User", back_populates="posted_jobs", foreign_keys=[recruiter_id])
    applications     = relationship("Application", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job {self.title} @ {self.company} [{self.status}]>"
