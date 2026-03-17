
"""
api/applications.py
───────────────────
Application endpoints.

Role rules:
  POST   /applications          → applicant only
  GET    /applications          → recruiter/admin (all), applicant (own only)
  GET    /applications/{id}     → recruiter/admin or the applicant who submitted it
  PATCH  /applications/{id}/decision → recruiter/admin only
"""

from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import oauth2_scheme, decode_token
from app.models.application import ApplicationStatus
from app.schemas.application import ApplicationCreate, ApplicationDecision, ApplicationResponse
from app.schemas.common import SuccessResponse, PaginatedResponse, MessageResponse
from app.services.application_service import application_service

router = APIRouter()


# ── Auth dependencies ─────────────────────────────────────────

async def get_payload(token: str = Depends(oauth2_scheme)) -> dict:
    return decode_token(token)


async def require_applicant(payload: dict = Depends(get_payload)) -> dict:
    if payload.get("role") not in ("applicant", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only applicants can submit applications"
        )
    return payload


async def require_recruiter(payload: dict = Depends(get_payload)) -> dict:
    if payload.get("role") not in ("recruiter", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can manage applications"
        )
    return payload


# ── POST /applications — submit ───────────────────────────────

@router.post(
    "",
    response_model=SuccessResponse[ApplicationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit a job application with resume upload",
)
async def submit_application(
    job_id:        str        = Form(..., description="Job ID to apply for"),
    cover_letter:  str        = Form(None, description="Optional cover letter"),
    linkedin_url:  str        = Form(None, description="Optional LinkedIn URL"),
    portfolio_url: str        = Form(None, description="Optional portfolio URL"),
    resume:        UploadFile = File(..., description="Resume file — PDF or Word"),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_applicant),
):
    """
    Submit a job application.\n
    Sends a **multipart/form-data** request with the resume file attached.\n
    After submission, the application is published to Kafka and
    the AI scoring consumer processes it automatically.
    """
    data = ApplicationCreate(
        job_id=job_id,
        cover_letter=cover_letter,
        linkedin_url=linkedin_url,
        portfolio_url=portfolio_url,
    )
    application = await application_service.submit(
        job_id=job_id,
        applicant_id=payload["sub"],
        applicant_email=payload.get("email", ""),
        data=data,
        resume_file=resume,
        db=db,
    )
    return SuccessResponse(data=application, message="Application submitted successfully")


# ── GET /applications — list ──────────────────────────────────

@router.get(
    "",
    response_model=PaginatedResponse[ApplicationResponse],
    summary="List applications (role-aware)",
)
async def list_applications(
    job_id:   Optional[str]               = Query(None, description="Filter by job"),
    status:   Optional[ApplicationStatus] = Query(None, description="Filter by status"),
    page:     int = Query(1,  ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_payload),
):
    """
    Role-aware listing:\n
    - **Recruiter/Admin**: sees all applications, can filter by job_id\n
    - **Applicant**: sees only their own applications
    """
    role = payload.get("role")
    user_id = payload.get("sub")

    # Applicants can only see their own applications
    applicant_id_filter = None if role in ("recruiter", "admin") else user_id

    return await application_service.list_applications(
        db=db,
        job_id=job_id,
        applicant_id=applicant_id_filter,
        status=status,
        page=page,
        per_page=per_page,
    )


# ── GET /applications/{id} — single ──────────────────────────

@router.get(
    "/{application_id}",
    response_model=SuccessResponse[ApplicationResponse],
    summary="Get a single application",
)
async def get_application(
    application_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_payload),
):
    application = await application_service.get_application(
        application_id=application_id,
        db=db,
    )

    # Applicants can only view their own applications
    role = payload.get("role")
    if role == "applicant" and application.applicant_id != payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own applications"
        )

    return SuccessResponse(data=application)


# ── PATCH /applications/{id}/decision — recruiter decides ─────

@router.patch(
    "/{application_id}/decision",
    response_model=SuccessResponse[ApplicationResponse],
    summary="Make a hiring decision (recruiter/admin only)",
)
async def make_decision(
    application_id: str,
    decision: ApplicationDecision,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_recruiter),
):
    """
    Make a hiring decision on an application.\n
    - **shortlist**: mark as promising\n
    - **rejected**: decline the applicant\n
    - **hired**: extend an offer\n
    Every decision is published to the `recruiter-actions` Kafka topic
    where the bias detection engine analyses patterns in real time.
    """
    application = await application_service.make_decision(
        application_id=application_id,
        decision=decision,
        recruiter_id=payload["sub"],
        recruiter_email=payload.get("email", ""),
        db=db,
    )
    return SuccessResponse(
        data=application,
        message=f"Decision recorded: {decision.status}"
    )