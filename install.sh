#!/usr/bin/env bash
# KIE MCP Kit — installer for Claude Code.
# Installs the skills and registers the KIE connector.
#
# Usage:  KIE_API_KEY=your_key ./install.sh [--force]
#   --force   overwrite skills that are already installed
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
SERVER="$SCRIPT_DIR/server/kie_server.py"
FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1

echo "🎨 KIE MCP Kit installer"
echo

# 1) Skills -------------------------------------------------------------------
# An existing folder is left alone unless --force: the same skill may already be
# installed from a plugin, and two copies of one name collide.
echo "→ Installing skills into $SKILLS_DIR"
mkdir -p "$SKILLS_DIR"
for s in generate-anything content-factory youtube-factory; do
  if [ -e "$SKILLS_DIR/$s" ] && [ "$FORCE" -eq 0 ]; then
    echo "  ↷ $s — already installed, skipped (re-run with --force to overwrite)"
    continue
  fi
  rm -rf "$SKILLS_DIR/$s"
  cp -R "$SCRIPT_DIR/skill/$s" "$SKILLS_DIR/$s"
  echo "  ✅ $s"
done
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

# `claude mcp add` fails when the name is taken (e.g. an older kie connector),
# so drop the existing registration first.
if claude mcp list 2>/dev/null | grep -q '^kie:'; then
  echo "→ Replacing the existing 'kie' registration"
  claude mcp remove kie >/dev/null 2>&1 || true
fi

echo "→ Registering the KIE connector with Claude Code (user scope)"
claude mcp add --scope user kie --env "KIE_API_KEY=$KIE_API_KEY" -- uv run "$SERVER"
echo "  ✅ connector registered"
echo
echo "Done. Check with:  claude mcp list   (expect: kie ✓ Connected)"
echo "Restart Claude Code so the new connector and skills load."
