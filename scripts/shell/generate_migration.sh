#!/bin/bash

# Exit on error
set -e

# Default to local environment if not specified
ENV=${1:-local}

# Validate environment parameter
if [ "$ENV" != "local" ] && [ "$ENV" != "dev" ]; then
    echo "Error: Environment must be either 'local' or 'dev'"
    echo "Usage: $0 [local|dev] <migration_message>"
    exit 1
fi

# Check if a message is provided
if [ -z "$2" ]; then
    echo "Error: Migration message is required"
    echo "Usage: $0 [local|dev] <migration_message>"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Set environment variables based on selected environment
export ENVIRONMENT=$ENV
export ENV_FILE=./env/$ENV.env

# Load environment variables from the env file
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment from $ENV_FILE"
    export $(grep -v '^#' $ENV_FILE | xargs)
else
    echo "Error: Environment file $ENV_FILE not found"
    exit 1
fi

# Add the project root to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Generate migration
echo "Generating migration..."
alembic revision --autogenerate -m "$2"

echo "Migration generated successfully!"