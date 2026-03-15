from sqlalchemy import (
    Column, Text, DateTime, ForeignKey,
    Numeric, JSON, String
)
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Score(Base):
    """
    AI-generated score for a single application.
    One-to-one with Application.
    """
    __tablename__ = "scores"

    id                  = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id      = Column(CHAR(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Overall score 0–100
    overall_score       = Column(Numeric(5, 2), nullable=False)

    # Sub-scores (each 0–100)
    skills_score        = Column(Numeric(5, 2), nullable=True)   # skill keyword match
    experience_score    = Column(Numeric(5, 2), nullable=True)   # years / level match
    education_score     = Column(Numeric(5, 2), nullable=True)   # degree / field match
    keyword_score       = Column(Numeric(5, 2), nullable=True)   # JD keyword density

    # Matched / missing skills stored as JSON arrays
    matched_skills      = Column(JSON, default=list)
    missing_skills      = Column(JSON, default=list)

    # Model metadata
    model_version       = Column(String(50), default="v1.0")
    scoring_notes       = Column(Text, nullable=True)

    # Raw extracted entities from resume (spaCy NER output)
    extracted_entities  = Column(JSON, default=dict)

    # Timestamps
    scored_at           = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    application         = relationship("Application", back_populates="score")

    def __repr__(self):
        return f"<Score app={self.application_id[:8]} overall={self.overall_score}>"
