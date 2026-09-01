---
title: 输入区过程摘要与社区证据-更新006
type: update
update_number: 6
category: builder-data-quality
status: ready-for-review
update_type: 交互增强与社区证据接入
created: 2026-09-01
plan: "[[../writer/plan|plan]]"
git_branch: feat/15-catalog-sync-filters
base_branch: main
pr_url:
tags:
  - spec
  - update
  - insight
  - community-evidence
---

# 功能更新方案

## 文档关联

- 原设计：[[../writer/plan|设计方案]]
- 前序更新：[[update-005|结构化大模型装机建议]]

---

## 1. 更新背景

### 1.1 问题描述

当前首页输入区只有文本框和“告诉我”按钮。用户提交“想玩星际公民需要什么电脑”这类开放式需求时，看不到需求识别、资料整理、规则校验和最终建议的进展，也看不到大模型结果与依据之间的关系。

当前游戏配置入口主要面向 Steam App ID；《星际公民》由 Cloud Imperium Games 官方渠道提供，不能假设存在 Steam App ID。需要支持非 Steam 游戏标识，并把官方配置要求与社区讨论区分开。

用户希望接入百度贴吧内容作为补充调查来源。社区帖子可能包含个人经验、过时配置、营销信息或相互矛盾的意见，只能作为低可信度参考，不能覆盖官方要求、商品参数或确定性兼容性规则。

### 1.2 外部调查证据

- [Star Citizen 官方 Game and Launcher Requirements](https://support.robertsspaceindustries.com/hc/en-us/articles/360000758928-Game-and-Launcher-Requirements)：公开列出 Windows、AVX/AVX2/FMA3、16GB 以上内存和 SSD 等最低要求，适合作为高可信度配置依据。
- [astron-tieba-mcp PyPI 项目](https://pypi.org/project/astron-tieba-mcp/)：提供 `search_content`、`get_content_detail` 等百度贴吧公开内容工具，支持 `uvx` 启动，说明其面向游客态公开内容且默认不需要认证。
- [social-platform-MCP 的贴吧实现 README](https://github.com/pxc1130/social-platform-MCP/blob/ce17d7c05ea85ae97767ac5e8b607e4f5d249a19/tieba-mcp/README.md)：可作为上述 MCP 的源码参考，但运行时依赖和公开接口稳定性仍需在本机验证。
- [百度贴吧开放 API 页面](https://tieba.baidu.com/tb/zt/tiebaapi/index.html)：说明过单吧内容和精华贴等合作接口，但页面年代较早，不能假设当前账号已获得调用权限。
- [百度贴吧高级搜索](https://tieba.baidu.com/f/search/adv)：可作为无 MCP/无 API 凭证时的人工检索入口，不把搜索结果页面直接当成结构化事实。
- [ModelScope open-webSearch MCP](https://modelscope.cn/mcp/servers/ifzzh520/open-webSearch)：已核对其公开条目与 `search` 工具；本实现固定使用其 npm 包 `open-websearch@2.1.9` 的 stdio 入口，并在服务端筛选贴吧 HTTPS 链接。
- [open-websearch 开源实现](https://github.com/Aas-ee/open-websearch)：用于核对 MCP 工具名、参数和 `MODE=stdio` 启动方式；第三方源码不复制进仓库。
- 调查到的社区示例：[新人想入坑，有几个问题](https://tieba.baidu.com/p/9584659358)、[老滚玩家从星空那边发现这个游戏](https://tieba.baidu.com/p/8590908492)。其中关于 32GB/64GB、CPU/GPU 和帧数的意见存在主观性，必须标记为社区参考，不能替代官方要求。

### 1.3 影响范围

- 首页输入区：增加过程摘要和模型结果预览。
- 游戏配置模型：支持非 Steam 游戏键，并增加“官方/社区/搜索”来源层级。
- 推荐上下文和任务队列：可选读取贴吧公开证据，并把证据安全地交给模型解释。
- API、配置、测试、README 和 `agnet`：增加可选贴吧 MCP sidecar 的配置说明与数据边界。

---

## 2. 更新目标

### 2.1 主要目标

- 在截图所示首页需求输入区下方显示“AI 工作摘要”：
  1. 识别预算、用途、分辨率、品牌和散热偏好；
  2. 查询游戏/官方资料与可选社区资料；
  3. 整理当前候选配件及价格状态；
  4. 执行兼容性硬规则复核；
  5. 生成并展示结构化模型结果。
- 对外展示的是可复现的阶段摘要、输入字段、引用来源、选择理由和不确定项，不展示或保存模型隐藏链式思考、内部 token、原始提示词或原始工具日志。
- 支持“星际公民 / Star Citizen / SC”等输入，载入官方配置要求；因其不是 Steam 游戏，不强行伪造 Steam App ID。
- 增加可选百度贴吧公开证据 Provider：优先通过外部 MCP sidecar 的只读工具检索，未配置时提供百度高级搜索入口；不使用登录态、Cookie、验证码绕过、隐藏反爬或批量隐蔽抓取。
- 将社区证据以低可信度条目展示并传给模型，只能影响解释和待确认项，不能改变配件、价格、功耗或兼容性硬规则。

### 2.2 非目标

- 不显示模型隐藏思考原文，不以“思考过程”名义伪造一段模型内部推理。
- 不把百度贴吧帖子当成官方系统要求、实时商品价格或硬件参数。
- 不实现贴吧发帖、评论、点赞、账号登录、Cookie 注入或验证码/反爬绕过。
- 不把任意 MCP 服务器、任意命令或任意网络地址交给模型；只允许本项目代码定义的只读工具。
- 不在 CI 中依赖贴吧、百度或 Star Citizen 外部网络；Fixture 和人工来源链接仍可完成测试。

---

## 3. 更新方案

### 3.1 输入区结构化过程摘要

文件：`apps/web/src/App.tsx`、`apps/web/src/features/recommendations/`

- 新增 `RequestInsightPanel`（名称可按现有组件约定调整），放在首页 hero 输入表单下方，默认不遮挡输入框。
- 每个阶段只展示状态、短说明和数据来源标签：`待处理`、`进行中`、`已完成`、`待确认`、`失败`。
- 未点击发送时可展示已识别的输入字段；点击“告诉我”后立即进入“识别需求”；生成方案后继续展示资料、规则和模型结果。
- 模型结果采用结构化卡片：结论、推荐定位、关键选择理由、兼容性状态、预算/价格状态、来源和待确认项。详细内容继续复用 `RecommendationCard`，避免两套事实不一致。
- 使用 `aria-live="polite"` 和进度条；错误状态提供重试；小屏下阶段列表可折叠。图标继续使用 Lucide，不用 emoji 代替状态图标。

### 3.2 非 Steam 游戏与官方配置

文件：`apps/api/app/features/games/`、`apps/web/src/App.tsx`、`apps/api/app/domain.py`

- 为 `GameRequirement` 增加可选的来源类型/外部键语义，允许 `rsi:star-citizen` 这类受控非数字标识；Steam Provider 仍只接受数字 App ID。
- Fixture 增加 Star Citizen 官方配置快照和别名，来源链接指向 RSI 官方要求页；缺少的字段保留“未提供”。
- 自然语言识别命中“星际公民”时，需求面板显示“已识别游戏”和“官方最低要求已载入”，可打开游戏详情查看来源。
- 官方配置优先级高于社区内容；不同来源冲突时显示冲突/待确认，不用模型自行裁决硬件兼容性。

### 3.3 百度贴吧证据 Provider

文件：`apps/api/app/features/community/tieba_mcp.py`、`apps/api/app/features/community/service.py`

- 以现有淘宝 MCP 连接器的 stdio 会话模式为参考，封装可选 ModelScope/open-webSearch sidecar。
- 只调用固定工具：`search`；单次查询限制关键词长度、结果数量、响应大小和超时，结果统一为 `CommunityEvidence`。搜索引擎参数由连接器固定为 `baidu`、`bing`，不会由模型动态扩展。
- 默认关闭。未启用或 sidecar 不可用时，不阻塞方案生成；返回“社区资料未取得”和百度高级搜索链接。
- 自动查询词由游戏名和硬件语义组成，例如：`星际公民 电脑配置 CPU 显卡 内存 SSD`。允许用户在设置/高级选项中覆盖查询词，但不把任意 URL 当作工具目标。
- 对标题、摘要、作者、时间和 URL 做字段归一化；对正文长度进行截断，不保存 Cookie、完整响应或原始 MCP 日志。
- 第三方实现中要求 Cookie 的版本不作为默认方案；本连接器不接收或保存 Cookie，任何外部认证配置也不进入项目 API。

### 3.4 推荐上下文与模型结果

文件：`apps/api/app/features/recommendations/schemas.py`、`tools.py`、`providers.py`、`apps/api/app/llm.py`

- 上下文新增社区证据集合和来源等级：官方要求 `high`、目录/商品参数 `medium`、社区帖子 `low`。
- 固定工具新增 `get_community_evidence`，只读取当前查询已归一化的证据；禁止模型直接调用 MCP、百度、数据库或外部 URL。
- Qwen 只负责把已收集事实组织成建议说明，结构化结果继续经过当前方案配件 ID、价格、兼容性和证据引用复核。
- Mock 结果也展示同样的过程摘要和来源状态，保证离线演示不会显示“联网成功”的假象。

### 3.5 API 与任务

- 扩展 `POST /api/plans/{plan_id}/recommendations` 请求体，增加 `community_query` 和 `include_community_evidence` 可选字段，保持旧调用兼容。
- 增加只读 `GET /api/community/search?query=...` 供输入区/高级设置预览社区资料状态；未启用时返回搜索入口和明确的 `unavailable` 状态。
- 建议任务阶段增加“整理官方资料/社区资料”状态；SSE 只发送阶段、进度、来源状态和完成事件，不发送 token、提示词或原始帖子正文。
- 任务失败或社区来源超时时仍完成确定性的硬件建议，并把社区部分标记为“待取得”。

---

## 4. 数据结构与接口

- `GameRequirement`：允许受控外部键；增加 `source_kind` 或等价来源层级字段。
- `CommunityEvidence`：`id`、`title`、`summary`、`url`、`author`、`published_at`、`source`、`confidence`、`status`；不保留完整帖子正文。
- `RecommendationContext`：增加 `community_evidence`，并限制数量、长度和可信度枚举。
- `RecommendationRequest`：增加 `community_query: str | None`、`include_community_evidence: bool`。
- `Recommendation`：证据列表可包含 `kind=community`，但价格和兼容性字段仍由服务端生成。
- `GET /api/community/search` 返回结构化摘要、来源链接、状态和是否启用，不返回 Cookie、MCP 原始响应或隐藏日志。

---

## 5. 实现步骤

- [x] 新增输入区过程摘要组件，并与现有建议任务进度/结果绑定。
- [x] 增加 Star Citizen 官方配置快照、别名识别和非 Steam 外部键校验。
- [x] 增加 ModelScope/open-webSearch 只读 sidecar 适配器、配置项、查询限制和失败降级。
- [x] 扩展建议上下文、Mock/Qwen 提示和来源等级，保证社区证据只能作为低可信度参考。
- [x] 增加 API、队列/SSE、前端状态与无障碍测试。
- [x] 更新 README、`.env.example`、根计划和 `agnet` 证据；不保存内部逐步思考原文、Cookie 或密钥。

## 6. 测试计划

- [x] Star Citizen 别名和非 Steam 标识可识别，Steam 数字 App ID 逻辑不回归。
- [x] 官方/社区来源等级、字段截断和来源链接标准化。
- [x] MCP 未启用、超时、无工具、错误响应时不阻塞建议任务。
- [x] 未知工具名、任意 URL、Cookie/密钥字段和超长正文被拒绝或清理。
- [x] 输入区阶段摘要的加载、完成、失败、离线和键盘/屏幕阅读器状态。
- [x] 社区证据不会改变服务端价格、配件身份、功耗或兼容性结论。
- [x] 后端全量回归、前端类型/单元测试、生产构建和迁移检查。

本机验证还对固定 npm 包完成了启动帮助和 MCP 工具清单核对；直接访问 Baidu/Bing 的搜索请求受当前网络 DNS 策略限制，未把这次失败包装成“已取得实时社区结果”。
异常、超时和取消路径会关闭 stdio 连接；本次实测产生的临时 npx/node 进程已确认退出。

---

## 7. 风险与回滚

| 风险 | 缓解措施 |
|---|---|
| 社区帖子过时或互相矛盾 | 低可信度标记、显示来源和时间；官方要求优先；不参与硬规则计算 |
| 游客态接口风控或不可用 | 默认关闭、超时/数量限制、Fixture/搜索入口降级，不使用绕过手段 |
| 非 Steam 游戏被误当作 Steam | 使用明确外部键和 `source_kind`，Steam Provider 仅接受数字 App ID |
| 用户将过程摘要误认为隐藏思考 | UI 文案明确“可审计过程摘要”，不展示内部推理或原始模型日志 |
| 外部证据污染模型上下文 | 固定字段、长度限制、来源等级、工具白名单和服务端二次校验 |

回滚时关闭 `MODELSCOPE_MCP_ENABLED`，隐藏社区资料入口，保留官方 Fixture、现有建议卡片和确定性兼容性功能；输入区过程摘要可独立保留为本地阶段展示。

---

## 8. 验收标准

- [x] 在首页输入区下方能看到需求识别、资料整理、候选整理、规则复核和结果生成的结构化阶段摘要。
- [x] 输入“想玩星际公民需要什么电脑”能识别 Star Citizen，展示官方最低/推荐配置来源，不要求伪造 Steam App ID。
- [x] 生成完成后能在输入区看到模型结果摘要，并能跳转/展开查看完整 `RecommendationCard`。
- [x] 配置 ModelScope open-webSearch MCP 后可以只读搜索公开帖子；未配置、超时或失败时页面清楚显示未取得，不影响方案生成。
- [x] 贴吧内容带来源、时间/作者（可取得时）和低可信度标识；不能覆盖官方要求、商品参数、价格和兼容性。
- [x] 不展示或保存隐藏思考、原始模型响应、Cookie、Token、任意 MCP 工具调用和未经核验的帖子结论。
- [x] 后端 Ruff、mypy、Pytest、迁移检查与前端类型、单元测试、生产构建全部通过。

#spec/更新
