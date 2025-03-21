"""Import all models here to ensure they are registered with SQLAlchemy."""

from src.app.core.db.base_class import Base  # noqa
from src.app.models.user import User  # noqa
# Import additional models here