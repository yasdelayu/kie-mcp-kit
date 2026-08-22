# Credits & attribution

## Original work here

- `server/kie_server.py` — the KIE MCP connector, an original 5-tool implementation
  over the public [KIE.ai API](https://docs.kie.ai), by [@yasdelayu](https://github.com/yasdelayu). MIT.
- The two READMEs (RU/EN), `install.sh`, and the kit layout — by @yasdelayu. MIT.

## Bundled

- `skill/generate-anything/SKILL.md` — the **generate-anything** skill by Anthropic,
  which drives the connector's tools. Used per Anthropic's terms.

## Pipeline skills (original, adapted)

- `skill/content-factory/SKILL.md` — by [@yasdelayu](https://github.com/yasdelayu), MIT.
  A KIE-native rewrite; the 5-stage campaign structure is adapted from Anthropic's
  `higgsfield-content-factory` skill (all Higgsfield/Marketing-Studio mechanics replaced
  with KIE models + the connector's tools).
- `skill/youtube-factory/SKILL.md` — by @yasdelayu, MIT. Workflow adapted from the
  "Claude + YouTube" method taught at [razgon.school](https://razgon.school/materials/ClaudeYouTube)
  (NexLev / vidIQ research → script → visuals → voiceover → assembly), re-implemented on KIE.
  Uses third-party NexLev / vidIQ MCPs when connected — those are not part of this kit.

## Third parties

- **[KIE.ai](https://kie.ai)** — the model aggregator the connector talks to over its
  public HTTP API. Not affiliated with this kit.
- The underlying models (Seedance, Kling, Veo, Sora 2, GPT-Image, Suno, ElevenLabs, …)
  belong to their respective vendors.

This kit is not endorsed by Anthropic or KIE.ai.
