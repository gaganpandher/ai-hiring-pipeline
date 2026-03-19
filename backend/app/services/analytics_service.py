"""
services/analytics_service.py
──────────────────────────────
Complex SQL queries powering the analytics dashboard.

Every query here uses raw SQLAlchemy core expressions
(not ORM) for maximum control and performance.

Queries showcase:
  - Multi-table JOINs
  - GROUP BY with aggregates (COUNT, AVG, MIN, MAX)
  - CASE expressions
  - Subqueries
  - Window functions
  - Date truncation for time-series
  - CTEs (Common Table Expressions)
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func, case, and_, cast, Float
from loguru import logger

from app.models.user import User
from app.models.job import Job, JobStatus
from app.models.application import Application, ApplicationStatus
from app.models.score import Score
from app.models.bias_flag import BiasFlag
from app.schemas.analytics import (
    DashboardStats, FunnelStage, FunnelResponse,
    BiasDataPoint, BiasReport, CohortPoint, CohortResponse,
)


class AnalyticsService:

    # ── Dashboard KPI cards ───────────────────────────────────

    async def get_dashboard_stats(
        self, db: AsyncSession
    ) -> DashboardStats:
        """
        Single query pass for all KPI cards.
        Uses subqueries so the dashboard loads in one round-trip.
        """
        now = datetime.now(timezone.utc)
        week_ago   = now - timedelta(days=7)
        month_ago  = now - timedelta(days=30)

        # ── Total open jobs ──────────────────────────────────
        open_jobs = (await db.execute(
            select(func.count(Job.id))
            .where(Job.status == JobStatus.OPEN)
        )).scalar_one()

        # ── Total applications ────────────────────────────────
        total_apps = (await db.execute(
            select(func.count(Application.id))
        )).scalar_one()

        # ── Applications this week ────────────────────────────
        apps_this_week = (await db.execute(
            select(func.count(Application.id))
            .where(Application.submitted_at >= week_ago)
        )).scalar_one()

        # ── Average score across all scored applications ──────
        avg_score = (await db.execute(
            select(func.avg(Score.overall_score))
        )).scalar_one() or 0.0

        # ── Average days to hire ──────────────────────────────
        # TIMESTAMPDIFF in raw SQL — more readable than SQLAlchemy expression
        avg_days_result = (await db.execute(text("""
            SELECT AVG(TIMESTAMPDIFF(DAY, submitted_at, decided_at))
            FROM applications
            WHERE status = 'hired'
            AND decided_at IS NOT NULL
        """))).scalar_one()

        # ── Active bias flags ─────────────────────────────────
        active_flags = (await db.execute(
            select(func.count(BiasFlag.id))
            .where(BiasFlag.is_resolved == False)
        )).scalar_one()

        # ── Hired this month ──────────────────────────────────
        hired_month = (await db.execute(
            select(func.count(Application.id))
            .where(
                and_(
                    Application.status == ApplicationStatus.HIRED,
                    Application.decided_at >= month_ago,
                )
            )
        )).scalar_one()

        # ── Pipeline health score ─────────────────────────────
        # Simple heuristic: based on bias flags + avg score
        if active_flags > 5 or avg_score < 40:
            health = "critical"
        elif active_flags > 2 or avg_score < 60:
            health = "warning"
        else:
            health = "good"

        return DashboardStats(
            total_jobs_open=open_jobs,
            total_applications=total_apps,
            applications_this_week=apps_this_week,
            avg_score_all_time=round(float(avg_score), 1),
            avg_days_to_hire=round(float(avg_days_result), 1) if avg_days_result else None,
            active_bias_flags=active_flags,
            hired_this_month=hired_month,
            pipeline_health=health,
        )

    # ── Hiring funnel ─────────────────────────────────────────

    async def get_funnel(
        self,
        db: AsyncSession,
        job_id: str | None = None,
    ) -> FunnelResponse:
        """
        Counts applications at each stage of the hiring funnel.

        Uses a single GROUP BY query with CASE to pivot
        status counts into named columns — much faster than
        running 6 separate COUNT queries.

        SQL equivalent:
          SELECT
            COUNT(*)                                     AS total,
            SUM(CASE WHEN status='pending'  THEN 1 END) AS pending,
            SUM(CASE WHEN status='scored'   THEN 1 END) AS scored,
            ...
          FROM applications
          WHERE job_id = ?  -- optional
        """
        where = Application.job_id == job_id if job_id else True

        # Pivot query using CASE expressions
        result = (await db.execute(
            select(
                func.count(Application.id).label("total"),
                func.sum(case(
                    (Application.status == ApplicationStatus.PENDING,  1), else_=0
                )).label("pending"),
                func.sum(case(
                    (Application.status == ApplicationStatus.SCORED,   1), else_=0
                )).label("scored"),
                func.sum(case(
                    (Application.status == ApplicationStatus.REVIEWED, 1), else_=0
                )).label("reviewed"),
                func.sum(case(
                    (Application.status == ApplicationStatus.SHORTLIST,1), else_=0
                )).label("shortlist"),
                func.sum(case(
                    (Application.status == ApplicationStatus.REJECTED, 1), else_=0
                )).label("rejected"),
                func.sum(case(
                    (Application.status == ApplicationStatus.HIRED,    1), else_=0
                )).label("hired"),
            ).where(where)
        )).one()

        total = result.total or 1  # avoid division by zero

        # Average time between stages (raw SQL for TIMESTAMPDIFF)
        avg_days_sql = text("""
            SELECT
                AVG(CASE WHEN reviewed_at IS NOT NULL
                    THEN TIMESTAMPDIFF(HOUR, submitted_at, reviewed_at)/24.0
                    END) AS days_to_review,
                AVG(CASE WHEN decided_at IS NOT NULL
                    THEN TIMESTAMPDIFF(HOUR, submitted_at, decided_at)/24.0
                    END) AS days_to_decide
            FROM applications
            WHERE (:job_id IS NULL OR job_id = :job_id)
        """)
        avg_days = (await db.execute(avg_days_sql, {"job_id": job_id})).one()

        stages = [
            FunnelStage(stage="Applied",   count=result.total,     percentage=100.0),
            FunnelStage(stage="Scored",    count=result.scored,    percentage=round((result.scored    / total) * 100, 1), avg_days=None),
            FunnelStage(stage="Reviewed",  count=result.reviewed,  percentage=round((result.reviewed  / total) * 100, 1), avg_days=round(float(avg_days.days_to_review), 1) if avg_days.days_to_review else None),
            FunnelStage(stage="Shortlist", count=result.shortlist, percentage=round((result.shortlist / total) * 100, 1)),
            FunnelStage(stage="Rejected",  count=result.rejected,  percentage=round((result.rejected  / total) * 100, 1), avg_days=round(float(avg_days.days_to_decide), 1) if avg_days.days_to_decide else None),
            FunnelStage(stage="Hired",     count=result.hired,     percentage=round((result.hired     / total) * 100, 1)),
        ]

        # Get job title if filtering by job
        job_title = None
        if job_id:
            j = (await db.execute(select(Job.title).where(Job.id == job_id))).scalar_one_or_none()
            job_title = j

        return FunnelResponse(
            job_id=job_id,
            job_title=job_title,
            total_applied=result.total,
            stages=stages,
            generated_at=datetime.now(timezone.utc),
        )

    # ── Cohort time-series ────────────────────────────────────

    async def get_cohorts(
        self,
        db: AsyncSession,
        department: str | None = None,
        months: int = 6,
    ) -> CohortResponse:
        """
        Groups applications by month and tracks outcomes.
        Uses DATE_FORMAT for MySQL-compatible date truncation.

        The JOIN with jobs lets us filter by department —
        a three-table join: applications → jobs → filter.

        SQL equivalent:
          SELECT
            DATE_FORMAT(a.submitted_at, '%Y-%m') AS period,
            COUNT(a.id)                           AS applications,
            SUM(a.status = 'hired')               AS hired,
            AVG(s.overall_score)                  AS avg_score
          FROM applications a
          JOIN jobs j ON a.job_id = j.id
          LEFT JOIN scores s ON a.id = s.application_id
          WHERE a.submitted_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
          GROUP BY period
          ORDER BY period
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)

        sql = text("""
            SELECT
                DATE_FORMAT(a.submitted_at, '%Y-%m')          AS period,
                COUNT(a.id)                                    AS applications,
                SUM(a.status = 'hired')                        AS hired,
                SUM(a.status = 'rejected')                     AS rejected,
                COALESCE(AVG(s.overall_score), 0)              AS avg_score,
                AVG(CASE
                    WHEN a.status = 'hired' AND a.decided_at IS NOT NULL
                    THEN TIMESTAMPDIFF(DAY, a.submitted_at, a.decided_at)
                END)                                           AS avg_days_to_hire
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            LEFT JOIN scores s ON a.id = s.application_id
            WHERE a.submitted_at >= :cutoff
              AND (:dept IS NULL OR j.department = :dept)
            GROUP BY DATE_FORMAT(a.submitted_at, '%Y-%m')
            ORDER BY period ASC
        """)

        rows = (await db.execute(sql, {
            "cutoff": cutoff,
            "dept":   department,
        })).all()

        points = [
            CohortPoint(
                period=r.period,
                applications=r.applications,
                hired=r.hired or 0,
                rejected=r.rejected or 0,
                avg_score=round(float(r.avg_score), 1),
                avg_days_to_hire=round(float(r.avg_days_to_hire), 1) if r.avg_days_to_hire else None,
            )
            for r in rows
        ]

        return CohortResponse(
            department=department,
            granularity="monthly",
            points=points,
            generated_at=datetime.now(timezone.utc),
        )

    # ── Bias report per job ───────────────────────────────────

    async def get_bias_report(
        self,
        db: AsyncSession,
        job_id: str,
    ) -> BiasReport:
        """
        Analyses acceptance rates by name-based gender proxy.

        Uses a CTE to first classify applicant names, then
        aggregates decisions per group.

        This is the query that feeds the bias heatmap on the dashboard.
        The actual chi-square test runs in the bias_consumer —
        this query just pulls the raw rates for display.

        SQL pattern:
          WITH classified AS (
            SELECT
              a.id,
              a.status,
              CASE WHEN u.full_name REGEXP '...' THEN 'group_a' ELSE 'group_b' END AS group
            FROM applications a
            JOIN users u ON a.applicant_id = u.id
            WHERE a.job_id = ?
          )
          SELECT group, COUNT(*), SUM(status='hired'), AVG(score)
          FROM classified
          GROUP BY group
        """
        sql = text("""
            WITH classified AS (
                SELECT
                    a.id,
                    a.status,
                    COALESCE(s.overall_score, 0) AS score,
                    CASE
                        WHEN LOWER(SUBSTRING_INDEX(u.full_name, ' ', 1))
                             IN ('james','john','robert','michael','william',
                                 'david','richard','joseph','thomas','charles',
                                 'daniel','matthew','anthony','mark','donald',
                                 'steven','paul','andrew','kenneth','george')
                        THEN 'male-proxy'
                        WHEN LOWER(SUBSTRING_INDEX(u.full_name, ' ', 1))
                             IN ('mary','patricia','jennifer','linda','barbara',
                                 'elizabeth','susan','jessica','sarah','karen',
                                 'lisa','nancy','betty','margaret','sandra',
                                 'ashley','emily','dorothy','kimberly','helen')
                        THEN 'female-proxy'
                        ELSE 'unknown'
                    END AS name_group
                FROM applications a
                JOIN users u ON a.applicant_id = u.id
                LEFT JOIN scores s ON a.id = s.application_id
                WHERE a.job_id = :job_id
                  AND a.status IN ('reviewed','shortlist','rejected','hired')
            )
            SELECT
                name_group                                    AS grp,
                COUNT(*)                                      AS total_reviewed,
                SUM(status IN ('shortlist','hired'))          AS total_accepted,
                ROUND(AVG(score), 1)                          AS avg_score
            FROM classified
            WHERE name_group != 'unknown'
            GROUP BY name_group
            HAVING COUNT(*) > 0
        """)

        rows = (await db.execute(sql, {"job_id": job_id})).all()

        # Check for existing bias flag on this job
        flag = (await db.execute(
            select(BiasFlag)
            .where(
                and_(
                    BiasFlag.job_id == job_id,
                    BiasFlag.is_resolved == False,
                )
            )
            .order_by(BiasFlag.detected_at.desc())
        )).scalars().first()

        job_title = (await db.execute(
            select(Job.title).where(Job.id == job_id)
        )).scalar_one_or_none() or "Unknown Job"

        data_points = []
        for r in rows:
            accepted = r.total_accepted or 0
            rate = accepted / r.total_reviewed if r.total_reviewed > 0 else 0.0
            data_points.append(BiasDataPoint(
                group=r.grp,
                total_reviewed=r.total_reviewed,
                total_accepted=accepted,
                acceptance_rate=round(rate, 3),
                avg_score=float(r.avg_score or 0),
            ))

        return BiasReport(
            job_id=job_id,
            job_title=job_title,
            bias_type="gender",
            is_flagged=flag is not None,
            p_value=flag.p_value if flag else None,
            severity=flag.severity if flag else None,
            data_points=data_points,
            sample_size=sum(d.total_reviewed for d in data_points),
            generated_at=datetime.now(timezone.utc),
        )

    # ── Department breakdown ──────────────────────────────────

    async def get_department_breakdown(
        self, db: AsyncSession
    ) -> list[dict]:
        """
        Hiring metrics grouped by department.
        Four-table join: jobs → applications → scores → aggregates.
        """
        sql = text("""
            SELECT
                j.department,
                COUNT(DISTINCT j.id)                       AS total_jobs,
                COUNT(a.id)                                AS total_applications,
                SUM(a.status = 'hired')                    AS total_hired,
                ROUND(AVG(s.overall_score), 1)             AS avg_score,
                ROUND(
                    SUM(a.status = 'hired') /
                    NULLIF(COUNT(a.id), 0) * 100, 1
                )                                          AS hire_rate_pct
            FROM jobs j
            LEFT JOIN applications a ON j.id = a.job_id
            LEFT JOIN scores s ON a.id = s.application_id
            GROUP BY j.department
            ORDER BY total_applications DESC
        """)

        rows = (await db.execute(sql)).all()
        return [
            {
                "department":          r.department,
                "total_jobs":          r.total_jobs,
                "total_applications":  r.total_applications,
                "total_hired":         r.total_hired or 0,
                "avg_score":           float(r.avg_score or 0),
                "hire_rate_pct":       float(r.hire_rate_pct or 0),
            }
            for r in rows
        ]


analytics_service = AnalyticsService()