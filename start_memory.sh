#!/bin/bash
# ES Memory MCP Server
# SQLite-based persistent memory

# Измени путь на свой
MCP_DIR="$HOME/Documents/Work/.claude-mcp"

cd "$MCP_DIR"
source .venv/bin/activate
python mcp_memory.py
