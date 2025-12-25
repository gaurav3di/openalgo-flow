from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.database import get_db
from app.core.openalgo import OpenAlgoClient
from app.core.auth import get_current_admin
from app.core.rate_limit import limiter, API_LIMIT
from app.core.encryption import encrypt_value, decrypt_safe
from app.models.settings import AppSettings
from app.schemas.settings import (
    SettingsUpdate,
    SettingsPublic,
    ConnectionTestResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


async def get_or_create_settings(db: AsyncSession) -> AppSettings:
    result = await db.execute(select(AppSettings).limit(1))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = AppSettings()
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


@router.get("", response_model=SettingsPublic)
@limiter.limit(API_LIMIT)
async def get_settings(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_current_admin)
):
    """Get current settings (without exposing API key)"""
    settings = await get_or_create_settings(db)
    return SettingsPublic(
        openalgo_host=settings.openalgo_host or "http://127.0.0.1:5000",
        openalgo_ws_url=settings.openalgo_ws_url or "ws://127.0.0.1:8765",
        is_configured=bool(settings.openalgo_api_key),
        has_api_key=bool(settings.openalgo_api_key)
    )


@router.put("")
@limiter.limit(API_LIMIT)
async def update_settings(
    request: Request,
    settings_update: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_current_admin)
):
    """Update settings"""
    settings = await get_or_create_settings(db)

    if settings_update.openalgo_api_key is not None:
        # Encrypt the API key before storing
        if settings_update.openalgo_api_key:
            settings.openalgo_api_key = encrypt_value(settings_update.openalgo_api_key)
            logger.info("API key encrypted and stored")
        else:
            settings.openalgo_api_key = None
    if settings_update.openalgo_host:
        settings.openalgo_host = settings_update.openalgo_host
    if settings_update.openalgo_ws_url:
        settings.openalgo_ws_url = settings_update.openalgo_ws_url

    await db.commit()
    await db.refresh(settings)

    return {
        "status": "success",
        "message": "Settings updated successfully"
    }


@router.post("/test", response_model=ConnectionTestResponse)
@limiter.limit(API_LIMIT)
async def test_connection(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_current_admin)
):
    """Test OpenAlgo connection"""
    settings = await get_or_create_settings(db)

    if not settings.openalgo_api_key:
        return ConnectionTestResponse(
            success=False,
            message="API key not configured"
        )

    # Decrypt the API key for use
    api_key = decrypt_safe(settings.openalgo_api_key)
    if not api_key:
        return ConnectionTestResponse(
            success=False,
            message="Failed to decrypt API key. Please re-enter your API key."
        )

    client = OpenAlgoClient(
        api_key=api_key,
        host=settings.openalgo_host
    )

    result = await client.test_connection()

    if result.get("status") == "success":
        return ConnectionTestResponse(
            success=True,
            message="Connection successful",
            data=result.get("data")
        )
    else:
        return ConnectionTestResponse(
            success=False,
            message=result.get("message", "Connection failed")
        )
