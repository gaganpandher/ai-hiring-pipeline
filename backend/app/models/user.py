from sqlalchemy import Column, String, Boolean, Enum, DateTime, Text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    APPLICANT = "applicant"


class User(Base):
    __tablename__ = "users"

    id           = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email        = Column(String(255), unique=True, nullable=False, index=True)
    full_name    = Column(String(255), nullable=False)
    password     = Column(String(255), nullable=False)
    role         = Column(Enum(UserRole), nullable=False, default=UserRole.APPLICANT)
    is_active    = Column(Boolean, default=True, nullable=False)
    phone        = Column(String(20), nullable=True)
    avatar_url   = Column(String(500), nullable=True)
    bio          = Column(Text, nullable=True)

    # Timestamps
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login   = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    posted_jobs      = relationship("Job", back_populates="recruiter", foreign_keys="Job.recruiter_id")
    applications     = relationship("Application", back_populates="applicant", foreign_keys="Application.applicant_id")
    audit_logs       = relationship("AuditLog", back_populates="actor")

    def __repr__(self):
        return f"<User {self.email} [{self.role}]>"
