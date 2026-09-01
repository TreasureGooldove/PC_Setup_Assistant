#!/usr/bin/env sh
set -eu

command -v node >/dev/null 2>&1 || {
  echo "[错误] 未找到 Node.js 18+，请先安装 Node.js。" >&2
  exit 1
}
command -v npx >/dev/null 2>&1 || {
  echo "[错误] 未找到 npx，请确认 Node.js 已加入 PATH。" >&2
  exit 1
}

echo "[预检] 启动固定版本 open-websearch MCP..."
MODE=stdio ALLOWED_SEARCH_ENGINES=baidu,bing npx --yes open-websearch@2.1.9 --help
echo "[完成] MCP 已可由 API 按需通过 npx 启动。"
echo "[提示] 仍需在 apps/api/.env 中设置 MODELSCOPE_MCP_ENABLED=true。"
