from sqlalchemy import Column, Enum, String

from src.app.core.db.base_class import Base, TimestampMixin, UUIDMixin


class SeasonalFood(Base, UUIDMixin, TimestampMixin):
    """Model for seasonal food data across different regions.

    This model stores information about foods that are in season during
    specific months in different regions.

    Attributes:
        id: Primary key for the seasonal food entry
        food_name: Name of the food item
        category: Category of the food (e.g., fruit, vegetable)
        db_category: Database category of the food (e.g., apple, banana)
        region: Geographic region where the food is in season
        season: General season category (Spring, Summer, Autumn, Winter)
        month: Specific month when the food is in season
    """

    __tablename__ = "seasonal_food"

    food_name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    db_category = Column(String, nullable=False, index=True, default="")
    region = Column(String, nullable=False, index=True)
    season = Column(
        Enum("Spring", "Summer", "Autumn", "Winter", name="season_enum"),
        nullable=False,
        index=True,
    )
    month = Column(String, nullable=False, index=True)
