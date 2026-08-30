# 天梯、手动选配与游戏查询修复

状态：实现完成，PR #12 已创建，等待 GitHub CI 与 squash 合并。

## 需求

- 天梯不再只是静态展示，应支持 CPU/显卡切换、型号搜索、品牌及价格筛选。
- 用户可从天梯或方案配置项进入候选列表，查看规格、排行、参考跑分、百分位、辅助点评和来源，再确认选入。
- 手动选入后重新计算总价与功耗，并执行插槽、内存代际、尺寸、散热、硬盘接口、显卡供电和电源余量检查。
- `warthuder` 等常见拼写应能找到 War Thunder，并展示最低/推荐配置。
- 演示方案不能调用真实导出任务，接口和界面都要返回清晰提示。

## 交互证据与结论

- 公开装机助手样本采用“配置项 → 搜索/品牌/价格候选 → 详情与历史/排行 → 确认使用 → 重算检查”的流程；本项目复用该信息架构，不复制品牌、图片或受保护素材。
- 太平洋电脑网 CPU 天梯用于理解横向比较信息结构：`https://diy.pconline.com.cn/tiantitu/cpu/`。
- Core i5-12600KF 规格核对入口：`https://product.pconline.com.cn/cpu/intel/1447887.html`。
- RTX 4070 系列规格核对入口：`https://product.pconline.com.cn/vga/c22604/`。
- War Thunder 系统需求入口：`https://store.steampowered.com/app/236390/War_Thunder/`。

## 实现决策

- FastAPI 服务层扩展 Fixture 目录、天梯过滤和游戏 Provider；React 通过原有 REST 接口读取数据。
- 规格与点评是结构化参考字段；价格来源继续明确标记 Fixture，避免把规格页误写成实时成交价来源。
- 模型不参与兼容性结论。服务端方案使用规则引擎复核；尚未持久化的演示方案在浏览器端执行同类确定性预检查，并对未知字段显示待确认。
- Steam 联网查询失败时回退 Fixture；加入规范化别名，保证 `warthuder`、`warthunder`、`War Thunder`、`战争雷霆` 和 App ID `236390` 可用。
- 演示 ID 的导出请求在 API 返回 409 `DEMO_PLAN_NOT_PERSISTED`，前端在发请求前给出同义提示。

## 验证证据

- 后端：Ruff、Mypy、21 个 Pytest 全部通过。
- 前端：TypeScript、6 个 Vitest 和生产构建全部通过。
- API 冒烟：`warthuder` 返回 App 236390；Core i5-12600KF 返回完整结构化字段；演示方案导出返回预期 409。
- 浏览器验收：完成天梯筛选、12600KF 详情展示、确认选入、兼容性提示，以及 War Thunder 最低/推荐配置查询。
