# workbuddy.md — WorkBuddy 开发上下文

> 本文件为「麦当劳程序员创意开发大赛」参赛项目的 WorkBuddy 联动奖励核验材料，记录使用 WorkBuddy 完成本 Skill 的开发、联调与发布全过程。
> **数据脱敏声明**：本文件不含任何真实的麦当劳 MCP Token、GitHub Token / PAT、账号凭证或个人敏感信息；涉及密钥处一律以环境变量占位符或「已脱敏」描述。

---

## 1. 项目概述

- **项目名称**：麦当劳优惠券省钱助手
- **项目地址**：https://github.com/tian1326/mcd-coupon-assistant
- **能力基础**：麦当劳中国官方 MCP 服务 `https://mcp.mcd.cn`（Streamable HTTP + Bearer Token，每分钟限 600 次请求）
- **目标**：基于官方 MCP 开发一个 WorkBuddy Skill，帮用户查门店、查券、配菜单、带券算价并比价推荐最省钱组合；默认不自动下单、不自动领券，任何写操作均需用户明确确认。

---

## 2. 开发过程（WorkBuddy 协作记录）

### 2.1 需求对齐
通过 WorkBuddy 的多选提问（AskUserQuestion）与用户确认三项关键决策：
- 主题：优惠券省钱助手（聚焦查券 / 领券 / 带券算价）
- 发布方式：在用户 GitHub 账号下新建公开仓库
- Token 处理方式：Skill 一律从环境变量 `MCD_MCP_TOKEN` 读取，禁止硬编码

### 2.2 调研官方 MCP
- 通过 WebFetch 拉取官方 `M-China/mcd-mcp-server` 仓库，确认：服务地址、传输协议、鉴权头格式、完整工具清单、限流规则。
- 确认核心工具：查询附近门店、查门店券（返回 `couponId`）、查餐品、查餐品详情、带券算价、可用券、自动绑券、我的券、当前时间等共 35 个。

### 2.3 设计并构建 Skill
产出文件（均经 `skill-creator` 校验通过）：
- `SKILL.md`：触发条件、MCP 调用链路、安全规则
- `README.md` / `MCP_INTEGRATION.md`：接入与使用文档、实际工具调用流程与业务价值
- `mcp-config.example.json`：MCP 连接器配置（Token 用 `${MCD_MCP_TOKEN}` 占位）
- `references/`：`coupon_solver.py`（本地候选组合求解器，缩窄算价次数避免触发限流）、`mcd-tools.md`、`coupon_price_guide.md`
- `LICENSE` / `.gitignore`

关键设计点：
- **带券算价边界**：`couponId` 只能来自「查门店券」，算价时 `discount` 为券原价口径，真实省钱 = 菜单原价合计 − `payableTotal`。
- **安全规则**：默认只读工作流，领券 / 下单等写操作强制要求用户明确确认。

### 2.4 只读联调验证
- 使用用户提供的麦当劳 MCP Token（**仅通过环境变量传入、仅在内存中使用，未写入任何文件、未提交到仓库**）对 `https://mcp.mcd.cn` 执行一次只读 `tools/list` 探测。
- 结果：Token 有效，返回 `serverInfo: mcd-mcp 1.0.0`，确认 35 个工具全部可用，服务地址正确。
- 探测脚本用完即删。

### 2.5 发布到 GitHub
- 本地 `git init` 并提交全部文件（不含任何 Token）。
- 使用用户提供的 GitHub PAT（**仅通过环境变量传入，推送后从 `git remote` 地址中清除，未写入文件、未提交**）新建公开仓库 `tian1326/mcd-coupon-assistant` 并推送到 `main` 分支。
- 校验：远程地址无 Token、仓库为 public、默认分支 `main`。

### 2.6 补齐参赛强制文件
- 发现官方报名要求仓库必须包含 `CONTEST_DECLARATION.md`（文件名与内容均不可改动）。
- 从官方 `M-China/mcd-developer-innovation-challenge` 的 `main` 分支逐字下载官方原文加入仓库并推送（commit 见仓库历史），确保内容未被改动。

### 2.7 报名 Issue
- 按官方固定格式生成报名 Issue 的标题与正文纯文本（含项目地址、项目简介，且项目地址不使用 Markdown 链接、项目简介标签与内容同行）。
- 因用户提供的 GitHub Token 为细粒度（fine-grained）类型，无法对第三方仓库 `M-China` 建 Issue（API 返回 403），最终改为用户手动在 `issues/new` 页面粘贴提交。

---

## 3. 数据脱敏说明（必读）

| 敏感项 | 处理方式 |
|---|---|
| 麦当劳 MCP Token | 仅通过环境变量 / 内存用于一次只读 `tools/list` 探测；**从未写入任何文件、从未提交到仓库**；仓库内配置一律使用 `${MCD_MCP_TOKEN}` 占位。 |
| GitHub PAT | 仅通过环境变量传入用于建库 + 推送；**推送后从 `git remote` 地址中清除，从未写入文件或提交**；建议用户用后撤销。 |
| 其他凭证 / 个人信息 | 无。本仓库不含任何真实账号凭证、密钥或个人数据。 |

---

## 4. 如何复现（核验 WorkBuddy 联动）

1. 在 WorkBuddy「连接器」页签接入 `mcd-mcp`（手动配置，填入用户自己的麦当劳 MCP Token）。
2. 将本仓库作为用户级 / 项目级 Skill 导入 WorkBuddy。
3. 对话中输入需求，例如：「帮我用券点一份巨无霸套餐加麦辣鸡翅，怎么最便宜？」，即可触发本 Skill 的查门店 → 查券 → 配菜单 → 带券算价 → 比价推荐工作流。
