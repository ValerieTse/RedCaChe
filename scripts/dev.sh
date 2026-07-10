#!/usr/bin/env bash
# One-command local dev: sets up the backend venv (first run), installs the
# frontend deps, and starts both servers. Ctrl-C stops everything.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# --- Backend ---
if [ ! -d "backend/.venv" ]; then
  echo "==> Creating backend virtualenv"
  python3 -m venv backend/.venv
  ./backend/.venv/bin/pip install --upgrade pip
  ./backend/.venv/bin/pip install -e "backend/.[dev]"
  ./backend/.venv/bin/python -m playwright install chromium
fi

# --- Frontend ---
if [ ! -d "frontend/node_modules" ]; then
  echo "==> Installing frontend dependencies"
  (cd frontend && npm install)
fi

echo "==> Starting backend on http://127.0.0.1:8000"
(cd backend && ./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000) &
BACKEND_PID=$!

echo "==> Starting frontend on http://localhost:5173"
(cd frontend && npm run dev) &
FRONTEND_PID=$!

trap 'echo "==> Stopping"; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true' INT TERM
wait
