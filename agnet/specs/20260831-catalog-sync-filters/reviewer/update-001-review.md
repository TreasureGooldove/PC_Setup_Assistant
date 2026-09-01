---
title: 候选详情同屏平台比价-更新001-审查报告
type: review
update_number: 1
category: catalog-sync
status: 未确认
result: 通过
created: 2026-08-31
plan: "[[../writer/plan|plan]]"
update: "[[../updater/update-001|update-001]]"
update_summary: "[[../updater/update-001-summary|update-001-summary]]"
tags:
  - spec
  - review
---

# Spec 审查报告

## 文档信息

- **审查日期**：2026-08-31 17:38 +08:00
- **审查对象**：[[../updater/update-001|update-001]]、[[../updater/update-001-summary|update-001-summary]]与当前分支代码
- **Spec 路径**：`agnet/specs/20260831-catalog-sync-filters/`

## 1. 审查摘要

| 类别 | 数量 | 状态 |
|---|---:|---|
| 已完成 | 12 | ✅ |
| 未完成 | 0 | ✅ |
| 不符项 | 0 | ✅ |
| 额外项 | 0 | ✅ |

> [!success]
> 更新目标已实现：候选选择后同屏展示平台报价和完整配置参数；淘宝 MCP 作为独立可选连接器接入；严格实时模式不会把 Fixture 金额冒充实时报价。

## 2. 详细检查结果

### 2.1 功能完成度

| 功能 | Spec 位置 | 实现位置 | 结论 |
|---|---|---|---|
| 候选详情同屏展示平台报价 | `updater/update-001.md:31-34` | `apps/web/src/features/catalog/PartPicker.tsx:496-500` | ✅ 报价组件直接嵌入右侧详情 |
| 复用独立商品详情报价展示 | `updater/update-001.md:54-58` | `apps/web/src/features/catalog/ProductDetailPage.tsx:10-11,81` | ✅ 复用 `OfferComparison` |
| 显示平台、金额、店铺、来源、状态、采集时间和核价入口 | `updater/update-001.md:33` | `apps/web/src/features/catalog/OfferComparison.tsx:24-62` | ✅ 字段均有渲染；实时/示例标签分开 |
| 切换候选时丢弃过期报价 | `updater/update-001.md:34,47-50` | `apps/web/src/App.tsx:1299-1321` | ✅ 使用递增请求标识和当前品类校验 |
| 展示完整结构化配置参数 | `updater/update-001.md:30,57-58` | `apps/web/src/features/catalog/PartPicker.tsx:482-494` | ✅ 不再截断字段，并保留统一格式化 |
| 淘宝 MCP stdio 会话 | `updater/update-001.md:67-70` | `apps/api/app/features/products/taobao_mcp.py:239-308` | ✅ 独立进程、持久会话、登录初始化和分页调用 |
| 新旧淘宝抓取工具名兼容 | `updater/update-001.md:69` | `apps/api/app/features/products/taobao_mcp.py:269-274` | ✅ 支持新工具名并回退旧工具名 |
| 淘宝商品引用校验与字段提取 | `updater/update-001.md:70` | `apps/api/app/features/products/taobao_mcp.py:36-61,116-220` | ✅ 校验允许域名和 HTTPS，并提取店铺、SKU、价格、参数 |
| 实时金额统一归一化 | `updater/update-001.md:70` | `apps/api/app/features/products/taobao_mcp.py:182-220`、`apps/api/app/features/builds/price_sources.py:119-127` | ✅ 只有明确金额才标记 `is_live=true` |
| 严格实时价格模式 | `updater/update-001.md:71,105-106` | `apps/api/app/config.py:19-25`、`apps/api/app/features/products/service.py:247-295` | ✅ 未取得实时授权报价时返回空报价，不返回 Fixture 金额 |
| MCP 日志不污染 stdio 协议 | `updater/update-001.md:71` | `apps/api/app/features/products/taobao_mcp_launcher.py:16-34` | ✅ 第三方日志重定向 stderr，协议仍使用 stdout |
| 关闭 API 时释放 MCP 进程 | `updater/update-001.md:67-70` | `apps/api/app/main.py:46-52` | ✅ 生命周期 finally 中统一关闭 |

### 2.2 数据模型检查

- `Offer` 未增加破坏性字段，淘宝报价复用 `platform`、`seller`、`sku`、`landed_price`、`captured_at`、`is_live` 等既有字段：`apps/api/app/domain.py:96-111`。
- `ProductDetail` 未改变公开响应结构；淘宝参数合并到已有 `Part.specs`，证据和数据源状态沿用既有模型：`apps/api/app/domain.py:172-185`、`apps/api/app/features/products/service.py:271-291`。
- 本地配置新增实时价格和淘宝 MCP 路径/映射字段，均不包含密钥：`apps/api/app/config.py:19-25,51-59`。

### 2.3 API 接口检查

| 接口 | Spec 定义 | 实现状态 | 说明 |
|---|---|---|---|
| `GET /api/products/{part_id}` | 返回报价、参数和来源状态 | ✅ | `apps/api/app/main.py:213-214` 调用商品详情服务；服务按配置加入淘宝结果 |
| 既有商品详情接口 | 不新增重复 HTTP 接口 | ✅ | 更新复用现有接口，响应仍为 `ProductDetail` |

### 2.4 测试检查

| 测试项 | 实际结果 | 状态 |
|---|---:|---|
| Ruff | 通过 | ✅ |
| Mypy | 35 个源文件通过 | ✅ |
| Pytest | 42 项通过 | ✅ |
| 前端 lint/typecheck | 通过 | ✅ |
| Vitest | 13 项通过 | ✅ |
| Vite 生产构建 | 通过 | ✅ |
| `git diff --check` | 通过 | ✅ |
| 淘宝 MCP 解析/引用校验/严格模式测试 | 3 项覆盖 | ✅ |
| 候选报价竞态回归 | `apps/web/src/App.test.tsx` 覆盖 | ✅ |

> [!warning]
> 当前本机未配置淘宝 MCP server 路径、商品映射或淘宝登录会话，因此本次审查验证的是连接器协议、解析和降级逻辑；真实平台金额须在本机安装外部服务、完成扫码并配置具体商品 ID/链接后再做一次联网验收。

## 3. 问题清单

### 高优先级 🔴

无。

### 中优先级 🟡

无。

### 低优先级 🟢

无。

## 4. 审查结论

### 是否可以归档

- [x] 可以归档（实现与更新方案一致；外部联网前置条件已明确记录）
- [ ] 需要修复后再归档
- [ ] 严重不符，需要重新实现

## 5. 文档关联

- 设计文档：[[../writer/plan|设计方案]]
- 更新方案：[[../updater/update-001|更新方案]]
- 实现总结：[[../updater/update-001-summary|实现总结]]

#spec/审查 #review
