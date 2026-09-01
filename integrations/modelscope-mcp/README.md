# ModelScope 公开检索 MCP

本目录提供“智能装机搭子”可选的公开资料检索连接。魔搭社区中实际核对的条目是 [open-webSearch](https://modelscope.cn/mcp/servers/ifzzh520/open-webSearch)，其对应的开源实现为 [Aas-ee/open-websearch](https://github.com/Aas-ee/open-websearch)，本项目按固定版本 `open-websearch@2.1.9` 通过 MCP stdio 调用。

仓库只保存配置示例和安装脚本，不复制第三方源码、`node_modules` 或缓存。MCP 结果只用于补充百度贴吧等公开页面的检索摘要，不能替代官方硬件参数、平台报价或兼容性规则。

## 安装与预检

先安装 Node.js 18+，然后在本目录执行对应脚本：

```powershell
.\install.bat
```

```sh
./install.sh
```

脚本会通过 npm 预取固定版本并执行帮助命令，确认本机能启动 MCP。它不会写入项目依赖目录，也不会要求账号、Cookie 或 API Key。首次运行 `npx` 可能需要访问 npm 镜像；网络受限时可改用企业允许的 npm registry。

## API 配置

复制 `apps/api/.env.example` 为本机未跟踪的 `apps/api/.env`，Windows 建议使用 `npx.cmd`：

```env
MODELSCOPE_MCP_ENABLED=true
MODELSCOPE_MCP_COMMAND=npx.cmd
MODELSCOPE_MCP_ARGS_JSON=["-y","open-websearch@2.1.9"]
MODELSCOPE_MCP_ENV_JSON={"MODE":"stdio","ALLOWED_SEARCH_ENGINES":"baidu,bing"}
MODELSCOPE_MCP_TIMEOUT_SECONDS=18
COMMUNITY_SEARCH_MAX_RESULTS=5
```

Linux/macOS 使用 `MODELSCOPE_MCP_COMMAND=npx`。API 会复用一个受锁保护的 stdio 会话，并只调用名称为 `search` 的工具，参数中的搜索引擎固定为 `baidu` 和 `bing`；不会把任意 MCP 工具暴露给模型。首页生成建议和 `GET /api/community/search` 都会显示来源状态。

配置完成后分别重启 API 和 Worker。建议先打开：

```text
http://localhost:8000/api/community/search?query=星际公民%20电脑配置
```

若返回 `live`，页面会展示短摘要和原帖链接；若返回 `disabled`、`empty` 或 `unavailable`，仍可使用百度贴吧高级搜索入口，方案生成不会失败。

## 数据与安全边界

- 只读取公开搜索结果，只保留 `https://tieba.baidu.com` 链接、标题、短摘要、作者和时间（能取得时）。
- 单次查询最多 180 个字符、8 条结果，网络调用有超时；超时和风控只会降级为未取得。
- 社区结果统一标记为低可信度，不能改变价格、配件身份、功耗或兼容性硬规则。
- 不使用登录态、Cookie、验证码绕过、浏览器指纹伪装或大规模隐蔽抓取。
- `MODELSCOPE_MCP_ENV_JSON` 仅允许非认证运行参数；项目会过滤名称包含 key、token、secret、cookie、password、auth 的字段。
- 不要把任何密钥、Cookie、代理账号或真实用户隐私写入仓库。

已对固定 npm 包执行本地启动和工具清单核对；具体搜索能否返回结果仍取决于本机 DNS、网络出口和第三方页面可用性，因此不能把“启动成功”当成“实时数据必然可得”。
