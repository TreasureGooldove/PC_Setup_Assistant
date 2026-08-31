---
title: 全品类候选与目录同步 Team Context
type: team-context
status: ready-for-review
git_branch: feat/15-catalog-sync-filters
base_branch: main
issue_url: https://github.com/TreasureGooldove/PC_Setup_Assistant/issues/15
---

# Team Context

## Control

- Spec：`20260831-catalog-sync-filters`
- Issue：https://github.com/TreasureGooldove/PC_Setup_Assistant/issues/15
- 当前阶段：本地验收完成，准备提交与 CI

## Task Progress

| 角色 | 状态 | 产物 | completed_at | updated_by |
|---|---|---|---|---|
| spec-lead | done | 本文件与范围控制 | - | spec-lead |
| spec-explorer | done | `explorer/exploration-report.md` | - | spec-explorer |
| spec-writer | done | `writer/plan.md` | - | spec-writer |
| spec-executor | done | `executor/implementation-summary.md` | - | spec-executor |
| spec-tester | done | `tester/test-plan.md` 与 `tester/test-result.md` | - | spec-tester |
| spec-reviewer | done | `reviewer/review.md` | 2026-08-31 11:10 +08:00 | spec-reviewer |

## Shared Decisions

- Fixture 是离线、测试和外部来源失败时的稳定底座，每个分类至少 12 个候选。
- 候选同步使用现有 SQLite 任务队列；公开页数据写入独立缓存后与 Fixture 去重合并。
- 只允许代码内固定的 ZOL 产品列表 URL；限制响应体、超时与数量，不携带 Cookie，不跟随重定向。
- 页面先展示本地候选，再显示同步状态；筛选不会等待外部网络完成。
- 兼容性所需字段缺失时标记待确认，外部文本不能覆盖硬规则。

## Problem Resolution Log

| 状态 | 问题 | 处理 |
|---|---|---|
| resolved | 散热、电源等分类候选太少 | 扩展结构化 Fixture，并允许受控缓存补充 |
| resolved | 外部页面不稳定会阻塞选配 | 队列化后台同步、SQLite 缓存和 Fixture 降级 |
| resolved | 下拉筛选效率低 | 改为品牌与类型/系列快捷筛选，保留搜索和价格区间 |
| resolved | 旧 Worker 不识别新任务类型 | 精确重启本地 Worker；失败状态保持回退候选，README 明确升级后需同步重启 |
| resolved | 同步状态更新时间误当数据采集时间 | 过期判断改用 `captured_at`，排队状态不再伪装为新鲜数据 |
