#!/bin/bash
set -e

REPO="https://github.com/mpkondrashin/claugel.git"
DEFAULT_DIR="$HOME/.claude-mcp"
CLAUDE_SETTINGS="$HOME/.claude/settings.json"

echo "=== Claude MCP Installer ==="
echo ""

# Install dir
read -r -p "Install directory [$DEFAULT_DIR]: " INSTALL_DIR
INSTALL_DIR="${INSTALL_DIR:-$DEFAULT_DIR}"

# Clone or update
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Directory exists, pulling latest..."
    git -C "$INSTALL_DIR" fetch --tags --quiet
    LATEST=$(gh api repos/mpkondrashin/claugel/tags --jq '.[0].name' 2>/dev/null)
    if [ -n "$LATEST" ] && [ "$LATEST" != "null" ]; then
        git -C "$INSTALL_DIR" checkout "$LATEST" --quiet
        echo "Checked out $LATEST"
    fi
else
    echo "Cloning repo..."
    git clone "$REPO" "$INSTALL_DIR"
    LATEST=$(gh api repos/mpkondrashin/claugel/tags --jq '.[0].name' 2>/dev/null)
    if [ -n "$LATEST" ] && [ "$LATEST" != "null" ]; then
        git -C "$INSTALL_DIR" checkout "$LATEST" --quiet
        echo "Checked out $LATEST"
    fi
fi

cd "$INSTALL_DIR"

# Python venv
echo ""
echo "Setting up Python environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt --quiet
echo "Done."

# .env
echo ""
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from template."
    echo ""
    echo ">>> Fill in your API tokens in: $INSTALL_DIR/.env"
    echo "    TRENDGPT_TOKEN=..."
    echo "    TM_KNOWLEDGE_TOKEN=..."
    echo ""
    read -r -p "Press Enter when done to continue..."
else
    echo ".env already exists, skipping."
fi

# Register MCPs in ~/.claude/settings.json
echo ""
echo "Registering MCP servers in ~/.claude/settings.json..."

mkdir -p "$HOME/.claude"

python3 - <<PYEOF
import json, os

settings_path = os.path.expanduser("$CLAUDE_SETTINGS")
install_dir = "$INSTALL_DIR"

# Load existing settings
if os.path.exists(settings_path):
    with open(settings_path) as f:
        settings = json.load(f)
else:
    settings = {}

settings.setdefault("mcpServers", {})
settings["mcpServers"]["tm-proxy"] = {
    "command": "/bin/bash",
    "args": [f"{install_dir}/start_tm_proxy.sh"]
}
settings["mcpServers"]["es-memory"] = {
    "command": "/bin/bash",
    "args": [f"{install_dir}/start_memory.sh"]
}

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)

print("  tm-proxy: registered")
print("  es-memory: registered")
PYEOF

echo ""
echo "=== Done! Restart Claude to activate MCP servers. ==="
