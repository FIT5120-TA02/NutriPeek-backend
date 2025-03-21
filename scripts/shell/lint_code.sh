#!/bin/bash

# Exit on error
set -e

# Activate virtual environment
source venv/bin/activate

# Lint code
echo "Linting code..."
flake8 src tests
mypy src

echo "Code linting complete!"