# 价格来源与推荐方法调研记录

日期：2026-08-30

## 小程序现场证据

- 配件列表支持关键词、价格区间和品牌筛选；CPU 详情包含商品图、规格字段、价格变化和“加入对比/使用”入口。
- 价格历史支持 90 天、180 天和一年视图。当前检查到的曲线图例为“京东”，详情页显示“价格更新于：刚刚”，并提供京东购物入口。
- 详情页同时提示购物小程序中的实际到手价可能变化；保存的主机记录还会显示加入时价格与当前价格的涨跌差。
- 本次检查未看到拼多多或淘宝被标注为当前报价来源，因此不能把它们默认为已接入。

## GitHub 公开实现参考

- [SenQi-666/jd-union-sdk](https://github.com/SenQi-666/jd-union-sdk)：Python 社区 SDK 示例，展示京东联盟的 `jd.union.open.category.goods.get`、关键词和分页参数。代码较旧，只作为字段/调用形态参考。
- [yangxiaozhan/shopunion_sdk](https://github.com/yangxiaozhan/shopunion_sdk)：社区多平台封装，展示淘宝 `materialSearch`、拼多多 `materialSearch`、京东 `materialSearch` 及各自的详情/转链方法，并要求平台凭证和推广位。
- [biheto/ValuSee](https://github.com/biheto/ValuSee)：更值得借鉴的是流程设计：区分商品匹配、SKU 匹配、价格和监督步骤；价格记录保留平台、SKU、时间、地区、优惠条件和用户确认状态，LLM 只做解释。
- [dtapps/pinduoduo](https://github.com/dtapps/pinduoduo)：展示拼多多多多客详情字段，如 `goods_sign`、`min_group_price`、`min_normal_price`、券字段和店铺信息。拼多多金额字段按分处理，接入时必须显式换算。
- [makelove/Taobao_topsdk](https://github.com/makelove/Taobao_topsdk)：旧版淘宝联盟 Python 示例，提供 `zk_final_price`、`reserve_price`、`volume` 等字段名称参考，不直接复制其 SDK。

官方文档入口：

- [京东联盟开放平台](https://union.jd.com/openplatform/api)
- [拼多多开放平台](https://open.pinduoduo.com/#/apidocument)
- [淘宝开放平台](https://open.taobao.com/api.htm?docId=24515&docType=2)

## 结论与实现边界

1. 报价源使用 Provider 分层：`fixture` 默认可用；京东、拼多多、淘宝分别保留适配器，不把平台 SDK 细节散落在方案服务里。
2. 内部报价统一记录平台、SKU/商品标识、原价、活动价、券后预估到手价、店铺、地区、链接、采集时间、来源状态和优惠说明。
3. 推荐价不是简单取全局最低值：先过滤 SKU/规格不确定、过期、地区不符和兼容性不通过的报价，再按券后价、来源新鲜度、SKU 完整度和可追溯性排序；硬件兼容性规则优先于价格排序。
4. 平台凭证不完整时适配器保持停用并回退 Fixture，不伪造“实时价”。公开商品页的人工确认数据可以作为低置信度报价，但必须标注来源、时间和“实际成交价以商品页为准”。
5. 不实现验证码绕过、账号登录代采、批量隐蔽抓取或自动下单；这不是报价推荐的必要能力，也会破坏数据可追溯性。

## 当前代码落点

- `apps/api/app/domain.py` 的 `Offer` 已支持平台、SKU、原价/活动价/券后价、店铺、地区和采集时间。
- `apps/api/app/features/builds/price_sources.py` 提供 JD/PDD/Taobao 字段标准化、金额单位换算和凭证完整性检查；它不发起真实平台请求。
- `apps/api/.env.example` 只提供本地变量名示例，不包含任何凭证。
- 后续接入真实 Provider 时，应先补充响应回放 fixture、金额和 SKU 校验、限流/重试、报价过期策略和集成测试，再开放到刷新报价任务。
