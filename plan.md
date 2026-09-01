# 智能装机搭子 MVP

状态：目录同步与结构化建议增强已完成本地验收并通过用户审查确认，正在执行 GitHub Flow（Issue #15）。

## 目标

构建一个面向普通用户的装机方案助手：通过对话收集预算与使用需求，生成多套硬件配置，执行兼容性校验，并支持实时进度与 Excel 清单导出。

## 技术方案

- 前端：React、TypeScript、Vite、TanStack Query、Lucide React。
- 后端：Python 3.13、FastAPI、Pydantic v2、SQLAlchemy、SQLite、httpx。
- 队列：SQLite 持久化任务表 + 独立 Worker；asyncio 处理网络，线程池处理阻塞导出，进程池接口预留给批量评分/视频处理。
- 数据：Fixture 默认启用，京东联盟/拼多多多多客/淘宝联盟适配器预留；报价保留平台、SKU、优惠与时间，不做验证码绕过和大规模隐蔽抓取。
- 模型：OpenAI 兼容客户端，环境变量配置 `qwen3.8-max`；没有本地凭证时使用 Mock。
- 实时：SSE 推送任务状态。
- 设计：默认企业简洁风，可切换玻璃拟态/新拟物派；响应式布局、键盘可用、`prefers-reduced-motion` 支持；页面信息层级参考公开装机问答产品，不复制其品牌和素材。

## 交付范围

1. 需求对话与结构化 NeedProfile。
2. 节省、均衡、性能三套方案。
3. CPU、主板、显卡、内存、硬盘、电源、散热、机箱等配置项。
4. 插槽、内存代际/容量、ATX/mATX/Mini-ITX 尺寸、显卡长度、散热器扣具/空间、硬盘接口、显卡供电、电源余量等硬规则校验。
5. 配件替换/锁定、报价刷新、方案保存、Excel 导出。
6. SQLite 任务队列、重试、租约、取消、背压、重启恢复和 SSE。
7. 单元、集成、并发与前端构建测试。
8. Windows/Linux 一键安装与启动脚手架，自动完成依赖同步、数据库迁移并拉起 API、Worker 和前端。

## Git 元数据

- `git_branch`: `feat/1-pc-builder-mvp`
- `base_branch`: `main`
- `issue_url`: https://github.com/TreasureGooldove/PC_Setup_Assistant/issues/1
- `pr_url`: https://github.com/TreasureGooldove/PC_Setup_Assistant/pull/2
- `merge_commit`: `51fcb630c6412f12ed41b266a966ad07cb52e9d6`

## Follow-up Git 元数据

- `git_branch`: `feat/4-steam-ladder-ui`
- `issue_url`: https://github.com/TreasureGooldove/PC_Setup_Assistant/issues/4
- `pr_url`: https://github.com/TreasureGooldove/PC_Setup_Assistant/pull/5
- `merge_commit`: `8643a7c`

## Current follow-up

- `issue_url`: https://github.com/TreasureGooldove/PC_Setup_Assistant/issues/6
- `branch`: `feat/6-builder-checks-price-sources`
- `scope`: 企业简洁风默认主题、ATX/mATX/Mini-ITX 机身偏好、逐项兼容性检查和多平台报价字段标准化。
- `pr_url`: https://github.com/TreasureGooldove/PC_Setup_Assistant/pull/7
- `merge_commit`: `858ce10`
- `status`: 已完成；CI、后端回归和前端回归均通过。

## Cross-platform bootstrap

- `issue_url`: https://github.com/TreasureGooldove/PC_Setup_Assistant/issues/9
- `scope`: Windows 使用 `install.bat`/`start.bat`，Linux 使用 `install.sh`/`start.sh`；`.bat` 采用 CRLF，`.sh` 采用 LF。
- `status`: 开发中；安装脚本已完成依赖同步与数据库迁移，启动脚本负责 API、Worker、Vite 联动。

## 天梯、手动选配与游戏查询修复

- `issue_url`: https://github.com/TreasureGooldove/PC_Setup_Assistant/issues/11
- `branch`: `feat/11-manual-builder-ladder-games`
- `pr_url`: https://github.com/TreasureGooldove/PC_Setup_Assistant/pull/12
- `scope`: 天梯筛选与可点击选配、配件规格/排行/点评/来源详情、手动替换后的兼容性复核、War Thunder 查询容错，以及演示方案导出保护。
- `data_boundary`: 价格继续使用 Fixture；规格页链接用于人工核对，Steam 系统需求使用可复现快照，联网 Provider 可选启用。
- `status`: 实现、本地回归和 GitHub CI 均已通过；本条记录随 PR #12 squash 合并后视为完成。

## 商品详情与多平台报价

- `issue_url`: https://github.com/TreasureGooldove/PC_Setup_Assistant/issues/13
- `branch`: `feat/13-product-marketplace-details`
- `pr_url`: https://github.com/TreasureGooldove/PC_Setup_Assistant/pull/14
- `scope`: 配置项主体直接换件、扩充 CPU/GPU/主板候选、统一目录天梯、独立商品详情、京东/拼多多报价与受控京东公开页参数解析。
- `data_boundary`: ZOL 天梯和 DIY 作为资料信源；公开页解析默认关闭且只允许 `item.jd.com`，不绕过登录、验证码或反爬；失败时显示 Fixture 与数据状态。
- `status`: 本地验收与 GitHub CI 全部通过；本记录随 PR #14 squash 合并后视为完成。

## 全品类候选与目录同步

- `issue_url`: https://github.com/TreasureGooldove/PC_Setup_Assistant/issues/15
- `branch`: `feat/15-catalog-sync-filters`
- `scope`: 各配件分类至少 12 个稳定候选；品牌、类型/系列、价格区间筛选；固定白名单公开目录的队列化同步、SQLite 缓存和失败回退。
- `data_boundary`: Fixture 始终作为稳定回退；公开目录同步默认开启，只读取固定 ZOL 产品列表页，不携带登录态、不跟随重定向、不绕过验证码或访问控制。
- `status`: 本地实现与用户审查完成，正在提交、推送并等待 GitHub Actions。

## 完整硬件参数详情增强

- `update`: `agnet/specs/20260831-catalog-sync-filters/updater/update-002.md`
- `scope`: 八类配件分组参数 schema、候选/商品详情复用参数表、已采集/待确认统计、京东参数归一化和无价格淘宝参数保留。
- `status`: 本地实现与回归验证完成，待 Spec 审查后进入提交与 CI 流程。

## 淘宝 MCP 与实时价格边界

- `scope`: 候选/商品详情同屏展示平台、金额、店铺、SKU、参数、状态和采集时间；新增可选淘宝 MCP stdio 连接器。
- `data_boundary`: 淘宝 MCP 作为独立 sidecar 使用，按内部配件 ID 映射具体淘宝/天猫商品链接或 ID；只有明确金额通过字段校验后才标记为实时。`REALTIME_PRICES_REQUIRED=true` 时不返回 Fixture 金额。
- `status`: 连接器与解析测试已加入；需要用户在本机安装外部 MCP、完成扫码授权并配置商品映射后才能取得真实淘宝报价。

## 生成方案交互与自定义预算

- `update`: `agnet/specs/20260831-catalog-sync-filters/updater/update-003.md`
- `scope`: 修复生成按钮无即时反馈；增加进度、完成/失败状态、结果定位和 1 元精度的自定义预算输入。
- `status`: 本地实现与前端回归验证完成，等待 Spec 审查确认。

## 预算生效与公开参数来源校准

- `update`: `agnet/specs/20260831-catalog-sync-filters/updater/update-004.md`
- `scope`: 修复 ¥2,500 精确预算在演示/API 生成链路中的传递与低预算选型；移除京东/拼多多按目录价推导的金额、店铺和采集时间；接入受控 ZOL 参数页解析并区分目录参考价、公开页参考价、实时授权报价和待联网；识别“战争雷霆”自然语言需求并载入最低/推荐配置，避免异步初始化覆盖用户输入。
- `evidence`: `agnet/specs/20260831-catalog-sync-filters/updater/update-004-summary.md`
- `status`: 本地实现、真实 ZOL 参数页验证与前后端回归测试完成，等待 Spec 审查和用户确认。

## 安全边界

对话中曾出现的模型密钥不参与开发，也不写入文件。使用前必须在服务商控制台撤销旧密钥并生成新密钥；新值只放入本地未跟踪的 `.env`。

## 结构化模型建议与依据卡片

- `update`: `agnet/specs/20260831-catalog-sync-filters/updater/update-005.md`
- `scope`: 将需求、游戏配置、当前方案、价格状态和兼容性结果整理为可审计的“AI 辅助建议”；提供固定只读上下文工具、可选 Qwen 结构化输出、确定性复核、Mock 降级、队列进度、来源证据和重新生成。
- `data_boundary`: 不展示或保存隐藏思考原文、原始模型响应、提示词、密钥或任意 MCP 执行能力；金额、配件身份和兼容性由服务端事实决定。
- `status`: 本地实现、数据库迁移、后端 59 项测试、前端 21 项测试和生产构建完成，等待 `reviewer/update-005-review.md` 用户确认。

## 输入区过程摘要与社区证据 Agent

- `update`: `agnet/specs/20260831-catalog-sync-filters/updater/update-006.md`
- `scope`: 在需求输入区展示五阶段可审计摘要；支持 Star Citizen 官方配置和非 Steam 标识；可选接入 ModelScope open-webSearch MCP 检索百度贴吧公开摘要，并将低可信度社区证据交给结构化建议流程。
- `agent_flow`: 用户输入 → 受控游戏/社区资料识别 → 本地候选、价格与兼容性整理 → Qwen 或 Mock 结构化解释 → 服务端事实复核 → 输入区摘要与完整建议卡片。
- `data_boundary`: ModelScope MCP 默认关闭，只固定调用 `search` 并保留 HTTPS 贴吧短字段；不接收 Cookie、Token、任意工具或隐藏推理；社区资料不能改写价格、配件身份、功耗和兼容性。
- `external_reference`: ModelScope 条目 `ifzzh520/open-webSearch`，固定 npm 包 `open-websearch@2.1.9`；第三方源码不复制入仓库。
- `status`: 本地实现与回归验证完成；后端 66 项测试、前端 23 项测试、Ruff、mypy、类型检查和生产构建通过，等待 Spec 审查确认；未执行提交、推送或合并。

## 需求提交与可核对方案自动生成

- `update`: `agnet/specs/20260831-catalog-sync-filters/updater/update-007.md`
- `scope`: 合并顶部“告诉我”和生成入口；用户提交非空需求后自动传递最新预算、用途、偏好和游戏识别结果，生成三套方案、结构化建议并定位到方案工作台；参数调整后保留“重新生成并核对”。
- `reference_boundary`: 仅借鉴公开装机问答产品的“提问—答复—依据”逻辑，不复制品牌、素材、文案或接口。
- `status`: 本地实现、前端质量门禁和真实浏览器主流程回归完成；自动生成流程使用本次提交的局部最新状态，筛选切换会同步刷新报价；用户已确认审查，正在执行提交、推送和合并。
