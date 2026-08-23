---
name: youtube-factory
description: >
  Faceless YouTube video factory. Research a niche with a YouTube-data MCP
  (NexLev / vidIQ) → write a narration script → generate a picture every 5–7s
  on KIE → animate the opening shots → voice it with ElevenLabs → assemble.
  Built for documentary / educational / listicle faceless channels.

  MUST USE when the user wants a faceless YouTube video or channel content:
  "make a faceless YouTube video about X", "analyze this channel and give me
  video ideas", "write a script and generate the visuals", "фейслес ютуб",
  "нарезка под закадр", "разбери канал и предложи темы".

  NOT for short UGC product ads (use content-factory) or one-off assets
  (use generate-anything).
metadata:
  homepage: https://github.com/yasdelayu/kie-mcp-kit
---

# YouTube Factory — faceless YouTube videos on KIE.ai

Turn a niche or a competitor channel into a finished faceless video: research →
script → visuals (a new image every 5–7s) → animate the opener → voiceover →
assemble. Visuals and voice run through the KIE connector; channel research runs
through whatever **YouTube-data MCP** the user has (NexLev or vidIQ).

**Requires the KIE connector** (`kie_post`, `kie_get`, `kie_upload_file`,
`kie_download`, `kie_fetch_model_docs`). Channel research is **optional but
recommended** — if a NexLev or vidIQ MCP is connected, use it; otherwise fall
back to `WebSearch` / `WebFetch`.

## Operating rules

- **Button-driven.** Every routing/confirm question is one `AskUserQuestion` with
  2–4 buttons and a smart default. Only free text: the topic/niche or a channel URL.
- **Plain language.** Don't narrate tool names, taskIds, or polling. One friendly
  banner per stage; a short "done — [deliverable]" between stages.
- **Price gate.** Before any batch of image/video/voice generations, state the
  total in credits **and dollars** (credits × $0.005) and wait for the go. Billed
  on submit; never resubmit a live taskId.
- **YouTube AI-content hygiene.** Fully-static AI slideshows get suppressed.
  Always animate at least the first several shots (motion = "real video" signal),
  vary imagery every 5–7s, and layer in graphs/numbers overlays for authenticity.

Stage banners:

| Stage | Banner |
|---|---|
| 1 | **🔍 Stage 1: Niche & competitor research — starting now.** Pulling what's actually winning in this niche — top channels, outlier videos, hooks — and turning it into video angles. |
| 2 | **✍️ Stage 2: Script — starting now.** Writing the narration to match what performs in this niche, at the right length. |
| 3 | **🖼️ Stage 3: Visuals — starting now.** Generating a fresh image every few seconds of script, then animating the opening shots. |
| 4 | **🎙️ Stage 4: Voiceover — starting now.** Narrating the script with natural emphasis and pacing. |
| 5 | **🎬 Stage 5: Assembly kit — starting now.** Packaging the voiceover, visuals, and overlay graphics so you can drop them into an editor. |

---

## STAGE 1 — Niche & competitor research

Send the banner. Ask the user (single `AskUserQuestion`) for the entry point:
- "I have a competitor channel/video URL" (they paste it)
- "Just a topic/niche — find the winners for me" (they type the niche)
- "I already have a script — skip to visuals" → jump to Stage 3

Then research **silently** using the connected YouTube-data MCP (NexLev or vidIQ —
whichever is present; check the tool registry). Typical calls:
- Resolve / analyze the channel, pull its recent + outlier videos and stats.
- Grab transcripts of the top-performing videos (bulk transcript tools) to learn
  structure, hook, pacing, average length.
- Find adjacent winning channels / niche outliers and keyword demand.
If neither MCP is connected, use `WebSearch` for "[niche] YouTube trending / outliers
[month year]" and `WebFetch` a couple of top videos' pages.

Synthesize a short **Niche Brief**: audience psychology, the hooks and themes that
repeat in winners, thumbnail patterns, typical video length, and **5 video ideas
that are NOT already saturated among the competitors**. End with `AskUserQuestion`:
"Pick the video to build" — list the 5 ideas as buttons (+ "Suggest 5 more").

---

## STAGE 2 — Script

Pull 2–3 top competitor transcripts for the chosen angle (via the research MCP),
learn their structure, then write an original narration script for the chosen idea,
**matched to the competitors' typical length** (state the target minutes). Structure:
cold-open hook (first 5–10s) → promise → body beats → payoff → CTA.

**Quality pass (optional, on by default for non-English users):** translate the
script to the user's language, review for clarity and flow, then translate back to
English (or the target publish language). Fixes awkward phrasing the first draft missed.

Save `./youtube-factory-output/<slug>/script.md`. Present it, confirm via button
("Looks good — generate visuals" / "Tighten the hook" / "Change length/tone").

---

## STAGE 3 — Visuals (image every 5–7s, then animate the opener)

Send the banner. **Learn any model before first use** with `kie_fetch_model_docs`, and
load the model guide once: `kie_workflow_file("generate-anything", "references/models.md")`
— durations, reference inputs, multishot, audio. For a recurring on-screen character use
**Ideogram Character** (same reference across every still); voiceover via **ElevenLabs**
(chunk scripts >5000 chars, `timestamps:true` to sync captions). For a **talking on-camera
host** that persists across scenes, use the **Gemini Omni reel recipe** (reusable
`characterId`+`audio_id`, last-frame chaining, fixed seed — see the models guide).

**1. Break the script into shots.** One image per **5–7 seconds** of narration —
each shot's prompt derived from what the voiceover is saying at that moment. A
10-minute video ≈ 85–120 shots; a 3-minute ≈ 25–35. Compute the shot count from the
script's spoken length and confirm the number in the price line.

**2. Generate the stills** (`gpt-image-2-text-to-image`, or i2i with a reference for
a consistent subject), `aspect_ratio:"16:9"`, `resolution:"2K"`. Keep a consistent
visual style across the whole video (state the style once, repeat it in every prompt).
Batch them: submit, **save every taskId**, poll ~30s, download to
`./youtube-factory-output/<slug>/images/` as `shot-001.png`, `shot-002.png`, …
Pass `preview:false` to `kie_download` here — 100+ inline thumbnails would flood
the context; the files still land on disk.

**3. Animate the opening shots** (`bytedance/seedance-2-mini`, image→video, 5s,
16:9). Animate at least the **first 5 shots** (more if budget allows) so the video
opens with real motion — this is what dodges YouTube's static-AI-slideshow
suppression. `first_frame_url` = the still's URL; motion prompt = a slow push/pan or
the subject's natural movement; `generate_audio:false` (voiceover is separate).
Save to `./youtube-factory-output/<slug>/clips/`.

Gate before generating: one `AskUserQuestion` — "Generate [N] images + animate the
first [k]? (~[credits] cr / ~$[usd])" · "Yes, all" · "First 10 as a style test
(Recommended)" · "Change style first".

---

## STAGE 4 — Voiceover

Generate the narration with **ElevenLabs on KIE** (fetch the ElevenLabs model docs;
or use a dedicated ElevenLabs MCP if the user has one connected). Insert emphasis/
pacing so it doesn't sound flat — tag the script with cues like `[serious]`,
`[emphasis]`, `[pause]`, `[excited]` at the right beats before generating. Let the
user pick a voice via button (a few presets + "browse voices"). Download the audio to
`./youtube-factory-output/<slug>/voiceover.mp3`. If the video is long, generate per
section and concatenate. State the VO cost in the price line before generating.

---

## STAGE 5 — Assembly kit + overlay graphics

**1. Overlay graphics pack.** Generate ~10 supporting stills — charts, numbers,
stat cards, simple diagrams (`gpt-image-2`, transparent-friendly, `2K`) — to layer
over the base footage. These "data" overlays read as authored, not auto-generated.
Save to `./youtube-factory-output/<slug>/overlays/`.

**2. Package for the editor.** Write an assembly sheet (`assembly.md`) mapping the
timeline: voiceover as the spine → animated clips for the opener → static images with
a slow zoom for the rest, each timestamped to its script beat → overlay graphics at
their moments → suggested thumbnail. Everything is already in the output folder.

**3. Render (optional).** If the user wants the video assembled automatically rather
than in CapCut, offer to build it with **hyperframes** (HTML→video) from the assembly
sheet — voiceover + Ken Burns on the stills + the animated openers. Otherwise the kit
is ready to drop into CapCut / Premiere: voiceover track, clips, images-with-zoom,
text/overlay layer.

Final button: "Done — kit is ready" · "Render it with hyperframes" · "Make the
thumbnail" · "Run again for the next idea".

---

## Quick reference

- **Research MCP:** NexLev or vidIQ (check the tool registry; use whichever is
  connected — channel analytics, outliers, bulk transcripts, niche/keyword finders).
- **Balance:** `kie_get /api/v1/chat/credit` → `data`. Cost = credits × $0.005.
- **Standard KIE job:** POST `/api/v1/jobs/createTask` `{model,input}` → save `taskId`
  → GET `/api/v1/jobs/recordInfo?taskId=…` → `resultJson.resultUrls[]`.
- **Animate the opener** (≥5 shots) — static-only AI videos get suppressed.
- **Copyrighted studio names** get filtered — describe the style instead.
