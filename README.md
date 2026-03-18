# claugel

MCP servers for [Claude Code](https://claude.ai/code) tailored for Trend Micro engineers.

Provides two servers:

- **es-memory** — persistent SQLite memory across Claude sessions
- **tm-proxy** — access to TrendGPT and Trend Micro knowledge services

---

## Requirements

- macOS (Linux should work; Windows not tested)
- Python 3.10+
- [Claude Code](https://claude.ai/code) CLI
- [GitHub CLI](https://cli.github.com/) (`gh`) — used by the installer and auto-updater
- Trend Micro VPN (GlobalProtect) — required by `tm-proxy`

---

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/mpkondrashin/claugel/main/install.sh | bash
```

The installer will:

1. Clone the repo (default location: `~/.claude-mcp`)
2. Create a Python virtual environment and install dependencies
3. Create `.env` from the template and prompt you to fill in API tokens
4. Register both MCP servers in Claude Code (`claude mcp add --scope user`)

Restart Claude Code after installation.

### API tokens

Edit `~/.claude-mcp/.env`:

```env
TRENDGPT_TOKEN=your_trendgpt_token_here
TM_KNOWLEDGE_TOKEN=your_tm_knowledge_token_here
```

Tokens are available in the internal Trend Micro developer portal.

---

## MCP servers

### es-memory

Persistent memory stored in a local SQLite database (`memory.db`). Survives across Claude sessions.

**Automatic backups** — on every startup, the database is backed up as a compressed `.db.gz` file. The last 3 backups are kept in the `backups/` directory.

To restore a backup:

```bash
gunzip -c ~/.claude-mcp/backups/memory_20260318_090000.db.gz > ~/.claude-mcp/memory.db
```

#### Available tools

| Tool | Description |
|---|---|
| `recall` | Morning recall: recent memories, open decisions, open questions |
| `memory_add` | Add a new memory entry |
| `memory_search` | Full-text search across memories |
| `entity_get` | Get a named entity by name |
| `entity_search` | Search entities by name |
| `entity_touch` | Mark entity as recently accessed |
| `decision_add` | Record a decision with reasoning |
| `decisions_open` | List all active decisions |
| `question_add` | Add an open question |
| `questions_open` | List all open questions |
| `question_resolve` | Mark a question as resolved |
| `questions_search` | Search questions |
| `people_list` | List people, optionally filtered by org |
| `projects_list` | List projects by status |
| `costs_add` | Log an AI cost entry |
| `costs_summary` | Monthly AI costs summary |
| `db_info` | Database tables, row counts, file size |
| `stats` | Statistics by table |

#### Memory schema

The database contains these tables: `memory`, `entities`, `decisions`, `questions`, `projects`, `people`, `ai_costs`. Full-text search is enabled on the `memory` table via SQLite FTS5.

---

### tm-proxy

Proxies requests to Trend Micro internal services. Requires VPN.

#### Available tools

| Tool | Description |
|---|---|
| `vpn_status` | Check if TM VPN is reachable |
| `ask_trendgpt` | Ask TrendGPT about TM products (Vision One, Apex One, Deep Security, etc.) |
| `search_kb` | Search Trend Micro Knowledge Base articles |
| `get_kb_article` | Fetch a full KB article by ID (format: `KA-XXXXXXX`) |
| `search_online_help` | Search Trend Micro Online Help documentation |
| `search_threat_encyclopedia` | Search threats and CVEs in the Threat Encyclopedia |
| `search_automation_center` | Search scripts and API docs in the Automation Center |
| `search_pdf_guides` | Search admin and installation PDF guides |
| `search_research_news` | Search Trend Micro research blog and news |
| `get_latest_product_versions` | Get latest product versions from the Download Center |

`ask_trendgpt` supports three model tiers: `haiku` (fast), `sonnet` (balanced), `opus` (best quality).

---

## Skills

Custom slash commands for Claude Code are stored in the `skills/` directory and loaded automatically.

| Skill | Command | Description |
|---|---|---|
| trendai-page | `/trendai-page <description>` | Generate an HTML page following TrendAI™ brand guidelines |

---

## Updates

The `check_update.sh` script checks GitHub for a newer tagged release, updates the repo, reinstalls dependencies, and shows a macOS notification.

To run manually:

```bash
~/.claude-mcp/check_update.sh
```

You can schedule it with `cron` or `launchd`.

---

## Project structure

```
.claude-mcp/
├── mcp_memory.py       # es-memory MCP server
├── mcp_tm_proxy.py     # tm-proxy MCP server
├── start_memory.sh     # startup wrapper for es-memory
├── start_tm_proxy.sh   # startup wrapper for tm-proxy
├── install.sh          # installer
├── check_update.sh     # auto-updater
├── seed_database.py    # optional: seed memory.db with initial data
├── requirements.txt    # Python dependencies (mcp, httpx)
├── skills/             # Claude Code custom slash commands
│   └── trendai-page.md
├── backups/            # compressed DB backups (memory_*.db.gz)
├── .env                # API tokens (git-ignored)
├── .env.example        # token template
└── memory.db           # SQLite database (git-ignored)
```

---

## License

Internal Trend Micro tool. Not for public distribution.
