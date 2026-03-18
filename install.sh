#!/bin/bash
set -e

REPO="https://github.com/mpkondrashin/claugel.git"
DEFAULT_DIR="$(pwd)/.claude-mcp"

echo "=== Claude MCP Installer ==="
echo ""

# Install dir (override with CLAUGEL_DIR env var if needed)
INSTALL_DIR="${CLAUGEL_DIR:-$DEFAULT_DIR}"
echo "Install directory: $INSTALL_DIR"

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
    read -r -p "Press Enter when done to continue..." </dev/tty 2>/dev/null || true
else
    echo ".env already exists, skipping."
fi

# Register MCPs for this project (.mcp.json in current directory)
echo ""
echo "Registering MCP servers..."
claude mcp add --scope project tm-proxy /bin/bash "$INSTALL_DIR/start_tm_proxy.sh"
claude mcp add --scope project es-memory /bin/bash "$INSTALL_DIR/start_memory.sh"
echo "  Done."

# CLI tools live in $INSTALL_DIR/bin — no global install
echo ""
echo "CLI tools available in: $INSTALL_DIR/bin"
echo "  To use mdpreview from anywhere, add to your shell profile:"
echo "    export PATH=\"$INSTALL_DIR/bin:\$PATH\""

echo ""
echo "=== Done! Restart Claude to activate MCP servers. ==="
