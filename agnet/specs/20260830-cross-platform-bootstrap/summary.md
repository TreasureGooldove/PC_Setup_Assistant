# 跨平台安装与启动脚手架

## 范围

- Windows：`install.bat` 安装依赖并执行迁移，`start.bat` 联动启动 API、Worker 和前端。
- Linux：`install.sh` 安装依赖并执行迁移，`start.sh` 联动启动 API、Worker 和前端。

## 设计决策

- 继续使用项目既定的 `uv`、`pnpm`、Alembic 和 Vite 开发命令，不引入新的系统服务管理器。
- 安装脚本只负责项目依赖与本地数据库初始化；`uv` 和 `pnpm` 作为用户环境前置依赖，缺失时给出明确提示。
- Windows 批处理使用 CRLF，Shell 脚本使用 LF，并由 `.gitattributes` 固化行尾约束。
- 启动脚本在依赖目录缺失时自动触发安装；Linux 使用退出清理逻辑，Windows 通过独立终端窗口便于分别查看日志。

## 验证证据

- `cmd.exe /d /c call install.bat --quiet`：成功完成 `uv sync`、Alembic 迁移和 `pnpm install`。
- Git Bash `bash -n install.sh`、`bash -n start.sh`：通过。
- Git Bash 执行 `install.sh`：成功完成依赖同步和数据库迁移。
- `.bat` 文件已验证为 CRLF，`.sh` 文件保持 LF。

## 已知边界

- 脚本面向本地开发环境，不负责生产部署、系统级服务注册或自动安装 Node.js/uv。
- Windows 启动脚本会打开三个命令行窗口；关闭这三个窗口即可停止对应开发服务。
