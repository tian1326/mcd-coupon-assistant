# MCP 接入说明

本文档说明「麦当劳优惠券省钱助手」实际使用的麦当劳 MCP Server、Tool、调用流程与业务价值。

## 1. MCP Server

| 项目 | 值 |
|---|---|
| Server 名称 | 麦当劳中国 MCP Server (`mcd-mcp`) |
| 接入地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP |
| 鉴权方式 | 请求头 `Authorization: Bearer <MCP Token>` |
| 官方平台 | <https://open.mcd.cn/mcp> |
| 使用指南 | <https://github.com/M-China/mcd-mcp-server> |
| 频率限制 | 600 次 / 分钟（超限 `429`） |
| 协议版本 | 2025-06-18 及更早 |

## 2. 使用的 Tool 清单

| # | Tool | 用途 | 写操作 |
|---|---|---|---|
| 1 | `now-time-info` | 获取当前时间，判断日期 / 时段 | 否 |
| 2 | `query-nearby-stores` | 查询附近门店，返回 `storeCode`、距离、营业状态 | 否 |
| 3 | `query-store-coupons` | 查询门店可用券，**返回 `couponId` 与适用商品** | 否 |
| 4 | `query-meals` | 拉取门店在售菜单（编码、名称、价格、标签） | 否 |
| 5 | `query-meal-detail` | 查询套餐组成与可替换项 | 否 |
| 6 | `calculate-price` | 计算原价 / 优惠 / 应付（可带 `couponId`） | 否 |
| 7 | `query-my-coupons` | 我的优惠券（不含 `couponId`，仅提示） | 否 |
| 8 | `available-coupons` | 麦麦省可领券列表（不含 `couponId`，仅提示） | 否 |
| 9 | `auto-bind-coupons` | 麦麦省一键领券（写操作，需确认） | 是 |
| 10 | `create-order` | 创建订单（写操作，需确认，本 Skill 默认不调用） | 是 |

> 实测线上 `tools/list` 共 35 个工具（2026-10-24）。其余如 `campaign-calendar`、`query-promotions`、
> `query-my-account`、`order-list`、麦乐送 / 团餐 / 派对 / 商城 / 抽奖等工具不在本 Skill 核心链路内，按需参考官方 README。

## 3. 调用流程

与 `SKILL.md` 的「Workflow」编号一致：

```
now-time-info
   ↓
query-nearby-stores(address)  →  选定 storeCode
   ↓
query-store-coupons(storeCode)  →  拿到 couponId + 适用商品   ← 算价唯一券源
   ↓
query-meals(storeCode)  →  菜单 / 价格 / 编码
   ↓ (套餐需拆解时)
query-meal-detail(productCode)
   ↓
coupon_solver.py（本地）  →  产出候选券组合，缩窄 calculate-price 调用
   ↓
calculate-price(storeCode, items, coupons) × Top-K  →  真实原价/优惠/应付
   ↓
比价 → 选 payableTotal 最低 → 输出推荐
   ↓ (可选, 需确认)
auto-bind-coupons → 重新 query-store-coupons + calculate-price
   ↓ (可选, 需确认)
create-order
```

## 4. 业务价值

- 把「凭经验凑券」变成「数据驱动的比价」：以官方实时菜单价、券适用性、算价结果为唯一真相源。
- 本地求解器只做候选生成，避免对每套餐都远程算价，降低限流风险。
- 明确的写操作边界（领券 / 下单需确认），杜绝误触真实订单。
