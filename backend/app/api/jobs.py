"""
api/jobs.py
───────────
Job posting endpoints.

Role rules enforced here:
  - GET  /jobs        → anyone (public job board)
  - GET  /jobs/{id}   → anyone
  - POST /jobs        → recruiter or admin only
  - PATCH /jobs/{id}  → recruiter (own jobs) or admin
  - PATCH /jobs/{id}/status → recruiter (own jobs) or admin
  - DELETE /jobs/{id} → recruiter (own jobs) or admin
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import oauth2_scheme, decode_token
from app.models.job import JobStatus
from app.schemas.job import JobCreate, JobUpdate, JobResponse
from app.schemas.common import SuccessResponse, PaginatedResponse, MessageResponse
from app.services.job_service import job_service

router = APIRouter()


# ── Dependency: get current user from token ───────────────────

async def get_current_user_payload(
    token: str = Depends(oauth2_scheme),
) -> dict:
    """Decodes JWT and returns the payload dict."""
    return decode_token(token)


async def require_recruiter(
    payload: dict = Depends(get_current_user_payload),
) -> dict:
    """Only recruiters and admins can post/edit jobs."""
    role = payload.get("role")
    if role not in ("recruiter", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters and admins can manage job postings"
        )
    return payload


# ── GET /jobs — public job listing ───────────────────────────

@router.get(
    "",
    response_model=PaginatedResponse[JobResponse],
    summary="List all jobs (filterable)",
)
async def list_jobs(
    status:     Optional[JobStatus] = Query(None, description="Filter by status"),
    department: Optional[str]       = Query(None, description="Filter by department"),
    search:     Optional[str]       = Query(None, description="Search title or description"),
    page:       int                 = Query(1,    ge=1),
    per_page:   int                 = Query(20,   ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint — no auth required.\n
    Applicants use this to browse open jobs.\n
    Supports filtering by status, department, and free-text search.
    """
    return await job_service.list_jobs(
        db=db,
        status=status,
        department=department,
        search=search,
        page=page,
        per_page=per_page,
    )


# ── GET /jobs/{id} — single job ───────────────────────────────

@router.get(
    "/{job_id}",
    response_model=SuccessResponse[JobResponse],
    summary="Get a single job by ID",
)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    job = await job_service.get_job(job_id=job_id, db=db)
    return SuccessResponse(data=job)


# ── POST /jobs — create job ───────────────────────────────────

@router.post(
    "",
    response_model=SuccessResponse[JobResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new job posting (recruiter/admin only)",
)
async def create_job(
    data: JobCreate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_recruiter),
):
    """
    Creates a new job posting.\n
    - Default status is **draft** — change to **open** when ready to accept applications.\n
    - Requires recruiter or admin role.
    """
    job = await job_service.create_job(
        data=data,
        poster_id=payload["sub"],
        poster_email=payload.get("email", ""),
        db=db,
    )
    return SuccessResponse(data=job, message="Job created successfully")


# ── PATCH /jobs/{id} — update job ────────────────────────────

@router.patch(
    "/{job_id}",
    response_model=SuccessResponse[JobResponse],
    summary="Update a job posting (poster or admin only)",
)
async def update_job(
    job_id: str,
    data: JobUpdate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_recruiter),
):
    """
    Partial update — only send the fields you want to change.\n
    Only the recruiter who created the job (or an admin) can edit it.
    """
    job = await job_service.update_job(
        job_id=job_id,
        data=data,
        actor_id=payload["sub"],
        actor_email=payload.get("email", ""),
        db=db,
    )
    return SuccessResponse(data=job, message="Job updated successfully")


# ── PATCH /jobs/{id}/status — change status ───────────────────

@router.patch(
    "/{job_id}/status",
    response_model=SuccessResponse[JobResponse],
    summary="Change job status (open / closed / filled)",
)
async def change_job_status(
    job_id: str,
    new_status: JobStatus,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_recruiter),
):
    """
    Changes a job's status.\n
    - **draft** → **open**: starts accepting applications\n
    - **open** → **closed**: stops accepting applications\n
    - **closed** → **filled**: position has been hired
    """
    job = await job_service.change_status(
        job_id=job_id,
        new_status=new_status,
        actor_id=payload["sub"],
        actor_email=payload.get("email", ""),
        db=db,
    )
    return SuccessResponse(data=job, message=f"Job status changed to {new_status}")


# ── DELETE /jobs/{id} ─────────────────────────────────────────

@router.delete(
    "/{job_id}",
    response_model=MessageResponse,
    summary="Delete a job posting (poster or admin only)",
)
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_recruiter),
):
    await job_service.delete_job(
        job_id=job_id,
        actor_id=payload["sub"],
        db=db,
    )
    return MessageResponse(message="Job deleted successfully")