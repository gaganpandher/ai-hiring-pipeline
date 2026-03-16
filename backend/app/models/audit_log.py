import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, DateTime,
    ForeignKey, JSON, Index,
    Enum as SAEnum, text
)
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class AuditAction(str, enum.Enum):
    USER_REGISTERED       = "user_registered"
    USER_LOGIN            = "user_login"
    USER_LOGOUT           = "user_logout"
    JOB_CREATED           = "job_created"
    JOB_UPDATED           = "job_updated"
    JOB_STATUS_CHANGED    = "job_status_changed"
    APPLICATION_SUBMITTED  = "application_submitted"
    APPLICATION_SCORED     = "application_scored"
    APPLICATION_REVIEWED   = "application_reviewed"
    APPLICATION_SHORTLISTED = "application_shortlisted"
    APPLICATION_REJECTED   = "application_rejected"
    APPLICATION_HIRED      = "application_hired"
    BIAS_FLAG_CREATED      = "bias_flag_created"
    BIAS_FLAG_RESOLVED     = "bias_flag_resolved"


class AuditLog(Base):
    __tablename__ = "audit_log"

    id         = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id   = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_email = Column(String(255), nullable=True)
    actor_role  = Column(String(50),  nullable=True)
    action      = Column(SAEnum(AuditAction), nullable=False, index=True)
    entity_type = Column(String(50),  nullable=True)
    entity_id   = Column(String(36),  nullable=True, index=True)
    payload     = Column(JSON, nullable=True)
    ip_address  = Column(String(45),  nullable=True)
    user_agent  = Column(String(300), nullable=True)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                         server_default=text("CURRENT_TIMESTAMP"), nullable=False, index=True)

    actor = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_entity",        "entity_type", "entity_id"),
        Index("ix_audit_created_action","created_at",  "action"),
        Index("ix_audit_actor_created", "actor_id",    "created_at"),
        {"comment": "Immutable audit trail"},
    )

    def __repr__(self):
        return f"<AuditLog action={self.action} actor={self.actor_id}>"