# Changelog

## Unreleased
- New campaigns and fact-checked era files: *Florence 1347 – Before the Plague*
  (`europe-1347-florence`), *Vienna 1683 – The Siege* (`europe-1683-vienna`),
  *Rome 46 BC – The Longest Year* (`europe-46bc-rome`), and
  *Baghdad 830 – The House of Wisdom* (`islamic-830-baghdad`).
- Generated one compact static Markdown file per technology
  (`techtree/generated/tech/<id>.md`, ~1.5 KB each) so web-fetching chatbots and
  local agents can look up individual technologies without loading 80+ KB category
  references.
- Reworked `scripts/visualize.py`: offline interactive HTML explorer for all 510
  technologies (search, filters, dependency inspector, layered SVG graph, Copy
  Mermaid) plus GitHub-safe `.mmd` output (17-category overview, `--category`, or
  campaign `--touched` subgraph).
- Strengthened `SKILL.md` §5.2/§5.3 against LLM sycophancy and switched
  `errors_for_evaluation` to ROT13 so mid-game saves do not spoil the player.
- Added static website & discovery files for SEO/GEO/AEO: `index.html`, `llms.txt`,
  `robots.txt`, `sitemap.xml`, `favicon.svg`, and `favicon.ico`.

## 0.2.0 – 2026-11-19
- Tech tree grown from 50 to 510 entries in 17 categories, one file per category
  (`techtree/core/<category>.yaml`); `techtree/core.yaml` now holds only schema,
  categories, regions and knowledge levels. New categories: life sciences, materials,
  electricity, computing, manufacturing, scientific method & ideas, economy, warfare.
- Era file Florence 1490 has a status for every entry, more people, events and hooks
  (including the voyages of discovery). Era files may set a `default:` status.
- Generated files split in three: index per era (always loaded), status per era and
  category, reference per category (both loaded on demand).
- Drafted by AI agents and fact-checked once by a second model; sources were checked
  for existence, not page by page.
- `docs/campaign-scenarios.md`: assessment of further campaign scenarios (German).

## 0.1.0 – 2026-11-16
- First draft of the skill (SKILL.md) with start defaults, difficulty axes, core
  mechanics, campaign file, evaluation.
- Modules: language barrier, social layer, content guidelines, voice mode.
- Tech tree: shared core (42 technologies) and era file Florence 1490.
- Campaign: Florence 1490; Vienna 1683 stub.
- Scripts: build compact tech tree, visualize tech tree / campaign progress.
