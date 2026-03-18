#!/bin/bash
set -e

REPO="https://github.com/mpkondrashin/claugel.git"
DEFAULT_DIR="$(pwd)/.claude-mcp"

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

# Register MCPs in user scope (~/.claude/settings.json)
echo ""
echo "Registering MCP servers..."
claude mcp add --scope user tm-proxy /bin/bash "$INSTALL_DIR/start_tm_proxy.sh"
claude mcp add --scope user es-memory /bin/bash "$INSTALL_DIR/start_memory.sh"
echo "  Done."

# Install CLI tools to ~/.local/bin
echo ""
echo "Installing CLI tools..."
mkdir -p "$HOME/.local/bin"
cp "$INSTALL_DIR/bin/mdpreview" "$HOME/.local/bin/mdpreview"
chmod +x "$HOME/.local/bin/mdpreview"
echo "  mdpreview -> ~/.local/bin/mdpreview"
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo "  NOTE: ~/.local/bin is not in your PATH."
    echo "  Add this to your ~/.zshrc or ~/.bashrc:"
    echo '    export PATH="$HOME/.local/bin:$PATH"'
fi

echo ""
echo "=== Done! Restart Claude to activate MCP servers. ==="
