#!/usr/bin/env bash
# One-command local dev: sets up the backend venv (first run), installs the
# frontend deps, and starts both servers. Ctrl-C stops everything.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Find a Python interpreter that meets the project's >=3.11 requirement.
# macOS ships an old system python3 (often 3.9), so we probe versioned names
# first and fall back to python3/python only if they are new enough.
find_python() {
  for candidate in python3.13 python3.12 python3.11 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
        echo "$candidate"
        return 0
      fi
    fi
  done
  return 1
}

# --- Backend ---
# Recreate the venv if it is missing or was built with an unsupported Python.
NEED_VENV=1
if [ -d "backend/.venv" ]; then
  if backend/.venv/bin/python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    NEED_VENV=0
  else
    echo "==> Existing backend/.venv uses an unsupported Python; recreating it"
    rm -rf backend/.venv
  fi
fi

if [ "$NEED_VENV" = "1" ]; then
  if ! PYTHON="$(find_python)"; then
    echo ""
    echo "ERROR: RedCache needs Python 3.11 or newer, but none was found."
    echo "Your default 'python3' is likely macOS's old built-in version."
    echo ""
    echo "Install a newer Python, then run ./scripts/dev.sh again:"
    echo "  - Download from https://www.python.org/downloads/  (any 3.11+), or"
    echo "  - macOS with Homebrew:  brew install python@3.12"
    echo ""
    exit 1
  fi
  echo "==> Creating backend virtualenv with $("$PYTHON" --version)"
  "$PYTHON" -m venv backend/.venv
  ./backend/.venv/bin/python -m pip install --upgrade pip
  ./backend/.venv/bin/python -m pip install -e "backend/.[dev]"
  ./backend/.venv/bin/python -m playwright install chromium
fi

# --- Frontend ---
if [ ! -d "frontend/node_modules" ]; then
  echo "==> Installing frontend dependencies"
  (cd frontend && npm install)
fi

# --- Pre-flight: fail fast with a clear message if a port is taken ---
check_port() {
  local port=$1 name=$2
  if lsof -i ":$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo ""
    echo "ERROR: Port $port is already in use, so the $name cannot start."
    echo "RedCache (or another app) may already be running."
    echo "  - If you started it in another Terminal window, press Ctrl+C there first."
    echo "  - To see what's using it:  lsof -i :$port -sTCP:LISTEN"
    echo ""
    exit 1
  fi
}
check_port 8000 "backend"
check_port 5173 "frontend"

echo "==> Starting backend on http://127.0.0.1:8000"
(cd backend && ./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000) &
BACKEND_PID=$!

echo "==> Starting frontend on http://localhost:5173"
(cd frontend && npm run dev) &
FRONTEND_PID=$!

trap 'echo "==> Stopping"; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true' INT TERM
wait
