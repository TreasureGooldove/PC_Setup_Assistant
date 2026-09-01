---
title: 输入区过程摘要与社区证据-更新006实现摘要
type: update-summary
update_number: 6
category: builder-data-quality
status: ready-for-review
created: 2026-09-01
plan: "[[../writer/plan|plan]]"
update: "[[update-006|update-006]]"
git_branch: feat/15-catalog-sync-filters
base_branch: main
pr_url:
tags:
  - spec
  - update
  - agent
  - community-evidence
---

# 更新总结

## 1. 完成内容

- 首页需求输入区增加“AI 工作摘要”面板，按需求识别、游戏与资料、候选与价格、兼容性复核、生成结论五个阶段展示状态、短说明、来源和进度。
- 面板只展示可核对的结构化摘要，不展示或保存模型隐藏推理、原始模型响应、提示词和 MCP 原始日志；结果可跳转到完整建议卡片。
- 增加 Star Citizen（星际公民）非 Steam 受控标识 `rsi:star-citizen`，载入 RSI 官方最低要求；短别名 `SC` 仅按独立词匹配，避免误识别普通单词。
- 增加 ModelScope `open-webSearch` 可选 stdio 连接器，固定调用 `search` 工具并筛选 `https://tieba.baidu.com` 公开链接，归一化标题、短摘要、作者和时间。
- 社区来源默认关闭；未启用、无结果、超时或连接失败均返回明确状态和人工搜索入口，不阻塞确定性的装机方案生成。
- 推荐上下文、Mock/Qwen 结构化建议和证据卡片增加社区状态；社区证据固定为低可信度，不能改写配件身份、价格、功耗或兼容性规则。
- 增加 ModelScope MCP 配置示例和 Windows/Linux 预检脚本，第三方包不 vendoring，项目不保存 Cookie、Token 或密钥。

## 2. 主要文件

```text
apps/api/app/domain.py
apps/api/app/config.py
apps/api/app/features/community/tieba_mcp.py
apps/api/app/features/community/service.py
apps/api/app/features/recommendations/tools.py
apps/api/app/features/recommendations/schemas.py
apps/api/app/features/recommendations/providers.py
apps/api/app/features/games/providers.py
apps/api/app/features/jobs/service.py
apps/api/app/main.py
apps/api/tests/test_agent_community.py
apps/web/src/features/recommendations/RequestInsightPanel.tsx
apps/web/src/features/recommendations/RequestInsightPanel.test.tsx
apps/web/src/App.tsx
apps/web/src/api.ts
apps/web/src/types.ts
integrations/modelscope-mcp/
README.md
plan.md
```

## 3. 外部调查与实现依据

- 魔搭条目：[ifzzh520/open-webSearch](https://modelscope.cn/mcp/servers/ifzzh520/open-webSearch)。
- 对应开源实现：[Aas-ee/open-websearch](https://github.com/Aas-ee/open-websearch)。
- 固定 npm 包版本：`open-websearch@2.1.9`；已完成本地包审查、帮助命令启动和工具清单核对。
- RSI 官方要求：[Game and Launcher Requirements](https://support.robertsspaceindustries.com/hc/en-us/articles/360000758928-Game-and-Launcher-Requirements)。

本机直接执行 Baidu/Bing 搜索时受到当前 DNS 网络策略限制，因此没有把启动成功或搜索失败包装成实时社区结果；线上启用后仍会通过 `live`/`empty`/`unavailable` 状态如实呈现。

## 4. 验证证据

> [!success]
> 后端 `uv run ruff check app tests`、`uv run mypy app` 和 `uv run pytest --basetemp=...` 通过：66 项测试全部通过。

> [!success]
> 前端 `pnpm.cmd lint`、`pnpm.cmd test` 和 `pnpm.cmd build` 通过：6 个测试文件、23 项测试全部通过，生产构建成功。

- 覆盖 Star Citizen 官方来源和非 Steam 键、`SC` 独立词匹配、社区结果字段截断、HTTPS/贴吧域名过滤、MCP 环境认证字段过滤、禁用降级、上下文注入和 API 路由。
- 覆盖 Agent 摘要面板的五阶段展示、离线模式标识、进度语义和生成按钮回调。
- 历史建议记录缺少新字段时使用兼容性摘要，不影响旧数据库读取。
- MCP 搜索在超时、取消或传输异常后会主动关闭 stdio 连接，实测临时 npx/node 进程已清理。
- 未读取或写入聊天中曾出现的模型密钥；没有提交 `.env`、数据库、Token、Cookie 或第三方依赖缓存。

## 5. 数据与安全边界

- 社区内容只作为低可信度参考，不能覆盖官方配置、商品参数、授权报价和硬件兼容性硬规则。
- MCP 进程只从本机配置启动；连接器只允许 `search` 工具，不接受模型传入的任意命令、URL、Cookie 或认证字段。
- 搜索查询最多 180 个字符，结果最多 8 条，网络调用有超时；只保留公开 HTTPS 贴吧链接和短字段，不保存原始响应。
- Fixture、人工搜索入口和确定性建议是外部网络不可用时的稳定回退。

## 6. 后续事项

- 如需 live 社区摘要，用户在本机安装 Node.js 后执行 `integrations/modelscope-mcp/install.bat` 或 `install.sh`，再在未跟踪 `.env` 中开启 `MODELSCOPE_MCP_ENABLED=true`。
- 如需 Qwen 参与结论，用户只在本机未跟踪 `.env` 配置新密钥，并在服务商控制台确认旧密钥已撤销；当前 CI 和离线演示不依赖模型。
- 本更新当前状态为 `ready-for-review`，未执行提交、推送、PR 或合并。

## 7. 文档关联

- 更新方案：[[update-006|更新方案]]
- 原设计：[[../writer/plan|设计方案]]
- 审查报告：[[../reviewer/update-006-review|审查报告]]

#spec/更新
