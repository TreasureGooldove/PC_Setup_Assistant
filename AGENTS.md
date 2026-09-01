# 智能装机搭子

面向普通用户的装机方案助手，支持需求对话、配件建议、兼容性校验和清单导出。

## 项目身份

- 技术栈：Python 3.13 / FastAPI / SQLite / React / TypeScript / Vite
- 类型：全栈 Web 应用
- 工作流：GitHub Flow + Spec 驱动开发

## 规则入口

- 长期规则与脱敏记录：`agnet/`
- 当前 Spec：`agnet/specs/20260831-catalog-sync-filters/`
- 根目录 `plan.md`：本次实现计划

## 开发约束

- 业务逻辑放在服务层，HTTP 层只做校验和编排。
- 外部数据默认使用 Fixture；可选同步只读取固定白名单公开产品页或官方接口，不使用登录态，也不绕过验证码、访问控制或反爬。
- 所有模型输出必须经过 Pydantic 和确定性规则复核。
- 不提交 `.env`、数据库、Token、密钥或真实用户隐私。
