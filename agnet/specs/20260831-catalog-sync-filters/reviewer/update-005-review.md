---
title: 结构化大模型装机建议-更新005-审查报告
type: review
update_number: 5
category: builder-data-quality
status: 未确认
result: 通过
created: 2026-08-31
plan: "[[../writer/plan|plan]]"
update: "[[../updater/update-005|update-005]]"
update_summary: "[[../updater/update-005-summary|update-005-summary]]"
tags:
  - spec
  - review
---

# Spec 审查报告

## 文档信息

- **审查日期**：2026-08-31
- **审查对象**：[[../updater/update-005|update-005]]、[[../updater/update-005-summary|update-005-summary]]与当前分支代码
- **Spec 路径**：`agnet/specs/20260831-catalog-sync-filters/`
- **分支**：`feat/15-catalog-sync-filters`

## 1. 审查摘要

| 类别 | 数量 | 状态 |
|---|---:|---|
| 已完成 | 8 | ✅ |
| 未完成 | 0 | ✅ |
| 不符项 | 0 | ✅ |
| 额外项 | 0 | ➕ |

> [!success]
> 更新目标已实现：用户提交需求并生成方案后，可以看到结构化的 AI 辅助建议、选择理由、兼容性/价格结论和可展开来源；可选 Qwen 只负责解释，Mock 与确定性校验保证离线可用。

## 2. 详细检查结果

### 2.1 功能完成度

| 功能 | Spec 位置 | 实现位置 | 结论 |
|---|---|---|---|
| 结构化建议领域模型与禁止隐藏思考字段 | `update-005.md:47-66` | `apps/api/app/domain.py:212-282`、`apps/web/src/types.ts:167-238` | ✅ 字段白名单与前后端类型一致 |
| 固定只读上下文工具 | `update-005.md:69-80` | `apps/api/app/features/recommendations/tools.py:14-210` | ✅ 仅允许 5 个工具，并限制输出字段/长度 |
| 当前方案、配件身份、证据引用确定性复核 | `update-005.md:80-91` | `apps/api/app/features/recommendations/schemas.py:121-176` | ✅ 不允许模型引入方案外配件或未知依据 |
| Mock/Qwen Provider 与失败降级 | `update-005.md:51-58,94-108` | `apps/api/app/features/recommendations/providers.py:14-96`、`apps/api/app/llm.py:63-111` | ✅ 无 Key、异常和非法结果可回退 |
| 队列任务、幂等 API、持久化结果和阶段进度 | `update-005.md:111-120` | `apps/api/app/features/jobs/service.py:30-44`、`apps/api/app/main.py:156-176`、`apps/api/app/database.py:42-50` | ✅ 复用 Worker/SSE，新增迁移 `apps/api/migrations/versions/003_recommendations.py:1-55` |
| 前端结构化建议卡片与状态 | `update-005.md:122-130` | `apps/web/src/features/recommendations/RecommendationCard.tsx:36-246`、`apps/web/src/App.tsx:1298-1359,2366-2378` | ✅ 加载、错误、空结果、离线、来源和重新生成均有入口 |
| 方案变更后结果失效 | `update-005.md:166-178` | `apps/api/app/features/recommendations/service.py:62-70`、`apps/web/src/App.tsx:1435-1504,1723-1786` | ✅ 读取时计算指纹，换件/锁定/需求变化会清理旧建议 |
| 文档、配置和回归测试 | `update-005.md:151-164` | `README.md:76-110`、`apps/api/.env.example:7-9`、新增测试文件 | ✅ 本地质量检查和全量回归通过 |

### 2.2 数据模型检查

- `Recommendation` 的结论、选择、兼容性、价格、证据、状态和时间字段均在 Pydantic 模型中定义，未知字段使用 `extra="forbid"` 拒绝。
- 价格结论由当前 `BuildPlan` 和已标记为实时的报价计算；没有可核验实时报价时固定为 `reference_only`，没有让模型写入金额、店铺或采集时间。
- 建议与 `plan_fingerprint` 绑定；方案变化后 API 返回 `stale=true`，满足更新方案的过期保护要求。

### 2.3 API 与队列检查

| 接口 | Spec 定义 | 实现状态 | 说明 |
|---|---|---|---|
| `POST /api/plans/{plan_id}/recommendations` | 异步生成建议，支持幂等 | ✅ | `apps/api/app/main.py:156-171`，返回任务对象 |
| `GET /api/recommendations/{id}` | 获取已校验建议 | ✅ | `apps/api/app/main.py:174-176` |
| `GET /api/jobs/{id}` | 读取任务状态和结果 | ✅ | 复用现有队列接口，任务结果包含建议 ID/结构 |
| `GET /api/jobs/{id}/events` | SSE 阶段进度 | ✅ | 建议任务只发送阶段、进度和完成状态，不发送 token/提示词 |

### 2.4 测试检查

| 测试项 | 实际结果 | 状态 |
|---|---:|---|
| 后端 Ruff | 通过 | ✅ |
| 后端 mypy | 41 个源文件通过 | ✅ |
| 后端 Pytest | 59 项通过 | ✅ |
| 前端 lint/typecheck | 通过 | ✅ |
| 前端 Vitest | 5 个测试文件、21 项通过 | ✅ |
| 前端生产构建 | 通过 | ✅ |
| Alembic 迁移 | `002_catalog_cache -> 003_recommendations` 通过 | ✅ |
| 运行链路 | Mock、War Thunder 证据、参考价状态和非过期结果通过 | ✅ |

> [!warning]
> 本地没有配置真实 Qwen Key，因此未进行外部模型实调；该情形属于默认离线路径，已由无 Key、结构化解析和超时回退测试覆盖，不影响 CI 稳定性。

## 3. 问题清单

### 高优先级 🔴

无。

### 中优先级 🟡

无。

### 低优先级 🟢

无。

## 4. 审查结论

> [!success]
> 按更新方案逐项核对，未发现未完成项、接口不符项或范围外实现；可以进入用户审查确认和后续分支收尾流程。

- [x] 可以进入确认（更新保留在当前 Spec，不归档）
- [ ] 需要修复后重新审查
- [ ] 严重不符，需要重新实现

## 5. 文档关联

- 更新方案：[[../updater/update-005|更新方案]]
- 实现摘要：[[../updater/update-005-summary|实现摘要]]
- 原设计：[[../writer/plan|设计方案]]

#spec/审查 #review
