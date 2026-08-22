# KIE model knowledge — how each model actually works

Practical cheatsheet compiled from the live KIE docs. **Read the row for the model
you're about to call**, then confirm the exact payload with `kie_fetch_model_docs`
(specs drift). This exists so you never guess a model's behaviour.

Reachable from any client via `kie_workflow_file("generate-anything", "references/models.md")`.

---

## The three rules that were being broken

1. **A reference means reference-mode — never text-to-X.** If the user attached or
   named a photo of a **product** or a **character**, you MUST route it into that
   model's reference input (below), not describe it in a text-to-image/video prompt.
   Upload local files with `kie_upload_file` first, then pass the returned URL.
2. **Don't chop what the model does in one shot.** Seedance and Veo hold **multiple
   cuts inside one generation** (storyboard prompting). Don't render "4 clips of 4s
   and edit later" for a job one 10s multishot generation does natively.
3. **Faces policy.** Product refs → always fine. A *style / archetype* (a cowboy
   monkey, a "Y2K girl" look) → fine, generate an **original** character in that
   aesthetic. A **real, recognizable third party's face** without consent → do NOT
   reproduce it (right-of-publicity / deepfake); take the aesthetic, not the face.
   Refuse toxic pairings outright (e.g. an intimate/adult product staged in a
   child's room). Don't over-refuse: only the recognizable-real-face case is off.

---

## Video

### Seedance 2.0 — the workhorse (text→video, image→video, reference→video)
- **Slugs:** `bytedance/seedance-2` (full: up to **1080p/4K**, multishot is its headline) · `bytedance/seedance-2-mini` (480p/720p, cheaper). Standard `createTask`/`recordInfo`.
- **Duration:** integer **4–15s, one file** (default 5). 10s = one generation, not four clips.
- **Aspect:** 1:1 · 4:3 · 3:4 · 16:9 · 9:16 · 21:9 · adaptive. **Audio:** native, `generate_audio` (default **true**; set **false** when you'll add your own track).
- **Three INPUT MODES — mutually exclusive, pick one per call:**
  1. `first_frame_url` — start from this exact image (i2v).
  2. `first_frame_url` + `last_frame_url` — interpolate between two exact keyframes.
  3. `reference_image_urls` (array, up to 9) + optional `reference_video_urls` (≤3, copy motion) + `reference_audio_urls` (≤3) — **this is how you feed a character/product/style ref.** You cannot also pass a first_frame in the same call.
- **Multishot:** YES. Declare the structure, then number shots in the prompt:
  `"Total 15s, 6 shots, 9:16. Shot 1: … Shot 2: …"` (full model) or timestamp bands
  `"0–3s wide … 3–6s medium …"`. Keep the SAME reference image across shots to hold identity. Best at 10–15s; at 4–5s keep one subject / one action / one camera move.
- **Prompt recipe:** Subject → Action → Environment → Camera → Light/Style → Constraints, ~60–100 words. One camera move per shot (dolly-in, orbit, tracking, crane, rack-focus); never stack conflicting moves. For i2v/refs, **don't re-describe looks** (the image supplies them) — spend words on motion; add "preserve design and colors".

### Kling v2.1 / v2.5 — clean single shots, NOT multishot
- **Slugs (per mode/tier):** `kling/v2-5-turbo-text-to-video-pro`, `kling/v2-5-turbo-image-to-video-pro`, `kling/v2-1-master-text-to-video`, plus `ai-avatar-*`. ~1080p (Pro/Master). Standard `createTask`.
- **Duration:** `"5"` or `"10"` seconds (string). Avatar models: length = the driving audio (≤5 min).
- **Reference:** exactly **ONE** still via `input.image_url` (becomes the first frame). **No multi-image ref, no identity token, no "elements".** For a product/character, that single image is your only anchor.
- **Multishot:** **No** — one prompt = one continuous shot. Hard cuts inside a prompt are unreliable. **Audio:** silent (except `ai-avatar-*`, which lip-syncs to `input.audio_url`).
- **Use when:** you want one polished 5/10s beat, cleaner motion than Seedance, and don't need cuts or multi-ref.

### Veo 3.1 — cinematic, dialogue-friendly, timestamp multishot
- **Non-standard envelope:** `model` = `veo3` (Quality) / `veo3_fast` (default) / `veo3_lite`; submit `POST /api/v1/veo/generate`, poll `GET /api/v1/veo/record-info`, `successFlag` 0/1/2/3, `data.resultUrls` is a **JSON-encoded string** (parse it). Fetch its docs before first use.
- **Duration:** 4 / 6 / 8s (default 8; REFERENCE mode forced to 8). >8s → Extend endpoint. **Res:** 720p/1080p/4K, 16:9 or true-vertical 9:16.
- **Reference:** one param `imageUrls` (array); the **mode** decides meaning — first-frame (1 img), first+last (2 imgs), or **REFERENCE_2_VIDEO** (1–3 "ingredient" images for character/product). With references, **describe interactions/actions, not appearance** (the images define looks) — this is what holds consistency.
- **Multishot:** YES via **timestamp prompting**: `[00:00-00:02] shot … [00:02-00:04] reverse … [00:06-00:08] wide crane`. **Audio:** native (dialogue in "quotes", SFX by description) — no on/off param, drive it in the prompt.
- **Use when:** you need real dialogue/lip-sync feel, cinematic register, or precise beat timing. Route talking-head UGC here rather than forcing Seedance.

---

## Image

### GPT-Image-2 — default image + product-consistent edits
- **Slugs:** `gpt-image-2-text-to-image` (prompt only) · `gpt-image-2-image-to-image` (**refs**). Standard `createTask`.
- **Reference/product:** i2i takes `input.input_urls` — a JSON array of **up to 16** image URLs; for i2i **both** `prompt` and `input_urls` are required. The images *are* the reference (no separate mask/subject param). Say *"use the provided product image exactly, do not redraw."*
- **Res/aspect:** `resolution` 1K/2K/4K — **2K/4K need an explicit non-1:1 `aspect_ratio`** (auto/1:1 fall back to 1K). Aspects incl. 9:16, 16:9, 3:4, 2:3, 2:1…
- **No multishot** (single still). A "storyboard look" = one image with panels, described in the prompt. Transient 500s: just resubmit (failed submit costs 0).

### Nano Banana (Gemini) — strong edits / multi-image blend
- **Slugs:** `google/nano-banana` (text-only, **no ref input**) · `google/nano-banana-edit` (refs via `input.image_urls`, up to 10) · `google/pro-image-to-image` = nano-banana-pro (refs via `input.image_input`). ~1024px native (base/edit).
- **Use when:** compositing several references into one (product + scene + style), or edits GPT-Image handles worse. Assign each ref's role in the prompt.

### Ideogram Character — keep ONE character consistent across scenes
- **Slugs:** `ideogram/character` (put a referenced person into a new scene) · `ideogram/character-remix` (re-render a base image in a new prompt). Ref via `input.reference_image_urls` — **only 1 image is used** (extras ignored); upload it first, ≤10MB. It anchors identity to face+hair.
- **Use when:** you need the *same* character across multiple stills/shots. Make **N separate generations** reusing the same reference (there's no multi-shot output). This is the right tool for a recurring UGC "creator" identity.

---

## Audio

### Suno — music
- **Non-standard envelope:** `POST /api/v1/generate`, poll `GET /api/v1/generate/record-info`; `model` = V4 / V4_5 / V4_5PLUS / V5 / V5_5; states PENDING / TEXT_SUCCESS / FIRST_SUCCESS / SUCCESS / *_FAILED. Returns **2 variations**.
- **Modes:** `customMode:false` (give an idea, Suno writes lyrics+style) · `customMode:true` + `instrumental:false` (your `prompt` = verbatim lyrics; `style`+`title` required) · `instrumental:true` (no vocals — the option for a UGC bed).
- **Duration:** only **V5_5 + customMode** exposes `duration` (10–360s, default 20); others are model-capped (V4 ~4min, V4_5 ~8min). Structure a song with inline tags `[Intro] [Verse] [Chorus] [Drop] [Outro] [End]`.
- **For a UGC bed:** `instrumental:true`, name genre+tempo+instrumentation, "mixed to sit under a voiceover".

### ElevenLabs — text-to-speech
- **Slug:** `elevenlabs/text-to-speech-turbo-2-5`. Standard `createTask`. Output MP3.
- **Voice:** ONE `voice` per call (preset name like "Rachel"/"Adam" or a voice ID; default James). Preview: `https://static.aiquickdraw.com/elevenlabs/voice/<voice_id>.mp3`. 32 languages. `timestamps:true` returns per-word timing (useful for caption/animation sync).
- **Limits:** 5000 chars/call (~5–6 min) — **chunk long scripts** and chain with `previous_text`/`next_text` for continuity. No multi-speaker/dialogue here (that's Eleven v3, not exposed) and no voice-clone upload on this endpoint.

---

## Quick routing

| Need | Model | Ref goes in |
|---|---|---|
| Product/character in a **video**, multishot, audio | Seedance 2.0 (full) | `reference_image_urls` (≤9) |
| Cheaper video, ≤720p | Seedance 2.0 Mini | `reference_image_urls` |
| One clean 5/10s shot, best motion | Kling v2.5 | `input.image_url` (1 only) |
| Dialogue / cinematic / exact beat timing | Veo 3.1 | `imageUrls` (REFERENCE_2_VIDEO) |
| Product-consistent **still** | GPT-Image-2 i2i | `input_urls` (≤16) |
| Composite several refs into one still | Nano Banana Edit | `image_urls` (≤10) |
| **Same character** across many stills | Ideogram Character | `reference_image_urls` (1) |
| Music bed | Suno (`instrumental:true`) | — |
| Voiceover | ElevenLabs | — |

> ⚠️ Prices aren't in the specs — they come back as `creditsConsumed` after the task.
> On a model's first use in a session, read its kie.ai page for the live credit rate,
> quote it (credits × $0.005), and wait for the go before submitting.
