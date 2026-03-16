"""
schemas/analytics.py
────────────────────
Pydantic schemas for the analytics dashboard.
These are response-only schemas — no create/update needed.
They define the exact shape of data the Recharts frontend expects.
"""

from pydantic import Field
from typing import List, Optional
from datetime import datetime
from app.schemas.base import Base


# ── Hiring Funnel ─────────────────────────────────────────────

class FunnelStage(Base):
    """One bar in the funnel chart."""
    stage:       str    = Field(description="e.g. 'Applied', 'Scored', 'Reviewed'")
    count:       int    = Field(description="Number of applications at this stage")
    percentage:  float  = Field(description="% of total that reached this stage")
    avg_days:    Optional[float] = Field(None, description="Avg days spent in this stage")


class FunnelResponse(Base):
    """Full funnel data for a job or across all jobs."""
    job_id:       Optional[str]         = None
    job_title:    Optional[str]         = None
    total_applied: int
    stages:       List[FunnelStage]
    generated_at: datetime


# ── Bias Report ───────────────────────────────────────────────

class BiasDataPoint(Base):
    """One row in the bias heatmap."""
    group:           str
    total_reviewed:  int
    total_accepted:  int
    acceptance_rate: float   = Field(description="0.0 to 1.0")
    avg_score:       float


class BiasReport(Base):
    """
    Full bias report for a job.
    Used to render the heatmap and alert cards on the dashboard.
    """
    job_id:       str
    job_title:    str
    bias_type:    str
    is_flagged:   bool
    p_value:      Optional[float]  = None
    severity:     Optional[str]    = None
    data_points:  List[BiasDataPoint]
    sample_size:  int
    generated_at: datetime


# ── Cohort Analytics ──────────────────────────────────────────

class CohortPoint(Base):
    """One data point in the cohort time-series chart."""
    period:          str    = Field(description="e.g. '2026-01', '2026-W03'")
    applications:    int
    hired:           int
    rejected:        int
    avg_score:       float
    avg_days_to_hire: Optional[float] = None


class CohortResponse(Base):
    """
    Time-series cohort data for the line chart.
    Groups applications by submission month and tracks outcomes.
    """
    department:   Optional[str]       = None
    granularity:  str                 = Field(description="monthly | weekly")
    points:       List[CohortPoint]
    generated_at: datetime


# ── Dashboard Summary ─────────────────────────────────────────

class DashboardStats(Base):
    """
    KPI cards shown at the top of the dashboard.
    Single API call returns everything the overview page needs.
    """
    total_jobs_open:        int
    total_applications:     int
    applications_this_week: int
    avg_score_all_time:     float
    avg_days_to_hire:       Optional[float]
    active_bias_flags:      int
    hired_this_month:       int
    pipeline_health:        str = Field(description="good | warning | critical")
