"""SQLAlchemy base class module."""

import uuid
from datetime import datetime
from typing import Any, Dict, TypeVar

from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    This class provides common functionality for all models.
    """

    id: Any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name.

        Returns:
            Table name in snake_case format.
        """
        return cls.__name__.lower() + "s"


class TimestampMixin:
    """Mixin to add created_at and updated_at columns to a model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class UUIDMixin:
    """Mixin to add a UUID primary key to a model."""

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )


ModelType = TypeVar("ModelType", bound=Base)