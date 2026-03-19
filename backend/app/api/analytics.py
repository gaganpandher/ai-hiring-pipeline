"""
api/analytics.py
────────────────
Analytics endpoints powering the dashboard.
All endpoints require recruiter or admin role.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import oauth2_scheme, decode_token
from app.schemas.analytics import (
    DashboardStats, FunnelResponse,
    BiasReport, CohortResponse,
)
from app.schemas.common import SuccessResponse
from app.services.analytics_service import analytics_service

router = APIRouter()


# ── Auth dependency ───────────────────────────────────────────

async def require_recruiter_or_admin(
    token: str = Depends(oauth2_scheme),
) -> dict:
    payload = decode_token(token)
    if payload.get("role") not in ("recruiter", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analytics require recruiter or admin role"
        )
    return payload


# ── GET /analytics/dashboard ──────────────────────────────────

@router.get(
    "/dashboard",
    response_model=SuccessResponse[DashboardStats],
    summary="KPI cards for the dashboard overview",
)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_recruiter_or_admin),
):
    """
    Returns all dashboard KPI cards in one call:\n
    - Open jobs, total applications, applications this week\n
    - Average AI score, average days to hire\n
    - Active bias flags, hired this month\n
    - Overall pipeline health indicator
    """
    stats = await analytics_service.get_dashboard_stats(db=db)
    return SuccessResponse(data=stats)


# ── GET /analytics/funnel ─────────────────────────────────────

@router.get(
    "/funnel",
    response_model=SuccessResponse[FunnelResponse],
    summary="Hiring funnel — applications at each stage",
)
async def get_funnel(
    job_id: Optional[str] = Query(None, description="Filter to a specific job — omit for all jobs"),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_recruiter_or_admin),
):
    """
    Returns application counts at every stage:\n
    Applied → Scored → Reviewed → Shortlisted → Hired/Rejected\n
    Also includes average days spent in each stage.\n
    Used to render the funnel bar chart on the dashboard.
    """
    funnel = await analytics_service.get_funnel(db=db, job_id=job_id)
    return SuccessResponse(data=funnel)


# ── GET /analytics/cohorts ────────────────────────────────────

@router.get(
    "/cohorts",
    response_model=SuccessResponse[CohortResponse],
    summary="Monthly cohort time-series data",
)
async def get_cohorts(
    department: Optional[str] = Query(None, description="Filter by department"),
    months:     int           = Query(6, ge=1, le=24, description="How many months back"),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_recruiter_or_admin),
):
    """
    Groups applications by submission month and tracks outcomes.\n
    Used to render the line chart showing hiring trends over time.\n
    Optionally filtered by department.
    """
    cohorts = await analytics_service.get_cohorts(
        db=db, department=department, months=months
    )
    return SuccessResponse(data=cohorts)


# ── GET /analytics/bias/{job_id} ──────────────────────────────

@router.get(
    "/bias/{job_id}",
    response_model=SuccessResponse[BiasReport],
    summary="Bias analysis for a specific job",
)
async def get_bias_report(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_recruiter_or_admin),
):
    """
    Analyses acceptance rates by demographic proxy for a job.\n
    Uses name-based gender classification to detect disparities.\n
    Returns acceptance rates per group and flags if a bias
    alert has been raised by the statistical detector.
    """
    report = await analytics_service.get_bias_report(db=db, job_id=job_id)
    return SuccessResponse(data=report)


# ── GET /analytics/departments ────────────────────────────────

@router.get(
    "/departments",
    summary="Hiring metrics grouped by department",
)
async def get_department_breakdown(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_recruiter_or_admin),
):
    """
    Four-table JOIN aggregating hiring metrics per department:\n
    - Total jobs, applications, hired\n
    - Average AI score\n
    - Hire rate percentage\n
    Used to render the department comparison table on the dashboard.
    """
    data = await analytics_service.get_department_breakdown(db=db)
    return {"success": True, "data": data}