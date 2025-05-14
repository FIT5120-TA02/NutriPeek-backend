"""Service for Farmers Market operations."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crud.crud_farmers_market import farmers_market_crud
from src.app.schemas.farmers_market import (
    FarmersMarketListResponse,
    FarmersMarketResponse,
)


class FarmersMarketService:
    """Service for farmers market operations.

    This class provides business logic for farmers market operations,
    acting as an intermediary between the API endpoints and CRUD operations.
    """

    async def get_farmers_market_by_id(
        self, db: AsyncSession, market_id: UUID
    ) -> FarmersMarketResponse:
        """Get a farmers market by its ID.

        Args:
            db: Database session
            market_id: UUID of the farmers market

        Returns:
            FarmersMarketResponse object

        Raises:
            HTTPException: If farmers market not found
        """
        market = await farmers_market_crud.get_by_id(db, market_id)
        if not market:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Farmers market with id {market_id} not found",
            )
        return FarmersMarketResponse.model_validate(market)

    async def get_all_farmers_markets(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        region: Optional[str] = None,
    ) -> FarmersMarketListResponse:
        """Get all farmers markets with optional filtering and pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            region: Optional filter by region

        Returns:
            FarmersMarketListResponse containing list of FarmersMarketResponse objects
        """
        markets = await farmers_market_crud.get_all(
            db, skip=skip, limit=limit, region=region
        )
        total = await farmers_market_crud.count(db, region=region)

        return FarmersMarketListResponse(
            items=[FarmersMarketResponse.model_validate(market) for market in markets],
            total=total,
        )


# Create a singleton instance
farmers_market_service = FarmersMarketService()
