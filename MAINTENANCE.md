# NutriPeek Backend - Maintenance Activities

This document provides guidelines for ongoing maintenance, extension, and enhancement of the NutriPeek backend codebase. It covers recommended approaches for adding new functionality, maintaining code quality, and implementing changes while preserving system integrity.

## Table of Contents

- [Adding New Functionality](#adding-new-functionality)
  - [Creating API Endpoints](#creating-api-endpoints)
  - [Adding Services](#adding-services)
  - [Extending Data Models](#extending-data-models)
  - [Adding Middleware](#adding-middleware)
- [Code Style & Standards](#code-style--standards)
  - [Python Style Guidelines](#python-style-guidelines)
  - [Documentation Requirements](#documentation-requirements)
  - [Naming Conventions](#naming-conventions)
- [Database Maintenance](#database-maintenance)
  - [Creating Migrations](#creating-migrations)
  - [Managing Database Changes](#managing-database-changes)
- [Testing Requirements](#testing-requirements)
  - [Test Coverage](#test-coverage)
  - [Test Strategy](#test-strategy)
- [Refactoring Guidelines](#refactoring-guidelines)
  - [When to Refactor](#when-to-refactor)
  - [Refactoring Approach](#refactoring-approach)
- [Version Control Workflow](#version-control-workflow)
  - [Branching Strategy](#branching-strategy)
  - [Commit Standards](#commit-standards)
- [Performance Optimization](#performance-optimization)

## Adding New Functionality

### Creating API Endpoints

When adding new API endpoints to the NutriPeek backend, follow these steps:

1. **Define the Schema**:

   - Create appropriate Pydantic schemas in `src/app/schemas/`
   - Define request and response models with proper validation
   - Example:

     ```python
     # src/app/schemas/example.py
     from pydantic import BaseModel, Field

     class ExampleRequest(BaseModel):
         name: str = Field(..., min_length=1, description="Name parameter")

     class ExampleResponse(BaseModel):
         message: str
         request_id: str
     ```

2. **Create the Router**:

   - Add a new router file in `src/app/api/v1/`
   - Follow the existing pattern with appropriate tags and prefix
   - Include comprehensive docstrings with parameter explanations
   - Example:

     ```python
     # src/app/api/v1/example.py
     from fastapi import APIRouter, Depends, status
     from sqlalchemy.ext.asyncio import AsyncSession

     from src.app.api.dependencies import get_async_db
     from src.app.schemas.example import ExampleRequest, ExampleResponse
     from src.app.services.example_service import example_service

     router = APIRouter(prefix="/examples", tags=["examples"])

     @router.post(
         "/",
         response_model=ExampleResponse,
         status_code=status.HTTP_201_CREATED,
         summary="Create a new example",
         description="Creates a new example resource with the provided details",
     )
     async def create_example(
         request: ExampleRequest, db: AsyncSession = Depends(get_async_db)
     ):
         """Create a new example.

         Args:
             request: Example request data
             db: Database session dependency

         Returns:
             Newly created example data
         """
         result = await example_service.create_example(request, db)
         return result
     ```

3. **Register the Router**:

   - Add your router to `src/app/api/v1/__init__.py`
   - Example:

     ```python
     from src.app.api.v1.example import router as example_router

     # Add router to the list of routers
     v1_routers = [
         # Other routers...
         example_router,
     ]
     ```

### Adding Services

The service layer contains business logic. When adding a new service:

1. **Create the Service File**:

   - Add a new service module in `src/app/services/`
   - Implement a class with the core business logic
   - Create a singleton instance at the module level
   - Example:

     ```python
     # src/app/services/example_service.py
     from sqlalchemy.ext.asyncio import AsyncSession

     from src.app.crud.example import example_crud
     from src.app.schemas.example import ExampleRequest, ExampleResponse

     class ExampleService:
         """Service for handling example operations."""

         async def create_example(
             self, data: ExampleRequest, db: AsyncSession
         ) -> ExampleResponse:
             """Create a new example.

             Args:
                 data: Example request data
                 db: Database session

             Returns:
                 Created example data
             """
             # Implement business logic
             result = await example_crud.create(db, obj_in=data.dict())

             # Transform data for response
             return ExampleResponse(
                 message=f"Created example for {data.name}",
                 request_id=str(result.id)
             )

     # Create singleton instance
     example_service = ExampleService()
     ```

2. **Register the Service**:

   - Add your service to `src/app/services/__init__.py`
   - Example:

     ```python
     from src.app.services.example_service import example_service

     __all__ = [
         # Other services...
         "example_service",
     ]
     ```

### Extending Data Models

When adding new database models:

1. **Define the Model**:

   - Create a new model file in `src/app/models/`
   - Inherit from appropriate base classes
   - Include comprehensive field definitions and relationships
   - Example:

     ```python
     # src/app/models/example.py
     import uuid
     from sqlalchemy import Column, String, Text

     from src.app.core.db.base_class import Base
     from src.app.models.mixins import TimestampMixin, UUIDMixin

     class Example(Base, UUIDMixin, TimestampMixin):
         """Example model."""

         __tablename__ = "examples"

         name = Column(String(255), nullable=False, index=True)
         description = Column(Text, nullable=True)
     ```

2. **Register the Model**:

   - Add the model to `src/app/models/__init__.py`
   - Add the model to `src/app/core/db/base.py`
   - Example:

     ```python
     # src/app/models/__init__.py
     from src.app.models.example import Example

     __all__ = [
         # Other models...
         "Example",
     ]
     ```

3. **Create CRUD Operations**:

   - Add CRUD operations in `src/app/crud/`
   - Implement standard create, read, update, delete methods
   - Example:

     ```python
     # src/app/crud/example.py
     from typing import List, Optional

     from sqlalchemy import select
     from sqlalchemy.ext.asyncio import AsyncSession

     from src.app.crud.base import CRUDBase
     from src.app.models.example import Example
     from src.app.schemas.example import ExampleCreate, ExampleUpdate

     class CRUDExample(CRUDBase[Example, ExampleCreate, ExampleUpdate]):
         """CRUD operations for Example model."""

         async def get_by_name(
             self, db: AsyncSession, *, name: str
         ) -> Optional[Example]:
             """Get example by name.

             Args:
                 db: Database session
                 name: Example name to search for

             Returns:
                 Example if found, None otherwise
             """
             result = await db.execute(
                 select(self.model).where(self.model.name == name)
             )
             return result.scalar_one_or_none()

     # Create singleton instance
     example_crud = CRUDExample(Example)
     ```

4. **Create a Database Migration**:
   - Generate a migration using Alembic (see [Database Maintenance](#database-maintenance))

### Adding Middleware

When adding new middleware components:

1. **Create the Middleware**:

   - Add a new middleware module in `src/app/middleware/`
   - Implement middleware following the Starlette `BaseHTTPMiddleware` pattern
   - Example:

     ```python
     # src/app/middleware/example_middleware.py
     from typing import Callable

     from fastapi import FastAPI
     from starlette.middleware.base import BaseHTTPMiddleware
     from starlette.requests import Request
     from starlette.responses import Response

     class ExampleMiddleware(BaseHTTPMiddleware):
         """Example middleware implementation."""

         def __init__(self, app: FastAPI, example_setting: str = "default"):
             """Initialize middleware.

             Args:
                 app: FastAPI application
                 example_setting: Example configuration setting
             """
             super().__init__(app)
             self.example_setting = example_setting

         async def dispatch(self, request: Request, call_next: Callable) -> Response:
             """Process request through middleware.

             Args:
                 request: Incoming request
                 call_next: Next middleware/handler in chain

             Returns:
                 Response from next handler with modifications
             """
             # Pre-processing
             # ... implement logic ...

             # Call next middleware/handler
             response = await call_next(request)

             # Post-processing
             # ... implement logic ...

             return response

     def setup_example_middleware(app: FastAPI, example_setting: str = "default") -> None:
         """Set up example middleware.

         Args:
             app: FastAPI application
             example_setting: Example configuration setting
         """
         app.add_middleware(
             ExampleMiddleware,
             example_setting=example_setting
         )
     ```

2. **Register the Middleware**:

   - Update `src/app/core/setup.py` to include your middleware
   - Add the middleware in the appropriate order (consider dependencies)
   - Example:

     ```python
     from src.app.middleware.example_middleware import setup_example_middleware

     def create_app() -> FastAPI:
         # ... existing code ...

         # Set up example middleware (add in appropriate order)
         setup_example_middleware(
             app,
             example_setting=settings.EXAMPLE_SETTING,
         )

         # ... existing code ...
     ```

## Code Style & Standards

### Python Style Guidelines

NutriPeek follows a strict set of Python coding standards:

1. **PEP 8 Compliance**:

   - Follow PEP 8 style guide with customized line length (max 200 characters)
   - Utilize Black formatter for consistent code style
   - Use isort for standardized import ordering

2. **Type Annotations**:

   - Use type hints for all function parameters and return values
   - Follow MyPy strict typing guidelines
   - Example:
     ```python
     def process_data(input_data: Dict[str, Any], limit: Optional[int] = None) -> List[Result]:
         # Implementation
     ```

3. **Error Handling**:

   - Use specific exception classes for different error conditions
   - Handle exceptions at appropriate levels
   - Always include error context in exception messages
   - Example:
     ```python
     try:
         result = await database_operation()
     except DatabaseConnectionError as e:
         raise ServiceError(f"Failed to connect to database: {str(e)}")
     except ValidationError as e:
         raise InvalidInputError(f"Invalid input data: {str(e)}")
     ```

4. **Asynchronous Patterns**:
   - Use `async`/`await` consistently in async functions
   - Avoid mixing sync and async code
   - Ensure proper exception handling in async contexts

### Documentation Requirements

Comprehensive documentation is required for all code components:

1. **Module Docstrings**:

   - Every module should have a docstring describing its purpose
   - Include usage examples for utility modules
   - Example:

     ```python
     """User authentication module.

     This module provides functions and classes for user authentication,
     including password hashing, token generation, and validation.
     """
     ```

2. **Class Docstrings**:

   - Document class purpose, attributes, and behavior
   - Include examples for complex classes
   - Example:

     ```python
     class UserAuthenticator:
         """Handles user authentication operations.

         This class provides methods for authenticating users,
         generating tokens, and validating credentials.

         Attributes:
             token_expiry: Token expiration time in seconds
             hash_algorithm: Algorithm used for password hashing
         """
     ```

3. **Function Docstrings**:

   - Follow Google style docstrings
   - Document parameters, return values, and exceptions
   - Include type information consistent with annotations
   - Example:

     ```python
     async def authenticate_user(
         username: str, password: str, db: AsyncSession
     ) -> Optional[User]:
         """Authenticate a user by username and password.

         Args:
             username: User's username
             password: User's password in plain text
             db: Database session

         Returns:
             User object if authentication successful, None otherwise

         Raises:
             AuthenticationError: If authentication backend fails
         """
     ```

### Naming Conventions

Follow these naming conventions consistently:

1. **Files and Modules**:

   - Use snake_case for files and modules
   - Be descriptive and specific
   - Examples: `food_detection_service.py`, `user_authentication.py`

2. **Classes**:

   - Use PascalCase for class names
   - Use noun phrases that describe the entity
   - Examples: `FoodDetectionService`, `UserAuthentication`

3. **Functions and Methods**:

   - Use snake_case for function and method names
   - Use verb phrases that describe the action
   - Examples: `detect_food_items()`, `authenticate_user()`

4. **Variables**:

   - Use snake_case for variable names
   - Be specific and avoid abbreviations
   - Examples: `food_items`, `user_credentials`

5. **Constants**:
   - Use UPPER_SNAKE_CASE for constants
   - Example: `MAX_UPLOAD_SIZE`, `DEFAULT_TIMEOUT`

## Database Maintenance

### Creating Migrations

When making changes to database models, always use Alembic to create migrations:

1. **Generate a Migration**:

   ```bash
   # Ensure your Python path is set correctly
   export PYTHONPATH=$PYTHONPATH:$(pwd)

   # Generate the migration
   alembic revision --autogenerate -m "Description of changes"
   ```

2. **Review the Migration**:

   - Always review the generated migration file in `migrations/versions/`
   - Verify that all intended changes are captured
   - Make manual adjustments if necessary

3. **Apply the Migration**:

   ```bash
   # Apply to development database
   alembic upgrade head
   ```

4. **Include in Version Control**:
   - Commit the migration file to the repository
   - Include a comment explaining the database changes

### Managing Database Changes

Follow these guidelines for database changes:

1. **Data Preservation**:

   - Always consider data preservation when modifying tables
   - Use `nullable=True` for new columns in existing tables
   - Implement data migration steps when necessary

2. **Schema Evolution**:

   - Make additive changes when possible (new tables, columns)
   - Avoid removing or renaming columns - add new ones and deprecate old ones
   - Use database constraints appropriately (foreign keys, unique constraints)

3. **Testing Migrations**:
   - Test migrations on a copy of production data before deployment
   - Verify both upgrade and downgrade paths
   - Measure migration time for large tables

## Testing Requirements

### Test Coverage

Maintain comprehensive test coverage for all code:

1. **Coverage Requirements**:

   - Minimum 80% code coverage overall
   - 100% coverage for critical components (authentication, data processing)
   - Run coverage reports regularly: `pytest --cov=src`

2. **Test Organization**:
   - Follow project structure in test organization
   - Place tests in corresponding directories under `tests/`
   - Example: `src/app/services/food_service.py` → `tests/services/test_food_service.py`

### Test Strategy

Apply these testing strategies:

1. **Unit Tests**:

   - Test individual functions and classes in isolation
   - Mock external dependencies
   - Focus on edge cases and error conditions
   - Example:

     ```python
     @pytest.mark.asyncio
     async def test_food_detection_service_invalid_image():
         # Arrange
         image_file = create_mock_invalid_image()

         # Act & Assert
         with pytest.raises(InvalidImageError):
             await food_detection_service.process_image(image_file)
     ```

2. **Integration Tests**:

   - Test interaction between components
   - Use test database for data persistence tests
   - Example:

     ```python
     @pytest.mark.asyncio
     async def test_food_detection_integration(test_db, test_image):
         # Arrange - test fixtures provide database and image

         # Act
         result = await food_detection_service.process_image(test_image)

         # Assert
         assert len(result.detected_items) > 0
         assert result.processing_time_ms > 0
     ```

3. **API Tests**:

   - Test API endpoints through HTTP requests
   - Verify status codes, headers, and response content
   - Use FastAPI TestClient
   - Example:

     ```python
     def test_detect_food_endpoint(client, test_image_file):
         # Arrange
         files = {"image": test_image_file}

         # Act
         response = client.post("/api/food-detection/detect", files=files)

         # Assert
         assert response.status_code == 200
         assert "detected_items" in response.json()
     ```

## Refactoring Guidelines

### When to Refactor

Consider refactoring in these situations:

1. **Code Smells**:

   - Duplicate code across multiple files
   - Excessively long functions or methods (>50 lines)
   - Highly nested conditional logic (>3 levels)
   - Functions with too many parameters (>5)

2. **Performance Issues**:

   - Identified bottlenecks through profiling
   - Excessive database queries
   - High memory usage

3. **Maintainability Issues**:
   - Difficult-to-understand code with inadequate documentation
   - Tightly coupled components
   - Inconsistent patterns or styles

### Refactoring Approach

Follow this approach when refactoring:

1. **Preparation**:

   - Ensure comprehensive tests cover the code to be refactored
   - Establish a baseline for functionality and performance
   - Create a dedicated branch for refactoring

2. **Implementation**:

   - Make small, incremental changes
   - Run tests frequently
   - Follow the "boy scout rule": leave code cleaner than you found it
   - Apply design patterns where appropriate

3. **Review**:

   - Verify test coverage after refactoring
   - Measure performance impact
   - Have another developer review the changes

4. **Common Refactoring Techniques**:
   - Extract method/class for complex logic
   - Replace conditional logic with polymorphism
   - Introduce design patterns for recurring problems
   - Optimize database queries

## Version Control Workflow

### Branching Strategy

NutriPeek follows a feature branch workflow:

1. **Branch Types**:

   - `main` - Production-ready code
   - `develop` - Integration branch for features
   - `feature/feature-name` - New features
   - `bugfix/issue-description` - Bug fixes
   - `hotfix/issue-description` - Critical production fixes

2. **Branch Lifecycle**:
   - Create a new branch from `develop` for features/fixes
   - Develop and test on the feature branch
   - Create a pull request to merge back to `develop`
   - Periodically merge `develop` into `main` for releases

### Commit Standards

Follow these commit message guidelines:

1. **Commit Structure**:

   - Use present tense ("Add feature" not "Added feature")
   - First line is a summary (max 50 characters)
   - Followed by a blank line and detailed description
   - Reference issue numbers when applicable

2. **Examples**:

   ```
   Add food detection endpoint for YOLO model

   - Implement image upload and validation
   - Add YOLO model integration
   - Include error handling for invalid images

   Fixes #123
   ```

## Performance Optimization

Follow these guidelines for performance optimization:

1. **Database Optimization**:

   - Use database indexes for frequently queried fields
   - Optimize complex queries with EXPLAIN
   - Use batch operations for multiple records
   - Implement caching for expensive queries

2. **Async Processing**:

   - Use async I/O for network and database operations
   - Implement background tasks for long-running processes
   - Use connection pooling for database connections

3. **Measurement and Monitoring**:
   - Profile code to identify bottlenecks
   - Monitor endpoint response times
   - Set performance budgets for critical paths
   - Use metrics to guide optimization efforts
