# 淘宝 MCP 接入

本项目通过 MCP 标准 stdio 客户端调用外部淘宝 MCP 服务，不复制第三方抓取实现。推荐单独克隆并安装用户指定的 [taobao_mcp](https://github.com/JeremyDong22/taobao_mcp)，再把它的 `server.py` 路径配置给 API。

## 安装外部服务

```powershell
git clone https://github.com/JeremyDong22/taobao_mcp.git
cd taobao_mcp
uv pip install -e .
playwright install chromium
```

首次获取报价时，API 会通过 MCP 调用 `taobao_initialize_login`。如果外部服务要求扫码，请在它打开的浏览器窗口完成登录；没有完成授权时，API 会返回“未获取实时价”，不会把 Fixture 价格冒充真实价格。

## API 配置

复制 `apps/api/.env.example` 为本机未跟踪的 `apps/api/.env`，按实际路径填写：

```env
REALTIME_PRICES_REQUIRED=true
TAOBAO_MCP_ENABLED=true
TAOBAO_MCP_COMMAND=python
TAOBAO_MCP_SERVER_PATH=D:\\tools\\taobao_mcp\\server.py
TAOBAO_MCP_WORKING_DIRECTORY=D:\\tools\\taobao_mcp
TAOBAO_MCP_FETCH_TOOL=taobao_fetch_product
TAOBAO_PRODUCT_URLS_JSON={"zol-gpu-2118113":"https://detail.tmall.com/item.htm?id=123456789012"}
```

`TAOBAO_PRODUCT_URLS_JSON` 是“内部配件 ID → 淘宝/天猫商品 ID 或链接”的映射。淘宝 MCP 是按具体商品引用查询的连接器，不是按关键词自动搜索全站的价格 API；没有映射的型号会标记为“未配置”。

`TAOBAO_MCP_COMMAND` 可以填写 `python` 或虚拟环境 Python 的绝对路径；连接器会通过本项目的 stdout-safe 启动包装器启动配置的 `server.py`。服务端工具名默认是 `taobao_fetch_product`，如果外部服务提供的是兼容旧版本的 `taobao_fetch_product_info`，连接器会自动尝试旧名称，也可修改该变量。

## 数据边界

- 店铺、SKU、商品参数、原价、活动价和采集时间均来自外部 MCP 返回，并经过内部字段校验。
- 只有解析到明确金额的结果才会标记 `is_live=true`；无法解析时显示暂不可用。
- 真实价格仍可能因地区、库存、活动、登录状态或 SKU 变化；页面保留商品链接供人工复核。
- 本项目不实现验证码绕过、账号代采、隐藏浏览器指纹或批量隐蔽抓取。
- 不要把淘宝账号、Cookie、Token 或任何密钥写入仓库。
