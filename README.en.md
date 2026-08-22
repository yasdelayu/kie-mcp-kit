<div align="center">

<img src="assets/banner.png" alt="KIE MCP Kit" width="100%">

# 🎨 KIE MCP Kit

**Let your AI agent generate images, video, music and speech right in the chat — on the latest models.**

Seedance · Kling · Veo · Sora 2 · GPT-Image-2 · Nano Banana · Flux · Suno · ElevenLabs — plus anything new KIE ships.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![KIE.ai](https://img.shields.io/badge/powered%20by-KIE.ai-black.svg)](https://kie.ai)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-ready-orange.svg)](https://docs.claude.com/en/docs/claude-code)

[Русский](README.md) · **English**

</div>

---

## What this is

A ready-to-use kit in two parts — your agent (Claude Code, Claude Desktop, Codex) can make any visual or audio asset from a plain-English request.

| Component | What it does |
|---|---|
| 🔌 **Connector** (`server/kie_server.py`) | A tiny MCP server: 5 generic tools that call [KIE.ai](https://kie.ai) — an aggregator of ~100 creative models. Deliberately "dumb": 5 generic tools instead of one per model. When KIE ships a new model, the connector doesn't change — the agent reads its docs. |
| 🧠 **Skill** (`skill/generate-anything`) | The brains. Catches your request → picks a model → reads its live docs for the payload shape → **quotes the price in dollars and waits for your go** → submits, polls, downloads the file. |

> 💡 You don't memorize commands. Say *"make a vertical UGC video of this bottle"* — the skill does the rest.

---

## Setup in 3 steps

### Step 1 — KIE.ai key

Go to [kie.ai](https://kie.ai) → sign in → **Dashboard → API Keys** → create a key and copy it. Top up your balance there too (1000 credits = $5).

### Step 2 — connector + skill

You need [`uv`](https://docs.astral.sh/uv/) — it runs the server and auto-installs its deps (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

**Fastest path (Claude Code)** — the script installs both the skill and the connector:

```bash
git clone https://github.com/yasdelayu/kie-mcp-kit && cd kie-mcp-kit
KIE_API_KEY=YOUR_KEY ./install.sh
```

<details>
<summary>Or set it up manually / another client</summary>

**Claude Code:**
```bash
claude mcp add --scope user kie --env KIE_API_KEY=YOUR_KEY -- uv run /path/to/kie-mcp-kit/server/kie_server.py
```
Check: `claude mcp list` → `kie ✓ Connected`.

**Codex CLI:**
```bash
codex mcp add kie --env KIE_API_KEY=YOUR_KEY -- uv run /path/to/kie-mcp-kit/server/kie_server.py
```

**Claude Desktop / any MCP client** — add to the config:
```json
{
  "mcpServers": {
    "kie": {
      "command": "uv",
      "args": ["run", "/path/to/kie-mcp-kit/server/kie_server.py"],
      "env": { "KIE_API_KEY": "YOUR_KEY" }
    }
  }
}
```
</details>

### Step 3 — the skill (if you registered the connector manually)

```bash
cp -r skill/generate-anything ~/.claude/skills/generate-anything
```

---

## How to use

The flow is always the same:

1. Ask in plain language: *"a ~124 bpm instrumental track to sit under a voiceover"*
2. The skill quotes the price: *"Suno V4 — ~X cr (~$Y). Go?"* — **nothing is billed before your go**
3. You say go → submit → poll → file on disk

| Job | What to say | Default model |
|---|---|---|
| Image from text | "draw …" | GPT-Image-2 |
| Image from references | "edit this photo …" + attach | GPT-Image-2 i2i |
| Video from text | "make a video …" | Seedance 2.0 Mini |
| Video from a still | "animate this photo" + attach | Seedance + first_frame |
| Music | "a track …" | Suno |
| Speech / voiceover | "voice this …" | ElevenLabs |
| Upscale, talking head, remove-bg, 4K | just ask | picks from ~100 models |

**Tips:**
- *"How much would X cost?"* — it calculates and answers, generating nothing.
- Local file as a reference — attach the path, the skill uploads it to KIE for you.
- Best video = two steps: make the still first (control the look), then animate it.
- Text drifts in video → bake it into the starting still, not the video prompt.
- ⚠️ Studio names ("Studio Ghibli") get filtered — describe the style instead.
- `500` on submit → just resubmit (costs 0). `fail` → read `failMsg` first.
- Tired of confirmations? Say *"stop asking, just generate"* — it still states the price.

**Price:** credits × **$0.005**. Balance: *"how much do I have left?"* → the skill hits `GET /api/v1/chat/credit`.

---

## Connector tools

| Tool | What it does |
|---|---|
| `kie_post(path, body)` | POST to any KIE endpoint — **submit** a task (usually `/api/v1/jobs/createTask`). |
| `kie_get(path)` | GET — **poll** status (`/api/v1/jobs/recordInfo?taskId=…`). |
| `kie_upload_file(localPath, uploadPath?)` | Local media file → KIE-hosted URL (~3 days) for `@Image`/`@Video`. |
| `kie_download(url, destPath)` | Save a result to disk (creates folders). |
| `kie_fetch_model_docs(path\|url, force?)` | A model's live docs from docs.kie.ai (cached ~3 days). |
| resource `kie://models` | Live KIE model catalog — the starting point when the job isn't a default. |

---

## Security

- 🔑 The key lives in your client's settings / an env var, **not** in the repo.
- 🌐 The API key only reaches KIE hosts (`KIE_BASE_URL` / `KIE_UPLOAD_URL`); the connector refuses any other origin.
- 📁 Set `KIE_WORKSPACE_DIR` to your project folder — file reads/writes are then confined to it (it refuses `/` or a bare `~`).
- 🖼️ Uploads are known media types only; downloads refuse script/executable destinations.

---

## Credits & license

- 🔌 **Connector** — [@yasdelayu](https://github.com/yasdelayu), an original 5-tool MCP implementation over the [KIE.ai API](https://docs.kie.ai). MIT.
- 🧠 **`generate-anything` skill** — Anthropic.
- **[KIE.ai](https://kie.ai)** — the third-party model aggregator the connector talks to (not affiliated).

See [CREDITS.md](CREDITS.md). License — [MIT](LICENSE).
