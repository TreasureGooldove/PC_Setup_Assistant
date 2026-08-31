---
title: 商品详情与多平台报价 Team Context
type: team-context
status: active
git_branch: feat/13-product-marketplace-details
base_branch: main
issue_url: https://github.com/TreasureGooldove/PC_Setup_Assistant/issues/13
---

# Team Context

## Control

- Spec：`20260831-product-marketplace-details`
- Issue：https://github.com/TreasureGooldove/PC_Setup_Assistant/issues/13
- 当前阶段：实现中

## Task Progress

| 角色 | 状态 | 产物 |
|---|---|---|
| spec-lead | doing | 本文件与范围控制 |
| spec-explorer | done | `explorer/exploration-report.md` |
| spec-writer | done | `writer/plan.md` |
| spec-executor | done | `executor/summary.md` |
| spec-tester | done | `tester/test-report.md` |
| spec-reviewer | done | `reviewer/review.md` |
| spec-ender | pending | PR、CI 与收尾报告 |

## Shared Decisions

- 配置清单中的配件主体和“换一件”按钮都进入同一个选配器。
- 商品详情是独立页面状态，保留返回选配器和直接使用配件两条路径。
- ZOL CPU/GPU 天梯与 DIY 页面作为结构和资料信源，不复制页面素材，不把其价格当实时成交价。
- 京东公开商品页解析默认关闭，仅允许 HTTPS `item.jd.com`，不使用登录态、浏览器指纹、验证码或反爬绕过。
- 京东与拼多多在无凭证或实时数据失败时显示带状态的 Fixture 报价。

## Problem Resolution Log

| 状态 | 问题 | 处理 |
|---|---|---|
| resolved | 现有候选目录过小 | 扩展 CPU、GPU、主板的结构化 Fixture，并让天梯复用同一目录 |
| resolved | 商品参数来源与稳定性冲突 | 采用受控公开页解析适配器 + Fixture 回退，不把失败猜成数据 |
