"""CRUD operations for DailyNutrientIntake model."""

from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crud.async_base import AsyncCRUDBase
from src.app.models.daily_nutrient_intake import DailyNutrientIntake


class DailyNutrientIntakeCRUD(AsyncCRUDBase[DailyNutrientIntake, None, None]):
    """CRUD operations for DailyNutrientIntake model.

    This class extends the base CRUD operations with methods specific to
    daily nutrient intake, including filtering by age and gender.
    """

    async def get_by_age_and_gender(
        self, db: AsyncSession, *, age: int, gender: str
    ) -> List[DailyNutrientIntake]:
        """Get recommended daily nutrient intakes for a specific age and gender.

        Args:
            db: Database session
            age: Age of the child
            gender: Gender of the child (boy/girl)

        Returns:
            List of DailyNutrientIntake objects matching the criteria
        """
        query = select(self.model).where(
            and_(self.model.age == age, self.model.gender == gender)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_nutrient_age_and_gender(
        self, db: AsyncSession, *, nutrient: str, age: int, gender: str
    ) -> Optional[DailyNutrientIntake]:
        """Get specific nutrient intake recommendation for a given age and gender.

        Args:
            db: Database session
            nutrient: The name of the nutrient
            age: Age of the child
            gender: Gender of the child (boy/girl)

        Returns:
            DailyNutrientIntake object if found, None otherwise
        """
        query = select(self.model).where(
            and_(
                self.model.nutrient == nutrient,
                self.model.age == age,
                self.model.gender == gender,
            )
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_all_nutrients(self, db: AsyncSession) -> List[str]:
        """Get all distinct nutrient names in the database.

        Args:
            db: Database session

        Returns:
            List of distinct nutrient names
        """
        query = select(self.model.nutrient).distinct()
        result = await db.execute(query)
        return result.scalars().all()


# Create a singleton instance
daily_nutrient_intake_crud = DailyNutrientIntakeCRUD(DailyNutrientIntake)
