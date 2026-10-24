---
name: mcd-coupon-assistant
description: |-
  This skill helps users find, claim, and optimally combine McDonald's China
  coupons to get the lowest price for a meal, powered by the official McDonald's
  MCP server (mcp.mcd.cn). Use it when a user asks how to order McDonald's most
  cheaply, wants to apply McDonald's coupons, or wants to compare coupon
  combinations before ordering. Trigger phrases include "麦当劳优惠券",
  "怎么点麦当劳最便宜", "帮我用券点餐", "麦当劳怎么省钱", "麦当劳套餐优惠",
  "附近麦当劳有什么券". It queries nearby stores, lists store / account /
  claimable coupons, matches coupons to the menu, calls calculate-price to
  compute real discounted totals, and recommends the cheapest combination. It
  never places an order or claims coupons without explicit user confirmation.
agent_created: true
---

# 麦当劳优惠券省钱助手 (McDonald's Coupon Saving Assistant)

## Purpose

帮助用户用麦当劳中国官方的优惠券，把一顿麦当劳点到最便宜。Skill 只负责「查门店 → 查券 → 配菜单 → 带券算价 → 比价推荐」，最终的下单 / 领券动作默认不做，必须用户明确确认才执行。所有实时菜单、价格、优惠、券状态都以官方 MCP 接口返回为准。

## When to use

用户出现以下意图时加载本 Skill：

- 询问「麦当劳怎么点最便宜 / 怎么省钱 / 有什么优惠」
- 想用券点餐：「帮我用券点一份巨无霸套餐」「附近麦当劳有什么券」
- 想比较不同券组合的价格
- 参加「麦当劳程序员创意开发大赛」中「优惠券 / 省钱」方向的作品

若用户只是想直接下单、看营养、或玩抽卡，引导到对应 Skill（如下单助手、营养私教、抽卡机），本 Skill 聚焦省钱比价。

## Prerequisites

本 Skill 依赖已在 WorkBuddy 中接入的麦当劳 MCP 连接器（server 名 `mcd-mcp`）。接入方式见仓库 `README.md` 与 `MCP_INTEGRATION.md`。要点：

- MCP 服务地址：`https://mcp.mcd.cn`（Streamable HTTP）
- 鉴权：`Authorization: Bearer YOUR_MCP_TOKEN`，Token 从 `https://open.mcd.cn/mcp` 申请
- **Token 一律从环境变量 `MCD_MCP_TOKEN` 读取，禁止硬编码进任何文件或提交到仓库**
- 频率限制：每个 Token 每分钟最多 600 次请求，超限返回 `429`，调用时控制节奏

## MCP connection (config reference)

WorkBuddy 的 `~/.workbuddy/mcp.json` 中加入（详见 `mcp-config.example.json`）：

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": {
        "Authorization": "Bearer ${MCD_MCP_TOKEN}"
      }
    }
  }
}
```

若客户端不支持 `${MCD_MCP_TOKEN}` 插值，则把占位符替换为真实 Token（并确保该文件不进版本库）。连接器添加后需手动启用，否则工具不可用。

## Workflow (tool call chain)

按以下顺序编排 MCP 工具调用，顺序不要随意调换——菜单和价格依赖门店与时段，券匹配与算价必须等候选餐品确定后再做。

1. **`now-time-info`** — 获取当前日期 / 时间 / 时段（早市 / 午市 / 晚市 / 夜市），用于判断活动是否进行中、是否影响套餐可用性。
2. **确定门店 `storeCode`**
   - 若用户给了城市 / 地址 / 门店名 → 调用 `query-nearby-stores(address)` 拿到候选门店列表（含 `storeCode`、距离、营业状态）。
   - 若未给 → 先向用户询问位置或默认一个附近门店；拿到 `storeCode` 后再继续。
3. **`query-store-coupons(storeCode)`** — 查询该门店下**可用券列表**。这是唯一能拿到 `couponId` 与 `products[].productCode`（券适用商品）的来源，算价必须用这里的 `couponId`。
4. **`query-my-coupons()`** — 查询账户下已有券（标题 / 有效期 / 状态）。注意：该接口**不返回 `couponId`**，不能直接喂给 `calculate-price`，仅作「你已有哪些券」的提示。
5. **`available-coupons`** — 查询麦麦省当前可领取的券列表（同样不返回 `couponId`，仅提示可领）。如需领取，走 `auto-bind-coupons`（写操作，见安全规则）。
6. **`query-meals(storeCode)`** — 拉取该门店在售菜单：分类、餐品 `productCode`、名称、价格（单位**元**，常为字符串）、标签。
   - 若涉及套餐且需要拆解 / 替换，调用 `query-meal-detail(productCode)` 获取套餐 `rounds` 与可替换项。
7. **本地匹配（可选）** — 把用户想要的餐品与第 3 步的门店券喂给 `references/coupon_solver.py`，让它产出「每件商品适用哪些券、建议带哪几张券去算价」的候选组合，减少远程 `calculate-price` 调用次数。本地求解只缩窄候选集，**不算最终价**。
8. **`calculate-price`** — 对候选组合逐一调用：传入 `storeCode`、选购商品列表（可含 `couponId`）。返回 `originalPrice`（原价）、`discount`（优惠）、`payableTotal`（应付）。**只取 Top-K 候选（建议 ≤3）调用，避免触发限流。**
9. **比价与推荐** — 选 `payableTotal` 最低的方案。省钱金额 = 菜单原价合计 − `payableTotal`（见下方边界）。
10. **（可选）领取更多券再算** — 若想进一步省钱，可建议用户领取麦麦省券（`auto-bind-coupons`，**写操作，需明确确认**），领完重新执行第 3 步与第 8 步。
11. **（可选）下单** — 本 Skill 默认不下单。若用户明确要下单，提示其使用下单助手或在确认后调用 `create-order`（**真实写操作，必须用户明确确认**）。

## Critical boundaries (must follow)

- **`couponId` 只来自 `query-store-coupons`**：`query-my-coupons` 与 `available-coupons` 只给标题 / 有效期 / 状态 / 标签，**没有 `couponId`**，无法喂给 `calculate-price` 的券入参。要「带券算价」必须先调 `query-store-coupons`（顺带拿到 `products[].productCode` 知道券适用于哪些商品）。
- **`discount` 口径不是「省了多少」**：`calculate-price` 返回的 `discount` 是相对该券的**原价口径**（`productOriginalPrice`）算的，不等于菜单促销价口径。例如冰美式中杯 `productOriginalPrice` 2300 分 vs 菜单促销价 1190 分，`discount` 1310 分不能直接当成「省了 13.1 元」。正确做法：用「菜单原价合计 − `payableTotal`」作为真实省钱金额。
- **价格单位**：`query-meals` 返回价格单位是**元**（字符串）；`calculate-price` 返回金额字段单位是**分**，展示时必须 ÷100 转成元。
- **套餐替换只能在同一 `round` 的候选项内进行**；「去酱」通过 `modification` 传，「可乐换无糖」属同轮零加价替换。不要凭商品常识臆测替换关系，以 `query-meal-detail` 返回为准。
- **`create-order` 是真实写操作**，只有用户明确确认后才能调用；本 Skill 不自动下单。
- **限流**：600 次 / 分钟，批量算价时控制并发与间隔，拿到 `429` 就降速重试。

## Safety rules

- 绝不调用 `create-order` 或 `auto-bind-coupons` 之类的写操作，除非用户**明确确认**具体动作。
- 绝不把 MCP Token 写进任何文件或提交到公开仓库；统一从环境变量读取。
- 所有价格、优惠、券状态以官方实时接口（`calculate-price` / `query-store-coupons`）返回为准，本地脚本仅是辅助候选生成。
- 不暗示官方背书，不用于商业售卖或引流变现（遵守麦当劳 MCP 服务条款）。

## Output format

推荐结果用简洁表格呈现：

```
门店：<storeName> (<distance>, <营业状态>)
┌──────────────┬─────────┬──────────────┬─────────┐
│ 商品         │ 单价(元)│ 适用券        │ 小计(元)│
├──────────────┼─────────┼──────────────┼─────────┤
│ 巨无霸套餐   │ 39.5    │ 省5元券       │ 34.5    │
│ 麦辣鸡翅(2)  │ 12.0    │ —            │ 12.0    │
└──────────────┴─────────┴──────────────┴─────────┘
原价合计：51.5 元   优惠：5.0 元   应付：46.5 元   省钱：5.0 元
提示：还可领取麦麦省券 X 张，领完可能更便宜（需你确认）。
```

并附上「下一步」选项：领取更多券 / 换门店比价 / 确认下单。
