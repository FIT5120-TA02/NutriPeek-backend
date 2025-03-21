# FastAPI Backend

A well-structured FastAPI backend for the onboarding project.

## Features

- FastAPI framework with async support
- PostgreSQL database with SQLAlchemy ORM
- Alembic for database migrations
- Pydantic for data validation
- Dependency injection
- Environment-based configuration
- Structured logging
- Exception handling
- Health check endpoint
- CORS middleware
- VS Code configuration

## Project Structure

```
src/
├── app/                    # Main application package
│   ├── api/                # API endpoints and routers
│   │   ├── v1/             # API version 1 endpoints
│   │   └── dependencies.py # Shared API dependencies
│   ├── core/               # Core application components
│   │   ├── config.py       # Application configuration
│   │   ├── db/             # Database connection and session management
│   │   ├── exceptions/     # Custom exception definitions
│   │   ├── logger.py       # Logging configuration
│   │   ├── setup.py        # Application setup and initialization
│   │   └── utils/          # Utility functions and helpers
│   ├── crud/               # CRUD operations for database models
│   ├── main.py             # Application entry point
│   ├── middleware/         # Custom middleware components
│   ├── models/             # SQLAlchemy ORM models
│   └── schemas/            # Pydantic schemas for request/response validation
├── migrations/             # Alembic database migrations
└── scripts/                # Utility scripts for development and deployment
```

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL

### Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd main-project-backend
```

2. Set up the virtual environment:

```bash
./scripts/setup_venv.sh
source venv/bin/activate
```

3. Create a PostgreSQL database:

```bash
createdb main_project_db
```

4. Create a new env file under `/env` folder and update the `.env.example` file with your database credentials.

5. Run database migrations:

```bash
alembic upgrade head
```

6. Start the development server:

```bash
uvicorn src.app.main:app --reload
```

The API will be available at http://localhost:8000.

API documentation is available at:

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Development

### Creating a New Endpoint

1. Create a new router file in `src/app/api/v1/`
2. Define your endpoints using FastAPI decorators
3. Include the router in `src/app/core/setup.py`

### Creating a New Model

1. Create a new model file in `src/app/models/`
2. Define your SQLAlchemy model
3. Create a new schema file in `src/app/schemas/`
4. Create a new CRUD file in `src/app/crud/`
5. Generate a migration with Alembic:

```bash
alembic revision --autogenerate -m "Add new model"
```

### Running Tests

```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
