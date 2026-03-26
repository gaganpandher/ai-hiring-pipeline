"""
services/job_service.py
───────────────────────
Business logic for job postings.
Handles create, read, update, status changes, and Kafka events.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from loguru import logger

from app.models.job import Job, JobStatus
from app.models.audit_log import AuditLog, AuditAction
from app.schemas.job import JobCreate, JobUpdate, JobResponse
from app.schemas.common import PaginatedResponse


class JobService:

    # ── Create ────────────────────────────────────────────────

    async def create_job(
        self,
        data: JobCreate,
        poster_id: str,
        poster_email: str,
        db: AsyncSession,
    ) -> JobResponse:
        dump = data.model_dump()
        job_id = dump.pop("id", None) or str(uuid.uuid4())

        existing = await db.execute(select(Job).where(Job.id == job_id))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job ID already exists. Please choose a different one."
            )

        job = Job(
            id=job_id,
            poster_id=poster_id,
            **dump
        )
        db.add(job)

        db.add(AuditLog(
            id=str(uuid.uuid4()),
            actor_id=poster_id,
            actor_email=poster_email,
            actor_role="recruiter",
            action=AuditAction.JOB_CREATED,
            entity_type="job",
            entity_id=job.id,
            payload={"title": job.title, "department": job.department},
        ))

        await db.commit()
        await db.refresh(job)

        # Publish to Kafka (non-blocking — don't fail if Kafka is down)
        try:
            from app.core.kafka import produce
            from app.core.config import settings
            await produce(settings.KAFKA_TOPIC_AUDIT_LOG, {
                "event": "job_created",
                "job_id": job.id,
                "title": job.title,
                "poster_id": poster_id,
            })
        except Exception as e:
            logger.warning(f"Kafka publish skipped: {e}")

        logger.info(f"Job created: {job.title} by {poster_email}")
        return await self._load_with_poster(job.id, db)

    # ── List (paginated + filtered) ───────────────────────────

    async def list_jobs(
        self,
        db: AsyncSession,
        status: JobStatus | None = None,
        department: str | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse[JobResponse]:

        # Build base query
        query = select(Job).options(selectinload(Job.poster))

        # Apply filters
        filters = []
        if status:
            filters.append(Job.status == status)
        if department:
            filters.append(Job.department.ilike(f"%{department}%"))
        if search:
            filters.append(or_(
                Job.title.ilike(f"%{search}%"),
                Job.description.ilike(f"%{search}%"),
            ))
        if filters:
            query = query.where(and_(*filters))

        # Total count for pagination
        count_q = select(func.count()).select_from(
            query.subquery()
        )
        total = (await db.execute(count_q)).scalar_one()

        # Apply pagination
        query = query.order_by(Job.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        rows = (await db.execute(query)).scalars().all()
        data = [JobResponse.model_validate(r) for r in rows]

        return PaginatedResponse.build(
            data=data, total=total, page=page, per_page=per_page
        )

    # ── Get single job ────────────────────────────────────────

    async def get_job(self, job_id: str, db: AsyncSession) -> JobResponse:
        job = await self._load_with_poster(job_id, db)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

    # ── Update ────────────────────────────────────────────────

    async def update_job(
        self,
        job_id: str,
        data: JobUpdate,
        actor_id: str,
        actor_email: str,
        db: AsyncSession,
    ) -> JobResponse:
        job = await self._get_or_404(job_id, db)

        # Only the poster or an admin can update
        if job.poster_id != actor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the job poster can edit this job"
            )

        # Apply only the fields that were sent (partial update)
        changed = {}
        for field, value in data.model_dump(exclude_unset=True).items():
            if getattr(job, field) != value:
                changed[field] = {"from": getattr(job, field), "to": value}
                setattr(job, field, value)

        if changed:
            db.add(AuditLog(
                id=str(uuid.uuid4()),
                actor_id=actor_id,
                actor_email=actor_email,
                actor_role="recruiter",
                action=AuditAction.JOB_UPDATED,
                entity_type="job",
                entity_id=job_id,
                payload={"changed_fields": changed},
            ))
            await db.commit()
            await db.refresh(job)

        return await self._load_with_poster(job_id, db)

    # ── Change status ─────────────────────────────────────────

    async def change_status(
        self,
        job_id: str,
        new_status: JobStatus,
        actor_id: str,
        actor_email: str,
        db: AsyncSession,
    ) -> JobResponse:
        job = await self._get_or_404(job_id, db)

        if job.poster_id != actor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the job poster can change status"
            )

        old_status = job.status
        job.status = new_status

        db.add(AuditLog(
            id=str(uuid.uuid4()),
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role="recruiter",
            action=AuditAction.JOB_STATUS_CHANGED,
            entity_type="job",
            entity_id=job_id,
            payload={"from": old_status, "to": new_status},
        ))
        await db.commit()
        await db.refresh(job)

        logger.info(f"Job {job_id} status: {old_status} → {new_status}")
        return await self._load_with_poster(job_id, db)

    # ── Delete ────────────────────────────────────────────────

    async def delete_job(
        self,
        job_id: str,
        actor_id: str,
        db: AsyncSession,
    ):
        job = await self._get_or_404(job_id, db)

        if job.poster_id != actor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the job poster can delete this job"
            )

        await db.delete(job)
        await db.commit()
        logger.info(f"Job {job_id} deleted by {actor_id}")

    # ── Helpers ───────────────────────────────────────────────

    async def _get_or_404(self, job_id: str, db: AsyncSession) -> Job:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

    async def _load_with_poster(
        self, job_id: str, db: AsyncSession
    ) -> JobResponse:
        result = await db.execute(
            select(Job)
            .options(selectinload(Job.poster))
            .where(Job.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return JobResponse.model_validate(job)


job_service = JobService()
