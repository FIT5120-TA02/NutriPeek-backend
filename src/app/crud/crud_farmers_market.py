"""CRUD operations for Farmers Market data."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crud.async_base import AsyncCRUDBase
from src.app.models.farmers_market import FarmersMarket


class FarmersMarketCRUD(AsyncCRUDBase[FarmersMarket, None, None]):
    """CRUD operations for FarmersMarket model.

    This class extends the base CRUD operations (create, read, update, delete)
    with farmers market specific query operations.
    """

    async def get_by_id(
        self, db: AsyncSession, market_id: UUID
    ) -> Optional[FarmersMarket]:
        """Get a farmers market by its UUID.

        Args:
            db: Database session
            market_id: UUID of the farmers market

        Returns:
            FarmersMarket object if found, otherwise None
        """
        result = await db.execute(select(self.model).where(self.model.id == market_id))
        return result.scalars().first()

    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        region: Optional[str] = None,
    ) -> List[FarmersMarket]:
        """Get all farmers markets with optional filtering and pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            region: Optional filter by region

        Returns:
            List of FarmersMarket objects
        """
        query = select(self.model)

        # Apply filters if provided
        if region:
            query = query.where(self.model.region == region)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def count(self, db: AsyncSession, region: Optional[str] = None) -> int:
        """Count farmers markets with optional filtering.

        Args:
            db: Database session
            region: Optional filter by region

        Returns:
            Count of FarmersMarket objects matching the criteria
        """
        query = select(self.model.id)

        # Apply filters if provided
        if region:
            query = query.where(self.model.region == region)

        result = await db.execute(query)
        return len(result.scalars().all())


# Create a singleton instance
farmers_market_crud = FarmersMarketCRUD(FarmersMarket)
