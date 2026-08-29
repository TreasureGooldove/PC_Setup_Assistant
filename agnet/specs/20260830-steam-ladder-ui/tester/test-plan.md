---
title: 游戏配置与硬件天梯测试计划
type: test-plan
status: completed
created: 2026-08-30
git_branch: feat/4-steam-ladder-ui
---

# 测试计划

## 后端

- 验证 `GET /api/ladder` 的 CPU/GPU 分类、档位和排序字段。
- 验证游戏名称/App ID 搜索、最低配置和推荐配置结构化返回。
- 验证 Steam Provider 默认停用，不配置外部服务时仍可使用 Fixture。
- 运行 Ruff、mypy 和 Pytest，确保新领域类型不破坏既有队列、兼容性和导出测试。

## 前端

- 验证默认进入配置方案视图，能够切换硬件天梯、游戏配置和主题。
- 验证游戏配置搜索结果、最低/推荐配置双列和本地降级数据。
- 验证生成方案时显示百分比、阶段文字和 `role=progressbar` 属性。
- 验证 375px 响应式布局、键盘焦点和 reduced-motion 规则不引入横向滚动。

## 交付检查

- 运行前端测试、类型检查和生产构建。
- 扫描仓库中的密钥、`.env`、数据库和构建产物。
- CI 通过后再创建 PR、squash 合并并清理功能分支。
