"""
api/auth.py — Authentication endpoints
"""

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import traceback
from fastapi.responses import JSONResponse
from app.core.database import get_db
from app.core.security import oauth2_scheme
from app.schemas.user import (
    UserRegister, UserResponse,
    TokenResponse, LoginResponse, RefreshRequest,
)
from app.schemas.common import SuccessResponse, MessageResponse
from app.services.auth_service import auth_service

router = APIRouter()


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


# ── Register ──────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
async def register(
    data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await auth_service.register(
            data=data,
            db=db,
            ip_address=get_client_ip(request),
        )
        return SuccessResponse(data=user, message="Account created successfully")
    except Exception as e:
        # Prints the FULL traceback to your PyCharm console
        logger.error(f"Register error: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise  # re-raise so FastAPI returns 500 or the HTTPException


# ── Login (OAuth2 form) ───────────────────────────────────────

@router.post(
    "/login",
    response_model=SuccessResponse[LoginResponse],
    summary="Login — OAuth2 form (username = email)",
)
async def login_form(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await auth_service.login(
            email=form_data.username,
            password=form_data.password,
            db=db,
            ip_address=get_client_ip(request),
        )
        return SuccessResponse(data=result, message="Login successful")
    except Exception as e:
        logger.error(f"Login error: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise


# ── Login (JSON body — used by React) ────────────────────────

@router.post(
    "/login/json",
    response_model=SuccessResponse[LoginResponse],
    summary="Login — JSON body",
)
async def login_json(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        body = await request.json()
        result = await auth_service.login(
            email=body.get("email", ""),
            password=body.get("password", ""),
            db=db,
            ip_address=get_client_ip(request),
        )
        return SuccessResponse(data=result, message="Login successful")
    except Exception as e:
        logger.error(f"Login JSON error: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise


# ── Refresh token ─────────────────────────────────────────────

@router.post(
    "/refresh",
    response_model=SuccessResponse[TokenResponse],
    summary="Get new access token using refresh token",
)
async def refresh_token(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    tokens = await auth_service.refresh(
        refresh_token=data.refresh_token,
        db=db,
    )
    return SuccessResponse(data=tokens, message="Token refreshed")


# ── Get current user ──────────────────────────────────────────

@router.get(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="Get current authenticated user",
)
async def get_me(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    user = await auth_service.get_current_user(token=token, db=db)
    return SuccessResponse(data=user)


# ── Logout ────────────────────────────────────────────────────

@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout and record in audit log",
)
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    from app.core.security import decode_token
    from app.models.audit_log import AuditLog, AuditAction
    import uuid

    payload    = decode_token(token)
    user_id    = payload.get("sub")
    user_email = payload.get("email")
    user_role  = payload.get("role")

    db.add(AuditLog(
        id=str(uuid.uuid4()),
        actor_id=user_id,
        actor_email=user_email,
        actor_role=user_role,
        action=AuditAction.USER_LOGOUT,
        entity_type="user",
        entity_id=user_id,
        ip_address=get_client_ip(request),
    ))
    await db.commit()
    return MessageResponse(message="Logged out successfully")

#-------Token________
@router.post(
    "/token",
    include_in_schema=False,  # hidden from Swagger docs list
    summary="OAuth2 token endpoint for Swagger UI",
)
async def token_for_swagger(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns token in the flat format Swagger OAuth2 expects.
    Not for frontend use — use /login/json instead.
    """
    result = await auth_service.login(
        email=form_data.username,
        password=form_data.password,
        db=db,
        ip_address=get_client_ip(request),
    )
    return JSONResponse({
        "access_token": result.tokens.access_token,
        "token_type": "bearer",
    })