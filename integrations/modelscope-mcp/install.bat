@echo off
setlocal

where node >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 Node.js 18+，请先安装 Node.js。
  exit /b 1
)

where npx >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 npx，请确认 Node.js 已加入 PATH。
  exit /b 1
)

echo [预检] 启动固定版本 open-websearch MCP...
set MODE=stdio
set ALLOWED_SEARCH_ENGINES=baidu,bing
npx.cmd --yes open-websearch@2.1.9 --help
if errorlevel 1 (
  echo [错误] MCP 预检失败，请检查 npm registry 或网络出口。
  exit /b 1
)

echo [完成] MCP 已可由 API 按需通过 npx 启动。
echo [提示] 仍需在 apps/api/.env 中设置 MODELSCOPE_MCP_ENABLED=true。
exit /b 0
