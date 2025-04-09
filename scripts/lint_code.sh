#!/bin/bash
echo "Running black..."
black src/ scripts/

echo "Running flake8..."
flake8 src/ scripts/

echo "Running mypy..."
mypy src/ scripts/
