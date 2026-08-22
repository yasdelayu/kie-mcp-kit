# Prompt library — concept seeds, hook scenes, settings, style cues

Model-agnostic creative scaffolding for the 5 UGC formats. Pull from here in
Stage 1 (idea generation) and Stage 3 (prompt building) so no two videos in the
same format share a concept. These are **prompt ideas**, not API presets — feed
them into KIE model prompts.

> Adapted from Anthropic's `higgsfield-content-factory` creative material. The
> Higgsfield-specific mechanics (preset slugs, hook/setting UUIDs, avatars) are
> intentionally dropped — only the reusable concept language is kept.

---

## Format 1 — UGC Entertainment
Challenge / dare / entertainment-first. Product is the punchline, not the subject. Audio on.

**Concept seeds:**
- Blind taste try — "guess which one is [brand]"
- "I'll give you $100 if you try it" street challenge
- "Will it pour?" — pour the product onto something absurd
- Product flies into frame → deadpan reaction
- Failed dare → recover → pivot to a quick review
- Epic-fail stumble → land badly → unbothered product hold

**Scene/hook flavor:** product hit, product dodge, near-miss crash, random-object mic, epic fail, camera bump.
**Style cue:** energetic, handheld, natural daylight, fast cut-in, real-person energy.

## Format 2 — Street Interview
Sidewalk stranger interviews, product appears mid-conversation. High-trust "real people". Setting: street. Audio on.

**Concept seeds:**
- "What's your favorite [niche] right now?" → stranger pulls the product from a bag
- "Sing for the product" — sing a jingle, get the bottle
- "Rate this out of 10" — sip, then score
- "Try this on a hot day" → first-sip face from a real stranger
- "Trade me your coffee for this" — bartering bit
- Two strangers, blind opinion → brand reveal

**Scene/hook flavor:** interview framing, mic-in-frame, candid sidewalk.
**Style cue:** documentary handheld, street ambient, natural light, authentic phone-quality.

## Format 3 — Unboxing
Premium reveal energy — hands, packaging, the moment of discovery. Audio on (ASMR-leaning).

**Concept seeds:**
- Trio reveal — three flavors/variants nestled in pastel paper
- Single-item solo drop with slow ribbon-pull
- Subscription box with a hand-written brand note
- Premium gift-set unbox, ribbon-tied, hangtag macro
- Hangtag close-up series — tags swinging
- Crate / "picked today" reveal

**Style cue:** close-up hands, tactile packaging, soft key light, slow reveal, crinkle/ribbon sound.

## Format 4 — Product Review
Honest talking-head — product in hand, ingredients read aloud, rankings, comparisons. Audio on.
(For real lip-synced talking, route to Veo 3.1; otherwise keep it non-verbal + caption.)

**Concept seeds:**
- Two-ingredient test — read the label, raise eyebrow, sip
- "Cold side of the fridge" ranking — "always [flavor], don't @ me"
- Side-by-side — generic competitor vs the hero product
- 7-day diary — empty bottles on the counter, "I tried this for a week"
- Beauty-editor mirror review (bathroom, close mirror)
- Final flavor ranking — all variants lined up, ranked on camera

**Style cue:** talking-head medium shot, product held to camera, honest tone, soft room light.

## Format 5 — ASMR
Sound-led close-ups. No VO, caption-only. `generate_audio:true`. Intimate settings only (kitchen/bathroom/bedroom).

**Concept seeds:**
- Macro cap-unscrew + glug pour into an iced glass
- Condensation-bead slide on a chilled bottle, then open
- Spoon-clink + ice-drop into a tall glass, product pouring in
- Bottle-on-marble tap-and-rotate with audible shifts
- Ribbon-pull / paper rustle (crossover with Unboxing)
- Two bottles clinking gently, no soundtrack

**Style cue:** extreme close-up, shallow depth, no music, audible product handling, condensation, glass clinks.

---

## Setting ideas (pick to vary scenes)
**Realistic:** Bedroom · Bathroom · Kitchen · Office · In Car · Street · Gym · Nature.
**Stylized (use sparingly):** Airplane Wing · Rooftop · Tiny-reviewer scale · Car Roof.

## Product-category → format emphasis
Not every format fits every product — weight the mix toward what fits, redistributing
excluded shares back into `ugc`/review first.

| Category | Lean into |
|---|---|
| Single-SKU beverage | Entertainment · Review · ASMR (+ Hyper Motion / TV Spot if cinematic requested) |
| Beverage with recipe angle | + Tutorial |
| Multi-SKU / gift box | + Unboxing |
| Food (snack/bar/sauce) | Entertainment · Review · ASMR · Tutorial |
| Skincare / beauty | Review · Unboxing · Tutorial · ASMR |
| Apparel / eyewear | Review · try-on angles · Entertainment |
| Electronics / gadget | Review · Unboxing · Tutorial |
| Software / app | Review · Tutorial (no physical hero — skip ASMR/Unboxing) |

## Prompt template (Stage 3 — every still & clip)
```
[Concept seed, made concrete for this product].
Product: [name], [color / packaging / label detail from the image]. Use the provided
product image exactly, do not redraw.
Style: [format style cue above].
Negative: no text overlay, no captions, no subtitles, no watermark, no lower-third,
no on-screen typography. Clean image only.
```

## Optional — live Higgsfield refs (off by default)
If the user has a **Higgsfield MCP connected** and explicitly wants it, you may query
its live presets/hooks/settings for extra reference variety, then translate the
returned ideas into KIE prompts using the template above. This is a reference-only
enrichment — generation still happens on KIE. Never require Higgsfield; this library
is the default source.
