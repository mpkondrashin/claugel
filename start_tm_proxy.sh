#!/bin/bash
# TM Proxy MCP Server
# Запускает прокси к TrendGPT и TM Knowledge Base

MCP_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$MCP_DIR"
bash check_update.sh
source .venv/bin/activate
python mcp_tm_proxy.py
