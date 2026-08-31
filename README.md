# 智能装机搭子

把“我想装一台电脑”变成一张清晰的方案表。

智能装机搭子是一款本地优先的装机方案助手：填写预算、用途和偏好，或直接用自然语言描述需求，系统就会生成多套可解释配置，展示兼容性、价格参考、功耗和导出清单。

当前版本是可运行的 MVP，默认使用可复现的本地参考数据，适合体验流程、验证规则和继续扩展数据源。

## 快速开始

### Windows 一键启动

在仓库根目录双击 `install.bat` 完成依赖安装，再双击 `start.bat`。启动脚本会分别打开 API、Worker 和 Vite，并打开 `http://localhost:5173/`；关闭它打开的三个终端窗口即可停止服务。

如果系统提示找不到 `uv` 或 `pnpm`，请先安装对应工具，再重新运行脚本。脚本不会创建或读取项目外的密钥文件。

### Linux 一键安装与启动

```sh
chmod +x install.sh start.sh
./install.sh
./start.sh
```

`start.sh` 会在依赖目录不存在时自动调用安装脚本，按 `Ctrl+C` 会同时停止 API、Worker 和前端开发服务器；如果系统安装了 `xdg-open`，还会自动打开本地预览页。

### 后端

```powershell
cd apps/api
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

另开终端启动任务 Worker：

```powershell
cd apps/api
uv run python -m app.worker
```

### 前端

```powershell
pnpm install
pnpm --dir apps/web dev
```

前端默认访问 `http://localhost:5173`，API 默认访问 `http://localhost:8000`。

启动后打开前端页面，填写预算和用途，选择 CPU/GPU 品牌与散热方式，点击“生成三套方案”。API 与 Worker 同时运行时，可以看到实时任务进度并导出 Excel；只启动前端也可以使用内置演示数据。

## 你会拿到什么

- 需求对话：支持预算、用途、分辨率、品牌、散热、噪声、外观和升级需求。
- 三档方案：省心省预算、均衡耐用、高性能释放。
- 装机检查：CPU 插槽、内存代际/容量、主板与机箱尺寸、显卡长度、散热器扣具与空间、冷排尺寸、硬盘接口、显卡供电和电源余量；缺失字段会显示“待确认”。
- 方案操作：点击配置项型号或“换一件”进入选配器，锁定配件、筛选候选并重新计算总价、功耗和兼容性。
- 商品详情：查看完整结构化参数、排行、优缺点、数据状态和信源，并同屏比较京东与拼多多报价。
- 清单导出：生成包含方案概览、配件明细和兼容性检查的 `.xlsx` 文件。
- 硬件天梯：CPU/显卡目录分别提供 15 个以上候选，用型号、品牌和价格筛选 S/A/B/C 档，点击型号可进入手动选配；结构参考 ZOL 天梯，分数为本地归一化结果。
- 游戏配置：按游戏名称、常用别名或 Steam App ID 查询最低配置与推荐配置；默认包含 War Thunder 等本地快照，Steam Store 适配器可选开启。
- 主题切换：默认企业简洁风，可在右上角设置中切换为玻璃拟态或新拟物派。
- 机身大小：可选择自动匹配、ATX、mATX 或 Mini-ITX 小钢炮，方案会同步选择主板与机箱规格。

## 从需求到清单

```text
填写需求 → 结构化解析 → 生成候选方案 → 硬件规则校验 → 查看/替换 → 导出清单
```

模型只参与需求理解和说明；预算计算、配件选择、兼容性判断、任务状态和 Excel 字段均由后端确定性代码校验。

## 配置

复制 `apps/api/.env.example` 为本地 `.env`。Fixture 模式不需要外部密钥；如需启用模型，只在本地配置新的服务商密钥。

```env
LLM_API_KEY=
LLM_API_BASE=https://example.invalid/compatible-mode/v1
LLM_MODEL=qwen3.8-max
STEAM_API_ENABLED=false
STEAM_API_BASE=https://store.steampowered.com/api
JD_PUBLIC_FETCH_ENABLED=false
JD_PRODUCT_URLS_JSON={}
```

`JD_PUBLIC_FETCH_ENABLED` 只控制显式配置的公开京东商品页参数解析。`JD_PRODUCT_URLS_JSON` 使用“内部配件 ID → `https://item.jd.com/<数字>.html`”映射；解析器只读取公开 HTML，不使用登录态、不执行页面脚本、不绕过验证码或反爬。读取失败会回退到结构化目录，并在商品详情中标明状态。

不要把 `.env` 或任何密钥提交到 Git。

## 测试

```powershell
cd apps/api
uv run pytest
uv run ruff check .

cd ../..
pnpm --dir apps/web lint
pnpm --dir apps/web typecheck
pnpm --dir apps/web test
pnpm --dir apps/web build
```

后端还可以运行类型检查和迁移检查：

```powershell
cd apps/api
uv run mypy app
uv run alembic upgrade head
```

## 目录

- `apps/api`：FastAPI、领域服务、SQLite 队列、Provider 和导出。
- `apps/web`：React 对话界面、方案面板和任务实时状态。
- `agnet`：脱敏的 Spec、决策记录、角色定义和验证证据。
- `design-system`：UI 设计系统源文件。
- `plan.md`：本次实现计划。

## 数据来源边界

默认使用可复现的 Fixture 数据。CPU/显卡天梯字段结构参考 [ZOL CPU 天梯](https://cpu.zol.com.cn/soc/) 与 [ZOL 显卡天梯](https://vga.zol.com.cn/soc/)，DIY 参数入口参考 [ZOL DIY](https://diy.zol.com.cn/)；应用内排名和分数是本地归一化值。京东、拼多多示例报价会明确标记“未联网”，点击后需在平台核价。京东联盟、拼多多多多客、淘宝联盟和视频证据能力通过 Provider 接口接入，报价标准化保留平台、SKU、券后预估价、店铺、地区和采集时间。

可选京东公开页解析只允许 HTTPS `item.jd.com` 的数字商品页，设置响应大小、类型、超时和重定向限制；不实现验证码绕过、浏览器指纹伪装、账号滥用或大规模隐蔽抓取。

## 开发约定

- Python API 与 Worker 位于 `apps/api`，React 工作台位于 `apps/web`。
- 任务使用 SQLite 持久化队列，支持幂等、租约、取消、重试、死信和 SSE 进度事件。
- Agent/Spec 的可审计资料统一放在 `agnet/`；根目录 `plan.md` 只保留项目计划摘要。
- 本地密钥只放在未跟踪的 `.env` 中。聊天中曾公开的密钥不应继续使用，应先在服务商控制台撤销并重新生成。

## 当前边界

已有：本地演示、需求对话、三套方案、兼容性规则、持久化 Worker、SSE、生成进度条、导出、扩展硬件天梯、型号直接换件、独立商品详情、京东/拼多多报价状态、受控京东公开参数解析、游戏最低/推荐配置查询和 CI。

预留：京东联盟/拼多多多多客/淘宝联盟真实报价、更多京东商品 ID 映射、Steam Store 更多字段标准化、用户提供的视频字幕或摘要证据、更多硬件规格和多用户存储。

暂不提供：自动购买、验证码绕过、账号登录代采、大规模不稳定网页抓取、隐蔽采集第三方内容。
