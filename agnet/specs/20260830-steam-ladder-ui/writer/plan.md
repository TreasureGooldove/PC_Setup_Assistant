---
title: 游戏配置与硬件天梯实现计划
type: implementation-plan
status: approved
created: 2026-08-30
git_branch: feat/4-steam-ladder-ui
base_branch: main
issue_url: https://github.com/TreasureGooldove/PC_Setup_Assistant/issues/4
---

# 实现计划

1. 增加 `GameRequirement`、`HardwareLadderEntry`、Steam Provider 与天梯 Fixture 数据。
2. 增加 `GET /api/games/search`、`GET /api/games/{id}/requirements`、`GET /api/ladder`。
3. 重做 Web 工作台布局：顶部导航、装机方案视图、硬件天梯视图、游戏配置查询卡片。
4. 保留原有对话、三套方案、兼容性、替换、锁定、SSE 和 Excel 导出。
5. 补充后端 API/Provider 测试、前端交互测试、响应式和秘密扫描证据。

## 非目标

- 不调用未配置凭证的外部 Steam 服务。
- 不实现网页抓取、验证码绕过、自动购买或第三方站点内容复制。
- 天梯排序仅作为参考，不作为兼容性判定依据。
