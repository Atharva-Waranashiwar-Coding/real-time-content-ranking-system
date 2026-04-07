#!/bin/bash
set -e

echo "🎨 Formatting code..."

# Black formatting
echo "  - Formatting Python with black..."
black services/ packages/ --line-length=100

# Ruff sorting imports
echo "  - Sorting imports with ruff..."
ruff check services/ packages/ --select I --fix

# Prettier formatting
echo "  - Formatting TypeScript/JavaScript..."
if command -v prettier &> /dev/null; then
  prettier --write "apps/web/**/*.{ts,tsx,json}"
fi

echo "✅ Formatting complete!"
