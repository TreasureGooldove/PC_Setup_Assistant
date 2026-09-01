---
title: 预算生效与公开参数来源校准-更新004实现摘要
type: update-summary
update_number: 4
status: ready-for-review
created: 2026-08-31
plan: "[[update-004|update-004]]"
git_branch: feat/15-catalog-sync-filters
base_branch: main
pr_url:
tags:
  - spec
  - update
  - data-quality
---

# 实现摘要

## 已完成

- 演示方案和 API 方案均使用规范化后的预算；预算为 ¥2,500 时，前端生成请求、后端任务和三套结果都保留 ¥2,500，不再用固定高预算组合或倍率改写总价。
- 低预算场景在满足品牌、插槽、内存代际、板型和散热约束的候选中优先选择较低参考价；完整独立显卡配置仍超出预算时，页面明确显示差额、最低完整配置参考价和“提高预算/使用已有配件/暂不购买独显”的行动建议。
- 删除京东、拼多多的目录价比例推导。没有可核验金额时，报价只保留平台搜索入口、`待联网` 状态、来源和“没有报价快照”，不生成店铺、采集时间或伪造金额。
- 新增受控 ZOL 公开参数页解析器，仅接受 `https://detail.zol.com.cn/<数字>/<数字>/param.shtml`，限制响应类型、大小、超时和重定向；用户提供的 B760M 页面可读取标题、CPU 插槽、芯片组、DDR4、最大内存、板型、尺寸、扩展接口和公开参考价。
- 将 ZOL 页面展示的京东金额标记为 `公开参考价`，与实时授权报价、目录参考价和待联网状态分开；拼多多在没有授权/可验证返回时保持待联网。
- 商品详情复用完整参数表，未知字段保留并显示待确认；详情页同时展示平台报价状态、卖家信息（可用时）、来源链接和数据状态。
- 自然语言输入可识别“战争雷霆”、War Thunder 等别名，需求面板显示已识别游戏及“最低/推荐配置已载入”，并可直接打开 Steam 配置参考；API 同步将该输入识别为游戏用途。
- 增加初始化请求竞态保护，用户提交需求后不会被异步创建默认会话覆盖，避免输入与需求记录看起来没有生效。

## 主要变更

- `apps/api/app/features/products/zol_public.py`：ZOL URL 校验、GB18030/HTML 解析、参数归一化、公开参考价和京东公开信息提取。
- `apps/api/app/features/products/service.py`：移除平台假报价，接入 ZOL 公开详情与来源证据，保留京东/拼多多搜索入口。
- `apps/api/app/features/builds/planner.py`、`apps/web/src/App.tsx`：预算感知候选选择、精确预算回传和预算不足提示。
- `apps/api/app/domain.py`、`apps/web/src/types.ts`、`apps/web/src/features/catalog/OfferComparison.tsx`、`ProductDetailPage.tsx`：允许报价金额/采集时间为空，区分实时、公开参考和待联网。
- `apps/api/app/features/builds/catalog.py`、`apps/web/src/features/catalog/offlineCatalog.ts`：加入用户提供的 ZOL 主板参数参考条目。
- `apps/web/src/App.tsx`：加入游戏别名识别、需求面板状态提示和初始化竞态保护。
- `apps/api/tests/`、`apps/web/src/*.test.tsx`：覆盖预算 HTTP 链路、低预算选型、无平台金额、ZOL 解析、详情展示和战争雷霆自然语言识别回归。

## 验证证据

> [!success]
> 后端 `uv run ruff check app tests`、`uv run mypy app` 和 `uv run pytest --basetemp .pytest-tmp` 全部通过：50 项测试通过。

> [!success]
> 前端 `pnpm.cmd lint`、`pnpm.cmd exec tsc --noEmit`、`pnpm.cmd test -- --run` 和 `pnpm.cmd build` 全部通过：4 个测试文件、19 项测试通过，生产构建成功。

> [!success]
> 受控联网验证使用用户提供的 ZOL 参数页：页面返回 HTML，解析到 24 个结构化参数字段和 2 个公开价格字段，并从存储接口中归一化 M.2/SATA 数量；主板参考价与页面公开京东金额均为 ¥1,159，拼多多未被虚构为有价报价。

- `git diff --check` 通过。
- 预算 HTTP 回归确认 PATCH 后生成任务读取 ¥2,500，三套计划预算均为 ¥2,500，并保留 `BUDGET_OVER` 说明。
- 未读取、写入或提交本地 `.env`、模型密钥和数据库；未使用登录态、验证码绕过或反爬绕过。

## 数据边界

> [!warning]
> ZOL 的参考报价和页面展示的京东金额不是实时成交价；京东/拼多多实时金额仍需用户配置合规的授权连接器或可核验商品返回。没有该返回时，界面会明确显示待联网而不是填入估算值。

- 公开参数页仅服务于规格校准，缺失字段不从型号名称推测。
- 现有 Fixture 仍用于离线演示和兼容性回退，界面会标明目录/示例来源。
