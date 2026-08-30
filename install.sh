#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if ! command -v uv >/dev/null 2>&1; then
  echo "[错误] 未找到 uv，请先安装 uv 并重新运行。" >&2
  exit 1
fi

if ! command -v pnpm >/dev/null 2>&1; then
  echo "[错误] 未找到 pnpm，请先安装 Node.js 和 pnpm 并重新运行。" >&2
  exit 1
fi

echo "[安装] 同步 Python 依赖..."
cd "$ROOT/apps/api"
uv sync

echo "[安装] 初始化数据库迁移..."
uv run alembic upgrade head

echo "[安装] 同步前端依赖..."
cd "$ROOT"
pnpm install

echo "[完成] 开发环境安装完成。"
