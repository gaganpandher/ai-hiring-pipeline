"""
services/application_service.py
────────────────────────────────
Fixed version — file saved first, path stored correctly in DB.
"""

import uuid
import os
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status, UploadFile
from loguru import logger
import traceback

from app.models.application import Application, ApplicationStatus
from app.models.job import Job, JobStatus
from app.models.audit_log import AuditLog, AuditAction
from app.schemas.application import (
    ApplicationCreate, ApplicationDecision, ApplicationResponse
)
from app.schemas.common import PaginatedResponse
from app.core.config import settings

MAX_RESUME_SIZE_MB = 5


def _get_upload_base() -> str:
    """
    Returns the correct upload base path for the current OS.
    If UPLOAD_DIR is a Linux path (starts with /) and we're on
    Windows, fall back to a path relative to this file.
    """
    base = settings.UPLOAD_DIR or ""
    if not base or base.startswith("/"):
        # Resolve relative to: backend/app/services/ → backend/uploads/
        base = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "uploads")
        )
    return base


class ApplicationService:

    # ── Submit ────────────────────────────────────────────────

    async def submit(
        self,
        job_id: str,
        applicant_id: str,
        applicant_email: str,
        data: ApplicationCreate,
        resume_file: UploadFile,
        db: AsyncSession,
    ) -> ApplicationResponse:
        try:
            # 1. Verify job exists and is open
            result = await db.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            if job.status != JobStatus.OPEN:
                raise HTTPException(
                    status_code=400,
                    detail="This job is not currently accepting applications"
                )

            # 2. Check duplicate
            existing = await db.execute(
                select(Application).where(
                    and_(
                        Application.job_id == job_id,
                        Application.applicant_id == applicant_id,
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=409,
                    detail="You have already applied for this job"
                )

            # 3. Read and validate resume bytes
            resume_bytes, resume_ext = await self._read_resume(resume_file)

            # 4. Generate IDs and save file FIRST
            #    so the correct path goes straight into the DB
            application_id = str(uuid.uuid4())
            resume_path = self._save_resume_bytes(
                resume_bytes, resume_ext, applicant_id, application_id
            )
            logger.info(f"Resume saved: {resume_path}")

            # 5. Create application with the real path already set
            application = Application(
                id=application_id,
                job_id=job_id,
                applicant_id=applicant_id,
                resume_path=resume_path,
                cover_letter=data.cover_letter,
                linkedin_url=data.linkedin_url,
                portfolio_url=data.portfolio_url,
                status=ApplicationStatus.PENDING,
            )
            db.add(application)

            # 6. Audit log
            db.add(AuditLog(
                id=str(uuid.uuid4()),
                actor_id=applicant_id,
                actor_email=applicant_email,
                actor_role="applicant",
                action=AuditAction.APPLICATION_SUBMITTED,
                entity_type="application",
                entity_id=application_id,
                payload={"job_id": job_id, "job_title": job.title},
            ))

            # 7. Single commit — both records saved together
            await db.commit()
            logger.info(f"Application {application_id} saved to DB")

            # 8. Publish to Kafka (non-blocking — never fails the request)
            try:
                from app.core.kafka import produce
                await produce(settings.KAFKA_TOPIC_APPLICATIONS, {
                    "event":           "application_submitted",
                    "application_id":  application_id,
                    "job_id":          job_id,
                    "applicant_id":    applicant_id,
                    "resume_path":     resume_path,
                    "job_title":       job.title,
                    "job_description": job.description,
                    "requirements":    job.requirements or "",
                    "submitted_at":    datetime.now(timezone.utc).isoformat(),
                })
                logger.info(f"Published {application_id} to Kafka")
            except Exception as ke:
                logger.warning(f"Kafka skipped (app still saved): {ke}")

            return await self._load_full(application_id, db)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Submit failed: {type(e).__name__}: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"{type(e).__name__}: {e}"
            )

    # ── List ──────────────────────────────────────────────────

    async def list_applications(
        self,
        db: AsyncSession,
        job_id: str | None = None,
        applicant_id: str | None = None,
        status: ApplicationStatus | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse[ApplicationResponse]:

        query = select(Application).options(
            selectinload(Application.job),
            selectinload(Application.applicant),
            selectinload(Application.score),
        )

        filters = []
        if job_id:
            filters.append(Application.job_id == job_id)
        if applicant_id:
            filters.append(Application.applicant_id == applicant_id)
        if status:
            filters.append(Application.status == status)
        if filters:
            query = query.where(and_(*filters))

        total = (await db.execute(
            select(func.count()).select_from(query.subquery())
        )).scalar_one()

        query = query.order_by(Application.submitted_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)
        rows  = (await db.execute(query)).scalars().all()

        return PaginatedResponse.build(
            data=[ApplicationResponse.model_validate(r) for r in rows],
            total=total, page=page, per_page=per_page
        )

    # ── Get single ────────────────────────────────────────────

    async def get_application(
        self, application_id: str, db: AsyncSession
    ) -> ApplicationResponse:
        return await self._load_full(application_id, db)

    # ── Decision ──────────────────────────────────────────────

    async def make_decision(
        self,
        application_id: str,
        decision: ApplicationDecision,
        recruiter_id: str,
        recruiter_email: str,
        db: AsyncSession,
    ) -> ApplicationResponse:

        result = await db.execute(
            select(Application).where(Application.id == application_id)
        )
        application = result.scalar_one_or_none()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        old_status = application.status
        application.status     = decision.status
        application.decided_at = datetime.now(timezone.utc)
        if decision.recruiter_notes:
            application.recruiter_notes = decision.recruiter_notes

        action_map = {
            ApplicationStatus.REVIEWED:  AuditAction.APPLICATION_REVIEWED,
            ApplicationStatus.SHORTLIST: AuditAction.APPLICATION_SHORTLISTED,
            ApplicationStatus.REJECTED:  AuditAction.APPLICATION_REJECTED,
            ApplicationStatus.HIRED:     AuditAction.APPLICATION_HIRED,
        }
        db.add(AuditLog(
            id=str(uuid.uuid4()),
            actor_id=recruiter_id,
            actor_email=recruiter_email,
            actor_role="recruiter",
            action=action_map.get(
                decision.status, AuditAction.APPLICATION_REVIEWED
            ),
            entity_type="application",
            entity_id=application_id,
            payload={"from": str(old_status), "to": str(decision.status)},
        ))
        await db.commit()

        try:
            from app.core.kafka import produce
            await produce(settings.KAFKA_TOPIC_RECRUITER_ACTIONS, {
                "event":          "decision_made",
                "application_id": application_id,
                "job_id":         application.job_id,
                "applicant_id":   application.applicant_id,
                "decision":       str(decision.status),
                "recruiter_id":   recruiter_id,
            })
        except Exception as e:
            logger.warning(f"Kafka skipped: {e}")

        return await self._load_full(application_id, db)

    # ── File helpers ──────────────────────────────────────────

    async def _read_resume(self, file: UploadFile) -> tuple[bytes, str]:
        """Read and validate resume. Returns (bytes, extension)."""
        contents = await file.read()

        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Resume file is empty")

        size_mb = len(contents) / (1024 * 1024)
        if size_mb > MAX_RESUME_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"Resume must be under {MAX_RESUME_SIZE_MB}MB"
            )

        ext = os.path.splitext(file.filename or "resume.pdf")[1].lower()
        if not ext:
            ext = ".pdf"

        return contents, ext

    def _save_resume_bytes(
        self,
        contents: bytes,
        ext: str,
        applicant_id: str,
        application_id: str,
    ) -> str:
        """Save bytes to disk. Returns absolute file path."""
        base       = _get_upload_base()
        upload_dir = os.path.join(base, "resumes", applicant_id)
        os.makedirs(upload_dir, exist_ok=True)

        filepath = os.path.normpath(
            os.path.join(upload_dir, f"{application_id}{ext}")
        )
        with open(filepath, "wb") as f:
            f.write(contents)

        return filepath

    # ── Load with relationships ───────────────────────────────

    async def _load_full(
        self, application_id: str, db: AsyncSession
    ) -> ApplicationResponse:
        result = await db.execute(
            select(Application)
            .options(
                selectinload(Application.job),
                selectinload(Application.applicant),
                selectinload(Application.score),
            )
            .where(Application.id == application_id)
        )
        app = result.scalar_one_or_none()
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
        return ApplicationResponse.model_validate(app)


application_service = ApplicationService()