---
title: 测试报告
type: test-report
status: completed
created: 2026-08-29
git_branch: feat/1-pc-builder-mvp
---

# 测试报告

## 结果

- 后端 Ruff：通过。
- 后端 mypy：通过，无错误。
- 后端 Pytest：9 项通过。
- Alembic 迁移：通过。
- 前端 lint/typecheck：通过。
- 前端 Vitest：2 项通过。
- 前端生产构建：通过。
- 秘密模式扫描：通过，未发现密钥、`.env` 或常见令牌模式。

## 验收覆盖

- 对话内容可解析为预算、CPU/GPU 品牌和散热偏好。
- 方案生成返回省心、均衡、高性能三档结果。
- 兼容性规则覆盖插槽、内存、显卡长度、散热空间、冷排尺寸和电源余量。
- 低预算方案会明确标记预算超出，不由模型静默掩盖。
- SQLite 队列覆盖幂等、并发领取、租约恢复、取消、重试和死信路径。
- HTTP 集成覆盖对话、异步生成和任务完成；导出单元测试覆盖工作表与字段。

## 证据

本次命令输出保存在：

`tester/artifacts/test-logs/20260829-2352-run-001/`

运行时的 API、Worker 和前端预览可分别通过 `http://localhost:8000`、Worker 进程和 `http://localhost:5173` 验证。
