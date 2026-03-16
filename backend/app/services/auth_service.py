"""
services/auth_service.py
────────────────────────
All authentication business logic lives here.
The API route (api/auth.py) stays thin — it just calls
these functions and returns the result.

Separating service logic from routes makes it:
  - Easier to unit test (no HTTP layer needed)
  - Reusable across multiple routes
  - Cleaner and easier to read
"""

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from loguru import logger

from app.models.user import User, UserRole
from app.models.audit_log import AuditLog, AuditAction
from app.schemas.user import UserRegister, UserResponse, TokenResponse, LoginResponse
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)
from app.core.config import settings
import uuid


class AuthService:

    # ── Register ─────────────────────────────────────────────

    async def register(
        self,
        data: UserRegister,
        db: AsyncSession,
        ip_address: str | None = None,
    ) -> UserResponse:
        """
        Create a new user account.
        Steps:
          1. Check email not already taken
          2. Hash the password (never store plaintext)
          3. Create User record in MySQL
          4. Write audit log entry
          5. Return UserResponse (no password)
        """

        # Step 1: Check for duplicate email
        # We query by email — this hits the index we defined on users.email
        existing = await db.execute(
            select(User).where(User.email == data.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists"
            )

        # Step 2: Hash password
        # bcrypt automatically salts the hash — each call produces
        # a different hash even for the same password
        hashed = hash_password(data.password)

        # Step 3: Create user
        user = User(
            id=str(uuid.uuid4()),
            email=data.email,
            password_hash=hashed,
            full_name=data.full_name,
            role=data.role,
            is_active=True,
        )
        db.add(user)

        # Step 4: Audit log
        log = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=user.id,
            actor_email=user.email,
            actor_role=user.role.value,
            action=AuditAction.USER_REGISTERED,
            entity_type="user",
            entity_id=user.id,
            payload={"email": user.email, "role": user.role.value},
            ip_address=ip_address,
        )
        db.add(log)

        # Commit both in one transaction — atomic operation
        # If audit log fails, user is also not created (and vice versa)
        await db.commit()
        await db.refresh(user)

        logger.info(f"New user registered: {user.email} [{user.role}]")
        return UserResponse.model_validate(user)

    # ── Login ─────────────────────────────────────────────────

    async def login(
        self,
        email: str,
        password: str,
        db: AsyncSession,
        ip_address: str | None = None,
    ) -> LoginResponse:
        """
        Authenticate user and return JWT tokens.
        Steps:
          1. Find user by email
          2. Verify password against bcrypt hash
          3. Update last_login_at timestamp
          4. Generate access + refresh tokens
          5. Write audit log
          6. Return tokens + user profile
        """

        # Step 1: Find user
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        # Step 2: Verify password
        # Important: we check BOTH "user exists" and "password correct"
        # before raising an error. This prevents timing attacks that
        # could reveal whether an email is registered.
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled. Contact support."
            )

        # Step 3: Update last login timestamp
        user.last_login_at = datetime.now(timezone.utc)

        # Step 4: Generate tokens
        # extra claims embedded in the JWT payload —
        # the middleware reads 'role' to enforce RBAC
        access_token = create_access_token(
            subject=user.id,
            extra={"email": user.email, "role": user.role.value}
        )
        refresh_token = create_refresh_token(subject=user.id)

        # Step 5: Audit log
        log = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=user.id,
            actor_email=user.email,
            actor_role=user.role.value,
            action=AuditAction.USER_LOGIN,
            entity_type="user",
            entity_id=user.id,
            ip_address=ip_address,
        )
        db.add(log)
        await db.commit()
        await db.refresh(user)

        logger.info(f"Login: {user.email}")

        return LoginResponse(
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            ),
            user=UserResponse.model_validate(user),
        )

    # ── Refresh token ─────────────────────────────────────────

    async def refresh(
        self,
        refresh_token: str,
        db: AsyncSession,
    ) -> TokenResponse:
        """
        Exchange a refresh token for a new access token.
        The frontend calls this automatically when the access
        token expires (handled by the Axios interceptor).
        """
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        user_id = payload.get("sub")
        result  = await db.execute(select(User).where(User.id == user_id))
        user    = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        new_access = create_access_token(
            subject=user.id,
            extra={"email": user.email, "role": user.role.value}
        )

        return TokenResponse(
            access_token=new_access,
            refresh_token=refresh_token,   # reuse same refresh token
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ── Get current user ──────────────────────────────────────

    async def get_current_user(
        self,
        token: str,
        db: AsyncSession,
    ) -> UserResponse:
        """
        Decode JWT and return the current user's profile.
        Called by GET /auth/me — the frontend calls this once
        on app load to restore the session.
        """
        payload = decode_token(token)
        user_id = payload.get("sub")

        result = await db.execute(select(User).where(User.id == user_id))
        user   = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserResponse.model_validate(user)


# ── Singleton instance ────────────────────────────────────────
# One instance shared across all requests.
# Safe because the class has no mutable state —
# all state lives in the db session passed as a parameter.
auth_service = AuthService()