#!/bin/bash
# ES Memory MCP Server
# SQLite-based persistent memory

MCP_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$MCP_DIR"
source .venv/bin/activate
python mcp_memory.py
