# KIE model knowledge — how each model actually works

Compiled from the live KIE docs (120 media models). **Find the row for the model
you're calling, then confirm the exact payload with `kie_fetch_model_docs`** — this
guide carries the non-obvious knowledge (which mode, how to feed a reference,
multishot, special features) that an OpenAPI spec alone won't tell you.

Reachable from any client via `kie_workflow_file("generate-anything", "references/models.md")`.
The full slug list is at the bottom — you can call **any** of them, not just the ones with notes.

---

## The rules

1. **A reference means reference-mode — never text-to-X.** A user's **product** or
   **character** photo goes into that model's reference input (columns below).
   Upload local files with `kie_upload_file` first. Never describe a supplied
   product/face in a text-only prompt.
2. **Don't chop what one generation does.** Seedance 2.5, Kling 3.0, Veo, Wan 2.6,
   PixVerse and others hold **multiple cuts in one render** — storyboard in the
   prompt, don't render "N clips and edit later".
3. **Faces & content.** Product refs and *style/archetype* looks are fine (generate
   an **original** character). Do NOT reproduce a real, recognizable third party's
   face without consent. Refuse toxic pairings. Several models expose a **`spicy` /
   NSFW** path — treat adult generation as the user's responsibility under KIE's and
   the destination platform's rules; never apply it to a real person, and note that
   `nsfw_checker:false` only disables KIE's filter layer, it is not an "adult unlock".

---

## VIDEO — pick by capability

| Model | slug | dur | max res | character/product ref | multishot | audio |
|---|---|---|---|---|---|---|
| **Seedance 2.5** ⭐ | `bytedance/seedance-2-5` | 4–30s | 1080p | `reference_image_urls` ≤30 (+video≤10, +audio≤10) | **YES, native** to 30s | native (`generate_audio` def true) |
| Seedance 2.0 (full) | `bytedance/seedance-2` | 4–15s | 1080p+ | `reference_image_urls` ≤9 | YES | native |
| Seedance 2.0 Fast | `bytedance/seedance-2-fast` | 4–15s | 720p | `reference_image_urls` ≤9 | limited | native |
| Seedance 2.0 Mini | `bytedance/seedance-2-mini` | 4–15s | 720p | `reference_image_urls` ≤9 | YES | native |
| Seedance 1.5 Pro | `bytedance/seedance-1.5-pro` | 4–12s | — | `input_urls` 0–2 only | no | opt-in (def false); **only tier with `fixed_lens`** (lock camera) |
| **Kling 3.0 Omni R2V** ⭐ | `kling-3.0-omni/reference-to-video` | 3–15s | 1080p | `elements[]`/`image_urls[]` — richest ref matrix | YES (`customize_multi_shots`+`multi_prompt` ≤6) | native |
| Kling 3.0 (legacy) | `kling-3.0/video` | 3–15s | 1080p | `kling_elements[]` ≤3 | YES (`multi_shots`+`multi_prompt` ≤5) | `sound` bool |
| Kling 2.6 | `kling-2.6/text-to-video`, `…/image-to-video` | 5/10s | 1080p | i2v: `image_urls` ≤1 (first frame) | no | native + dialogue |
| Kling 2.5 Turbo | `kling/v2-5-turbo-{text,image}-to-video-pro` | 5/10s | ~1080p | i2v: `image_url` ×1 | no | silent |
| Kling 2.1 | `kling/v2-1-master-image-to-video`, `…/v2-1-standard` | 5/10s | ~1080p | `image_url` ×1 (+`cfg_scale`,`negative_prompt`) | no | silent |
| **Veo 3.1** | `veo3`/`veo3_fast`/`veo3_lite` (`/api/v1/veo/generate`) | 4/6/8s | 4K | `imageUrls` REFERENCE_2_VIDEO 1–3 | YES (timestamp `[00:00-00:02]…`) | native, dialogue in quotes |
| **Sora 2 / Pro** | `sora-2-text-to-video`, `sora-2-pro-{text,image}-to-video` | per-10s | high | i2v `image_urls` (first frame); identity `character_id_list` | no | native synced; `remove_watermark` |
| Hailuo 2.3 / 02 | `hailuo/2-3-image-to-video-pro`, `hailuo/02-*` | 6/10s | 1080p | i2v `image_url` ×1 (02 adds `end_image_url`) | no | silent |
| **Wan 2.6** | `wan/2-6-{text,image,video}-to-video` | 5/10/15s | — | i2v `image_urls` ×1 | YES (`multi_shots` bool) | native + lip-sync |
| **Wan 2.7 R2V** ⭐ | `wan/2-7-r2v` | 2–10s | — | `reference_image[]`≤5 + `reference_video[]`≤5 (mixed) | composes refs | `reference_voice` |
| Wan 2.5 | `wan/2-5-{text,image}-to-video` | 5/10s | — | i2v `image_url` ×1 (talking avatar) | no | native + lip-sync |
| Wan 2.2 Animate | `wan/2-2-animate-move`, `…-replace` | source | — | **motion transfer / char-swap** (image + driving video) | no | none |
| **PixVerse V6** | `pixverse-v6/{text,image}-to-video` | 1–15s | — | i2v `image_urls`≤2; **Fusion** `image_references`≤7 (`reference-to-video`) | YES (`generate_multi_clip_switch`) | native |
| MiniMax H3 | `minimax-h3/{text,image,reference}-to-video` | 4–15s | — | R2V `reference_image_urls`≤9 (+video+audio) | YES | native + lip-sync |
| Runway Gen-4 | `/api/v1/runway/generate` (+ `/extend`, `/aleph`) | 5/10s | 1080p | `imageUrl` ×1; **Aleph** = v2v edit | no | silent |
| Grok Imagine | `grok-imagine/{text,image}-to-video` | 6–30s | — | i2v `image_urls`≤7 OR `task_id` | no | native + dialogue |
| HappyHorse 1.0/1.1 | `happyhorse/*`, `happyhorse-1-1/reference-to-video` | 3–15s | — | R2V `reference_image[]` 1–9 | YES | native |

**Special video modes worth knowing:**
- **Motion / camera control (puppeteer):** `kling-2.6/motion-control`, `kling-3.0/motion-control` — a character image reproduces the exact gestures + lip movement of a driving video (`input_urls` ×1 image + `video_urls` ×1). 3.0 adds `background_source`.
- **Video-to-video edit / restyle:** Runway `aleph`, `wan/2-6-video-to-video`, `wan/2-7-videoedit`, `happyhorse/video-edit`, `kling-3.0-omni/transformation`. Edit real footage by instruction (swap outfit, restyle, relight).
- **Extend / continue:** `pixverse-v6/extend`, `grok-imagine/extend`, Runway `/extend`, Veo Extend — append a segment to a prior clip (usually by its taskId).
- **First+last-frame transition:** Seedance/Veo/PixVerse `transition`/Hailuo-02 `end_image_url` — morph between two exact stills.
- **PixVerse templates:** `template_id` = ~50 viral/product effect presets.
- **Grok spicy:** `mode:'spicy'` on `grok-imagine/text-to-video` (direct) or image-to-video via `task_id` — adult path (see rule 3).

**Video prompt recipe:** Subject → Action → Environment → Camera → Light/Style → Constraints (~60–100 words). One camera move per shot; never stack conflicting moves. For i2v/refs, **don't re-describe looks** (the image supplies them) — spend words on motion; add "preserve design and colors". Multishot models: name the shots/beats explicitly (`Shot 1… Shot 2…` or timestamp bands).

---

## IMAGE — pick by capability

| Model | slug | reference param | max res | note |
|---|---|---|---|---|
| **GPT-Image-2** ⭐ | `gpt-image-2-text-to-image`, `…-image-to-image` | i2i `input_urls` ≤16 | 4K* | default; product-consistent edits. *2K/4K need non-1:1 aspect |
| GPT-Image-1.5 | `gpt-image/1.5-{text,image}-to-image` | i2i `input_urls` ≤16 | — | strongest likeness across edits; safety always on |
| **Nano Banana Pro / 2** | `google/pro-image-to-image`, `nano-banana-2` | `image_input[]` ≤14 | 4K | Gemini 3; text rendering + world knowledge |
| Nano Banana / Edit / 2-Lite | `google/nano-banana`, `…-edit`(≤10), `nano-banana-2-lite`(≤10) | `image_urls[]` | 1–2K | cheap compositing |
| **Seedream 4.5 Edit** | `seedream/4.5-edit` | `image_urls[]` ≤14 | 4K | widest ref fan-in |
| Seedream 5 Pro/Lite | `seedream/5-pro-image-to-image`(≤10), `…5-lite-image-to-image`(≤14) | `image_urls[]` | 2–4K | pro=fast precision; lite=cheap 4K |
| Seedream 4.0 | `bytedance/seedream-v4-{text-to-image,edit}` | edit `image_urls[]` ≤10 | 4K | **`max_images` 1–6** batch; `seed` |
| **Ideogram Character** | `ideogram/character`, `…-edit`, `…-remix` | `reference_image_urls` (1 used) | — | keep ONE character across scenes; remix separates char vs style refs |
| Ideogram V3 | `ideogram/v3-{text-to-image,edit,remix}` | v3-edit `image_url`+`mask_url` | — | best typography/logos |
| Flux-2 Pro/Flex | `flux-2/{pro,flex}-{text,image}-to-image` | i2i `input_urls` 1–8 | — | literal text/labels/logos, photoreal materials |
| Flux Kontext | `/api/v1/flux/kontext/generate` | `inputImage` ×1 | — | camelCase params; single-image edit |
| Imagen 4 / Fast / Ultra | `google/imagen4`, `…-fast`, `…-ultra` | **text-only, no ref** | — | photoreal + typography; safety always on |
| Qwen3 / Pro | `qwen3/{text-to-image,image-to-image}`, `qwen3/pro-*` | i2i `image_urls` 1–3 | 2K | compositing (subject+product+bg); CJK text |
| Qwen / Qwen-Edit | `qwen/{text-to-image,image-to-image,image-edit}` | `image_url` ×1 | — | best complex CJK text; `num_images` batch on edit |
| Z-Image Turbo | `z-image` | text-only | — | sub-second, open-source, bilingual text |

**Special image modes:** **layer decomposition** `seedream/5-pro-layer-decomposition` (split a flat image into editable transparent layers) · **segment map** `grok-imagine-image-2-0/segment-map` (returns masks, not an image) · consistency series: reuse the same reference across N calls (Ideogram Character / GPT-Image-1.5).

**Image prompt tips:** i2i → say *"use the provided product image exactly, do not redraw"*. For 2K/4K on GPT-Image, set an explicit non-1:1 aspect. Transient 500s → resubmit (failed submit costs 0).

---

## LIP-SYNC / TALKING AVATAR

| Model | slug | character | mouth driver | note |
|---|---|---|---|---|
| **OmniHuman 1.5** ⭐ | `omnihuman-1-5` | `image_url` ×1 (people/pets/anime) | `audio_url` | optional `prompt` steers camera/emotion; <60s. Pre-gate with `…/human-identification` |
| Kling AI Avatar | `kling/ai-avatar-standard`, `…-pro` | `image_url` ×1 (face) | `audio_url` | length = audio; Pro = 1080p |
| InfiniTalk | `infinitalk/from-audio` | `image_url` ×1 | `audio_url` | `prompt` mandatory |
| Volcengine lip-sync | `volcengine/video-to-video-lip-sync` | **existing video** `video_url` | `audio_url` | re-syncs footage; `separate_vocal` |
| Wan 2.5 i2v | `wan/2-5-image-to-video` | `image_url` ×1 | dialogue text | talking avatar from a still |
| Gemini Omni | `gemini-omni-character`→`gemini-omni-video` | register identity once → reuse | generative | reusable characterId + audio_ids (see recipe below) |

### Gemini Omni — talking-head reel recipe (one creator across scenes)

When one "creator" must persist across a multi-scene talking-head reel, Gemini Omni
beats Kling/Wan lip-sync (reusable identity + native multishot). Production pattern:

1. **Register the identity ONCE** → `gemini-omni-character` (text `descriptions` + 1 image [+ audio]) → `characterId`. An **original** character or one you have consent to use — not a real third party's face.
2. **Voice** → `gemini-omni-audio` → `audio_id`.
3. **Each scene** → `gemini-omni-video`:
   ```json
   {"model":"gemini-omni-video","input":{
     "prompt":"[persona] in [location]; [camera move]; speaks in [lang]: \"<line>\". End on a wide shot.",
     "character_ids":["<characterId>"], "audio_ids":["<audio_id>"],
     "seed":<FIXED>, "aspect_ratio":"9:16", "duration":"10",
     "image_url":"<prev_last_frame>", "image_urls":["<prev_last_frame>","<product_url>"]}}
   ```
4. **Continuity chain (the key trick):** after each scene, extract its **last frame**
   (ffmpeg) → `kie_upload_file` → pass as `image_url` of the NEXT scene. Stops the
   character/scene jumping between cuts.
5. **Fixed `seed` across all scenes** — stabilizes voice + face.
6. **Product image from scene 2 onward** (not the intro), via `image_urls`.
7. Concatenate scenes with ffmpeg → final reel.

Per-scene prompt shape: *persona + location + one camera move + the spoken line in
quotes + "end on a wide shot"* (so the last frame stitches to the next scene).

---

## AUDIO

**Suno (music)** — `POST /api/v1/generate` (+ suno-api endpoints), models V4 / V4_5 / V5 / V5_5.
- Generate: `customMode:false` (idea→lyrics+style) · `customMode:true`+`instrumental:false` (verbatim lyrics + `style`+`title`) · `instrumental:true` (UGC bed). Section tags `[Intro][Verse][Chorus][Drop][Outro][End]`. `duration` only on V5_5+custom.
- Extras: **persona** (`/generate-persona` → `personaId`, reuse voice/style on V5/V5.5) · **mashup** (2 tracks) · **add-instrumental / add-vocals** (over an uploaded stem) · **extend** · **stem separation** (`/vocal-removal`) · **timestamped lyrics** (`/get-timestamped-lyrics` → word-level sync for captions/karaoke).

**Speech (TTS)**
| Model | slug | note |
|---|---|---|
| ElevenLabs Turbo v2.5 | `elevenlabs/text-to-speech-turbo-2-5` | fast; 1 `voice`; `timestamps` |
| ElevenLabs Multilingual v2 | `elevenlabs/text-to-speech-multilingual-v2` | `stability`/`similarity_boost`/`style`/`speed`; 68 voices |
| **ElevenLabs Dialogue v3** ⭐ | `elevenlabs/text-to-dialogue-v3` | **multi-speaker**: `dialogue[]` of {text, voice}; inline emotion tags |
| **Gemini 3.1 Flash TTS** | `google/gemini-3-1-flash-tts` | most directable: `scene` + per-speaker accent/voice; multi-speaker |
| Audio isolation | `elevenlabs/audio-isolation` | strip noise/music → clean voice |

All TTS cap ~5000 chars/call → chunk long scripts.

---

## UTILITY (post-processing)

| Job | slug | note |
|---|---|---|
| Remove background | `recraft/remove-background` | subject on transparent — run before compositing |
| Upscale image | `topaz/image-upscale` (1/2/4×), `recraft/crisp-upscale` (fixed) | final polish |
| Upscale video | `topaz/video-upscale` (1/2/4×), `grok-imagine/upscale` (720/1080p, KIE task only) | |
| Human/subject detect | `omnihuman-1-5/subject-detection`, `…/human-identification` | masks / valid-human gate before paying |

---

## Full catalog (call any with `kie_fetch_model_docs`)

**Video:** bytedance/seedance-2, seedance-2-5, seedance-2-fast, seedance-2-mini, seedance-1.5-pro, v1-pro/lite-{text,image}-to-video(+fast) · kling-3.0/video, kling-3.0-omni/{text-to-video,image-to-video,reference-to-video,transformation}, kling/v3-turbo-{text,image}-to-video, kling/v2-5-turbo-{text,image}-to-video-pro, kling/v2-1-master-{text,image}-to-video, kling/v2-1-standard, kling-2.6/{text,image}-to-video · veo3/veo3_fast/veo3_lite · sora-2-{text,image}-to-video, sora-2-pro-{text,image}-to-video · hailuo/2-3-image-to-video-{pro,standard}, hailuo/02-{text,image}-to-video-{pro,standard} · wan/2-5-{text,image}-to-video, wan/2-6-{text,image,video}-to-video, wan/2-7-{text-to-video,image-to-video,r2v,videoedit}, wan/2-2-animate-{move,replace} · pixverse-v6/{text-to-video,image-to-video,transition,extend,reference-to-video} · minimax-h3/{text,image,reference}-to-video · runway generate/extend/aleph · grok-imagine/{text,image}-to-video, grok-imagine-video-1-5-preview, grok-imagine/extend · happyhorse/{text,image,reference}-to-video, happyhorse/video-edit, happyhorse-1-1/reference-to-video · gemini-omni-video

**Motion/lipsync:** kling-2.6/motion-control, kling-3.0/motion-control, kling/ai-avatar-{standard,pro} · omnihuman-1-5(+subject-detection,+human-identification) · infinitalk/from-audio · volcengine/video-to-video-lip-sync · gemini-omni-character

**Image:** gpt-image-2-{text,image}-to-image, gpt-image/1.5-{text,image}-to-image · google/nano-banana, nano-banana-edit, pro-image-to-image, nano-banana-2, nano-banana-2-lite · bytedance/seedream-v4-{text-to-image,edit}, seedream/4.5-{text-to-image,edit}, seedream/5-{lite,pro}-{text-to-image,image-to-image}, seedream/5-pro-layer-decomposition · flux-2/{pro,flex}-{text,image}-to-image, flux-kontext · google/imagen4(+fast,+ultra) · qwen/{text-to-image,image-to-image,image-edit}, qwen3/{text-to-image,image-to-image}, qwen3/pro-text-to-image, qwen2/* · ideogram/character, character-edit, character-remix, v3-{text-to-image,edit,remix} · z-image · grok-imagine/{text-to-image,image-to-image}, grok-imagine-image-2-0/{text-to-image,segment-edit,segment-map} · recraft/{remove-background,crisp-upscale} · topaz/{image,video}-upscale · 4o-image

**Audio:** suno (generate + persona/mashup/add-instrumental/add-vocals/extend/vocal-removal/get-timestamped-lyrics) · elevenlabs/{text-to-speech-turbo-2-5,text-to-speech-multilingual-v2,text-to-dialogue-v3,audio-isolation} · google/{gemini-2-5-pro-tts,gemini-3-1-flash-tts}, gemini-omni-audio

> ⚠️ Prices come back as `creditsConsumed` after the task (specs don't list them).
> On a model's first use in a session, read its kie.ai page for the credit rate,
> quote it (credits × $0.005), and wait for the go before submitting.
