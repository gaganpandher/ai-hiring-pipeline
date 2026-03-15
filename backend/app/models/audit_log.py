from sqlalchemy import (
    Column, String, Text, Enum, DateTime,
    ForeignKey, JSON
)
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class AuditAction(str, enum.Enum):
    # Auth
    USER_REGISTER       = "user.register"
    USER_LOGIN          = "user.login"
    USER_LOGOUT         = "user.logout"
    # Jobs
    JOB_CREATED         = "job.created"
    JOB_UPDATED         = "job.updated"
    JOB_CLOSED          = "job.closed"
    # Applications
    APPLICATION_SUBMIT  = "application.submit"
    APPLICATION_REVIEW  = "application.review"
    APPLICATION_SHORTLIST = "application.shortlist"
    APPLICATION_REJECT  = "application.reject"
    APPLICATION_HIRE    = "application.hire"
    APPLICATION_WITHDRAW = "application.withdraw"
    # Scoring
    SCORE_GENERATED     = "score.generated"
    # Bias
    BIAS_DETECTED       = "bias.detected"
    BIAS_RESOLVED       = "bias.resolved"


class AuditLog(Base):
    """
    Immutable append-only log of every significant action.
    Also mirrored to the Kafka audit-log topic.
    No UPDATE or DELETE should ever run on this table.
    """
    __tablename__ = "audit_logs"

    id           = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id     = Column(CHAR(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    action       = Column(Enum(AuditAction), nullable=False, index=True)

    # What entity was affected
    entity_type  = Column(String(50), nullable=True)   # e.g. "application"
    entity_id    = Column(CHAR(36), nullable=True, index=True)

    # Full snapshot of changes (before/after)
    payload      = Column(JSON, default=dict)

    # Request metadata
    ip_address   = Column(String(45), nullable=True)
    user_agent   = Column(String(500), nullable=True)

    # Timestamp (no updated_at — this is append-only)
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    actor        = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.actor_id} on {self.entity_type}:{self.entity_id}>"
