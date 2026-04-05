#!/bin/bash
# MindIQ Frontend - One-click deployment script
# Usage: bash deploy_frontend.sh [dev|stage|prod]
#   default: dev

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_ENV="${1:-dev}"

# Validate environment
if [[ "$APP_ENV" != "dev" && "$APP_ENV" != "stage" && "$APP_ENV" != "prod" ]]; then
    echo "[ERROR] Invalid environment: $APP_ENV"
    echo "Usage: bash deploy_frontend.sh [dev|stage|prod]"
    exit 1
fi

ENV_FILE="$ROOT_DIR/env/${APP_ENV}.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "[ERROR] Environment file not found: $ENV_FILE"
    exit 1
fi

echo "=================================="
echo "  MindIQ Frontend [$APP_ENV]"
echo "=================================="

# Check node/npm
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js not found. Please install Node.js (>=20) first."
    exit 1
fi
if ! command -v npm &> /dev/null; then
    echo "[ERROR] npm not found. Please install npm first."
    exit 1
fi

echo "[INFO] Node version: $(node -v)"
echo "[INFO] npm version: $(npm -v)"

cd "$SCRIPT_DIR"

# --- Generate .env.local from central config ---
echo "[INFO] Loading env from $ENV_FILE"
grep '^NEXT_PUBLIC_' "$ENV_FILE" > "$SCRIPT_DIR/.env.local"
echo "[INFO] Generated frontend/.env.local for [$APP_ENV]"

# --- Install dependencies ---
echo "[INFO] Installing npm dependencies..."
npm install

# --- Start server ---
echo ""
echo "=================================="
echo "  Starting Frontend [$APP_ENV] on port 3000"
echo "=================================="
echo ""

if [ "$APP_ENV" = "dev" ]; then
    echo "[INFO] Dev mode: hot reload ENABLED"
    npm run dev
else
    echo "[INFO] $APP_ENV mode: building for production (no hot reload)..."
    npm run build
    echo "[INFO] Starting production server..."
    npm run start
fi
