#!/usr/bin/env bash
# KIE MCP Kit — installer for Claude Code.
# Installs the generate-anything skill and registers the KIE connector.
# Usage:  KIE_API_KEY=your_key ./install.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
SERVER="$SCRIPT_DIR/server/kie_server.py"

echo "🎨 KIE MCP Kit installer"
echo

# 1) Skill --------------------------------------------------------------------
echo "→ Installing the generate-anything skill into $SKILLS_DIR"
mkdir -p "$SKILLS_DIR"
cp -R "$SCRIPT_DIR/skill/generate-anything" "$SKILLS_DIR/generate-anything"
echo "  ✅ skill installed"
echo

# 2) Dependencies -------------------------------------------------------------
if ! command -v uv >/dev/null 2>&1; then
  echo "  ⚠️  'uv' not found — it runs the connector and auto-installs its deps."
  echo "     Install it:  curl -LsSf https://astral.sh/uv/install.sh | sh"
  echo "     Then re-run this script."
  exit 1
fi

# 3) Connector ----------------------------------------------------------------
if ! command -v claude >/dev/null 2>&1; then
  echo "  ⚠️  'claude' CLI not found — skipping connector registration. Register it yourself:"
  echo "     claude mcp add --scope user kie --env KIE_API_KEY=YOUR_KEY -- uv run \"$SERVER\""
  exit 0
fi

if [ -z "${KIE_API_KEY:-}" ]; then
  echo "→ No KIE_API_KEY in the environment. Register the connector yourself:"
  echo "     claude mcp add --scope user kie --env KIE_API_KEY=YOUR_KEY -- uv run \"$SERVER\""
  echo "  (get a key at https://kie.ai → Dashboard → API Keys)"
  exit 0
fi

echo "→ Registering the KIE connector with Claude Code (user scope)"
claude mcp add --scope user kie --env "KIE_API_KEY=$KIE_API_KEY" -- uv run "$SERVER"
echo "  ✅ connector registered"
echo
echo "Done. Check with:  claude mcp list   (expect: kie ✓ Connected)"
echo "Then just ask Claude: \"make a 9:16 video of a coffee cup with Seedance\""
