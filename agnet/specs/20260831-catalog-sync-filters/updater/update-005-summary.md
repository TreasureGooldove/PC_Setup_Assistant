---
title: 结构化大模型装机建议-更新005实现摘要
type: update-summary
update_number: 5
category: builder-data-quality
status: ready-for-review
created: 2026-08-31
plan: "[[../writer/plan|plan]]"
update: "[[update-005|update-005]]"
git_branch: feat/15-catalog-sync-filters
base_branch: main
pr_url:
tags:
  - spec
  - update
  - recommendation
---

# 更新总结

## 1. 完成内容

- 增加 `Recommendation` 领域模型，包含需求摘要、配置取舍、兼容性结论、价格状态、证据、待确认项和下一步；不包含隐藏思考字段。
- 增加版本化的最小上下文与固定只读工具：需求、游戏配置、当前方案、兼容性和报价依据。工具输出会截断长文本，不暴露数据库、凭证、原始响应或任意执行能力。
- 增加 Mock 与可选 Qwen OpenAI 兼容 Provider。Qwen 默认关闭；无 Key、超时、异常或结构化结果校验失败时，自动回退到本地结构化建议。
- 增加建议任务、幂等 API、持久化结果和 SSE 阶段进度；建议绑定方案指纹，换件或方案变化后读取结果会标记为过期。
- 增加前端建议卡片：结论、需求理解、兼容性、价格依据、逐项选择理由、来源链接、待确认项和重新生成；包含加载、错误、空结果和本地演示状态。
- 增加 `003_recommendations` Alembic 迁移，并同步 `.env.example`、README 和根计划。

## 2. 主要文件

```text
apps/api/app/domain.py
apps/api/app/database.py
apps/api/app/llm.py
apps/api/app/features/recommendations/
apps/api/app/features/jobs/service.py
apps/api/app/main.py
apps/api/migrations/versions/003_recommendations.py
apps/api/tests/test_recommendations.py
apps/api/tests/test_llm_recommendations.py
apps/web/src/features/recommendations/
apps/web/src/App.tsx
apps/web/src/api.ts
apps/web/src/types.ts
apps/web/src/styles.css
README.md
plan.md
```

## 3. 验证证据

> [!success]
> 后端 `uv run ruff check app tests`、`uv run mypy app` 和 `uv run pytest --basetemp=...` 通过：59 项测试全部通过。

> [!success]
> 前端 `pnpm.cmd lint`、`pnpm.cmd typecheck`、`pnpm.cmd test -- --run` 和 `pnpm.cmd build` 通过：5 个测试文件、21 项测试全部通过，生产构建成功。

> [!success]
> `uv run alembic upgrade head` 成功从 `002_catalog_cache` 升级到 `003_recommendations`。本地运行链路验证了 Mock 建议、`reference_only` 价格状态、War Thunder 游戏证据和 `stale=false`。

- 未配置或读取任何真实模型密钥；Qwen 真实服务调用不作为本地 CI 依赖。
- `git diff --check` 通过；未提交 `.env`、数据库、Token 或原始模型响应。

## 4. 数据与安全边界

> [!warning]
> 当前默认展示的是本地 Mock/参考价建议。Qwen 和实时商品报价只有在用户自行配置合规凭证或连接器后才会启用，页面会保留对应来源状态，不把参考金额伪装成实时成交价。

- 模型只能引用当前方案内的配件和已知证据；服务端重新计算价格与兼容性摘要。
- 游戏配置查询失败时只生成低可信度的“待取得”证据，不阻塞装机建议。
- 自定义上下文工具采用固定白名单，不支持任意网络、数据库、命令、登录态或验证码绕过。

## 5. 后续事项

- 如需真实 Qwen 建议，用户在本机未跟踪 `.env` 中配置新密钥，并重启 API 与 Worker。
- 如需真实电商金额，继续使用已接入的合规授权连接器或明确商品返回；本更新不新增网页爬虫。
- 本更新保留在当前 Spec 目录，等待审查确认，不执行归档、提交或推送。

## 6. 文档关联

- 更新方案：[[update-005|更新方案]]
- 原设计：[[../writer/plan|设计方案]]
- 原总结：[[../executor/summary|实现总结]]
- 审查报告：[[../reviewer/update-005-review|审查报告]]

#spec/更新
