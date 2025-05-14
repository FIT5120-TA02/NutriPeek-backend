"""Farmers market API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.dependencies import get_async_db
from src.app.schemas.farmers_market import (
    FarmersMarketListResponse,
    FarmersMarketResponse,
)
from src.app.services.farmers_market_service import farmers_market_service

router = APIRouter(prefix="/farmers-markets", tags=["farmers-markets"])


@router.get("", response_model=FarmersMarketListResponse)
async def get_farmers_markets(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    region: Optional[str] = Query(None, description="Filter by region"),
    db: AsyncSession = Depends(get_async_db),
) -> FarmersMarketListResponse:
    """Get a list of farmers markets with optional filtering and pagination.

    This endpoint returns a list of all farmers markets in the database,
    with optional filtering by region and pagination support.

    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (for pagination)
        region: Optional filter by region name
        db: Database session dependency

    Returns:
        FarmersMarketListResponse containing list of farmers markets and total count
    """
    return await farmers_market_service.get_all_farmers_markets(
        db=db, skip=skip, limit=limit, region=region
    )


@router.get("/{market_id}", response_model=FarmersMarketResponse)
async def get_farmers_market_by_id(
    market_id: UUID, db: AsyncSession = Depends(get_async_db)
) -> FarmersMarketResponse:
    """Get detailed information about a specific farmers market.

    This endpoint returns detailed information about a specific farmers market
    identified by its UUID.

    Args:
        market_id: UUID of the farmers market to retrieve
        db: Database session dependency

    Returns:
        FarmersMarketResponse containing detailed farmers market information

    Raises:
        HTTPException: If the farmers market is not found (404)
    """
    return await farmers_market_service.get_farmers_market_by_id(
        db=db, market_id=market_id
    )
