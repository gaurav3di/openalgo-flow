from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.openalgo import OpenAlgoClient
from app.core.auth import get_current_admin
from app.core.rate_limit import limiter, READ_LIMIT
from app.core.encryption import decrypt_safe
from app.models.settings import AppSettings

router = APIRouter(prefix="/symbols", tags=["symbols"])


async def get_openalgo_client(db: AsyncSession = Depends(get_db)) -> OpenAlgoClient:
    result = await db.execute(select(AppSettings).limit(1))
    settings = result.scalar_one_or_none()

    if not settings or not settings.openalgo_api_key:
        raise HTTPException(status_code=400, detail="OpenAlgo not configured")

    # Decrypt the API key
    api_key = decrypt_safe(settings.openalgo_api_key)
    if not api_key:
        raise HTTPException(status_code=500, detail="Failed to decrypt API key. Please re-enter your API key.")

    return OpenAlgoClient(
        api_key=api_key,
        host=settings.openalgo_host
    )


@router.get("/search")
@limiter.limit(READ_LIMIT)
async def search_symbols(
    request: Request,
    query: str = Query(..., min_length=1),
    exchange: str = Query(default="NSE"),
    client: OpenAlgoClient = Depends(get_openalgo_client),
    _: bool = Depends(get_current_admin)
):
    """Search for symbols"""
    result = await client.search_symbols(query, exchange)
    return result


@router.get("/quotes")
@limiter.limit(READ_LIMIT)
async def get_quotes(
    request: Request,
    symbol: str = Query(...),
    exchange: str = Query(default="NSE"),
    client: OpenAlgoClient = Depends(get_openalgo_client),
    _: bool = Depends(get_current_admin)
):
    """Get quotes for a symbol"""
    result = await client.get_quotes(symbol, exchange)
    return result
