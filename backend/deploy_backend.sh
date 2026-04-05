#!/bin/bash
# MindIQ Backend - One-click deployment script
# Usage: bash deploy_backend.sh [dev|stage|prod]
#   default: dev

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_NAME="my_good_ipip"
APP_ENV="${1:-dev}"

# Validate environment
if [[ "$APP_ENV" != "dev" && "$APP_ENV" != "stage" && "$APP_ENV" != "prod" ]]; then
    echo "[ERROR] Invalid environment: $APP_ENV"
    echo "Usage: bash deploy_backend.sh [dev|stage|prod]"
    exit 1
fi

ENV_FILE="$ROOT_DIR/env/${APP_ENV}.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "[ERROR] Environment file not found: $ENV_FILE"
    exit 1
fi

echo "=================================="
echo "  MindIQ Backend [$APP_ENV]"
echo "=================================="

# --- Conda setup ---
if ! command -v conda &> /dev/null; then
    echo "[ERROR] conda not found. Please install Anaconda/Miniconda first."
    exit 1
fi

eval "$(conda shell.bash hook 2>/dev/null || conda shell.zsh hook 2>/dev/null)"

if conda info --envs | grep -q "^${ENV_NAME} "; then
    echo "[INFO] Conda env '${ENV_NAME}' already exists."
else
    echo "[INFO] Creating conda env '${ENV_NAME}' with Python 3.11..."
    conda create -n "$ENV_NAME" python=3.11 -y
fi

echo "[INFO] Activating conda env '${ENV_NAME}'..."
conda activate "$ENV_NAME"

# --- Install dependencies ---
cd "$SCRIPT_DIR"
echo "[INFO] Installing Python dependencies..."
pip install -r requirements.txt

# --- Generate .env from central config ---
echo "[INFO] Loading env from $ENV_FILE"
grep -v '^#' "$ENV_FILE" | grep -v '^$' | grep -v '^NEXT_PUBLIC_' > "$SCRIPT_DIR/.env"
echo "[INFO] Generated backend/.env for [$APP_ENV]"

# --- WeasyPrint system library path (macOS Homebrew) ---
if [ -d "/opt/homebrew/lib" ]; then
    export DYLD_LIBRARY_PATH="/opt/homebrew/lib:${DYLD_LIBRARY_PATH:-}"
    echo "[INFO] Set DYLD_LIBRARY_PATH for WeasyPrint (Homebrew)"
fi

# --- Start server ---
echo ""
echo "=================================="
echo "  Starting Backend [$APP_ENV] on port 3001"
echo "=================================="
echo ""

if [ "$APP_ENV" = "dev" ]; then
    echo "[INFO] Dev mode: hot reload ENABLED"
    uvicorn main:app --host 0.0.0.0 --port 3001 --reload
else
    echo "[INFO] $APP_ENV mode: hot reload DISABLED (restart to apply changes)"
    uvicorn main:app --host 0.0.0.0 --port 3001 --workers 2
fi
