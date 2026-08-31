---
title: 商品详情与多平台报价测试报告
type: test-report
status: passed
created: 2026-08-31
---

# 测试报告

## 自动化

- 后端 Ruff：通过。
- 后端 Mypy：30 个源文件无错误。
- 后端 Pytest：26 项通过。
- Alembic：升级到最新迁移成功。
- 前端 lint/typecheck：通过。
- 前端 Vitest：7 项通过。
- 前端生产构建：通过，主 JS gzip 约 92.54 kB。
- 秘密扫描与 `git diff --check`：通过。

## 运行验收

- API 返回 20 个 GPU 候选；商品详情返回 `jd,pdd` 两个平台报价。
- `MPG X870E CARBON MAX WIFI 暗黑` 返回 5 个 M.2 插槽等结构化参数。
- 浏览器点击当前显卡型号后直接打开选配器并显示 20 个候选，当前型号正确定位。
- 商品详情显示平台报价、示例状态、参数、数据来源和使用按钮。
- 375×812 视口无横向溢出，商品详情从页首打开。

## 证据

- `tester/artifacts/product-detail.png`
