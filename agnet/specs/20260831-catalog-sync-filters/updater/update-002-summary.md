---
title: 完整硬件参数详情-更新002实现摘要
type: update-summary
update_number: 2
status: ready-for-review
created: 2026-08-31
plan: "[[update-002|update-002]]"
tags:
  - spec
  - update
---

# 实现摘要

## 已完成

- 新增统一参数 schema，覆盖八类配件的基础资料、性能、平台、接口、尺寸、供电、散热和售后信息。
- 新增 `DetailedSpecTable`，按分组表格展示参数；已采集值、单位、待确认字段和统计数量清晰区分。
- 候选详情与独立商品详情复用同一组件，并补入品牌、型号、参考功耗等已有可靠信息。
- 未归一化的商品页字段保留在“其他已采集字段”中；京东常见硬件标签增加统一映射。
- 淘宝 MCP 返回参数但没有明确价格时，参数仍会写入商品详情；价格状态继续保持不可用，不伪装为实时价。

## 验证证据

- 后端：`uv run ruff check .`、`uv run mypy app` 通过。
- 后端：`uv run pytest -q --basetemp .pytest-tmp-detail`，44 项通过。
- 前端：`pnpm.cmd lint`、`pnpm.cmd test -- --run`，15 项通过。
- 前端：`pnpm.cmd build` 通过。
- `git diff --check` 通过；测试临时目录已清理，未写入密钥或本地 `.env`。

## 数据边界

- 字段 schema 只负责完整展示，不会从型号名称推断未经验证的参数。
- 真实商品参数仍取决于已配置的京东公开商品页或淘宝 MCP；没有来源时显示“待确认”。
