---
name: legal-case-dossier
description: "Civil litigation case preparation tool — generates a structured five-module legal case dossier from raw materials (chat screenshots, transfer records, dialogue text). Activates when user provides case materials and specifies: plaintiff/defendant identity, disputed amount, and core dispute point (e.g., investment vs loan claim). Use for private lending disputes, credit disputes, investment-return disputes, and similar civil cases involving financial evidence analysis."
---

# Legal Case Dossier — 五模块案卷包

## Quick Start

**Trigger:** User provides raw case materials + identity/dispute details.

**Output:** Five-module legal case dossier (起诉状草稿 / 证据册 / 时间轴 / 证据定性分析 / 辩论防御构建)

**Workflow:**

1. Parse materials → identify evidence categories
2. Map timeline (资金往来明细)
3. Build evidence chain (证据链优先)
4. Assess evidence quality (证据三性)
5. Output five modules

## Module Output Structure

| Module | Content |
|--------|---------|
| 模块一 | 起诉状草稿 + 代理词提纲 + 证据清单 |
| 模块二 | 证据册整理（身份/转账/合意/催收） |
| 模块三 | 资金往来表 + Timeline + 关系图 |
| 模块四 | 证据三性评估 + 关键信号提取 |
| 模块五 | 预判抗辩点 + 穿透策略 + 辩护话术 |

## Core Evidence Principles

- **30分钟窗口原则**：单笔转账缺乏直接聊天对应 → 查找转账前后30分钟内对话，或以长期交易习惯推定
- **默示自认识别**：对方仅对还款时间提异议而未否认借款事实 → 构成债务自认，重点标注
- **证据链优先**：聊天提议→转账动作→聊天确认→催款回复，缺一补全
- **去噪原则**：提交法庭时隐私遮盖，但完整记录备查；标注"借、还、息、周转"等定性关键词

## Dispute Type Routing

| 对方主张 | 我方应对 |
|---------|---------|
| 投资论 | 追问有无书面协议/管理参与/利润分红 → "名为投资，实为借贷" |
| 亏损共担论 | 审查有无风险共担协议；主张"保底条款无效，按借贷处理" |
| 旧账论 | 要求对方举证旧账证据链，反向举证 |
| 已还清论 | 逐笔核对还款记录vs本金+利息，找出差额 |

## Key Signal Extraction

- 默示自认语句（对方未否认借贷事实）
- 固定付息行为（民间借贷核心特征）
- 生活化语言 → 法律语言翻译
- 金额吻合度 & 行为一致性分析
- 诚信危机证据（态度变化/失联/对他人欠款）

---

**Detailed workflow and templates:** See `references/case-workflow.md`
