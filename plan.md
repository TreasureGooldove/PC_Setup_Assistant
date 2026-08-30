# 智能装机搭子 MVP

状态：已完成（MVP 的 PR #2、follow-up 的 PR #5，以及检查/报价增强的 PR #7 均已 squash 合并到 `main`）。

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
- `status`: 实现和本地回归已完成，PR #12 已创建，等待 CI 与 squash 合并。

## 安全边界

对话中曾出现的模型密钥不参与开发，也不写入文件。使用前必须在服务商控制台撤销旧密钥并生成新密钥；新值只放入本地未跟踪的 `.env`。
