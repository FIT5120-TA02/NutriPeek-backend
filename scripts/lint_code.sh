#!/bin/bash
echo "Running black..."
black src/

echo "Running flake8..."
flake8 src/

echo "Running mypy..."
mypy src/
