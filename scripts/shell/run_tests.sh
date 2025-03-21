#!/bin/bash

# Exit on error
set -e

# Activate virtual environment
source venv/bin/activate

# Run tests
pytest -v