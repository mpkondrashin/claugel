#!/bin/bash
# Check GitHub for new tag and update if available

REPO="mpkondrashin/claugel"
MCP_DIR="$(cd "$(dirname "$0")" && pwd)"

# Get current tag (skip if not on a tag)
CURRENT=$(git -C "$MCP_DIR" describe --tags --exact-match 2>/dev/null)
if [ -z "$CURRENT" ]; then
    exit 0
fi

# Get latest tag via gh CLI
LATEST=$(gh api "repos/$REPO/tags" --jq '.[0].name' 2>/dev/null)
if [ -z "$LATEST" ] || [ "$LATEST" = "null" ] || [ "$CURRENT" = "$LATEST" ]; then
    exit 0
fi

# Update
git -C "$MCP_DIR" fetch --tags --quiet
git -C "$MCP_DIR" checkout "$LATEST" --quiet

source "$MCP_DIR/.venv/bin/activate"
pip install -r "$MCP_DIR/requirements.txt" --quiet

# macOS notification
osascript -e "display notification \"MCP обновлён: $CURRENT → $LATEST. Перезапусти Claude.\" with title \"Claude MCP Update\""
