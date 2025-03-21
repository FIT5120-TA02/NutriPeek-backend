#!/bin/bash

# Exit on error
set -e

# Activate virtual environment
source venv/bin/activate

# Set environment variables to use local configuration
export ENVIRONMENT=local
export ENV_FILE=./env/.env.local

# Add the project root to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Check if the database exists
echo "Checking if database exists..."
if ! psql -lqt | cut -d \| -f 1 | grep -qw onboarding_db_local; then
    echo "Database onboarding_db_local does not exist. Creating..."
    createdb onboarding_db_local
    echo "Database created successfully."
else
    echo "Database onboarding_db_local already exists."
fi

# Run migrations
echo "Running Alembic migrations..."
alembic upgrade head

echo "Database initialization complete!"
echo "Your local database is now ready to use."