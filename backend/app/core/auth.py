"""
Authentication module for single-user admin access
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
import logging
from pathlib import Path

from app.core.database import get_db
from app.models.settings import AppSettings

logger = logging.getLogger(__name__)

# Security configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30  # 30 days session

# Persist SECRET_KEY to survive server restarts
DATA_DIR = Path(__file__).parent.parent.parent / "data"
SECRET_KEY_FILE = DATA_DIR / ".secret_key"


def get_or_create_secret_key() -> str:
    """Get existing secret key or create a new one"""
    DATA_DIR.mkdir(exist_ok=True)

    if SECRET_KEY_FILE.exists():
        return SECRET_KEY_FILE.read_text().strip()

    # Generate new key and save it
    key = secrets.token_urlsafe(32)
    SECRET_KEY_FILE.write_text(key)
    logger.info("Generated new secret key")
    return key


SECRET_KEY = get_or_create_secret_key()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify a JWT token and return its payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_admin(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> bool:
    """
    Dependency to verify admin authentication.
    Returns True if authenticated, raises HTTPException otherwise.
    """
    # Check if setup is complete
    result = await db.execute(select(AppSettings).limit(1))
    settings = result.scalar_one_or_none()

    # If no settings or setup not complete, allow access to setup endpoints
    if not settings or not settings.is_setup_complete:
        # Check if this is a setup-related endpoint
        if request.url.path in ["/api/auth/setup", "/api/auth/status"]:
            return True
        # For other endpoints, require setup first
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Setup not complete. Please set admin password first."
        )

    # Setup is complete, require authentication
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("sub") != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True


async def get_optional_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> bool:
    """
    Optional authentication - doesn't raise exception if not authenticated.
    Used for endpoints that have different behavior based on auth status.
    """
    if not credentials:
        return False

    payload = verify_token(credentials.credentials)
    if not payload or payload.get("sub") != "admin":
        return False

    return True
