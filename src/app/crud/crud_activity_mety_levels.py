"""CRUD operations for Activity METy Level model."""

from typing import List, Optional

from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crud.async_base import AsyncCRUDBase
from src.app.models.activity_mety_level import ActivityMETyLevel


class CRUDActivityMETyLevel(AsyncCRUDBase[ActivityMETyLevel, dict, dict]):
    """CRUD operations for Activity METy Level model."""

    async def get_distinct_activities(self, db: AsyncSession) -> List[str]:
        """Get a list of distinct specific activities.

        Args:
            db: Database session

        Returns:
            List of distinct specific activities
        """
        stmt = select(distinct(ActivityMETyLevel.specific_activity)).order_by(
            ActivityMETyLevel.specific_activity
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_mety_level_by_age_and_activity(
        self, db: AsyncSession, *, age: int, specific_activity: str
    ) -> Optional[ActivityMETyLevel]:
        """Get METy level for a specific age and activity.

        Args:
            db: Database session
            age: Age to filter by
            specific_activity: Specific activity to filter by

        Returns:
            ActivityMETyLevel object if found, None otherwise
        """
        stmt = select(ActivityMETyLevel).where(
            ActivityMETyLevel.age == age,
            ActivityMETyLevel.specific_activity == specific_activity,
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_closest_age_mety_level(
        self, db: AsyncSession, *, age: int, specific_activity: str
    ) -> Optional[ActivityMETyLevel]:
        """Get METy level for the closest available age for a specific activity.

        If exact age match is not found, finds the closest available age.

        Args:
            db: Database session
            age: Target age
            specific_activity: Specific activity to filter by

        Returns:
            ActivityMETyLevel object for the closest age if found, None otherwise
        """
        # First try exact match
        exact_match = await self.get_mety_level_by_age_and_activity(
            db, age=age, specific_activity=specific_activity
        )
        if exact_match:
            return exact_match

        # If no exact match, find all ages for this activity
        stmt = (
            select(ActivityMETyLevel.age)
            .where(ActivityMETyLevel.specific_activity == specific_activity)
            .distinct()
        )
        result = await db.execute(stmt)
        available_ages = result.scalars().all()

        if not available_ages:
            return None

        # Find closest age
        closest_age = min(available_ages, key=lambda x: abs(x - age))

        # Get METy level for closest age
        return await self.get_mety_level_by_age_and_activity(
            db, age=closest_age, specific_activity=specific_activity
        )


activity_mety_level_crud = CRUDActivityMETyLevel(ActivityMETyLevel)
