#!/bin/bash

# Exit on error
set -e

# Check if a message is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <migration_message>"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Generate migration
echo "Generating migration..."
alembic revision --autogenerate -m "$1"

echo "Migration generated successfully!"