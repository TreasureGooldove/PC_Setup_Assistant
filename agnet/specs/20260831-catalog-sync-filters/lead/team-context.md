---
title: 全品类候选与目录同步 Team Context
type: team-context
status: github-flow
git_branch: feat/15-catalog-sync-filters
base_branch: main
issue_url: https://github.com/TreasureGooldove/PC_Setup_Assistant/issues/15
---

# Team Context

## Control

- Spec：`20260831-catalog-sync-filters`
- Issue：https://github.com/TreasureGooldove/PC_Setup_Assistant/issues/15
- 当前阶段：审查已确认，执行提交、CI、PR 与合并

## Task Progress

| 角色 | 状态 | 产物 | completed_at | updated_by |
|---|---|---|---|---|
| spec-lead | done | 本文件与范围控制 | - | spec-lead |
| spec-explorer | done | `explorer/exploration-report.md` | - | spec-explorer |
| spec-writer | done | `writer/plan.md` | - | spec-writer |
| spec-executor | done | `executor/implementation-summary.md` | - | spec-executor |
| spec-tester | done | `tester/test-plan.md` 与 `tester/test-result.md` | - | spec-tester |
| spec-reviewer | done | `reviewer/review.md` | 2026-08-31 11:10 +08:00 | spec-reviewer |
| spec-reviewer | done | `reviewer/update-001-review.md` | 2026-08-31 17:38 +08:00 | spec-reviewer |
| spec-updater | done | `updater/update-002.md` 与 `updater/update-002-summary.md` | 2026-08-31 18:02 +08:00 | spec-updater |
| spec-updater | done | `updater/update-003.md` 与 `updater/update-003-summary.md` | 2026-08-31 | spec-updater |
| spec-reviewer | done | `reviewer/update-003-review.md` | 2026-08-31 | spec-reviewer |
| spec-updater | done | `updater/update-004.md` 与 `updater/update-004-summary.md` | 2026-08-31 | spec-updater |
| spec-reviewer | done | `reviewer/update-004-review.md` | 2026-08-31 | spec-reviewer |
| spec-updater | done | `updater/update-005.md` 与 `updater/update-005-summary.md` | 2026-08-31 | spec-updater |
| spec-reviewer | done | `reviewer/update-005-review.md` | 2026-08-31 | spec-reviewer |
| spec-updater | done | `updater/update-006.md` 与 `updater/update-006-summary.md` | 2026-09-01 | spec-updater |
| spec-updater | done | `updater/update-007.md` 与 `updater/update-007-summary.md` | 2026-09-01 | spec-updater |

## Shared Decisions

- Fixture 是离线、测试和外部来源失败时的稳定底座，每个分类至少 12 个候选。
- 候选同步使用现有 SQLite 任务队列；公开页数据写入独立缓存后与 Fixture 去重合并。
- 只允许代码内固定的 ZOL 产品列表 URL；限制响应体、超时与数量，不携带 Cookie，不跟随重定向。
- 页面先展示本地候选，再显示同步状态；筛选不会等待外部网络完成。
- 兼容性所需字段缺失时标记待确认，外部文本不能覆盖硬规则。
- 淘宝 MCP 作为独立可选 sidecar；具体商品引用来自本机映射，未完成授权或字段解析失败时不生成实时报价。
- ModelScope open-webSearch MCP 作为独立可选 sidecar；仅用于公开社区搜索摘要，固定 `search` 工具和引擎范围；社区证据永远低于官方要求、商品参数和确定性规则。

## Problem Resolution Log

| 状态 | 问题 | 处理 |
|---|---|---|
| resolved | 散热、电源等分类候选太少 | 扩展结构化 Fixture，并允许受控缓存补充 |
| resolved | 外部页面不稳定会阻塞选配 | 队列化后台同步、SQLite 缓存和 Fixture 降级 |
| resolved | 下拉筛选效率低 | 改为品牌与类型/系列快捷筛选，保留搜索和价格区间 |
| resolved | 旧 Worker 不识别新任务类型 | 精确重启本地 Worker；失败状态保持回退候选，README 明确升级后需同步重启 |
| resolved | 同步状态更新时间误当数据采集时间 | 过期判断改用 `captured_at`，排队状态不再伪装为新鲜数据 |
| resolved | 点击生成后缺少即时反馈，用户误以为按钮无效 | 增加显式点击处理、进度状态、完成/失败反馈，并在完成后定位方案工作台 |
| resolved | 预算只能通过滑块调整，无法输入精确金额 | 增加 1 元精度的自定义预算输入、边界提示和统一规范化 |
| resolved | ¥2,500 仍沿用高预算组合，平台金额由目录价比例推导 | 低预算改用兼容的低价候选并明确超预算；京东/拼多多无核验金额时只保留搜索入口和待联网状态 |
| resolved | 用户提供的 ZOL 主板参数页未进入商品详情 | 增加固定路径公开页解析、参数字段归一化和来源证据；页面电商金额仅标记为公开参考价 |
| resolved | 输入“8000元玩战争雷霆的游戏主机”与默认预算/分辨率相同，用户看不出输入是否生效 | 识别 War Thunder 游戏别名，载入最低/推荐配置状态并提供查看入口；初始化默认会话不会覆盖用户刚提交的需求 |
| resolved | 需求已识别并生成方案，但缺少可读的依据说明 | 将需求、游戏、配件、价格和兼容性汇总为固定字段的 AI 辅助建议；模型仅解释当前方案，服务端复核配件身份和事实 |
| resolved | 需求输入区无法核对资料整理过程，且非 Steam 游戏缺少配置入口 | 增加五阶段结构化 Agent 摘要、Star Citizen 官方配置和非 Steam 外部键；社区资料按低可信度独立展示 |
| resolved | 需要公开社区资料补充装机讨论，但第三方 MCP 稳定性和权限边界不明确 | 核对 ModelScope open-webSearch 条目与固定版本工具清单；通过受控 stdio 连接只取贴吧 HTTPS 短摘要，默认关闭并提供失败降级 |
| resolved | 提交需求后需要再次点击生成，且筛选候选变化后报价可能保留旧型号 | 合并顶部提交与生成入口，显式传递最新需求状态；筛选导致默认候选变化时同步刷新报价，并在顶部导航时清理选配弹层 |

## Update 001

| 状态 | 更新 | 处理 |
|---|---|---|
| ready-for-review | 候选详情需要同屏比价与完整参数 | 提取报价组件、加入候选切换竞态保护、展示全部结构化字段并补齐前端测试 |
| ready-for-review | 需要接入淘宝商品实时数据 | 通过 MCP stdio 客户端连接外部服务，支持商品映射、登录初始化、分页和新旧工具名；严格模式拒绝 Fixture 金额 |
| ready-for-review | 详情参数仍不够完整且缺少分组 | 新增八类配件参数 schema 与复用表格；未知字段保留，缺失字段显示待确认；京东和淘宝参数不再因价格缺失而丢弃 |
