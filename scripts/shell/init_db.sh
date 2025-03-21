#!/bin/bash

# Exit on error
set -e

# Activate virtual environment
source venv/bin/activate

# Create database
echo "Creating database..."
createdb on_boarding_local || echo "Database already exists"

# Run migrations
echo "Running migrations..."
alembic upgrade head

echo "Database initialization complete!"