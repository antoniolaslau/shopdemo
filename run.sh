#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "==> Dropping old database (if any)..."
rm -f shopdemo.db

echo "==> Seeding database..."
python3 seed.py

echo ""
echo "==> Starting ShopDemo at http://localhost:8001"
echo "    Press Ctrl+C to stop."
echo ""
uvicorn main:app --reload --port 8001
