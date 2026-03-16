"""schemas/__init__.py — exports all schemas for clean imports."""

from app.schemas.user        import (
    UserRegister, UserLogin, UserUpdate,
    UserResponse, UserSummary,
    TokenResponse, LoginResponse, RefreshRequest,
)
from app.schemas.job         import (
    JobCreate, JobUpdate,
    JobResponse, JobSummary,
)
from app.schemas.application import (
    ApplicationCreate, ApplicationDecision,
    ApplicationResponse, ApplicationSummary, ScoreSummary,
)
from app.schemas.analytics   import (
    FunnelResponse, BiasReport, CohortResponse, DashboardStats,
)
from app.schemas.common      import (
    SuccessResponse, PaginatedResponse,
    ErrorResponse, MessageResponse,
)