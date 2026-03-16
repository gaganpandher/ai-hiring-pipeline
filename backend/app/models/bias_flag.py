import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, Integer, DateTime,
    ForeignKey, JSON, Enum as SAEnum, Boolean,
    Index, text, CheckConstraint
)
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class BiasType(str, enum.Enum):
    GENDER    = "gender"
    AGE       = "age"
    ETHNICITY = "ethnicity"
    LOCATION  = "location"


class FlagSeverity(str, enum.Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


class BiasFlag(Base):
    __tablename__ = "bias_flags"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id         = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    bias_type      = Column(SAEnum(BiasType), nullable=False)
    affected_group = Column(String(100), nullable=False)
    severity       = Column(SAEnum(FlagSeverity), nullable=False)
    p_value        = Column(Float, nullable=False)
    effect_size    = Column(Float, nullable=True)
    sample_size    = Column(Integer, nullable=False)
    stats_breakdown = Column(JSON, nullable=True)
    is_resolved    = Column(Boolean, default=False, server_default=text("0"), nullable=False)
    resolution_note = Column(String(500), nullable=True)
    resolved_at    = Column(DateTime, nullable=True)
    detected_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                            server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    job = relationship("Job", back_populates="bias_flags")

    __table_args__ = (
        CheckConstraint("p_value >= 0 AND p_value <= 1", name="ck_pvalue_range"),
        CheckConstraint("sample_size > 0",               name="ck_sample_positive"),
        Index("ix_biasflag_job_type",    "job_id",   "bias_type"),
        Index("ix_biasflag_severity",    "severity", "is_resolved"),
        Index("ix_biasflag_detected_at", "detected_at"),
        {"comment": "Statistical bias detection results"},
    )

    def __repr__(self):
        return f"<BiasFlag job={self.job_id} type={self.bias_type} p={self.p_value:.4f}>"