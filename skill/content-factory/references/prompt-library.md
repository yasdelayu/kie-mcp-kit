# Prompt library — concept seeds, hook scenes, settings, style cues

Model-agnostic creative scaffolding for the 5 UGC formats — a compilation of
common short-form ad tropes. Pull from here in Stage 1 (idea generation) and
Stage 3 (prompt building) so no two videos in the same format share a concept.
These are **prompt ideas**, not API presets — feed them into KIE model prompts.

---

## Format 1 — UGC Entertainment
Challenge / dare / entertainment-first. The product is the punchline, not the subject. Audio on.

**Concept seeds:**
- Blind pick — line up look-alikes and guess which one is the brand
- Bribe-to-try — offer a stranger cash to taste/use it on the spot
- Absurd stress test — put the product through a ridiculous "does it survive?" moment
- Product launches into frame → straight-faced reaction
- Botched dare → shrug it off → cut to a quick verdict
- Pratfall bit → clumsy landing → product held perfectly intact

**Scene/hook flavor:** impact moment, dodge, near-miss, mic-to-a-random-object, comedic fail, jolt of the camera.
**Style cue:** high-energy, handheld, natural daylight, quick cut-in, real-person feel.

## Format 2 — Street Interview
Sidewalk stranger interviews; the product appears mid-conversation. "Real people" trust. Setting: street. Audio on.

**Concept seeds:**
- "What are you into in [niche] lately?" → they pull the product out of a bag
- Perform-for-it — do a small bit, earn the product
- On-the-spot score — try it, then rate it out of ten
- Hot-day handoff — offer it to a passerby, catch the first reaction
- Swap bit — trade them something for their current drink/item
- Two strangers give blind takes → reveal the brand after

**Scene/hook flavor:** interview framing, mic in shot, candid sidewalk.
**Style cue:** documentary handheld, street ambience, natural light, authentic phone quality.

## Format 3 — Unboxing
Premium reveal energy — hands, packaging, the moment of discovery. Audio on (ASMR-leaning).

**Concept seeds:**
- Variant trio nestled in soft tissue, opened one by one
- Single item, slow ribbon-pull reveal
- Subscription box with a hand-written note
- Gift set, ribbon-tied, close macro on the tag
- Tag/label detail series in tight close-up
- Rustic crate or "just picked" reveal

**Style cue:** close-up hands, tactile packaging, soft key light, slow reveal, crinkle/ribbon sound.

## Format 4 — Product Review
Honest talking-head — product in hand, ingredients read aloud, rankings, comparisons. Audio on.
(For real lip-synced talking, route to Veo; otherwise keep it non-verbal + caption.)

**Concept seeds:**
- Label read — check the ingredients on camera, react, taste
- Opinionated ranking — "this one's my pick, fight me"
- Head-to-head against a generic alternative
- Multi-day diary — a row of empties, "used it all week"
- Mirror review in a bathroom, close and casual
- Line up every variant and rank them on camera

**Style cue:** talking-head medium shot, product held to camera, honest tone, soft room light.

## Format 5 — ASMR
Sound-led close-ups. No VO, caption-only. `generate_audio:true`. Intimate settings only (kitchen/bathroom/bedroom).

**Concept seeds:**
- Macro cap-unscrew + pour into an iced glass
- Condensation bead sliding down a chilled bottle, then the open
- Ice drop + spoon clink as the product pours in
- Tap-and-rotate on a hard surface, audible shifts
- Paper/ribbon rustle (crossover with Unboxing)
- Two bottles clinking softly, no music bed

**Style cue:** extreme close-up, shallow depth, no music, audible handling, condensation, glass clinks.

---

## Setting ideas (pick to vary scenes)
**Realistic:** Bedroom · Bathroom · Kitchen · Office · In Car · Street · Gym · Nature.
**Stylized (use sparingly):** Airplane Wing · Rooftop · Tiny-reviewer scale · Car Roof.

## Product-category → format emphasis
Not every format fits every product — weight the mix toward what fits, redistributing
excluded shares back into UGC/review first.

| Category | Lean into |
|---|---|
| Single-SKU beverage | Entertainment · Review · ASMR (+ cinematic formats if requested) |
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

## Optional — pull refs from an external MCP (off by default)
If you have another content/reference MCP connected (e.g. a marketing-studio tool you
already use) and explicitly want it, you may query it for extra idea variety, then
translate what it returns into KIE prompts using the template above. Reference-only —
generation still happens on KIE. This library is the default source; never require an
external MCP.
