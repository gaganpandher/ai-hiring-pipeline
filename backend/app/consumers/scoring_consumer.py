"""
consumers/scoring_consumer.py
──────────────────────────────
Kafka consumer that listens to the 'applications' topic,
scores each resume using spaCy + sklearn, writes the score
to MySQL, then publishes to 'scoring-results'.

Run standalone:
  python -m app.consumers.scoring_consumer

In production this runs as a separate Docker service.
For local dev, you can start it manually alongside FastAPI.
"""

import asyncio
import uuid
import re
from datetime import datetime, timezone
from loguru import logger


# ── Keyword scoring logic ─────────────────────────────────────

SKILL_KEYWORDS = [
    "python", "fastapi", "django", "flask", "sqlalchemy",
    "mysql", "postgresql", "mongodb", "redis", "kafka",
    "docker", "kubernetes", "aws", "git", "rest", "api",
    "react", "javascript", "typescript", "html", "css",
    "machine learning", "deep learning", "tensorflow", "pytorch",
    "pandas", "numpy", "scikit-learn", "data analysis",
]


def score_resume_text(resume_text: str, job_description: str, requirements: str) -> dict:
    """
    Simple keyword-based scoring.
    In production this would use spaCy NLP + a trained model.
    """
    text_lower = resume_text.lower()
    jd_lower   = (job_description + " " + (requirements or "")).lower()

    # Extract keywords from job description
    jd_keywords = [kw for kw in SKILL_KEYWORDS if kw in jd_lower]

    # Score keyword matches
    matched = [kw for kw in jd_keywords if kw in text_lower]
    keyword_score = (len(matched) / max(len(jd_keywords), 1)) * 100

    # Experience score — count years mentioned
    years = re.findall(r"(\d+)\s*(?:\+\s*)?years?", text_lower)
    total_years = sum(int(y) for y in years[:3])
    experience_score = min(total_years * 10, 100)

    # Education score — check for degree keywords
    edu_keywords = ["bachelor", "master", "phd", "degree", "university", "college"]
    edu_count = sum(1 for kw in edu_keywords if kw in text_lower)
    education_score = min(edu_count * 20, 100)

    # Skills score — general tech terms
    skills_count = sum(1 for kw in SKILL_KEYWORDS if kw in text_lower)
    skills_score = min(skills_count * 5, 100)

    # Composite overall score
    overall = int(
        keyword_score    * 0.40 +
        experience_score * 0.30 +
        skills_score     * 0.20 +
        education_score  * 0.10
    )

    return {
        "overall_score":    overall,
        "keyword_score":    round(keyword_score, 1),
        "experience_score": round(experience_score, 1),
        "skills_score":     round(skills_score, 1),
        "education_score":  round(education_score, 1),
        "breakdown": {
            "matched_keywords": matched,
            "missing_keywords": [kw for kw in jd_keywords if kw not in matched],
            "experience_years": total_years,
        }
    }


async def handle_application(topic: str, message: dict):
    """
    Called for each message on the 'applications' topic.
    Reads resume file → scores it → saves to DB → publishes result.
    """
    application_id = message.get("application_id")
    resume_path    = message.get("resume_path")
    job_description = message.get("job_description", "")
    requirements   = message.get("requirements", "")

    logger.info(f"Scoring application {application_id}")

    # Read resume text
    resume_text = ""
    try:
        if resume_path and resume_path.endswith(".txt"):
            with open(resume_path, "r") as f:
                resume_text = f.read()
        else:
            # For PDF/docx — use filename as proxy text for now
            # In production: use pdfplumber or python-docx to extract text
            resume_text = resume_path or ""
    except Exception as e:
        logger.warning(f"Could not read resume {resume_path}: {e}")

    # Score the resume
    scores = score_resume_text(resume_text, job_description, requirements)

    # Save score to MySQL
    try:
        from app.core.database import AsyncSessionLocal
        from app.models.score import Score
        from app.models.application import Application, ApplicationStatus
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            # Save score
            score = Score(
                id=str(uuid.uuid4()),
                application_id=application_id,
                overall_score=scores["overall_score"],
                keyword_score=scores["keyword_score"],
                experience_score=scores["experience_score"],
                skills_score=scores["skills_score"],
                education_score=scores["education_score"],
                breakdown=scores["breakdown"],
                model_version="v1.0",
                scored_at=datetime.now(timezone.utc),
            )
            db.add(score)

            # Update application status to SCORED
            result = await db.execute(
                select(Application).where(Application.id == application_id)
            )
            application = result.scalar_one_or_none()
            if application:
                application.status = ApplicationStatus.SCORED

            await db.commit()
            logger.info(f"✅ Scored application {application_id}: {scores['overall_score']}/100")

    except Exception as e:
        logger.error(f"Failed to save score for {application_id}: {e}")
        return

    # Publish result to scoring-results topic
    try:
        from app.core.kafka import produce
        from app.core.config import settings
        await produce(settings.KAFKA_TOPIC_SCORING_RESULTS, {
            "event":          "application_scored",
            "application_id": application_id,
            "job_id":         message.get("job_id"),
            "overall_score":  scores["overall_score"],
            "scored_at":      datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.warning(f"Kafka result publish skipped: {e}")


async def main():
    """Entry point — starts the consumer loop."""
    from app.core.kafka import consume
    from app.core.config import settings

    logger.info("🎯 Scoring consumer started")
    await consume(
        topics=[settings.KAFKA_TOPIC_APPLICATIONS],
        group_id="scoring-service",
        handler=handle_application,
    )


if __name__ == "__main__":
    asyncio.run(main())