"""Base CRUD operations module."""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.app.core.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base class for CRUD operations.

    Attributes:
        model: SQLAlchemy model class.
    """

    def __init__(self, model: Type[ModelType]) -> None:
        """Initialize CRUDBase.

        Args:
            model: SQLAlchemy model class.
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get a record by ID.

        Args:
            db: Database session.
            id: Record ID.

        Returns:
            Record if found, None otherwise.
        """
        result = db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records.

        Args:
            db: Database session.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of records.
        """
        result = db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record.

        Args:
            db: Database session.
            obj_in: Input data.

        Returns:
            Created record.
        """
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """Update a record.

        Args:
            db: Database session.
            db_obj: Database object to update.
            obj_in: Input data.

        Returns:
            Updated record.
        """
        obj_data = db_obj.__dict__
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """Remove a record.

        Args:
            db: Database session.
            id: Record ID.

        Returns:
            Removed record if found, None otherwise.
        """
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
