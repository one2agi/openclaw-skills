---
name: reddit-readonly
description: >-
  Browse and search Reddit in read-only mode using SearXNG web search + PullPush historical API.
  Use when the user asks to browse subreddits, search for posts by topic,
  inspect comment threads, or build a shortlist of links to review and reply to manually.
metadata: {"clawdbot":{"emoji":"🔎","requires":{"bins":["node"]}}}
---

# Reddit Readonly

Read-only Reddit browsing using SearXNG + PullPush.

## ⚠️ Important Note

**Reddit API 在代理环境下不可用**（CAPTCHA 拦截）。本技能使用替代方案：

1. **SearXNG Web 搜索** — 实时内容（`site:reddit.com`）
2. **PullPush API** — 历史存档数据

---

## What this skill is for

- Finding posts in one or more subreddits (hot/new/top/controversial/rising)
- Searching for posts by query (within a subreddit or across all)
- Pulling historical posts and comments
- Producing a *shortlist of permalinks* so the user can open Reddit and reply manually

## Hard rules

- **Read-only only.** This skill never posts, replies, votes, or moderates.
- Be polite with requests:
  - Prefer small limits (5–10) first.
  - Expand only if needed.
- When returning results to the user, always include **permalinks**.

---

## Method 1: SearXNG Web Search（实时内容）

### 搜索命令

```
web_search query="关键词 site:reddit.com" count=10
```

### 搜索策略

| 场景 | 查询方式 |
|------|---------|
| 通用搜索 | `"关键词 site:reddit.com"` |
| 限定子版块 | `"关键词 site:reddit.com/r/productivity"` |
| 限定时间 | `"关键词 site:reddit.com" + 时间过滤` |
| 精确短语 | `"\"精确短语\" site:reddit.com"` |

### 最佳实践

```bash
# 1. 先用通用搜索探查
web_search query="life management system site:reddit.com" count=10

# 2. 根据结果聚焦到特定子版块
web_search query="PARA method productivity site:reddit.com/r/productivity" count=10

# 3. 获取具体帖子内容（用 web_fetch）
web_fetch url="https://www.reddit.com/r/productivity/comments/xxx/..." maxChars=5000
```

---

## Method 2: PullPush API（历史数据）

### API 端点

```
https://api.pullpush.io/reddit/search/submission/?q={关键词}&subreddit={子版块}&size={数量}&after={时间戳}
```

### 命令示例

```bash
# 搜索帖子
node {baseDir}/scripts/reddit-readonly.mjs pullpush posts "life management" --subreddit productivity --limit 10

# 搜索评论
node {baseDir}/scripts/reddit-readonly.mjs pullpush comments "productivity system" --subreddit all --limit 20
```

### PullPush 限制

- ⚠️ 数据有延迟（非实时）
- ⚠️ 不支持全文搜索
- ✅ 适合历史趋势分析

---

## Suggested agent workflow

1. **Clarify scope** if needed: subreddits + topic keywords + timeframe.
2. **判断时效性**：
   - 需要最新讨论 → 用 SearXNG web_search
   - 需要历史数据 → 用 PullPush API
3. Start with web_search using small limits (5-10).
4. For 1–3 promising items, fetch context via `web_fetch`.
5. Present the user a shortlist:
   - title, subreddit, score, created time
   - permalink
   - a brief reason why it matched

---

## Output format

### 搜索结果格式

```markdown
## Reddit 搜索结果：[关键词]

### 来源
- 实时：SearXNG Web 搜索
- 历史：PullPush API

### 帖子列表

1. **[帖子标题]**
   - 子版块：r/xxx
   - 评分：xxx | 评论：xxx
   - 链接：https://www.reddit.com/xxx
   - 摘要：...

2. ...

### 总结
- 共找到 X 条结果
- 最佳资源：...
```

---

## Troubleshooting

- **SearXNG 无结果**：尝试不同关键词，或扩大范围
- **PullPush 无结果**：数据可能未被存档，切换到 SearXNG
- **web_fetch 失败**：Reddit 可能需要登录查看，改为参考搜索摘要

---

## 环境限制说明

Reddit API (oauth.reddit.com) 在代理环境下会被 CAPTCHA 拦截。
这不是认证问题，而是 Reddit 的反爬系统检测到代理出口 IP。
解决方案：使用 SearXNG（搜索引擎代理）+ PullPush（独立存档）。

---

*更新日期：2026-04-17*
*替代方案：SearXNG + PullPush*
