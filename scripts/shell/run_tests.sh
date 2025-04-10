#!/bin/bash

# Exit on error
set -e

# Activate virtual environment
source venv/bin/activate

# Run tests with environment variables from test.env
# export $(grep -v "^#" .env | xargs) && python -m pytest -v
