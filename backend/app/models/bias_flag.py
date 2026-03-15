from sqlalchemy import (
    Column, String, Text, Enum, DateTime,
    ForeignKey, Numeric, Boolean, Integer
)
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class BiasDimension(str, enum.Enum):
    GENDER    = "gender"
    AGE       = "age"
    ETHNICITY = "ethnicity"
    NAME      = "name"       # name-based inference bias
    LOCATION  = "location"


class BiasSeverity(str, enum.Enum):
    LOW      = "low"       # p < 0.10
    MEDIUM   = "medium"    # p < 0.05
    HIGH     = "high"      # p < 0.01
    CRITICAL = "critical"  # p < 0.001


class BiasFlag(Base):
    """
    A bias detection event tied to a specific application decision.
    Created by the Bias Detector Kafka consumer when a statistically
    significant disparity is found.
    """
    __tablename__ = "bias_flags"

    id              = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id  = Column(CHAR(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id          = Column(CHAR(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    dimension       = Column(Enum(BiasDimension), nullable=False)
    severity        = Column(Enum(BiasSeverity),  nullable=False)

    # Statistical test details
    p_value         = Column(Numeric(10, 6), nullable=True)   # chi-squared p-value
    chi_square_stat = Column(Numeric(10, 4), nullable=True)
    sample_size     = Column(Integer, nullable=True)          # decisions analysed

    # Human-readable explanation
    description     = Column(Text, nullable=True)

    # e.g. {"female_acceptance_rate": 0.12, "male_acceptance_rate": 0.38}
    evidence        = Column(Text, nullable=True)  # JSON stored as text

    # Resolved by admin?
    is_resolved     = Column(Boolean, default=False)
    resolved_by     = Column(CHAR(36), ForeignKey("users.id"), nullable=True)
    resolved_at     = Column(DateTime(timezone=True), nullable=True)
    resolution_note = Column(Text, nullable=True)

    # Timestamps
    detected_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    application     = relationship("Application", back_populates="bias_flags")

    def __repr__(self):
        return f"<BiasFlag {self.dimension} [{self.severity}] p={self.p_value}>"
