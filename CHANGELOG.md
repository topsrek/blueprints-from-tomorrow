# Changelog

## 1.0.0 – 2026-11-25
First public release.

- Game-master rules (`SKILL.md`) with start defaults, difficulty axes, core
  mechanics, save file and final evaluation, hardened against LLM sycophancy:
  no silent fixes or hints, mistakes logged ROT13-encoded in
  `errors_for_evaluation` until the evaluation.
- Optional modules: voice mode, language barrier, social layer, content guidelines.
- Tech tree of 510 technologies in 17 categories (`techtree/core/<category>.yaml`)
  with explanations, pitfalls, first appearances in 12 world regions and sources.
- Five campaigns with fact-checked era files: *Florence 1490*, *Florence 1347 –
  Before the Plague*, *Vienna 1683 – The Siege*, *Rome 46 BC – The Longest Year*
  and *Baghdad 830 – The House of Wisdom*. Any other place and year works through
  the generic tree (`techtree/generated/all-techs.md`).
- Pre-built Markdown for web-fetching chatbots: era index, compact briefing,
  per-category slices and one ~2 KB file per technology.
- Website at https://blueprintsfromtomorrow.com with one page per campaign,
  `llms.txt`, `sitemap.xml` and `robots.txt`.
- Scripts: tech-tree build and validation, page build, interactive tech-tree
  explorer (`visualize.py`), logo and font build, Cloudflare deploy.
- Licensed under CC BY-SA 4.0 (content), MIT (scripts) and SIL OFL 1.1 (Allo
  typeface).
