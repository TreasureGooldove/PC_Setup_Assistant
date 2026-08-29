# 智能装机搭子 MVP

状态：MVP 已完成（PR #2 已于 2026-08-29 squash 合并到 `main`）；游戏配置、硬件天梯、主题切换与生成进度条 follow-up 见 Issue #4。

## 目标

构建一个面向普通用户的装机方案助手：通过对话收集预算与使用需求，生成多套硬件配置，执行兼容性校验，并支持实时进度与 Excel 清单导出。

## 技术方案

- 前端：React、TypeScript、Vite、TanStack Query、Lucide React。
- 后端：Python 3.13、FastAPI、Pydantic v2、SQLAlchemy、SQLite、httpx。
- 队列：SQLite 持久化任务表 + 独立 Worker；asyncio 处理网络，线程池处理阻塞导出，进程池接口预留给批量评分/视频处理。
- 数据：Fixture 默认启用，京东/拼多多官方适配器预留，禁止验证码绕过和不稳定网页抓取。
- 模型：OpenAI 兼容客户端，环境变量配置 `qwen3.8-max`；没有本地凭证时使用 Mock。
- 实时：SSE 推送任务状态。
- 设计：默认玻璃拟态、可切换新拟物派，响应式布局、键盘可用、`prefers-reduced-motion` 支持；页面信息层级参考公开装机问答产品，不复制其品牌和素材。

## 交付范围

1. 需求对话与结构化 NeedProfile。
2. 节省、均衡、性能三套方案。
3. CPU、主板、显卡、内存、硬盘、电源、散热、机箱等配置项。
4. 插槽、内存代际、尺寸、散热、电源余量等硬规则校验。
5. 配件替换/锁定、报价刷新、方案保存、Excel 导出。
6. SQLite 任务队列、重试、租约、取消、背压、重启恢复和 SSE。
7. 单元、集成、并发与前端构建测试。

## Git 元数据

- `git_branch`: `feat/1-pc-builder-mvp`
- `base_branch`: `main`
- `issue_url`: https://github.com/TreasureGooldove/PC_Setup_Assistant/issues/1
- `pr_url`: https://github.com/TreasureGooldove/PC_Setup_Assistant/pull/2
- `merge_commit`: `51fcb630c6412f12ed41b266a966ad07cb52e9d6`

## 安全边界

对话中曾出现的模型密钥不参与开发，也不写入文件。使用前必须在服务商控制台撤销旧密钥并生成新密钥；新值只放入本地未跟踪的 `.env`。
