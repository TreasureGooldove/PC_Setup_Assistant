---
title: 预算生效与公开参数来源校准-更新004-审查报告
type: review
update_number: 4
category: builder-data-quality
status: 未确认
result: 通过
created: 2026-08-31
plan: "[[../writer/plan|plan]]"
update: "[[../updater/update-004|update-004]]"
update_summary: "[[../updater/update-004-summary|update-004-summary]]"
tags:
  - spec
  - review
---

# Spec 审查报告

## 文档信息

- **审查日期**：2026-08-31
- **审查对象**：[[../updater/update-004|update-004]]、[[../updater/update-004-summary|update-004-summary]]与当前分支代码
- **Spec 路径**：`agnet/specs/20260831-catalog-sync-filters/`
- **分支**：`feat/15-catalog-sync-filters`

## 1. 审查摘要

| 类别 | 数量 | 状态 |
|---|---:|---|
| 已完成 | 7 | ✅ |
| 未完成 | 0 | ✅ |
| 不符项 | 0 | ✅ |
| 额外项 | 0 | ➕ |

> [!success]
> 更新目标已实现：¥2,500 会贯穿演示和 API 生成链路；低预算会得到真实参考价下的明确超预算说明；京东/拼多多无核验金额时不再生成假报价；用户提供的 ZOL 参数页可以受控联网解析并区分公开参考价；“8000元玩战争雷霆的游戏主机”会被识别并展示最低/推荐配置。

## 2. 详细检查结果

### 2.1 功能完成度

| 功能 | Spec 位置 | 实现位置 | 结论 |
|---|---|---|---|
| 精确预算贯穿页面与 API 生成 | `update-004.md:29,55` | `apps/web/src/App.tsx:1365-1381`、`apps/api/app/main.py:110-124` | ✅ 生成前统一规范化预算；API 先保存完整 `NeedProfile`，任务从会话读取最新预算 |
| 低预算候选调整与诚实提示 | `update-004.md:30,56` | `apps/web/src/App.tsx:637-743`、`apps/api/app/features/builds/planner.py:19-156,166-214` | ✅ 低预算选择较低的兼容候选；不足时保留完整配置价格并说明差额和可执行行动 |
| 无核验报价时不生成平台金额 | `update-004.md:31,57` | `apps/api/app/features/products/service.py:199-225,399-445`、`apps/web/src/features/catalog/OfferComparison.tsx:25-84` | ✅ 京东/拼多多只保留搜索入口和 `待联网`；金额、店铺和采集快照为空时明确显示待取得 |
| ZOL 参数页受控解析与字段合并 | `update-004.md:32,48,58` | `apps/api/app/features/products/zol_public.py:19-51,149-189,242-278`、`apps/api/app/features/products/service.py:277-344` | ✅ 仅接受固定 HTTPS 数字路径，限制 HTML、大小、超时和重定向；字段合并到详情并保留未知字段 |
| 价格与来源状态区分 | `update-004.md:33,49-50,59` | `apps/api/app/domain.py:96-112`、`apps/api/app/features/products/service.py:307-425`、`apps/web/src/features/catalog/ProductDetailPage.tsx:22-73` | ✅ 支持目录参考、ZOL 公开参考、实时授权和待联网语义；ZOL 页面电商金额不标记实时 |
| 既有候选/兼容性/详情展示回归 | `update-004.md:34,40,43` | `apps/web/src/features/catalog/OfferComparison.tsx:89-128`、`DetailedSpecTable.tsx:28-98`、`PartPicker.tsx:482-500` | ✅ 候选报价、完整参数表、来源状态和换件入口继续复用，缺失字段显示待确认 |
| 自然语言识别战争雷霆并载入配置 | `update-004.md` 更新目标与验收标准 | `apps/web/src/App.tsx` 的游戏别名识别/需求状态卡片、`apps/api/app/features/conversations/service.py`、对应前后端测试 | ✅ 保留输入的 8,000 元预算，识别 War Thunder，显示最低/推荐配置已载入，并提供查看入口；异步初始化不会覆盖用户提交 |

### 2.2 数据模型检查

- `Offer.price` 与 `Offer.captured_at` 改为可空：`apps/api/app/domain.py:96-112`；这与“未取得平台金额时不得显示伪造数据”的更新目标一致，已保留已有 `list_price`、`discount_price`、`landed_price` 字段兼容实时报价。
- 前端 `Offer` 同步允许金额和采集时间为空，并增加 `public_reference` 状态：`apps/web/src/types.ts:82-119`。
- ZOL 解析结果使用独立 `ZolProductSnapshot`：`apps/api/app/features/products/zol_public.py:23-31`；未知参数以 `zol_` 前缀保留，未把缺失值猜测为结构化硬件字段。

### 2.3 API 与外部来源检查

| 接口/来源 | Spec 定义 | 实现状态 | 说明 |
|---|---|---|---|
| `PATCH /api/conversations/{id}/profile` + `POST /api/plans/generate` | 生成时使用最新结构化预算 | ✅ | `apps/api/app/main.py:110-124`；队列任务读取更新后的会话 |
| `GET /api/products/{part_id}` | 返回参数、报价、证据和状态 | ✅ | `apps/api/app/main.py:213-214` 与 `get_product_detail` 组合返回 |
| ZOL 公开参数页 | 固定主机/路径、公开 HTML、参考价 | ✅ | `validate_zol_product_url` 与 `fetch_zol_public_product` 执行限制；不带登录态、不跟随重定向 |
| 京东/拼多多 | 无核验返回时保留平台入口 | ✅ | 只有 ZOL 页面明确展示的京东公开金额才标记 `public_reference`；拼多多无金额不伪造 |

### 2.4 测试检查

| 测试项 | 实际结果 | 状态 |
|---|---:|---|
| 后端 Ruff | 通过 | ✅ |
| 后端 mypy | 36 个源文件通过 | ✅ |
| 后端 Pytest | 50 项通过 | ✅ |
| 前端类型检查/lint | 通过 | ✅ |
| 前端 Vitest | 4 个测试文件、19 项通过 | ✅ |
| 前端生产构建 | 通过 | ✅ |
| `git diff --check` | 通过 | ✅ |
| 用户提供的 ZOL 页面联网样本 | 解析 24 个结构化参数、2 个公开价格字段；参考价 ¥1,159，京东公开参考价 ¥1,159 | ✅ |

> [!warning]
> ZOL 页面报价和页面中的京东金额属于公开参考信息，不代表实时成交价；京东/拼多多实时价格仍依赖用户配置合规授权连接器或明确商品返回。联网样本验证不作为 CI 的外部网络依赖。

## 3. 问题清单

### 高优先级 🔴

无。

### 中优先级 🟡

无。

### 低优先级 🟢

无。

## 4. 审查结论

> [!success]
> 严格按更新方案核对后，未发现未完成项或实现不符项，可以进入用户确认和后续 Git 提交流程。

- [x] 可以归档（实现与更新方案一致；等待用户确认）
- [ ] 需要修复后再归档
- [ ] 严重不符，需要重新实现

## 5. 文档关联

- 设计文档：[[../writer/plan|设计方案]]
- 更新方案：[[../updater/update-004|更新方案]]
- 实现总结：[[../updater/update-004-summary|实现总结]]

#spec/审查 #review
