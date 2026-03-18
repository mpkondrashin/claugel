#!/usr/bin/env python3
"""
ES Memory MCP Server
SQLite-based persistent memory for Claude Code.

Setup:
  pip install mcp

Run:
  python mcp_memory.py

First run will create memory.db with schema.
"""

import sqlite3
import json
import re
import gzip
import shutil
from pathlib import Path
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# ============ CONFIG ============

# Измени путь на свой
DB_PATH = Path.home() / "Documents" / "Work" / ".claude-mcp" / "memory.db"

ALLOWED_TABLES = {
    'memory', 'entities', 'decisions', 'relationships',
    'questions', 'thought_arc', 'ai_costs', 'context',
    'people', 'projects'
}

# ============ INIT ============

mcp = FastMCP("es-memory")


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    """Initialize database with schema"""
    db = get_db()

    # Memory table (main storage)
    db.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            content TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            source TEXT DEFAULT 'user'
        )
    """)

    # Entities (people, projects, concepts)
    db.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT DEFAULT 'concept',
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_accessed TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Decisions log
    db.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            topic TEXT NOT NULL,
            decision TEXT NOT NULL,
            reasoning TEXT,
            status TEXT DEFAULT 'active'
        )
    """)

    # Questions (open items)
    db.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            question TEXT NOT NULL,
            domain TEXT DEFAULT 'general',
            status TEXT DEFAULT 'open',
            resolution TEXT
        )
    """)

    # Projects
    db.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # People
    db.execute("""
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            org TEXT,
            role TEXT,
            notes TEXT,
            last_contact TEXT
        )
    """)

    # AI Costs tracking
    db.execute("""
        CREATE TABLE IF NOT EXISTS ai_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            service TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT DEFAULT 'mixed',
            note TEXT
        )
    """)

    # Full-text search for memory
    db.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts
        USING fts5(content, content=memory, content_rowid=id)
    """)

    # Triggers to keep FTS in sync
    db.execute("""
        CREATE TRIGGER IF NOT EXISTS memory_ai AFTER INSERT ON memory BEGIN
            INSERT INTO memory_fts(rowid, content) VALUES (new.id, new.content);
        END
    """)

    db.execute("""
        CREATE TRIGGER IF NOT EXISTS memory_ad AFTER DELETE ON memory BEGIN
            INSERT INTO memory_fts(memory_fts, rowid, content) VALUES('delete', old.id, old.content);
        END
    """)

    db.commit()
    db.close()


# Initialize on import
init_db()


# ============ TOOLS ============

@mcp.tool()
def db_info() -> str:
    """Get database info: tables, counts, size"""
    db = get_db()

    tables = db.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '%_fts%'
    """).fetchall()

    info = {"tables": {}}
    for t in tables:
        name = t['name']
        count = db.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()[0]
        info["tables"][name] = count

    info["db_path"] = str(DB_PATH)
    if DB_PATH.exists():
        info["size_kb"] = DB_PATH.stat().st_size // 1024

    db.close()
    return json.dumps(info, indent=2)


@mcp.tool()
def memory_search(query: str, limit: int = 10) -> str:
    """Search memory by text (FTS). Returns matching memories."""
    db = get_db()

    try:
        rows = db.execute("""
            SELECT m.id, m.timestamp, substr(m.content, 1, 200) as preview, m.weight
            FROM memory m
            JOIN memory_fts ON memory_fts.rowid = m.id
            WHERE memory_fts MATCH ?
            ORDER BY m.weight DESC, m.timestamp DESC
            LIMIT ?
        """, (query, limit)).fetchall()
    except:
        # Fallback to LIKE if FTS fails
        rows = db.execute("""
            SELECT id, timestamp, substr(content, 1, 200) as preview, weight
            FROM memory
            WHERE content LIKE ?
            ORDER BY weight DESC, timestamp DESC
            LIMIT ?
        """, (f"%{query}%", limit)).fetchall()

    results = [dict(r) for r in rows]
    db.close()
    return json.dumps(results, indent=2)


@mcp.tool()
def memory_add(content: str, weight: float = 1.0) -> str:
    """Add new memory entry"""
    db = get_db()
    cursor = db.execute(
        "INSERT INTO memory (content, weight) VALUES (?, ?)",
        (content, weight)
    )
    db.commit()
    memory_id = cursor.lastrowid
    db.close()
    return json.dumps({"id": memory_id, "status": "added"})


@mcp.tool()
def entity_get(name: str) -> str:
    """Get entity by name"""
    db = get_db()
    row = db.execute(
        "SELECT * FROM entities WHERE name = ?", (name,)
    ).fetchone()
    db.close()

    if row:
        return json.dumps(dict(row), indent=2)
    return json.dumps({"error": "Entity not found"})


@mcp.tool()
def entity_search(query: str, limit: int = 10) -> str:
    """Search entities by name"""
    db = get_db()
    rows = db.execute("""
        SELECT * FROM entities
        WHERE name LIKE ? OR description LIKE ?
        LIMIT ?
    """, (f"%{query}%", f"%{query}%", limit)).fetchall()
    db.close()
    return json.dumps([dict(r) for r in rows], indent=2)


@mcp.tool()
def entity_touch(name: str, context: str = "mcp") -> str:
    """Mark entity as accessed, update last_accessed"""
    db = get_db()
    db.execute("""
        UPDATE entities SET last_accessed = CURRENT_TIMESTAMP
        WHERE name = ?
    """, (name,))
    db.commit()
    db.close()
    return json.dumps({"status": "touched", "name": name})


@mcp.tool()
def decisions_open() -> str:
    """Get all open/active decisions"""
    db = get_db()
    rows = db.execute("""
        SELECT * FROM decisions WHERE status = 'active'
        ORDER BY timestamp DESC
    """).fetchall()
    db.close()
    return json.dumps([dict(r) for r in rows], indent=2)


@mcp.tool()
def decision_add(topic: str, decision: str, reasoning: str = None, status: str = "active") -> str:
    """Add new decision"""
    db = get_db()
    cursor = db.execute("""
        INSERT INTO decisions (topic, decision, reasoning, status)
        VALUES (?, ?, ?, ?)
    """, (topic, decision, reasoning, status))
    db.commit()
    decision_id = cursor.lastrowid
    db.close()
    return json.dumps({"id": decision_id, "status": "added"})


@mcp.tool()
def recall() -> str:
    """Morning RECALL: recent memories, open decisions, open questions"""
    db = get_db()

    # Recent memories
    memories = db.execute("""
        SELECT id, timestamp, substr(content, 1, 100) as preview
        FROM memory ORDER BY timestamp DESC LIMIT 5
    """).fetchall()

    # Open decisions
    decisions = db.execute("""
        SELECT topic, decision FROM decisions
        WHERE status = 'active' LIMIT 5
    """).fetchall()

    # Open questions
    questions = db.execute("""
        SELECT question, domain FROM questions
        WHERE status = 'open' LIMIT 5
    """).fetchall()

    db.close()

    return json.dumps({
        "recent_memories": [dict(m) for m in memories],
        "open_decisions": [dict(d) for d in decisions],
        "open_questions": [dict(q) for q in questions]
    }, indent=2)


@mcp.tool()
def stats() -> str:
    """Database statistics by table"""
    db = get_db()

    stats = {}
    for table in ALLOWED_TABLES:
        try:
            count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            stats[table] = count
        except:
            stats[table] = 0

    db.close()
    return json.dumps(stats, indent=2)


@mcp.tool()
def questions_open(limit: int = 20) -> str:
    """Get open questions"""
    db = get_db()
    rows = db.execute("""
        SELECT * FROM questions WHERE status = 'open'
        ORDER BY timestamp DESC LIMIT ?
    """, (limit,)).fetchall()
    db.close()
    return json.dumps([dict(r) for r in rows], indent=2)


@mcp.tool()
def question_add(question: str, domain: str = "general") -> str:
    """Add new question"""
    db = get_db()
    cursor = db.execute("""
        INSERT INTO questions (question, domain) VALUES (?, ?)
    """, (question, domain))
    db.commit()
    q_id = cursor.lastrowid
    db.close()
    return json.dumps({"id": q_id, "status": "added"})


@mcp.tool()
def question_resolve(question_id: int, resolution: str) -> str:
    """Resolve a question"""
    db = get_db()
    db.execute("""
        UPDATE questions SET status = 'resolved', resolution = ?
        WHERE id = ?
    """, (resolution, question_id))
    db.commit()
    db.close()
    return json.dumps({"id": question_id, "status": "resolved"})


@mcp.tool()
def questions_search(query: str, limit: int = 10) -> str:
    """Search questions"""
    db = get_db()
    rows = db.execute("""
        SELECT * FROM questions WHERE question LIKE ?
        LIMIT ?
    """, (f"%{query}%", limit)).fetchall()
    db.close()
    return json.dumps([dict(r) for r in rows], indent=2)


@mcp.tool()
def people_list(org: str = None) -> str:
    """List people, optionally by org"""
    db = get_db()
    if org:
        rows = db.execute("SELECT * FROM people WHERE org = ?", (org,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM people").fetchall()
    db.close()
    return json.dumps([dict(r) for r in rows], indent=2)


@mcp.tool()
def projects_list(status: str = "active") -> str:
    """List projects by status"""
    db = get_db()
    rows = db.execute("""
        SELECT * FROM projects WHERE status = ?
    """, (status,)).fetchall()
    db.close()
    return json.dumps([dict(r) for r in rows], indent=2)


@mcp.tool()
def costs_add(date: str, service: str, amount: float, category: str = "mixed", note: str = None) -> str:
    """Add AI cost entry"""
    db = get_db()
    cursor = db.execute("""
        INSERT INTO ai_costs (date, service, amount, category, note)
        VALUES (?, ?, ?, ?, ?)
    """, (date, service, amount, category, note))
    db.commit()
    cost_id = cursor.lastrowid
    db.close()
    return json.dumps({"id": cost_id, "status": "added"})


@mcp.tool()
def costs_summary() -> str:
    """AI costs summary by month"""
    db = get_db()
    rows = db.execute("""
        SELECT
            strftime('%Y-%m', date) as month,
            service,
            SUM(amount) as total
        FROM ai_costs
        GROUP BY month, service
        ORDER BY month DESC
    """).fetchall()
    db.close()
    return json.dumps([dict(r) for r in rows], indent=2)


# ============ BACKUP ============

def backup_db(keep: int = 3):
    """Create a compressed backup of memory.db, keeping last `keep` copies."""
    if not DB_PATH.exists():
        return

    backup_dir = DB_PATH.parent / "backups"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"memory_{timestamp}.db.gz"

    with DB_PATH.open("rb") as src, gzip.open(backup_path, "wb", compresslevel=6) as dst:
        shutil.copyfileobj(src, dst)

    # Rotate: keep only the last `keep` backups
    backups = sorted(backup_dir.glob("memory_*.db.gz"))
    for old in backups[:-keep]:
        old.unlink()

    print(f"Backup created: {backup_path.name} ({backup_path.stat().st_size} bytes)")


# ============ RUN ============

if __name__ == "__main__":
    print(f"Memory DB: {DB_PATH}")
    backup_db(keep=3)
    mcp.run()
