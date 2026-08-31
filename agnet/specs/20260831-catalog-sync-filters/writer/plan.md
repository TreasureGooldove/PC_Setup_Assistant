---
title: 全品类候选与目录同步实现计划
type: implementation-plan
status: approved
created: 2026-08-31
git_branch: feat/15-catalog-sync-filters
base_branch: main
issue_url: https://github.com/TreasureGooldove/PC_Setup_Assistant/issues/15
---

# 实现计划

1. 扩展内存、硬盘、电源、散热和机箱 Fixture，使全部八类候选均不少于 12 个。
2. 增加目录缓存表与同步状态表，提供短事务保存、读取、去重和过期判断。
3. 实现固定白名单 ZOL 列表页解析器，限制 URL、重定向、响应类型、响应大小、超时和条目数。
4. 将目录同步接入持久化 Worker，复用任务进度、幂等、重试和 SSE。
5. 扩展目录接口，返回品牌、类型/系列、价格范围、来源和同步状态，并支持服务端筛选。
6. 重构 `PartPicker`，增加搜索提交、品牌/类型快捷筛选、价格区间、清空、同步按钮与图片商品行。
7. 增加解析、缓存、筛选、队列、并发和前端交互测试，执行全量质量门禁与浏览器验收。
8. 更新 README、根计划与 Spec 证据，提交 PR，等待 CI 后 squash 合并并删除分支。

## 非目标

- 不登录第三方账号，不执行购买、支付或自动下单。
- 不绕过验证码、反爬、访问控制、设备指纹或地区限制。
- 不承诺公开页参考价是实时最低价或最终到手价。
