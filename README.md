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

Run from the directory where you want to install claugel:

```bash
curl -fsSL https://raw.githubusercontent.com/mpkondrashin/claugel/main/install.sh | bash
```

By default, claugel is installed into `.claude-mcp/` inside the current directory. To use a different path, set `CLAUGEL_DIR` before running:

```bash
curl -fsSL https://raw.githubusercontent.com/mpkondrashin/claugel/main/install.sh | CLAUGEL_DIR=~/my-mcp bash
```

The installer will:

1. Clone the repo into `.claude-mcp/` inside the current directory
2. Create a Python virtual environment and install dependencies
3. Create `.env` from the template and prompt you to fill in API tokens
4. Register both MCP servers for the current project (`claude mcp add --scope project`)

Everything stays inside `.claude-mcp/` — nothing is written outside the installation directory.

Restart Claude Code after installation.

### API tokens

Edit `.claude-mcp/.env` in your project directory:

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
gunzip -c .claude-mcp/backups/memory_20260318_090000.db.gz > .claude-mcp/memory.db
```

#### Tools

---

##### `recall`

Morning recall: recent memories, open decisions, open questions. Use at the start of a session to restore context.

```
recall()
```

---

##### `memory_add`

Add a free-form memory entry. Accepts optional `weight` (default 1.0) to boost relevance in search.

```
memory_add("Vision One API uses Bearer token auth. Get token from Console → API Keys.")
memory_add("Always check TMV1-Submission-Remaining-Count header for sandbox quota.", weight=1.5)
```

---

##### `memory_search`

Full-text search across all memory entries.

```
memory_search("sandbox quota")
memory_search("Vision One auth", limit=5)
```

---

##### `entity_get`

Retrieve a named entity (person, project, concept) by exact name.

```
entity_get("Vision One")
entity_get("Deep Security")
```

---

##### `entity_search`

Search entities by partial name match.

```
entity_search("Vision")
entity_search("Cloud", limit=5)
```

---

##### `entity_touch`

Mark an entity as recently accessed (updates `last_accessed` timestamp).

```
entity_touch("Vision One")
entity_touch("Apex One", context="incident investigation")
```

---

##### `decision_add`

Record a decision with topic, decision text, optional reasoning, and status.

```
decision_add(
    topic="File Security product choice",
    decision="Use Vision One File Security for new deployments, not Cloud One FSS",
    reasoning="Cloud One FSS is being phased out",
    status="active"
)
```

---

##### `decisions_open`

List all active (unresolved) decisions.

```
decisions_open()
```

---

##### `question_add`

Add an open question to track. Useful for noting things to follow up on.

```
question_add("What file types does Vision One Sandbox support?", domain="products")
question_add("How to integrate Vision One with Splunk?", domain="integrations")
```

---

##### `questions_open`

List all open (unresolved) questions.

```
questions_open()
questions_open(limit=5)
```

---

##### `question_resolve`

Mark a question as resolved with an answer. Use the question's `id` from `questions_open`.

```
question_resolve(question_id=3, resolution="Sandbox supports PE, PDF, Office, and archive formats.")
```

---

##### `questions_search`

Search questions by text.

```
questions_search("Splunk")
questions_search("sandbox", limit=5)
```

---

##### `people_list`

List people stored in the database, optionally filtered by organization.

```
people_list()
people_list(org="Trend Micro")
```

---

##### `projects_list`

List projects filtered by status (`active`, `completed`, etc.).

```
projects_list()
projects_list(status="completed")
```

---

##### `costs_add`

Log an AI cost entry for tracking monthly spend.

```
costs_add(date="2026-03-18", service="Claude", amount=1.87, category="codegen")
costs_add(date="2026-03-18", service="TrendGPT", amount=0.00, note="internal, no charge")
```

---

##### `costs_summary`

Show AI costs grouped by month.

```
costs_summary()
```

---

##### `link_add`

Add a URL to the links registry. The `description` field is the most important — the richer and more detailed it is, the better Claude can suggest the link when working on a relevant task. Claude performs full-text search across title and description to surface links proactively.

```
link_add(
    url="https://automation.trendmicro.com/xdr/api-v3",
    title="Vision One API v3 Reference",
    description="Official REST API reference for Vision One (XDR). Covers all
    endpoints: alerts, workbench, sandbox submission, response actions, SIEM
    connectors. Use when writing scripts to automate alert triage, isolate
    endpoints, fetch detections, or integrate with SIEM.",
    tags="api,vision-one,xdr"
)
```

---

##### `link_search`

Full-text search across link titles and descriptions. Use natural language — the query matches against the rich description text.

```
link_search("sandbox file upload python")
link_search("how to authenticate Vision One API")
link_search("webhook alert notification", limit=5)
```

---

##### `link_list`

List all links, optionally filtered by tag.

```
link_list()
link_list(tag="api")
link_list(tag="vision-one")
```

---

##### `link_delete`

Delete a link by its ID (from `link_list` or `link_search`).

```
link_delete(3)
```

---

##### `db_info`

Show database tables with row counts and file size.

```
db_info()
```

---

##### `stats`

Show per-table row count statistics.

```
stats()
```

---

#### Memory schema

The database contains these tables: `memory`, `entities`, `decisions`, `questions`, `projects`, `people`, `ai_costs`, `links`. Full-text search is enabled on `memory` (content) and `links` (title + description) via SQLite FTS5.

---

### tm-proxy

Proxies requests to Trend Micro internal services. Requires VPN (GlobalProtect).

#### Tools

---

##### `vpn_status`

Check if the Trend Micro internal network is reachable.

```
vpn_status()
```

---

##### `ask_trendgpt`

Ask TrendGPT a question about Trend Micro products. Supports three model tiers: `haiku` (fast), `sonnet` (balanced), `opus` (best quality).

```
ask_trendgpt("How do I configure XDR alert suppression in Vision One?")
ask_trendgpt("What's the difference between Apex One SaaS and on-premise?", model="sonnet")
ask_trendgpt("Explain the Vision One risk index scoring algorithm.", model="opus")
```

---

##### `search_kb`

Search Trend Micro Knowledge Base articles. Results can be filtered by product.

```
search_kb("agent deployment fails on Windows Server 2022")
search_kb("DKIM configuration", top_k=5, products=["Cloud Email Gateway Security"])
search_kb("sandbox submission error", format="content")
```

---

##### `get_kb_article`

Fetch the full text of a KB article by its ID.

```
get_kb_article("KA-0123456")
```

---

##### `search_online_help`

Search the Trend Micro Online Help documentation.

```
search_online_help("how to create a custom detection rule")
search_online_help("API rate limits", top_k=3)
search_online_help("SAML SSO setup", format="content")
```

---

##### `search_threat_encyclopedia`

Search for malware families, ransomware groups, or CVEs.

```
search_threat_encyclopedia("LockBit")
search_threat_encyclopedia("CVE-2024-21412", num_results=3)
search_threat_encyclopedia("Earth Preta")
```

---

##### `search_automation_center`

Search the Automation Center for scripts, playbooks, and API documentation.

```
search_automation_center("isolate endpoint Vision One")
search_automation_center("Python script list alerts", products=["Vision One"])
search_automation_center("Deep Security API policy update")
```

---

##### `search_pdf_guides`

Search admin and installation PDF guides.

```
search_pdf_guides("Apex One installation guide Windows")
search_pdf_guides("Deep Security upgrade procedure", products=["Deep Security"])
```

---

##### `search_research_news`

Search the Trend Micro research blog and threat news.

```
search_research_news("Earth Preta APT campaign 2025")
search_research_news("ransomware supply chain attack")
search_research_news("LockBit affiliate TTPs")
```

---

##### `get_latest_product_versions`

Get the latest release versions from the Trend Micro Download Center.

```
get_latest_product_versions()
get_latest_product_versions(products=["Apex One", "Deep Security"])
```

---

## Skills

Custom slash commands for Claude Code are stored in the `skills/` directory and loaded automatically when Claude Code starts in a directory that has this MCP configured.

---

##### `/trendai-page`

Generate a complete, self-contained HTML page following TrendAI™ brand guidelines (colors, typography, dark/light mode, ADA compliance).

```
/trendai-page landing page for Vision One with Hero, Features, and CTA sections
/trendai-page one-pager for a security operations report, light background
/trendai-page product comparison table: Apex One vs Deep Security
```

---

## CLI tools

Standalone command-line utilities located in `.claude-mcp/bin/`. The installer does not copy them anywhere — they stay inside the installation directory.

---

##### `mdpreview`

Open a Markdown file in the browser with GitHub-style formatting and syntax highlighting. No dependencies beyond Python 3 and an internet connection (loads marked.js and highlight.js from CDN).

```bash
.claude-mcp/bin/mdpreview README.md
```

To call it without the path, add `.claude-mcp/bin` to your shell profile:

```bash
export PATH="$PWD/.claude-mcp/bin:$PATH"
```

The rendered page matches GitHub's Markdown style, with full GFM support (tables, fenced code blocks, task lists) and automatic syntax highlighting for code blocks.

---

## Updates

The `check_update.sh` script checks GitHub for a newer tagged release, updates the repo, reinstalls dependencies, and shows a macOS notification.

To run manually:

```bash
.claude-mcp/check_update.sh
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
├── bin/                # CLI tools installed to ~/.local/bin
│   └── mdpreview       # Markdown preview in browser
├── backups/            # compressed DB backups (memory_*.db.gz)
├── .env                # API tokens (git-ignored)
├── .env.example        # token template
└── memory.db           # SQLite database (git-ignored)
```

---

## License

Internal Trend Micro tool. Not for public distribution.
