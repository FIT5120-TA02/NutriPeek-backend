# NutriPeek FastAPI Backend

A FastAPI backend for the NutriPeek project with ML-powered food detection capabilities.

## Features

- FastAPI framework with async support
- PostgreSQL database with SQLAlchemy ORM
- Alembic for database migrations
- Pydantic for data validation
- Dependency injection
- Environment-based configuration
- Structured logging
- YOLO-based food detection using Ultralytics
- Exception handling
- Health check endpoint
- CORS middleware
- VS Code debugging and launch configurations
- Comprehensive test suite

## Technology Stack

- **Python**: >= 3.8, <= 3.12 (compatible with Ultralytics requirements)
- **Web Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Testing**: pytest, pytest-asyncio
- **ML Framework**: Ultralytics YOLO, PyTorch
- **Image Processing**: OpenCV
- **Code Quality**: Black, Flake8, MyPy, isort

## Project Structure

```
/
├── src/                    # Source code
│   ├── app/                # Main application package
│   │   ├── api/            # API endpoints and routers
│   │   │   ├── v1/         # API version 1 endpoints
│   │   │   └── dependencies.py
│   │   ├── core/           # Core application components
│   │   │   ├── config.py   # Application configuration
│   │   │   ├── db/         # Database connection and session management
│   │   │   ├── exceptions/ # Custom exception definitions
│   │   │   ├── logger.py   # Logging configuration
│   │   │   ├── ml/         # Machine learning components
│   │   │   │   └── models/ # ML model files (.pt)
│   │   │   ├── setup.py    # Application setup and initialization
│   │   │   └── utils/      # Utility functions and helpers
│   │   ├── crud/           # CRUD operations for database models
│   │   ├── middleware/     # Custom middleware components
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic schemas for request/response validation
│   │   ├── services/       # Business logic and service layer
│   │   └── main.py         # Application entry point
├── tests/                  # Test suite
│   ├── api/                # API endpoint tests
│   ├── core/               # Core component tests
│   ├── services/           # Service layer tests
│   └── conftest.py         # Test fixtures and configuration
├── migrations/             # Alembic database migrations
├── scripts/                # Utility scripts for development and deployment
│   └── python/             # Python utility scripts
├── .vscode/                # VS Code configurations
│   └── launch.json         # Debug configurations
├── env/                    # Environment configurations
├── requirements.txt        # Project dependencies
├── pyproject.toml          # Python project configuration
├── alembic.ini             # Alembic configuration
└── .env                    # Environment variables (development only)
```

## Getting Started

### Prerequisites

- Python 3.8-3.12
- PostgreSQL
- Virtual environment management tool (venv, virtualenv, etc.)

### Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd nutripeek-backend
```

2. Set up the virtual environment:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a PostgreSQL database:

```bash
createdb nutripeek_db
```

5. Create an environment file:

```bash
# Copy the example env file
cp env/example.env env/local.env

# Edit the file with your database credentials and other settings
```

6. Run database migrations:

```bash
alembic upgrade head
```

7. Start the development server:

```bash
# Using uvicorn directly
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

# Using VS Code launch configuration
# Press F5 with "FastAPI: Run Server (Local)" configuration selected
```

The API will be available at http://localhost:8000.

API documentation is available at:

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Development

### Adding New Dependencies

When adding new packages to the project:

```bash
# Install the package
pip install package-name

# Add it to requirements.txt
pip freeze > requirements.txt

# Or manually add with version:
# echo "package-name==1.0.0" >> requirements.txt
```

### Creating a New Endpoint

1. Create a new router file in `src/app/api/v1/`
2. Define your endpoints using FastAPI decorators
3. Include the router in `src/app/core/setup.py`
4. Add corresponding tests in `tests/api/v1/`

Example:

```python
# src/app/api/v1/example.py
from fastapi import APIRouter, Depends

from src.app.schemas.example import ExampleResponse

router = APIRouter(prefix="/example", tags=["example"])

@router.get("/", response_model=ExampleResponse)
async def get_example():
    return {"message": "Example endpoint"}
```

### Creating a New Service

1. Create a new service file in `src/app/services/`
2. Define your service class with business logic
3. Add corresponding tests in `tests/services/`

### Creating a New Model

1. Create a new model file in `src/app/models/`
2. Define your SQLAlchemy model
3. Create a new schema file in `src/app/schemas/`
4. Create a new CRUD file in `src/app/crud/`
5. Add corresponding tests
6. Generate a migration with Alembic:

```bash
alembic revision --autogenerate -m "Add new model"
```

### Working with the YOLO Model

The project includes YOLO-based food detection capabilities:

1. Model files should be placed in `src/app/core/ml/models/`
2. The default model used is `yolo11n.pt` for food detection
3. Use the `FoodDetectionService` to process images

To test the YOLO model directly:

```bash
# Using the command line
python scripts/python/test_yolo_model.py --input path/to/image.jpg

# Using VS Code launch configuration
# Select "Script: Test YOLO Model" and press F5
```

## Testing

The project follows a test-driven development approach. When creating new features, always add corresponding tests.

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=src

# Run specific test file
pytest tests/api/v1/test_example.py

# Run tests for a specific module
pytest tests/services/

# Using VS Code launch configuration
# Select "Tests: Run All Tests" and press F5
```

### Test Structure

- Unit tests should be placed in the corresponding module directory
- Use fixtures from `conftest.py` to set up test dependencies
- Mock external services when appropriate
- Test both success and error paths
- When testing a feature, make sure to test at all levels (API, service, data)

## Deployment

Instructions for deployment would be placed here.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
