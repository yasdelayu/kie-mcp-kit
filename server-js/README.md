# KIE connector — Node build

A Node/JavaScript port of `../server/kie_server.py`, feature-for-feature: the same
7 tools (`kie_post`, `kie_get`, `kie_upload_file`, `kie_download`,
`kie_fetch_model_docs`, `kie_workflows`, `kie_workflow_file`), the same
`kie://models` resources, the same guards (origin allowlist, workspace confinement,
media allowlist, trailing-dot check) and the same inline image preview.

**Why a second build?** The Python server needs `uv`. This one runs on plain Node
(≥18) — which is what lets it ship as a **`.mcpb`** you drag onto Claude Desktop with
no toolchain to install. Pick whichever fits: `uv` present → the Python build; want
drag-and-drop for non-developers → this one.

## Run

```bash
cd server-js
npm install
node kie_server.mjs --selftest      # prints: selftest ok
```

## Register (Claude Code)

```bash
claude mcp add --scope user kie --env KIE_API_KEY=YOUR_KEY -- node /abs/path/to/kie-mcp-kit/server-js/kie_server.mjs
```

Or in any MCP client's config: `command: "node"`, `args: ["/abs/path/.../server-js/kie_server.mjs"]`,
`env: { "KIE_API_KEY": "…" }`. Same env vars as the Python build
(`KIE_API_KEY`, `KIE_BASE_URL`, `KIE_UPLOAD_URL`, `KIE_DOCS_BASE`, `KIE_WORKSPACE_DIR`).

Preview uses **jimp** (pure JS, no native binaries) so it bundles cleanly into a
`.mcpb`; previews are emitted as jpeg thumbnails.
