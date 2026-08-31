---
title: 商品详情与多平台报价实现计划
type: implementation-plan
status: approved
created: 2026-08-31
git_branch: feat/13-product-marketplace-details
base_branch: main
issue_url: https://github.com/TreasureGooldove/PC_Setup_Assistant/issues/13
---

# 实现计划

1. 扩展领域类型与结构化硬件目录，CPU/GPU 各不少于 15 项，主板不少于 10 项。
2. 让天梯从统一目录生成，并补充 ZOL 天梯、DIY 的来源链接与更新时间。
3. 实现商品详情聚合、双平台 Fixture 报价和受控京东公开页参数解析 Provider。
4. 增加 `GET /api/products/{part_id}`，返回配件、报价、证据和数据状态。
5. 配置清单的配件主体支持直接换件；选配器增加“商品详情”，详情页支持返回和选用。
6. 完善商品参数标签、报价状态、采集时间、来源和响应式样式。
7. 增加后端解析/接口/目录测试和前端交互测试，执行 lint、类型检查、测试、构建、秘密扫描与本地预览。
8. 更新 README、根计划和 Spec 证据，提交 PR，等待 CI 后 squash 合并并删除分支。

## 非目标

- 不实现购买、登录、支付或自动下单。
- 不绕过京东/拼多多登录、验证码、设备指纹或反爬。
- 不声称 Fixture、搜索入口或过期数据是实时最低价。
