#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
API_DIR="$ROOT/apps/api"

if [ ! -d "$API_DIR/.venv" ] || [ ! -d "$ROOT/node_modules" ]; then
  "$ROOT/install.sh"
fi

cleanup() {
  status=$?
  trap - INT TERM EXIT
  for pid in ${API_PID:-} ${WORKER_PID:-} ${WEB_PID:-}; do
    if [ -n "$pid" ]; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  wait ${API_PID:-} ${WORKER_PID:-} ${WEB_PID:-} 2>/dev/null || true
  exit "$status"
}

trap cleanup INT TERM EXIT

echo "[启动] API、Worker 和前端开发服务器..."
(
  cd "$API_DIR"
  uv run alembic upgrade head
  exec uv run uvicorn app.main:app --reload --port 8000
) &
API_PID=$!

(
  cd "$API_DIR"
  exec uv run python -m app.worker
) &
WORKER_PID=$!

(
  cd "$ROOT"
  exec pnpm --dir apps/web dev
) &
WEB_PID=$!

echo "[完成] 前端：http://localhost:5173/"
echo "[完成] API：http://localhost:8000/health"
echo "按 Ctrl+C 可同时停止三个服务。"

if command -v xdg-open >/dev/null 2>&1; then
  sleep 3
  xdg-open "http://localhost:5173/" >/dev/null 2>&1 &
fi

wait "$WEB_PID"
