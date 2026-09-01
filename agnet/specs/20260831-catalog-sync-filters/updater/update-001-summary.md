---
title: 候选详情同屏平台比价-更新001实现摘要
type: update-summary
update_number: 1
status: ready-for-review
created: 2026-08-31
plan: "[[update-001|update-001]]"
tags:
  - spec
  - update
---

# 实现摘要

## 已完成

- 候选选配器和商品详情页复用平台报价卡，展示平台、金额、店铺、来源、状态、采集时间和核价链接。
- 候选详情展示当前数据中的全部结构化参数，快速切换候选时丢弃过期报价响应。
- 新增淘宝 MCP stdio 连接器：支持路径配置、登录初始化、分页返回、较新/旧抓取工具名兼容、商品引用校验、店铺/价格/参数提取和统一 `Offer` 归一化。
- 新增 `REALTIME_PRICES_REQUIRED` 严格模式；未取得可核验实时金额时不把 Fixture 金额作为报价返回。
- 新增外部淘宝 MCP 安装与配置说明；第三方抓取代码保持独立，不复制进仓库。

## 验证证据

- 后端：`uv run ruff check .` 通过。
- 后端：`uv run mypy app` 通过。
- 后端：`uv run pytest -q --basetemp .pytest-tmp-taobao`，42 项通过。
- 前端：`pnpm.cmd lint`、`pnpm.cmd typecheck`、`pnpm.cmd test -- --run`，13 项通过。
- 前端：`pnpm.cmd build` 通过。
- `git diff --check` 通过；未向仓库写入密钥或本地 `.env`。

## 已知边界

- 淘宝 MCP 按具体商品 ID/链接查询，不提供自动关键词搜索全站价格；需配置“内部配件 ID → 商品引用”映射。
- 真实淘宝价格依赖外部 MCP 安装、浏览器扫码授权、商品映射和平台当前返回；本地未配置时仍显示明确的未配置/未联网状态。
- 京东、拼多多联盟真实报价适配器仍需用户自行配置官方授权，默认不会伪造实时数据。
