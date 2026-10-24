# 麦当劳中国 MCP 工具速查（优惠券 / 算价方向）

服务地址：`https://mcp.mcd.cn`（Streamable HTTP，`Authorization: Bearer <token>`）
调用名前缀（WorkBuddy 内）：`mcp__mcd-mcp__`
实测工具总数：35（2026-10-24 对线上服务 `tools/list` 实测；随版本推进可能变化，以线上为准）

## 本 Skill 直接使用的工具

| Tool name | 用途 | 写操作 |
|---|---|---|
| `now-time-info` | 获取当前完整时间信息，用于判断日期 / 时段 / 活动是否进行中 | 否 |
| `query-nearby-stores` | 按地址查询附近可用门店，返回 `storeCode`、距离、营业状态 | 否 |
| `query-store-coupons` | 查询指定门店下可用券列表，**返回 `couponId` 与 `products[].productCode`** | 否 |
| `query-meals` | 拉取门店在售菜单：分类、餐品 `productCode`、名称、价格（元，字符串）、标签 | 否 |
| `query-meal-detail` | 查询餐品详情 / 套餐组成 / 可替换项（用于套餐拆解与替换） | 否 |
| `calculate-price` | 根据选购商品列表（可含 `couponId`）计算原价、优惠、应付总价 | 否 |
| `query-my-coupons` | 我的优惠券查询（账户下全部可用券），**不返回 `couponId`** | 否 |
| `available-coupons` | 麦麦省可领取优惠券列表，**不返回 `couponId`** | 否 |
| `auto-bind-coupons` | 麦麦省一键领券（自动领取所有可领券），**写操作** | 是 |
| `create-order` | 创建订单（真实写操作），本 Skill 默认不调用 | 是 |
| `query-survey-coupon` | 按订单号查询满意度答卷及关联奖券 | 否 |

## 相关性较低（本 Skill 可忽略或按需使用）

- `campaign-calendar`：当月营销活动日历（联名 / 限定），可用于判断是否叠加活动。
- `query-promotions`：促销查询。
- `query-my-account`：积分查询。
- `order-list` / `query-order` / `cancel-order`：历史 / 详情 / 取消订单。
- 麦乐送 / 团餐 / 派对 / 商城 / 抽奖 等工具（`delivery-*`、`query-party-*`、`mall-*`、`*lottery*`）：超出省钱比价范围，按需参考官方 README。

## 关键边界

1. **带券算价的 `couponId` 只能来自 `query-store-coupons`**；`query-my-coupons` / `available-coupons` 没有 `couponId`，不能直接喂 `calculate-price`。
2. **`calculate-price` 的 `discount` 是相对券原价口径**，不等于菜单促销价口径。真实省钱 = 菜单原价合计 − `payableTotal`。
3. **价格单位**：`query-meals` 为「元」（字符串）；`calculate-price` 金额字段为「分」，展示 ÷100。
4. **限流**：600 次 / 分钟，超限 `429`；批量算价控制并发。
