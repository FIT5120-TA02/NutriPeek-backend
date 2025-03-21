#!/bin/bash

# Exit on error
set -e

# Activate virtual environment
source venv/bin/activate

# Format code
echo "Formatting code..."
isort src tests
black src tests

echo "Code formatting complete!"