#!/bin/bash
# MindIQ - One-click start all services
# Usage: bash start_all.sh [dev|stage|prod]
#   default: dev

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_NAME="my_good_ipip"
APP_ENV="${1:-dev}"

# Validate environment
if [[ "$APP_ENV" != "dev" && "$APP_ENV" != "stage" && "$APP_ENV" != "prod" ]]; then
    echo "[ERROR] Invalid environment: $APP_ENV"
    echo "Usage: bash start_all.sh [dev|stage|prod]"
    exit 1
fi

ENV_FILE="$ROOT_DIR/env/${APP_ENV}.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "[ERROR] Environment file not found: $ENV_FILE"
    exit 1
fi

echo "======================================"
echo "  MindIQ - Starting All Services"
echo "  Environment: $APP_ENV"
echo "======================================"
echo ""

# ========== Backend ==========
echo "[1/2] Setting up Backend..."

# Initialize conda
eval "$(conda shell.bash hook 2>/dev/null || conda shell.zsh hook 2>/dev/null)"

# Create conda env if not exists
if ! conda info --envs | grep -q "^${ENV_NAME} "; then
    echo "[INFO] Creating conda env '${ENV_NAME}' with Python 3.11..."
    conda create -n "$ENV_NAME" python=3.11 -y
fi

conda activate "$ENV_NAME"

# WeasyPrint system library path (macOS Homebrew)
if [ -d "/opt/homebrew/lib" ]; then
    export DYLD_LIBRARY_PATH="/opt/homebrew/lib:${DYLD_LIBRARY_PATH:-}"
fi

cd "$ROOT_DIR/backend"
pip install -q -r requirements.txt

# Generate backend .env from central config
grep -v '^#' "$ENV_FILE" | grep -v '^$' | grep -v '^NEXT_PUBLIC_' > "$ROOT_DIR/backend/.env"
echo "[INFO] Generated backend/.env for [$APP_ENV]"

# Start backend in background
if [ "$APP_ENV" = "dev" ]; then
    echo "[INFO] Backend starting with hot reload..."
    uvicorn main:app --host 0.0.0.0 --port 3001 --reload &
else
    echo "[INFO] Backend starting without hot reload (restart to apply changes)..."
    uvicorn main:app --host 0.0.0.0 --port 3001 --workers 2 &
fi
BACKEND_PID=$!

# ========== Frontend ==========
echo "[2/2] Setting up Frontend..."

cd "$ROOT_DIR/frontend"

# Generate frontend .env.local from central config
grep '^NEXT_PUBLIC_' "$ENV_FILE" > "$ROOT_DIR/frontend/.env.local"
echo "[INFO] Generated frontend/.env.local for [$APP_ENV]"

npm install --silent

if [ "$APP_ENV" = "dev" ]; then
    echo "[INFO] Frontend starting with hot reload..."
    npm run dev &
else
    echo "[INFO] Frontend building for production..."
    npm run build
    echo "[INFO] Frontend starting production server..."
    npm run start &
fi
FRONTEND_PID=$!

# ========== Done ==========
echo ""
echo "======================================"
echo "  All Services Running [$APP_ENV]"
echo "======================================"
echo ""
echo "  Backend:  http://localhost:3001  (PID: $BACKEND_PID)"
echo "  Frontend: http://localhost:3000  (PID: $FRONTEND_PID)"
echo "  API Docs: http://localhost:3001/docs"
echo ""
if [ "$APP_ENV" = "dev" ]; then
    echo "  Hot reload: ENABLED (code changes auto-apply)"
else
    echo "  Hot reload: DISABLED (restart to apply changes)"
fi
echo ""
echo "  Press Ctrl+C to stop all services"
echo ""

# Trap Ctrl+C to kill both processes
cleanup() {
    echo ""
    echo "[INFO] Stopping all services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    wait $FRONTEND_PID 2>/dev/null
    echo "[INFO] All services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for either process to exit
wait
