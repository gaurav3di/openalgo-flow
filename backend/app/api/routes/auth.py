"""
Authentication routes for single-user admin access
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from datetime import timedelta

from app.core.database import get_db
from app.core.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_admin,
    ACCESS_TOKEN_EXPIRE_HOURS,
)
from app.core.rate_limit import limiter, AUTH_LIMIT, API_LIMIT
from app.models.settings import AppSettings

router = APIRouter(prefix="/auth", tags=["authentication"])


class SetupRequest(BaseModel):
    """Initial admin setup request"""
    username: str = Field(..., min_length=3, max_length=50, description="Admin username")
    password: str = Field(..., min_length=8, description="Admin password (min 8 characters)")


class LoginRequest(BaseModel):
    """Login request"""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_HOURS * 3600


class AuthStatusResponse(BaseModel):
    """Auth status response"""
    is_setup_complete: bool
    is_authenticated: bool = False


@router.get("/status", response_model=AuthStatusResponse)
@limiter.limit(API_LIMIT)
async def get_auth_status(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Check authentication status.
    Public endpoint - no auth required.
    """
    result = await db.execute(select(AppSettings).limit(1))
    settings = result.scalar_one_or_none()

    is_setup = settings.is_setup_complete if settings else False

    return AuthStatusResponse(
        is_setup_complete=is_setup,
        is_authenticated=False  # Frontend will check token validity separately
    )


@router.post("/setup", response_model=TokenResponse)
@limiter.limit(AUTH_LIMIT)
async def setup_admin(
    request: Request,
    setup_data: SetupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Initial admin setup - sets the admin password.
    Only works if setup is not already complete.
    """
    result = await db.execute(select(AppSettings).limit(1))
    settings = result.scalar_one_or_none()

    if settings and settings.is_setup_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Setup already complete. Use login instead."
        )

    # Create or update settings with username and password
    if not settings:
        settings = AppSettings(
            admin_username=setup_data.username,
            admin_password_hash=get_password_hash(setup_data.password),
            is_setup_complete=True
        )
        db.add(settings)
    else:
        settings.admin_username = setup_data.username
        settings.admin_password_hash = get_password_hash(setup_data.password)
        settings.is_setup_complete = True

    await db.commit()

    # Generate token for immediate login
    access_token = create_access_token(
        data={"sub": setup_data.username},
        expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )

    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(AUTH_LIMIT)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Admin login - returns JWT token.
    """
    result = await db.execute(select(AppSettings).limit(1))
    settings = result.scalar_one_or_none()

    if not settings or not settings.is_setup_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Setup not complete. Please set admin password first."
        )

    if not settings.admin_password_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password not configured"
        )

    # Verify username matches
    if settings.admin_username != login_data.username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(login_data.password, settings.admin_password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": "admin"},
        expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )

    return TokenResponse(access_token=access_token)


@router.post("/change-password")
@limiter.limit(AUTH_LIMIT)
async def change_password(
    request: Request,
    change_data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_current_admin)
):
    """
    Change admin password.
    Requires authentication.
    """
    result = await db.execute(select(AppSettings).limit(1))
    settings = result.scalar_one_or_none()

    if not settings or not settings.admin_password_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Settings not found"
        )

    if not verify_password(change_data.current_password, settings.admin_password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    settings.admin_password_hash = get_password_hash(change_data.new_password)
    await db.commit()

    return {"status": "success", "message": "Password changed successfully"}


@router.post("/logout")
@limiter.limit(API_LIMIT)
async def logout(request: Request, _: bool = Depends(get_current_admin)):
    """
    Logout - client should discard the token.
    This endpoint just validates the token is still valid.
    """
    return {"status": "success", "message": "Logged out successfully"}


@router.get("/verify")
@limiter.limit(API_LIMIT)
async def verify_token_endpoint(request: Request, _: bool = Depends(get_current_admin)):
    """
    Verify if the current token is valid.
    Returns 200 if valid, 401 if invalid.
    """
    return {"status": "success", "message": "Token is valid"}


class ProfileResponse(BaseModel):
    """Profile response"""
    username: str
    created_at: str


@router.get("/profile", response_model=ProfileResponse)
@limiter.limit(API_LIMIT)
async def get_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_current_admin)
):
    """
    Get current admin profile.
    Requires authentication.
    """
    result = await db.execute(select(AppSettings).limit(1))
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Settings not found"
        )

    return ProfileResponse(
        username=settings.admin_username or "admin",
        created_at=settings.created_at.isoformat() if settings.created_at else ""
    )
