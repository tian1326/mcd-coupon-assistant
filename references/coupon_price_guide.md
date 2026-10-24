# 优惠券算价边界与坑位清单

本文件沉淀联调中确认的接口边界，避免「凭常识猜格式」导致算错价。所有结论以官方 `mcp.mcd.cn` 实时返回为准。

## 1. couponId 的来源

| 接口 | 是否返回 couponId | 能否直接用于 calculate-price |
|---|---|---|
| `query-store-coupons` | ✅ 返回 `couponId` + `products[].productCode` | ✅ 可以 |
| `query-my-coupons` | ❌ 仅标题 / 有效期 / 状态 / 标签 | ❌ 不行 |
| `available-coupons` | ❌ 同上 | ❌ 不行 |

**结论**：要「带券算价」，必须先调 `query-store-coupons` 拿 `couponId` 与适用商品。`query-my-coupons` / `available-coupons` 仅用于告知用户「已有哪些券 / 可领哪些券」。

## 2. discount 口径 ≠ 省了多少

`calculate-price` 返回的 `discount` 字段是相对**该券的原价口径**（`productOriginalPrice`，单位分）计算的，不是相对于菜单促销价。

示例（实测）：
- 冰美式中杯：菜单促销价 1190 分（11.9 元），`productOriginalPrice` 2300 分（23.0 元）
- 带券后 `discount` = 1310 分

若直接把 `discount`(13.1 元) 当作「省了 13.1 元」，会严重高估优惠。

**正确算法**：
```
真实省钱 = 菜单原价合计(元) − payableTotal(元)
其中 payableTotal 来自 calculate-price 的应付总价
```

## 3. 价格单位

- `query-meals` 返回的价格：单位**元**，常为字符串（如 `"39.5"`），使用前转 float。
- `calculate-price` 返回的金额字段：单位**分**（整数），展示前 ÷100。
- 不要混用两套单位做加减。

## 4. 套餐替换规则

- 套餐替换只能发生在**同一个 `round` 的候选项**内（来自 `query-meal-detail`）。
- 「去酱」通过 `modification` 传递；「可乐换无糖」属同轮零加价替换。
- 不要假设「薯条能换成玉米杯」之类跨轮替换——以接口返回为准。

## 5. 限流与重试

- 每 Token 600 次 / 分钟，超限返回 `429`。
- 批量 `calculate-price` 时只取 Top-K（≤3）候选，控制间隔；遇 `429` 降速后重试。

## 6. 写操作保护

- `auto-bind-coupons`（领券）、`create-order`（下单）均为**真实写操作**。
- 必须等用户**明确确认具体动作**后再调用；本 Skill 不自动领券、不自动下单。
