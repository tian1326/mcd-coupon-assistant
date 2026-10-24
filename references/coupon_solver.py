#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优惠券候选组合求解器（本地辅助，不算最终价）

作用：把「用户想要的餐品」与「门店可用券(query-store-coupons 返回)」做本地匹配，
产出若干「建议带哪些 couponId 去 calculate-price 算价」的候选组合，
从而减少远程 calculate-price 调用次数、避免触发限流。

注意：
- 本脚本只缩窄候选集，最终价格/优惠/可用性一律以官方 calculate-price 返回为准。
- 它不知道每张券的真实优惠金额（discount 是服务端按券原价口径算的），
  所以只负责「推荐带哪几张券」，不负责「算省了多少」。

输入（stdin, JSON）：
{
  "items":   [ {"code":"P1","name":"巨无霸套餐","price":39.5}, ... ],
  "coupons": [ {"couponId":"C1","title":"省5元","products":["P1","P2"]}, ... ]
}
说明：
- items[].price 单位「元」（与 query-meals 一致）。
- coupons[].products 为该券适用商品 code 列表；为空或缺失表示「全场/订单级券」。

输出（stdout, JSON）：
{
  "candidates": [
    {"label": "不帯券(基线)", "couponIds": []},
    {"label": "每件商品带一张适用券", "couponIds": ["C1","C3"]},
    {"label": "适用券 + 全场券", "couponIds": ["C1","C3","C9"]}
  ],
  "item_coupon_map": { "P1": ["C1","C2"], ... }
}
"""

import json
import sys


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"invalid json: {e}"}, ensure_ascii=False))
        return

    items = data.get("items", []) or []
    coupons = data.get("coupons", []) or []

    # 建立 商品code -> 适用券列表
    item_coupon_map = {it.get("code"): [] for it in items}
    store_wide = []  # 全场/订单级券（无 products 或为空）
    for c in coupons:
        cid = c.get("couponId")
        if not cid:
            continue
        prods = c.get("products") or []
        if not prods:
            store_wide.append(cid)
            continue
        for p in prods:
            if p in item_coupon_map:
                if cid not in item_coupon_map[p]:
                    item_coupon_map[p].append(cid)

    # 候选1：基线（不带券）
    candidates = [{"label": "不帯券(基线)", "couponIds": []}]

    # 候选2：每件商品带第一张适用券（去重，保序）
    per_item = []
    for it in items:
        code = it.get("code")
        applicable = item_coupon_map.get(code, [])
        if applicable:
            first = applicable[0]
            if first not in per_item:
                per_item.append(first)
    if per_item:
        candidates.append({
            "label": "每件商品带一张适用券",
            "couponIds": per_item,
        })

    # 候选3：适用券 + 全场券
    combined = list(per_item) + [c for c in store_wide if c not in per_item]
    if combined and (per_item or store_wide):
        candidates.append({
            "label": "适用券 + 全场券",
            "couponIds": combined,
        })

    # 候选4：仅全场券（无适用券时也有意义）
    if store_wide and not per_item:
        candidates.append({
            "label": "仅全场券",
            "couponIds": list(store_wide),
        })

    out = {
        "candidates": candidates,
        "item_coupon_map": item_coupon_map,
        "store_wide_coupons": store_wide,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
