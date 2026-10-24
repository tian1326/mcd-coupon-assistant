# 麦当劳优惠券省钱助手 (mcd-coupon-assistant)

一个基于 **麦当劳中国官方 MCP 服务**（`https://mcp.mcd.cn`）的 WorkBuddy Skill，
帮你把一顿麦当劳点到最便宜：查附近门店 → 查券 → 配菜单 → 带券算价 → 比价推荐。

> 本 Skill 只做「省钱比价」，默认**不下单、不自动领券**；任何写操作（领券 / 下单）都需你明确确认。

---

## ✨ 功能

- 🏪 **选门店**：按地址查附近麦当劳，拿到 `storeCode`、距离、营业状态
- 🎟️ **查券**：门店可用券（`query-store-coupons`，含 `couponId` 与适用商品）、账户券、麦麦省可领券
- 🍔 **配菜单**：拉取门店在售菜单，支持套餐拆解与替换（`query-meal-detail`）
- 🧮 **带券算价**：调用官方 `calculate-price` 计算真实原价 / 优惠 / 应付
- 💡 **比价推荐**：本地求解器缩窄候选组合，给出最便宜方案与「省了多少」

## ⚠️ 关键边界（已在联调中确认）

1. **带券算价的 `couponId` 只能来自 `query-store-coupons`**；`query-my-coupons` / `available-coupons` 不返回 `couponId`，不能直接喂 `calculate-price`。
2. **`calculate-price` 的 `discount` 是相对券原价口径**，不等于菜单促销价口径。真实省钱 = 菜单原价合计 − `payableTotal`。
3. **价格单位**：`query-meals` 为「元」（字符串）；`calculate-price` 金额为「分」，展示 ÷100。
4. **限流**：每 Token 600 次 / 分钟，超限返回 `429`。

更完整的坑位清单见 [`references/coupon_price_guide.md`](references/coupon_price_guide.md)。

---

## 🚀 快速开始

### 1. 申请麦当劳 MCP Token

1. 打开 [麦当劳 MCP 开放平台](https://open.mcd.cn/mcp)
2. 右上角【登录】→ 手机号验证登录
3. 进入【控制台】→ 点击激活 → 申请 MCP Token → 复制

> Token 相当于服务访问凭证，**切勿提交到公开仓库或出现在截图里**。

### 2. 在 WorkBuddy 接入麦当劳 MCP

打开 WorkBuddy「管理连接器」→ 自定义配置，加入（参考 [`mcp-config.example.json`](mcp-config.example.json)）：

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

- 客户端支持环境变量插值时，先 `export MCD_MCP_TOKEN=你的Token`；不支持则把占位符替换为真实 Token（并确保该配置文件不进版本库）。
- 添加后**手动启用**连接器，否则工具不可用。

### 3. 导入本 Skill

将本仓库作为用户级或项目级 Skill 放入：

- 用户级：`~/.workbuddy/skills/mcd-coupon-assistant/`
- 项目级：`<项目>/.workbuddy/skills/mcd-coupon-assistant/`

放入后，直接在对话里说：

> 「帮我用券点一份巨无霸套餐加麦辣鸡翅，怎么最便宜？」

Skill 会自动走查门店 → 查券 → 算价 → 推荐 的完整链路。

### 4. 本地验证求解器（可选）

```bash
echo '{"items":[{"code":"P1","name":"巨无霸套餐","price":39.5}],
        "coupons":[{"couponId":"C1","title":"省5元","products":["P1"]}]}' \
  | python references/coupon_solver.py
```

---

## 📂 目录结构

```
mcd-coupon-assistant/
├── SKILL.md                      # Skill 主体：触发条件、调用链路、安全规则
├── README.md                     # 本文件
├── MCP_INTEGRATION.md            # MCP 接入与工具清单、调用流程
├── mcp-config.example.json       # MCP 连接器配置示例（Token 用环境变量）
├── references/
│   ├── mcd-tools.md              # 麦当劳 MCP 工具速查（优惠券方向）
│   ├── coupon_price_guide.md     # 算价边界与坑位清单
│   └── coupon_solver.py          # 本地候选组合求解器
├── .gitignore
└── LICENSE
```

## 🔒 安全与合规

- 遵守麦当劳中国《使用条款》及《麦当劳 MCP 服务规则》。
- 允许个人以**非商业用途**复制使用示例配置 / 代码，仅限连接与使用麦当劳 MCP 服务。
- 未经书面授权，不得用于商业售卖、付费分发、引流变现或暗示官方背书。
- 本项目不构成对麦当劳及其关联方商标的任何授权。

## 🏆 参赛

本项目形态为「WorkBuddy Skill + 麦当劳 MCP」，可参加「麦当劳程序员创意开发大赛」：
- 活动主页：<https://builderx.csdn.net/activity-site/m-code/pages>
- 官方仓库：<https://github.com/M-China/mcd-developer-innovation-challenge>
- MCP 服务仓库：<https://github.com/M-China/mcd-mcp-server>
