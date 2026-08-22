---
name: content-factory
description: >
  Bulk UGC content factory on KIE.ai. A 5-stage pipeline — Research → Plan →
  Generate → Schedule → Cost report — that turns one product image into dozens
  of viral short videos plus an image asset pack, all generated through the KIE
  MCP connector (kie_post / kie_get / kie_upload_file / kie_download).

  MUST USE when the user wants to mass-produce marketing content: "make me 100
  UGC videos", "build a content campaign for this product", "generate a batch of
  ads/reels", "content factory", "виральные ролики пачкой", "контент-завод".

  NOT for one-off single generations (use generate-anything for a single asset).
metadata:
  homepage: https://github.com/yasdelayu/kie-mcp-kit
---

# Content Factory — bulk UGC campaigns on KIE.ai

A 5-stage pipeline: **Research → Plan → Generate → Schedule → Cost report.**
Everything is generated through the KIE connector's five tools; there is no
special "studio" API — you pick real KIE models and drive them directly.

**Requires the KIE connector** (`kie_post`, `kie_get`, `kie_upload_file`,
`kie_download`, `kie_fetch_model_docs`, resource `kie://models`). If those tools
aren't present, tell the user to install the KIE MCP Kit first.

## Operating rules

- **UGC-first.** Every campaign defaults to an even split across 5 UGC formats:
  UGC Entertainment · Street Interview · Unboxing · Product Review · ASMR.
- **Button-driven UX.** Every clarifying question is one `AskUserQuestion` with
  2–4 concrete buttons and a smart default. The only typing allowed is a product
  URL paste or an image attach. Never a free-form "type your answer" for routing.
- **Plain language.** The user is not a developer. Never narrate tool names,
  taskIds, model slugs, polling, or payload internals. Send ONE friendly stage
  banner when a stage starts; between stages a short "Stage N done — [deliverable]".
- **Price gate (inherited from generate-anything).** Before ANY batch submit,
  state the total cost in credits **and dollars** (credits × $0.005) and wait for
  the user's go. Cost is billed on submit — never resubmit a live taskId.
- **No on-screen text, ever.** Generated videos/images carry zero rendered text —
  no captions, subtitles, watermarks, lower-thirds. The "caption" field in the
  plan is social-post copy for the upload step only, never a generation instruction.

Stage banners (use these):

| Stage | Banner |
|---|---|
| 1 | **🔍 Stage 1: Research & ideas — starting now.** Scanning what's trending this week in your product's niche across TikTok, Instagram and YouTube, then turning it into 15+ viral ideas. |
| 2 | **🗂️ Stage 2: Content plan — starting now.** Building your full video plan as a polished HTML document — every video mapped, dated, ready to generate. |
| 3 | **🎬 Stage 3: Generating — starting now.** Producing your videos on KIE, one format batch at a time. I'll ask before each batch fires. |
| 4 | **📅 Stage 4: Scheduling — starting now.** Laying everything onto a calendar you approve (exportable, or pushed to Meta Ads if connected). |
| 5 | **💰 Stage 5: Cost report — starting now.** Compiling what you actually spent on KIE versus what this volume costs the traditional way. |

---

## ONBOARDING — run first, single message, no pauses

Send ONE `AskUserQuestion` covering A + B + C as buttons, plus the product-attach
prompt in the same message. The user clicks and attaches, then the pipeline runs.

- **A — Starting stage:** "Stage 1 — full pipeline (needs a product image)" ·
  "Stage 2 — build plan (I have a brief)" · "Stage 3 — generate now (I have a plan)" ·
  "Stage 4 — schedule (content ready)". Default: Stage 1.
- **B — Video volume:** "50" · "100 (Recommended)" · "150" · "200" · Other→any number.
  Store as `[VIDEO_COUNT]`. Compute `floor(N/5)` per format **silently** — do not
  show the split yet; it surfaces naturally inside the Stage 1 brief.
- **C — Output aspect:** "9:16 vertical (Recommended)" · "1:1 square" · "16:9 wide".
- **Product:** "Attach your product image OR drop a product URL — that's all I need."
  If an image is already attached, skip this. If they picked Stage 3/4, ask for the
  existing plan file instead.

**5-format even split** (`per_format = floor(VIDEO_COUNT/5)`; remainder distributed
from format 1):

| # | Format | KIE recipe (see Stage 3) |
|---|---|---|
| 1 | **UGC Entertainment** — challenge/dare, product is the punchline | still → i2v, audio on |
| 2 | **Street Interview** — sidewalk stranger with product | still → i2v (talking → Veo), audio on |
| 3 | **Unboxing** — premium reveal, hands + packaging | still → i2v, audio on (ASMR-leaning) |
| 4 | **Product Review** — honest talking-head, product in hand | still → i2v (talking → Veo), audio on |
| 5 | **ASMR** — sound-led close-ups, no VO | still → i2v, `generate_audio:true` |

Cinematic formats (Hyper Motion / TV Spot / Wild Card) stay OFF by default; only
add them on explicit request.

> 📚 **Idea source:** pull concept seeds, hook scenes, settings, per-format prompt
> patterns and the category→format map from
> [references/prompt-library.md](references/prompt-library.md) — in Stage 1 (to vary
> the 15+ ideas) and Stage 3 (to build each prompt). It's the default reference;
> an external content/reference MCP is an optional extra source, off by default (see the library).

---

## STAGE 1 — Trend research & viral ideas

Send the Stage 1 banner first. Then, **silently**:

1. **Auto-detect the product** from the image (category, variants/SKUs, palette,
   demographic cues) and, if a URL was given, `WebFetch` it for name/claims/voice.
   Do NOT ask the user to confirm niche/market/goal — auto-set (market defaults to
   "Global / English", goal to "awareness + conversion") and announce as one line.
2. **Run 8 trend searches** (`WebSearch`), replacing `[niche]` and `[month year]`:
   trending videos this week · viral Reels · YouTube Shorts · brand content going
   viral · top Meta ads · UGC trend · scroll-stopping hooks · competitor strategy.
   Do not enumerate the queries to the user.
3. **Fetch 2 best source pages** (`WebFetch`) for concrete hook lines / patterns.
4. **Synthesize the Viral Content Brief** — 15+ seed ideas, ≥75% UGC-family.

The brief is the ONLY place the numeric split appears before generation — weave it
in as "based on what's winning this week, here's the mix: 20 challenge clips · 20
sidewalk interviews · 20 unboxings · 20 reviews · 20 ASMR pours", framed as a
consequence of the trends, not a config rule.

Per idea, required fields:
```
N. [Title]
- Format: [1–5]
- Still prompt: [what the starting frame shows — person/hands + product, scene]
- Motion prompt: [what HAPPENS in the 5s — concrete verbs + one camera move]
- Video model: seedance-2-mini (default) | veo3 (if talking/lip-sync) | kling (multi-shot)
- Duration/aspect/audio: [4–15s] / [9:16|1:1|16:9] / [audio on/off]
- Social caption: [post copy for upload — NEVER rendered on screen]
- Inspired by / why viral now: [specific trend from research]
```

End Stage 1 with an `AskUserQuestion`: "Brief is UGC-first — proceed to Stage 2
(Recommended)" · "Add more UGC ideas" · "Swap secondary ideas" · "Adjust the mix".

---

## STAGE 2 — Video content plan

One `AskUserQuestion` (buttons, smart defaults) for campaign-level fields only:
campaign name (auto default) · date range ("Next 30 days (Recommended)" / 60 / 90) ·
variants (multiSelect of detected SKUs). Do NOT re-ask the split — it's already set.

Then generate one **HTML plan** with `[VIDEO_COUNT]` rows, grouped by format bucket
(order: Entertainment → Street Interview → Unboxing → Product Review → ASMR). Each
row: #, Date, Format, Still prompt, Motion prompt, Video model, Duration, Aspect,
Audio, Social caption, Goal. Vary the concept seed within each format so no two are
identical. Interleave formats across the date window so the feed isn't 20 reviews
in a row. Save to `./content-factory-output/<brand>/plan.html` (or `KIE_WORKSPACE_DIR`
if set). Present it, ask for button feedback before Stage 3.

---

## STAGE 3 — Generate on KIE (two-step, batch-gated)

> ⚠️ Ask permission before EACH format batch fires. Never auto-run the whole plan.

### Setup (silent)
1. **Register the product image once:** `kie_upload_file({ localPath })` → hosted URL.
   Reuse this URL as the reference for every still. (A friendly "getting your product
   ready…" line is fine; no tool names.)
2. **Learn any model you haven't used this session** with `kie_fetch_model_docs`
   before calling it. Defaults whose shapes are known: `gpt-image-2-text-to-image`,
   `gpt-image-2-image-to-image`, `bytedance/seedance-2-mini`. Veo/Suno use their own
   envelopes — fetch their docs first.

### The two-step recipe (per video)
KIE has no preset system — control the look in a **still**, then animate it. This
beats text→video for consistency.

**Step A — still** (`gpt-image-2-image-to-image`, product URL in `input_urls`):
```
kie_post /api/v1/jobs/createTask
{ "model":"gpt-image-2-image-to-image",
  "input":{ "prompt":"[Still prompt]. Product: [name + label/color from image]. Use the provided product image exactly, do not redraw. [format style cue].",
            "input_urls":["<product_url>"], "aspect_ratio":"[9:16|1:1|16:9]", "resolution":"2K" } }
```
Poll `recordInfo`, take `resultJson.resultUrls[0]` → upload it with `kie_upload_file`
(or pass the URL straight through) to use as the video's first frame.

**Step B — animate** (`bytedance/seedance-2-mini`, image→video):
```
kie_post /api/v1/jobs/createTask
{ "model":"bytedance/seedance-2-mini",
  "input":{ "prompt":"[Motion prompt — concrete verbs + one camera move]",
            "first_frame_url":"<still_url>", "resolution":"720p",
            "aspect_ratio":"[9:16|1:1|16:9]", "duration":5,
            "generate_audio":[true for ASMR/VO, false for a clean plate] } }
```

Format-specific routing:
- **Entertainment / ASMR:** Seedance i2v. ASMR → `generate_audio:true`, close-up
  handling prompt (pour, cap-unscrew, condensation), no VO.
- **Unboxing:** still of hands + packaging → Seedance i2v, audio on.
- **Street Interview / Product Review (talking):** KIE image→video lip-sync is weak.
  For real talking-head, route to **Veo 3.1** (`veo3`, its own `/api/v1/veo/generate`
  envelope — fetch docs) or keep it non-verbal (reaction/sip, caption carries the line).
  State the model swap in the price line.

### Batch gates
Process one format at a time in order 1→5. Before each batch, one `AskUserQuestion`:
> "Ready to generate the **[N] [format]** videos? (~[credits] cr / ~$[usd], [aspect], audio [on/off])"
> "Yes — generate all [N]" · "Start with 3 as a quality check (Recommended)" ·
> "Skip this batch" · "Change settings first"

On go: submit all stills for the batch, **save every taskId**, poll ~30s, download
finished stills, then submit the animations, poll, download to
`./content-factory-output/<brand>/videos/`. Show results, then auto-prompt the next
batch ("Generate next" / "Redo this one" / "Pause"). On `fail`, read `failMsg`, log
the row IDs, offer Retry/Skip — never silently drop.

### Image asset pack (after all video batches)
Fire ONE gate. Pack size = `floor(VIDEO_COUNT/5)`, split **40% Social (1:1) · 20%
Hero (16:9) · 20% With-people · 20% Without-people**. Generate via
`gpt-image-2-image-to-image` (product URL in `input_urls`, `resolution:"2K"`). Save to
`./content-factory-output/<brand>/asset-pack/` with descriptive names
(`social-01-…png`, `hero-02-…png`). Each prompt: product description + brand cues +
the asset's scene; "no text, no watermark".

**Standalone image-pack mode:** if the user asks only for the image pack ("just make
the static visuals"), skip Stages 1–2 and the video batches — register the product,
pick pack size via one button question (default 20), generate, save, done.

---

## STAGE 4 — Schedule / publish

First `AskUserQuestion`: "How do you want to schedule?"
- "Give me an exportable calendar (Recommended)" → write
  `./content-factory-output/<brand>/calendar.csv` — columns: Date · Time · Format ·
  Video file · Image file · Social caption · Goal · Notes. Then go to Stage 5.
- "Push to Meta Ads (I have the Meta MCP connected)" → if a Meta Ads MCP is available
  (search the tool registry), confirm objective/budget/dates via buttons, create
  campaigns + ad sets, upload the generated videos/images as creatives, schedule per
  the plan. If no Meta MCP is found, fall back to the CSV export and say so.

Never invent a Meta integration that isn't connected — default to the CSV.

---

## STAGE 5 — Cost comparison report

1. **Actual KIE spend:** sum `creditsConsumed` from every job's `recordInfo` in this
   run (stills + videos + image pack). USD = credits × **$0.005**. Current balance:
   `kie_get /api/v1/chat/credit` (`data` = number).
2. **Traditional cost model** (2026 industry-average midpoints, show low/mid/high):

| Asset | Low | Mid | High |
|---|--:|--:|--:|
| UGC creator video | 250 | 750 | 1,500 |
| Product Review video | 300 | 900 | 2,000 |
| Unboxing video | 300 | 800 | 1,500 |
| ASMR / close-up video | 250 | 700 | 1,400 |
| Street interview video | 300 | 900 | 1,800 |
| Social still (1:1) | 100 | 250 | 500 |
| Hero banner (16:9) | 1,000 | 2,500 | 5,000 |
| Product shot w/ people | 500 | 1,500 | 3,000 |
| Product shot w/o people | 200 | 700 | 1,500 |

3. **Compute:** `traditional_mid = Σ(count × mid)`; `savings% = 1 − kie_usd/traditional_mid`
   (cap 99.99%). Time: KIE render hours vs traditional weeks.
4. **Render HTML** to `./content-factory-output/<brand>/cost-report.html`: hero number
   card ("delivered for $X instead of $Y–$Z — saved N% and W weeks"), volume table,
   KIE spend breakdown (credits + USD at $0.005/cr), traditional breakdown (low/mid/high),
   side-by-side bars (plain HTML/CSS, no chart libs), time-savings panel, methodology
   footer (traditional = 2026 industry-average estimates, not a quote).
5. Present via button: "Done — close pipeline (Recommended)" · "Re-render with my own
   rate card" · "Run again for another product".

---

## Quick reference

- **Balance:** `kie_get /api/v1/chat/credit` → `data`.
- **Standard job:** POST `/api/v1/jobs/createTask` `{model,input}` → save `taskId` →
  GET `/api/v1/jobs/recordInfo?taskId=…` until `state:success` → `resultJson.resultUrls[]`.
- **Exceptions:** Veo (`/api/v1/veo/generate`, `successFlag`, resultUrls is a JSON
  string), Suno (`/api/v1/generate`). Fetch their docs before use.
- **Copyrighted studio names** ("Studio Ghibli") get filtered — describe the style.
- **Transient 500 on submit** → resubmit (costs 0). Never resubmit a live taskId.
