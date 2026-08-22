<div align="center">

<img src="assets/banner.png" alt="KIE MCP Kit" width="100%">

# 🎨 KIE MCP Kit

**Let your AI agent generate images, video, music and speech right in the chat — on the latest models.**

Seedance · Kling · Veo · GPT-Image-2 · Nano Banana · Flux · Suno · ElevenLabs — plus anything new KIE ships.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![KIE.ai](https://img.shields.io/badge/powered%20by-KIE.ai-black.svg)](https://kie.ai)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-ready-orange.svg)](https://docs.claude.com/en/docs/claude-code)
[![uv](https://img.shields.io/badge/runs%20on-uv-DE5FE9.svg)](https://docs.astral.sh/uv/)

**English** · [Русский](README.ru.md)

</div>

---

## What this is

A ready-to-use kit: **one MCP connector + three skills**, and your agent (Claude Code, Claude Desktop, Codex) can make any visual or audio asset — or a whole content campaign — from a plain-English request.

| Component | What it does |
|---|---|
| 🔌 **Connector** (`server/kie_server.py`) | A tiny MCP server: 5 generic tools that call [KIE.ai](https://kie.ai) — an aggregator of ~100 creative models. Deliberately "dumb": 5 generic tools instead of one per model, so a new KIE model works without touching the connector — the agent just reads its docs. |
| 🧠 **generate-anything** | Single assets. Catches your request → picks a model → reads its live docs → **quotes the price in dollars and waits for your go** → submits, polls, downloads. |
| 🏭 **content-factory** | Bulk UGC product ads. A 5-stage pipeline: research → plan → generate (still→video, in batches) → schedule → cost report. |
| 📺 **youtube-factory** | Faceless YouTube videos. Research a niche (NexLev/vidIQ) → script → a new image every 5–7s + animated openers → ElevenLabs voiceover → assembly kit. |

> 💡 You don't memorize commands. Say *"make a vertical UGC video of this bottle"* — the skill does the rest.

---

## Requirements

| Need | Why | Get it |
|---|---|---|
| A **KIE.ai API key** | Pays for and authorizes generations | [kie.ai](https://kie.ai) → Dashboard → API Keys |
| **[uv](https://docs.astral.sh/uv/)** | Runs the connector and auto-installs its Python deps | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| An **MCP client** | Drives the tools | Claude Code, Claude Desktop, or Codex |

The connector's Python dependencies (`fastmcp`, `requests`, `pillow`) are declared inline in the script — `uv` installs them into an ephemeral environment on first run. You never manage a venv.

---

## Install

### Step 1 — get your KIE key

Go to [kie.ai](https://kie.ai) → sign in → **Dashboard → API Keys** → create a key and copy it. Top up your balance there too (**1000 credits = $5**, i.e. **$0.005/credit**).

### Step 2 — one-command install (Claude Code)

```bash
git clone https://github.com/yasdelayu/kie-mcp-kit && cd kie-mcp-kit
KIE_API_KEY=YOUR_KEY ./install.sh
```

The script installs all three skills into `~/.claude/skills/` and registers the connector with Claude Code (user scope). Then jump to [Verify](#verify).

### Step 2 (alternative) — manual setup

<details open>
<summary><b>Claude Code</b></summary>

```bash
# from the cloned repo folder:
claude mcp add --scope user kie \
  --env KIE_API_KEY=YOUR_KEY \
  -- uv run "$(pwd)/server/kie_server.py"
```

`--scope user` makes it available in every project. To use a project scope instead, drop `--scope user`.
</details>

<details>
<summary><b>Codex CLI</b></summary>

```bash
codex mcp add kie \
  --env KIE_API_KEY=YOUR_KEY \
  -- uv run /path/to/kie-mcp-kit/server/kie_server.py
```
</details>

<details>
<summary><b>Claude Desktop / any MCP client</b></summary>

Add this to the client's MCP config (Claude Desktop: **Settings → Developer → Edit Config**):

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

Use an **absolute** path to `kie_server.py`. Fully quit and reopen the app afterward.
</details>

### Step 3 — install the skills (only if you set up the connector manually)

```bash
mkdir -p ~/.claude/skills
cp -r skill/generate-anything  ~/.claude/skills/generate-anything
cp -r skill/content-factory    ~/.claude/skills/content-factory
cp -r skill/youtube-factory    ~/.claude/skills/youtube-factory
```

---

## Verify

```bash
claude mcp list          # expect:  kie  ✓ Connected
```

Then, in Claude Code, ask for something small:

```text
How much would a 5-second 720p Seedance video cost?
```

The skill answers with a price and generates nothing. If that works, you're set. You can also smoke-test the server directly (no API key needed — it only checks the pure logic):

```bash
uv run server/kie_server.py --selftest      # prints: selftest ok
```

---

## Usage

You mostly just talk to the agent. Here's what triggers what.

### generate-anything — single assets

| Say this | What happens |
|---|---|
| `Draw a serene mountain cabin at golden hour, 9:16` | GPT-Image-2 image |
| `Make a 5s video of this product, UGC handheld` (+ attach a photo) | still → Seedance video |
| `An upbeat ~124 bpm instrumental to sit under a voiceover` | Suno track |
| `Voice this paragraph in a warm female voice` | ElevenLabs speech |
| `How much would a 10s Kling video cost?` | price only, no generation |

The flow every time: the skill **names the model + price in dollars** and waits for your **"go"**, then submits, polls, and downloads the file. Nothing is billed before you say go. Say *"stop asking, just generate"* to skip the wait (it still states the price).

### content-factory — bulk UGC product ads

Launch it:

```text
Build a content campaign for this product — 100 UGC videos. (attach product photo)
```

It runs 5 stages, each gated by a button choice you click:

1. **Research** — scans this week's trends in your product's niche → 15+ viral ideas.
2. **Plan** — a polished HTML plan: every video mapped, dated, split across 5 UGC formats (Entertainment · Street Interview · Unboxing · Product Review · ASMR).
3. **Generate** — for each idea: a product still (GPT-Image-2) → animated to video (Seedance), in batches you approve one at a time, plus an image asset pack.
4. **Schedule** — an exportable CSV calendar (or pushed to Meta Ads if you have that MCP).
5. **Cost report** — an HTML report: what you actually spent on KIE vs traditional production.

Idea variety is pulled from [`skill/content-factory/references/prompt-library.md`](skill/content-factory/references/prompt-library.md) — concept seeds, hook scenes, settings, and per-format prompt patterns.

Output lands in `./content-factory-output/<brand>/`.

### youtube-factory — faceless YouTube videos

Launch it:

```text
Analyze this channel and make a faceless video on the best untapped idea. (paste channel URL)
```

Stages: research the niche/competitors → write a narration script → generate one image every 5–7s and **animate the opening shots** (static-only AI videos get suppressed by YouTube) → voice it with ElevenLabs → package an assembly kit + overlay graphics ready for an editor.

> **Works in any MCP client, not just Claude Code.** The skills are also embedded in the
> connector: in a plain Claude Desktop chat, claude.ai, or Cursor — where file-based skills
> don't load — the agent calls `kie_workflows` to pull the same instructions and run the
> pipeline. In Claude Code the file skills auto-trigger; elsewhere the tool carries them.

Output lands in `./youtube-factory-output/<slug>/`.

---

## Optional integrations

The kit works on its own, but `youtube-factory` gets better with a YouTube-research MCP connected, and you can auto-assemble the final cut instead of editing by hand. All third-party — installed separately, not bundled here.

| Add | What it gives | Used for |
|---|---|---|
| [NexLev](https://nexlev.io) MCP | YouTube channel database — analytics, outliers, transcripts, a 20k+ niche finder. Has an official MCP for Claude. | Stage 1 research: find winning channels/videos and pull competitor transcripts |
| [vidIQ](https://vidiq.com) MCP | Channel analytics + keyword research on a larger database | Stage 1 research: alternative to or alongside NexLev |
| **HyperFrames** (Claude skill) | Renders finished video from HTML | Stage 5: auto-assemble the video instead of editing manually |
| [CapCut](https://www.capcut.com) | Manual video editor | Stage 5: hand-assemble from the kit's output |

> Without a research MCP, Stage 1 falls back to plain web search — it still works, just with less YouTube-specific data.

---

## Connector tools

| Tool | What it does |
|---|---|
| `kie_post(path, body)` | POST to any KIE endpoint — **submit** a task (usually `/api/v1/jobs/createTask`). |
| `kie_get(path)` | GET — **poll** status (`/api/v1/jobs/recordInfo?taskId=…`) or check balance. |
| `kie_upload_file(localPath, uploadPath?)` | Local media file → KIE-hosted URL (~3 days) for `@Image`/`@Video` references. |
| `kie_download(url, destPath, preview?)` | Save a result to disk (creates folders; media-only). For an image it also returns a small **inline preview** so it shows in the chat — `preview:false` to skip (batches). |
| `kie_workflows(workflow?)` | List the bundled workflows, or load one's full instructions. Works in **any** MCP client — no file-based skill needed. |
| `kie_workflow_file(workflow, path)` | Read a reference file a workflow points to (e.g. the prompt library). |
| `kie_fetch_model_docs(path\|url, force?)` | A model's live docs from docs.kie.ai (cached ~3 days). |
| resource `kie://models` | Live KIE model catalog — the starting point when the job isn't a default. |

**Job lifecycle:** `POST /api/v1/jobs/createTask {model, input}` → save `taskId` → `GET /api/v1/jobs/recordInfo?taskId=…` until `state:success` → download `resultJson.resultUrls[]`. Exceptions: **Veo** (`/api/v1/veo/generate`, `successFlag`) and **Suno** (`/api/v1/generate`) use their own envelopes — the skills fetch their docs first. **Balance:** `GET /api/v1/chat/credit` → `data` is the credit number.

---

## Environment variables

| Variable | Default | Required |
|---|---|---|
| `KIE_API_KEY` | — | **Yes** |
| `KIE_BASE_URL` | `https://api.kie.ai` | No |
| `KIE_UPLOAD_URL` | `https://kieai.redpandaai.co/api/file-stream-upload` | No |
| `KIE_DOCS_BASE` | `https://docs.kie.ai` | No |
| `KIE_WORKSPACE_DIR` | *(unset — the working directory is used)* | Recommended |

Set them in your MCP client's `env` block (see the config above). File tools are **always** confined to the workspace: `KIE_WORKSPACE_DIR` when set, otherwise the server's working directory. Point it at your project folder — a host-launched server can inherit an arbitrary working directory, and `/` or a bare home directory is refused outright.

---

## Security

- 🔑 The key lives in your client's settings / an env var, **never** in the repo.
- 🌐 The API key only reaches KIE hosts (`KIE_BASE_URL` / `KIE_UPLOAD_URL`); the connector refuses any other origin, and credentials are dropped on cross-origin redirects.
- 📁 Uploads/downloads are confined to the workspace (`KIE_WORKSPACE_DIR`, else the working directory), symlinks included; `/` and a bare home directory are refused.
- 🖼️ Both directions are restricted to an **allowlist** of media types, so a script, executable, or dotfile destination is never reachable — including names Windows would rewrite (`clip.mp4.` → `clip.mp4`).

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `uv: command not found` | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh`, then restart the shell. |
| `claude mcp list` shows `kie ✗` | Check the path to `server/kie_server.py` is absolute and correct; confirm `KIE_API_KEY` is set in the client's env; restart the client. |
| `Blocked: … may only reach …` | You pointed a tool at a non-KIE host. Leave `KIE_BASE_URL`/`KIE_UPLOAD_URL` at defaults unless KIE tells you otherwise. |
| `500` on submit | Transient — resubmit. A failed submit costs 0 credits. |
| Job `state: fail` | Read `failMsg`. Filter rejections (e.g. a copyrighted studio name) need a reworked prompt, not a retry. |
| Not enough credits | Top up at kie.ai. Ask *"how much do I have left?"* to check the balance. |

---

## Update & uninstall

```bash
# update
cd kie-mcp-kit && git pull                        # connector updates apply on the next restart
KIE_API_KEY=YOUR_KEY ./install.sh --force         # only if the skills changed

# uninstall
claude mcp remove kie
rm -rf ~/.claude/skills/{generate-anything,content-factory,youtube-factory}
```

---

## Support

If this kit saves you time, you can tip the author:

- **USDT (TRC-20):** `TWVSReEvpN4fqDQHMPzmo5zM4ij9iB44CH` → [view on Tronscan](https://tronscan.org/#/address/TWVSReEvpN4fqDQHMPzmo5zM4ij9iB44CH)

> ⚠️ **TRC-20 (TRON) network only** — sending USDT on any other network will lose the funds. Tips support this open-source kit; they don't go to KIE.ai or the model vendors.

---

## Credits & license

- 🔌 **Connector** — [@yasdelayu](https://github.com/yasdelayu), an original 5-tool MCP implementation over the [KIE.ai API](https://docs.kie.ai). MIT.
- 🧠 **generate-anything** skill — Anthropic.
- 🏭 **content-factory** / 📺 **youtube-factory** — by @yasdelayu (MIT). Original KIE-native content pipelines.
- **[KIE.ai](https://kie.ai)** — the third-party model aggregator the connector talks to (not affiliated). NexLev / vidIQ are third-party MCPs used only when you connect them.

See [CREDITS.md](CREDITS.md). License — [MIT](LICENSE).
