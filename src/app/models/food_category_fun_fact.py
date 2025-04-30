"""Food Category Fun Fact model module."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.app.core.db.base_class import Base, TimestampMixin, UUIDMixin


class FoodCategoryFunFact(Base, UUIDMixin, TimestampMixin):
    """Food Category Fun Fact model for storing fun facts about food categories.

    Attributes:
        category: The food category name
        fun_fact: A fun fact about the food category
    """

    __tablename__ = "food_category_fun_fact"

    food_category: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, unique=True
    )
    fun_fact: Mapped[str] = mapped_column(Text, nullable=False)
