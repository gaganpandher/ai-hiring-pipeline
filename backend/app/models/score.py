import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float,
    DateTime, ForeignKey, JSON,
    Index, text, CheckConstraint
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Score(Base):
    __tablename__ = "scores"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"),
                            unique=True, nullable=False, index=True)
    overall_score    = Column(Integer, nullable=False)
    skills_score     = Column(Float, nullable=True)
    experience_score = Column(Float, nullable=True)
    education_score  = Column(Float, nullable=True)
    keyword_score    = Column(Float, nullable=True)
    breakdown        = Column(JSON, nullable=True)
    model_version    = Column(String(50), nullable=False, default="v1.0")
    scored_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    application = relationship("Application", back_populates="score")

    __table_args__ = (
        CheckConstraint("overall_score >= 0 AND overall_score <= 100", name="ck_score_range"),
        Index("ix_scores_overall", "overall_score"),
        {"comment": "AI-generated resume scores"},
    )

    def __repr__(self):
        return f"<Score app={self.application_id} score={self.overall_score}>"