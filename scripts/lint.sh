#!/bin/bash
set -e

echo "🔍 Running linting checks..."

# Ruff linting
echo "  - Checking with ruff..."
ruff check services/ packages/ apps/web/lib --fix || true

# Black format check
echo "  - Verifying black formatting..."
black --check services/ packages/ --line-length=100 || true

# mypy type checking for Python (optional, slower)
echo "  - Running type checks..."
mypy services/ packages/ --ignore-missing-imports || true

# Prettier for frontend
echo "  - Checking TypeScript formatting..."
if command -v prettier &> /dev/null; then
  prettier --check apps/web/{pages,lib,styles} || true
fi

echo "✅ Linting complete!"
