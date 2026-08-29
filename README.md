# 智能装机搭子

一个面向普通用户的装机方案助手。输入预算、用途和偏好后，系统会生成多套配置，显示兼容性提示、价格参考与功耗，并支持导出 Excel。

## 快速开始

### 后端

```powershell
cd apps/api
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

另开终端启动任务 Worker：

```powershell
cd apps/api
uv run python -m app.worker
```

### 前端

```powershell
pnpm install
pnpm --dir apps/web dev
```

前端默认访问 `http://localhost:5173`，API 默认访问 `http://localhost:8000`。

## 配置

复制 `apps/api/.env.example` 为本地 `.env`。Fixture 模式不需要外部密钥；如需启用模型，只在本地配置新的服务商密钥。

```env
LLM_API_KEY=
LLM_API_BASE=https://example.invalid/compatible-mode/v1
LLM_MODEL=qwen3.8-max
```

不要把 `.env` 或任何密钥提交到 Git。

## 测试

```powershell
cd apps/api
uv run pytest
uv run ruff check .

cd ../..
pnpm --dir apps/web lint
pnpm --dir apps/web typecheck
pnpm --dir apps/web test
pnpm --dir apps/web build
```

## 目录

- `apps/api`：FastAPI、领域服务、SQLite 队列、Provider 和导出。
- `apps/web`：React 对话界面、方案面板和任务实时状态。
- `agnet`：脱敏的 Spec、决策记录、角色定义和验证证据。
- `design-system`：UI 设计系统源文件。
- `plan.md`：本次实现计划。

## 数据来源边界

首版默认使用可复现的 Fixture 数据。京东联盟、拼多多官方开放平台和视频证据能力只通过适配器接口接入；不实现验证码绕过、隐蔽抓取或对第三方内容的复制。
