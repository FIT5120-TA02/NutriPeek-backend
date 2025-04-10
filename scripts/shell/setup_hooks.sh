#!/bin/bash

# Exit on error
set -e

echo "Setting up Git hooks..."

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Install pre-push hooks using pre-commit for pre-push
echo "Installing pre-push hooks..."
pre-commit install --hook-type pre-push --config .pre-push-config.yaml

echo "Git hooks have been set up successfully!"
echo "These hooks will run:"
echo "- Before commit: linting and tests"
echo "- Before push: tests with coverage report"
