"""CRUD operations for ChildEnergyRequirement model."""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crud.async_base import AsyncCRUDBase
from src.app.models.child_energy_requirement import ChildEnergyRequirement
from src.app.schemas.child_energy_requirement import (
    ChildEnergyRequirementCreate,
    ChildEnergyRequirementUpdate,
)


class CRUDChildEnergyRequirement(
    AsyncCRUDBase[
        ChildEnergyRequirement,
        ChildEnergyRequirementCreate,
        ChildEnergyRequirementUpdate,
    ]
):
    """CRUD operations for ChildEnergyRequirement model.

    Extends the base CRUD class with custom operations for ChildEnergyRequirement.
    """

    async def get_unique_activity_levels(self, db: AsyncSession) -> List[float]:
        """Get all unique physical activity levels in the database.

        Args:
            db: Database session

        Returns:
            List of unique physical activity level values
        """
        result = await db.execute(
            select(ChildEnergyRequirement.physical_activity_level)
            .distinct()
            .order_by(ChildEnergyRequirement.physical_activity_level)
        )
        return result.scalars().all()

    async def find_nearest_pal(
        self, db: AsyncSession, target_pal: float, age: int, gender: str
    ) -> Optional[ChildEnergyRequirement]:
        """Find the record with the nearest physical activity level to the target.

        Args:
            db: Database session
            target_pal: Target physical activity level
            age: Age of the child in years
            gender: Gender of the child (boy/girl)

        Returns:
            ChildEnergyRequirement record with the nearest PAL value, or None if no records exist
        """
        # First check if there's an exact match
        result = await db.execute(
            select(ChildEnergyRequirement).where(
                ChildEnergyRequirement.physical_activity_level == target_pal,
                ChildEnergyRequirement.age == age,
                ChildEnergyRequirement.gender == gender,
            )
        )
        exact_match = result.scalars().first()
        if exact_match:
            return exact_match

        # If no exact match, find the nearest value using absolute difference
        # First get all available PAL values for this age and gender
        result = await db.execute(
            select(ChildEnergyRequirement)
            .where(
                ChildEnergyRequirement.age == age,
                ChildEnergyRequirement.gender == gender,
            )
            .order_by(
                func.abs(ChildEnergyRequirement.physical_activity_level - target_pal)
            )
        )

        # Return the closest match
        return result.scalars().first()


child_energy_requirement = CRUDChildEnergyRequirement(ChildEnergyRequirement)
