# OpenClaw Skills

Collection of Claude Code skills, workflows and automation patterns for the OpenClaw multi-agent system.

## Structure

```
openclaw-skills/
├── workspace/skills/         # Main skills (25)
├── plugin-skills/             # Plugin skills (8)
├── agents/xingchen/skills/    # Xingchen agent skills (2)
└── agents/moling/skills/      # Moling agent skills (7)
```

## Core Skills (workspace/skills)

| Skill | Description |
|-------|-------------|
| agent-browser-clawdbot | Headless browser automation CLI optimized for AI agents with accessibility tree snapshots and ref-based element selection |
| agent-creator | Guide for creating new OpenClaw agents with proper workspace structure, identity files, configuration, and initial tuning |
| auto-update | Auto-update OpenClaw and skills with OpenClaw cron, per-skill defaults, backups, and migration-aware summaries |
| automation-design | 自动化任务设计方法论。在创建 cron 任务、spawn sub-agent、或设计任何自动化流程之前使用 |
| blog-ops | 博客运维技能（全局共享版），提供完整的博客运营 SOP |
| browser | Puppeteer-based browser automation with multi-step flow support, login checks, tab management, and recovery from stale refs/timeouts |
| gemini-deep-research | Perform complex, long-running research tasks using Gemini Deep Research Agent with multi-source synthesis, competitive analysis, market research |
| gog | Google Workspace CLI for Gmail, Calendar, Drive, Contacts, Sheets, and Docs |
| healthcheck | Track water and sleep with JSON file storage |
| last30days-official | Research what people actually say about any topic in the last 30 days from Reddit, X, YouTube, TikTok, Hacker News, Polymarket, GitHub, and the web |
| marketing-framework | 营销技能框架，基于 AIDA 变体。包含钩子定位、痛点戳刺、信任建立、行动召唤等模块 |
| metacognition-protocol | 元认知协议生成器。当用户提供提示词并要求生成元认知监管协议时使用，生成包含监控规范和创意建议的协议模板 |
| minimax-tts-voice | Use MiniMax speech-02-hd model for high-quality text-to-speech synthesis. Supports 58 Mandarin Chinese + 16 English voices (74 total) |
| multi-source-research | 多源研究助手，整合网页搜索、学术平台（知网/arXiv）、社交媒体（微博/抖音）、新闻聚合。支持自动去重、按来源和可信度分类 |
| n8n | Manage n8n workflows and automations via API. Use when working with n8n workflows, executions, or automation tasks |
| notion-mcp | Notion MCP 集成，通过 MCP 协议连接 Notion 工作区，支持 database 和 page 操作 |
| openclaw-md-guide | OpenClaw 工作区文档机制指南。当需要理解 Bootstrap 文件体系、Context Injection、记忆管理时使用 |
| self-improvement-loop | 每个 agent 都有独立的自我改进反馈循环 — 隔离的 learnings 目录、独立 cron 扫描、绑定到自己的 channel bot 的通知 |
| skill-creator | Guide for creating effective skills. Use when users want to create a new skill (or update an existing skill) |
| skill-improvement | Use when optimizing existing Claude skills, checking skill quality, auditing skill compliance |
| skill-security-auditor | Command-line security analyzer for ClawHub skills. Scan SKILL.md files for malicious patterns, credential leaks, and C2 infrastructure with 20+ detection patterns |
| task-father | Generator for file-based task state machines (registry + task folders + lifecycle state + queue files + cron specs/jobs) |
| task-tracker-pro | Advanced task tracking with directory structure, JSON state persistence, and workflow management |
| windows-docker-wsl2 | Control Windows Docker Desktop from WSL2. Use when needing to list, start, stop, inspect, or manage containers and images |
| xiaohongshu-prompt-generator | 小红书图文生图 Prompt 生成器，支持多种风格和场景的图文内容生成 |

## Plugin Skills (plugin-skills)

| Skill | Description |
|-------|-------------|
| browser-automation | Use when controlling web pages with the OpenClaw browser tool, especially multi-step flows, login checks, tab management |
| doubao-automation | Automate 豆包 (Doubao) AI Chat web interactions — sending messages, clicking the image generation button, typing in the input box, navigating to AI creation pages |
| legal-case-dossier | Civil litigation case preparation tool — generates a structured five-module legal case dossier from raw materials (chat screenshots, transfer records, dialogue text) |
| obsidian-vault-maintainer | Maintain an Obsidian-friendly memory wiki vault with wikilinks, frontmatter, and official Obsidian CLI awareness |
| qqbot-channel | QQ channel management skill. Use qqbot_channel_api to list guilds and channels, inspect members, publish posts, manage announcements |
| qqbot-media | QQBot rich media send and receive support. Use `<qqmedia>` tags to send image, voice, video, or file attachments |
| qqbot-remind | QQBot scheduled reminders. Create, list, and cancel one-time or recurring reminders |
| wiki-maintainer | Maintain the OpenClaw memory wiki vault with deterministic pages, managed blocks, and source-backed updates |

## Agent-Specific Skills

### Xingchen Agent (agents/xingchen/skills)

| Skill | Description |
|-------|-------------|
| bilibili-summarizer | Summarize video content from Bilibili/B站, Douyin/抖音, YouTube, Xiaohongshu/小红书. Extract subtitles, evaluate information density, supports local video files |
| wechat-article-reader | Use when user shares a WeChat public account article link, searches/lists articles by account name, queries trending articles by keyword |

### Moling Agent (agents/moling/skills)

| Skill | Description |
|-------|-------------|
| gemini-deep-research | Perform complex, long-running research tasks using Gemini Deep Research Agent with multi-source synthesis, competitive analysis, market research |
| in-depth-research-1-0-0 | Conduct exhaustive multi-source investigation with methodology tracking, source evaluation, and iterative depth |
| market-research | Research markets with sizing, segmentation, competitor mapping, pricing checks, and demand validation. Use for TAM, SAM, SOM, whitespace, competitor analysis |
| multi-source-research | 多源研究助手，整合网页搜索、学术平台（知网/arXiv）、社交媒体（微博/抖音）、新闻聚合。支持自动去重、按来源和可信度分类 |
| reddit-readonly | Reddit read-only access for research and content gathering |
| report-searcher | 搜索权威行业报告、白皮书、PDF 文件的专用 skill。使用 SearXNG 搜索引擎配合高级搜索运算符精准定位 Deloitte、麦肯锡、艾瑞咨询、政府统计等权威机构的报告 |

---

## Usage

Skills are invoked using the `/` command or via the Claude Code skill system:

```
/skill-name
```

Example:
```
/bilibili-summarizer
/multi-source-research 研究量子计算市场
```

## License

MIT
