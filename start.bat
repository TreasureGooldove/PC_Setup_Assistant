@echo off
setlocal

set "ROOT=%~dp0"

if not exist "%ROOT%apps\api\.venv" goto :install
if not exist "%ROOT%node_modules" goto :install
goto :start_services

:install
call "%ROOT%install.bat" --quiet
if errorlevel 1 (
  pause
  exit /b 1
)

:start_services
echo [启动] API、Worker 和前端开发服务器...
start "智能装机搭子 API" /D "%ROOT%apps\api" cmd /k "uv run alembic upgrade head && uv run uvicorn app.main:app --reload --port 8000"
start "智能装机搭子 Worker" /D "%ROOT%apps\api" cmd /k "uv run python -m app.worker"
start "智能装机搭子 Web" /D "%ROOT%" cmd /k "pnpm --dir apps/web dev"

timeout /t 3 /nobreak >nul
start "" "http://localhost:5173/"
echo [完成] 已打开 http://localhost:5173/
echo 关闭对应的三个终端窗口即可停止本地服务。
exit /b 0
