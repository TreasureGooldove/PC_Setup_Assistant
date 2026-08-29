---
title: 实现计划
type: implementation-plan
status: approved
created: 2026-08-29
git_branch: feat/1-pc-builder-mvp
base_branch: main
pr_url: https://github.com/TreasureGooldove/PC_Setup_Assistant/pull/2
---

# 实现计划

1. 建立 FastAPI 特性模块、Pydantic 类型、SQLite 存储和迁移。
2. 实现 Fixture 配件数据、预算规划、兼容性规则、方案服务和 Mock/可选 Qwen 客户端。
3. 实现 SQLite JobQueue、独立 Worker、线程/进程池边界、SSE 事件和 Excel 导出。
4. 实现 React 单页工作台：需求表单、对话提示、三套方案、兼容性、替换/锁定和导出。
5. 添加测试、README、CI、秘密扫描和 Spec 总结。

## 接口范围

`/health`、`/ready`、`/api/conversations`、`/api/conversations/{id}/messages`、`/api/plans/generate`、`/api/plans/{id}`、`/api/plans/{id}/items/{slot}`、`/api/plans/{id}/refresh-offers`、`/api/jobs/{id}`、`/api/jobs/{id}/events`、`/api/jobs/{id}/cancel`、`/api/plans/{id}/exports`。

## 非目标

不实现登录系统、支付、真实购买、不稳定网页抓取、验证码绕过和自动下载第三方视频。
