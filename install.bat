@echo off
setlocal

set "ROOT=%~dp0"
set "QUIET=0"
if /I "%~1"=="--quiet" set "QUIET=1"

where uv >nul 2>nul
if errorlevel 1 goto :missing_uv

where pnpm >nul 2>nul
if errorlevel 1 goto :missing_pnpm

echo [安装] 同步 Python 依赖...
pushd "%ROOT%apps\api"
uv sync
if errorlevel 1 goto :install_failed

echo [安装] 初始化数据库迁移...
uv run alembic upgrade head
if errorlevel 1 goto :install_failed
popd

echo [安装] 同步前端依赖...
pushd "%ROOT%"
pnpm install
if errorlevel 1 goto :install_failed
popd

echo [完成] 开发环境安装完成。
if "%QUIET%"=="0" pause
exit /b 0

:missing_uv
echo [错误] 未找到 uv，请先安装 uv 并重新运行。
goto :failed

:missing_pnpm
echo [错误] 未找到 pnpm，请先安装 Node.js 和 pnpm 并重新运行。
goto :failed

:install_failed
popd
echo [错误] 安装或数据库迁移失败。

:failed
if "%QUIET%"=="0" pause
exit /b 1
