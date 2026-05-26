# OpenClaw Skills

Collection of Claude Code skills, workflows and automation patterns for the OpenClaw multi-agent system.

## Structure

```
openclaw-skills/
├── workspace/skills/         # Main skills (25)
├── plugin-skills/           # Plugin skills (9)
├── agents/xingchen/skills/  # Xingchen agent skills (2)
└── agents/moling/skills/    # Moling agent skills (7)
```

## Skills Overview

### Core Skills (workspace/skills)
- `agent-browser-clawdbot` - Agent browser clawdbot integration
- `agent-creator` - Create new agents
- `auto-update` - Automated update system
- `automation-design` - Automation workflow design
- `blog-ops` - Blog operations
- `browser` - Browser automation
- `gemini-deep-research` - Gemini-powered deep research
- `gog` - GOG integration
- `healthcheck` - System health checks
- `last30days-official` - Last 30 days official updates
- `marketing-framework` - Marketing automation
- `metacognition-protocol` - Self-reflection protocols
- `minimax-tts-voice` - MiniMax TTS voice synthesis
- `multi-source-research` - Multi-source research
- `n8n` - n8n workflow integration
- `notion-mcp` - Notion MCP integration
- `self-improvement-loop` - Self-improvement automation
- `skill-creator` - Create new skills
- `skill-improvement` - Skill enhancement
- `skill-security-auditor` - Security auditing for skills
- `task-father` - Task management
- `task-tracker-pro` - Advanced task tracking
- `xiaohongshu-prompt-generator` - Xiaohongshu content prompts
- `windows-docker-wsl2` - WSL2 Docker setup
- `openclaw-md-guide` - OpenClaw markdown guide

### Plugin Skills (plugin-skills)
- `browser-automation` - Browser automation
- `doubao-automation` - Doubao automation
- `legal-case-dossier` - Legal case management
- `qqbot-channel` - QQ bot channel integration
- `qqbot-media` - QQ bot media handling
- `qqbot-remind` - QQ bot reminders
- `wiki-maintainer` - Wiki maintenance
- `obsidian-vault-maintainer` - Obsidian vault management

### Agent-Specific Skills
#### Xingchen Agent
- `bilibili-summarizer` - Bilibili video summarizer
- `wechat-article-reader` - WeChat article reader

#### Moling Agent
- `gemini-deep-research` - Deep research capabilities
- `in-depth-research-1-0-0` - Versioned research
- `market-research` - Market research
- `multi-source-research` - Multi-source research
- `reddit-readonly` - Reddit read-only access
- `report-searcher` - Report searching

## Usage

Skills are invoked using the `/` command or via the Claude Code skill system.

```
/skill-name
```

## License

MIT
