---
title: 全品类候选与目录同步-审查报告
type: review
category: catalog-sync
status: 未确认
result: 需修复
created: 2026-08-31
plan: "[[../writer/plan|plan]]"
summary: "[[../executor/implementation-summary|implementation-summary]]"
tags:
  - spec
  - review
---

# Spec 审查报告

## 文档信息

- 审查日期：2026-08-31 11:10 +08:00
- 审查对象：[[../writer/plan|实现计划]]、[[../executor/implementation-summary|实现摘要]]与当前分支代码
- Spec 路径：`agnet/specs/20260831-catalog-sync-filters/`

## 1. 审查摘要

| 类别 | 数量 | 状态 |
|---|---:|---|
| 已完成 | 7 | ✅ |
| 未完成 | 1 | ❌ |
| 不符项 | 0 | ✅ |
| 额外项 | 0 | ✅ |

> [!failure]
> 用户复核发现候选详情面板没有同屏展示京东与拼多多报价；原计划未覆盖该交互，需通过 update-001 补齐后重新审查。

## 2. 详细检查结果

### 2.1 功能完成度

| 功能 | Spec 位置 | 实现位置 | 结论 |
|---|---|---|---|
| 八品类稳定候选不少于 12 个 | `writer/plan.md:13` | `apps/api/app/features/builds/catalog_accessories.py:39`、`apps/api/tests/test_catalog_sync.py:26` | ✅ 已完成 |
| SQLite 缓存、同步状态与过期判断 | `writer/plan.md:14` | `apps/api/app/database.py:72`、`apps/api/app/database.py:83`、`apps/api/app/features/catalog_sync/service.py:360` | ✅ 已完成 |
| 固定白名单公开目录解析与响应限制 | `writer/plan.md:15` | `apps/api/app/features/catalog_sync/service.py:24`、`apps/api/app/features/catalog_sync/service.py:94`、`apps/api/app/features/catalog_sync/service.py:229`、`apps/api/app/features/catalog_sync/service.py:280` | ✅ 已完成 |
| 队列任务、进度、重试与 SSE 复用 | `writer/plan.md:16` | `apps/api/app/features/jobs/service.py:33`、`apps/api/app/main.py:187` | ✅ 已完成 |
| 目录筛选、分面、来源与同步状态接口 | `writer/plan.md:17` | `apps/api/app/main.py:166`、`apps/api/app/features/catalog_sync/service.py:463` | ✅ 已完成 |
| 选配器厂商、系列、价格、更新与图片列表 | `writer/plan.md:18` | `apps/web/src/features/catalog/PartPicker.tsx:233`、`apps/web/src/features/catalog/PartPicker.tsx:277`、`apps/web/src/features/catalog/PartPicker.tsx:301`、`apps/web/src/features/catalog/PartPicker.tsx:325`、`apps/web/src/features/catalog/PartPicker.tsx:379` | ✅ 已完成 |
| 自动化与本地浏览器验收 | `writer/plan.md:19` | `apps/api/tests/test_catalog_sync.py:38`、`apps/api/tests/test_catalog_sync.py:150`、`apps/web/src/features/catalog/PartPicker.test.tsx:68`、`tester/test-result.md:20` | ✅ 已完成 |

### 2.2 数据模型检查

| 模型 | 设计要求 | 实现位置 | 状态 |
|---|---|---|---|
| 候选缓存 | 标准化 `Part`、分类、来源、采集和过期时间 | `apps/api/app/database.py:72` | ✅ 一致 |
| 同步状态 | 分类、状态、来源、数量、消息、采集和更新时间 | `apps/api/app/database.py:83` | ✅ 一致 |
| 前端目录响应 | 候选、品牌/系列分面、价格范围和同步状态 | `apps/web/src/types.ts:76` | ✅ 一致 |

### 2.3 API 接口检查

| 接口 | Spec 定义 | 实现状态 | 说明 |
|---|---|---|---|
| `GET /api/catalog/{category}` | 搜索、厂商、系列、价格和排序 | ✅ | `apps/api/app/main.py:166` |
| `POST /api/catalog/{category}/refresh` | 创建持久化同步任务 | ✅ | `apps/api/app/main.py:187` |
| `GET /api/jobs/{id}/events` | 复用 SSE 进度 | ✅ | 复用既有任务事件接口，目录任务由 `apps/api/app/features/jobs/service.py:33` 执行 |

### 2.4 测试检查

| 测试项 | 实际结果 | 状态 |
|---|---:|---|
| Ruff | 通过 | ✅ |
| Mypy | 33 个源文件通过 | ✅ |
| Pytest | 38 项通过 | ✅ |
| 前端类型检查 | 通过 | ✅ |
| Vitest | 9 项通过 | ✅ |
| Vite 生产构建 | 通过 | ✅ |
| Alembic 全新数据库迁移 | `002_catalog_cache (head)` | ✅ |
| 当前树目标词与密钥模式扫描 | 0 命中 | ✅ |

## 3. 问题清单

### 高优先级 🔴

无。

### 中优先级 🟡

1. **候选详情缺少平台比价**
   - Spec 位置：`writer/plan.md:18`
   - 问题：右侧详情只有目录参考价，京东与拼多多报价必须进入独立商品详情页后才能查看。
   - 建议：复用现有 `/api/products/{part_id}` 报价结构，在候选详情中直接展示平台、参考到手价、店铺、状态、采集时间与核价链接；示例报价必须明确标记未联网。

### 低优先级 🟢

无。

> [!warning]
> 外部列表参考价可能延迟或缺少兼容字段；实现已按计划保留更新时间、参考价提示和待确认状态，不把外部文本提升为硬规则。

## 4. 审查结论

- [ ] 可以进入 GitHub 交付与归档阶段
- [x] 需要修复后再归档
- [ ] 严重不符，需要重新实现

> [!tip]
> GitHub Actions 通过并完成 squash 合并后，再将交付状态和 PR 地址写入收尾摘要。

## 5. 文档关联

- 设计文档：[[../writer/plan|实现计划]]
- 实现总结：[[../executor/implementation-summary|实现摘要]]
- 测试结果：[[../tester/test-result|测试结果]]

#spec/审查 #review
