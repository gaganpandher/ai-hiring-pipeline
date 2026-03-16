import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime,
    Enum as SAEnum, Index, text
)
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN     = "admin"
    RECRUITER = "recruiter"
    APPLICANT = "applicant"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.APPLICANT)
    is_active = Column(Boolean, default=True, nullable=False, server_default=text("1"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc),
                        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                        nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    posted_jobs  = relationship("Job",         back_populates="poster",    lazy="select")
    applications = relationship("Application", back_populates="applicant", lazy="select")
    audit_logs   = relationship("AuditLog",    back_populates="actor",     lazy="select")

    __table_args__ = (
        Index("ix_users_role_active", "role", "is_active"),
        {"comment": "System users with role-based access control"},
    )

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"