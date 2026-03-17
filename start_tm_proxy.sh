#!/bin/bash
# TM Proxy MCP Server
# Запускает прокси к TrendGPT и TM Knowledge Base

# Измени путь на свой
MCP_DIR="$HOME/Documents/Work/.claude-mcp"

cd "$MCP_DIR"
bash check_update.sh
source .venv/bin/activate
python mcp_tm_proxy.py
