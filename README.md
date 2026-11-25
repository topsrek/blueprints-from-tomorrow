<h1>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo/logo.svg">
    <img src="assets/logo/logo-on-light.svg" alt="Blueprints from Tomorrow" width="370">
  </picture>
</h1>

*A time-travel role-playing game that tests how much of our civilization you really
understand.* Free, non-profit, open source. Runs directly in any AI chatbot or voice
agent from plain static Markdown files — **no app, no account, no installation**.

You travel into the past **as yourself**, with whatever is in your pockets right now.
Work your way up to scholars, craftsmen, engineers, and rulers, and try to explain
hygiene, steam engines, lenses, statistics, or the rule of law well enough that people
of the era can actually use or build it. People build **literally what you explain,
mistakes included**. At the end: what did you change, and what did you get wrong?

---

## Play in 10 seconds

### Option 1 — Any web-enabled AI chat or voice agent (recommended)

Paste this into ChatGPT, Claude, Gemini, Perplexity, or any agent with web access:

```text
Let's play Blueprints from Tomorrow. Read https://blueprintsfromtomorrow.com/llms.txt
and follow its instructions to start a campaign.
```

*(German: „Lass uns Blueprints from Tomorrow spielen. Lies https://blueprintsfromtomorrow.com/llms.txt und folge den Anweisungen zum Start.“)*

Once indexed, simply saying **"I want to play Blueprints from Tomorrow"** is enough:
the agent finds `llms.txt`, loads `SKILL.md`, asks only two questions (where/when and
difficulty), and fetches the small static Markdown files it needs on demand.

### Option 2 — Skill-capable agent / local repository

Install this repository as a skill (or give your chatbot `SKILL.md`,
`techtree/generated/<era>.md`, and `campaigns/<campaign>.md`) and say:

> **"Load Blueprints from Tomorrow"** *(or „Lade Blueprints from Tomorrow“)*

To continue a saved game in a new chat, paste your campaign file and say **"continue"**.

**No Python or scripts required to play.** Every generated Markdown file — including
the 510 compact per-technology lookup files — is pre-built and committed directly to
the repository so both web-fetching chatbots and local agents can read them statically.

---

## Campaigns

| Campaign | Era & Setting | Focus & Challenge | Files |
|---|---|---|---|
| **Florence 1490** | High Renaissance, Lorenzo de' Medici, Ficino, Savonarola | Core *Build* campaign: workshops, lenses, printing, plague, voyages of discovery | [campaign](campaigns/florence-1490.md) · [era index](techtree/generated/europe-1490-florence.md) |
| **Florence 1347** | Eve of the Black Death, famine, no printing press | Pure hygiene & epidemic test with rotating two-month priors | [campaign](campaigns/florence-1347.md) · [era index](techtree/generated/europe-1347-florence.md) |
| **Vienna 1683** | Ottoman siege, dysentery, counter-mining | Tight timeline, siege sanitation, and an era that already understands experiments | [campaign](campaigns/vienna-1683.md) · [era index](techtree/generated/europe-1683-vienna.md) |
| **Rome 46 BC** | Caesar's 445-day calendar reform, Varro, Cicero | *Explain* campaign: huge infrastructure, slave economy, approaching Ides of March | [campaign](campaigns/rome-46bc.md) · [era index](techtree/generated/europe-46bc-rome.md) |
| **Baghdad 830** | Abbasid Baghdad, Caliph al-Ma'mun, House of Wisdom | Ahead of medieval Europe: paper, algebra, hospitals, translations, looming Mihna | [campaign](campaigns/baghdad-830.md) · [era index](techtree/generated/islamic-830-baghdad.md) |

You can also choose **any custom place and year** at campaign start.

---

## How the 510-technology context works

The tech tree covers **510 technologies across 17 categories** with 4 era dimensions
(`knowledge`, `use`, `producibility`, `acceptance`), historical pitfalls, local hooks,
and real literature sources. `build_techtree.py` pre-generates static Markdown so the
GM gets rich world context upfront in **one file** and only fetches deep details on demand:

1. **Predefined campaign:** `techtree/generated/<era>.md` (~32k tokens) — loaded once at campaign start; already contains worldview, people, events, quest hooks, and all 510 local statuses, beliefs, and materials (playable even without mid-game fetches, e.g. in voice mode).
2. **Any custom time & culture:** `techtree/generated/all-techs.md` (~22k tokens) — loaded once at start; lists all 510 technologies with prerequisites and historical first-appearance dates across 12 world regions to prevent anachronisms.
3. **Deep check & evaluation sources:** `techtree/generated/tech/<id>.md` (~2 KB per tech, linked via `catalog/<category>.md`) — fetched on demand for detailed `pitfalls` and primary literature `sources`.

Mid-game saves encode `errors_for_evaluation` in **ROT13** so checking or pasting your
save file does not spoil the final evaluation.

---

## Repository layout

```text
index.html                   static landing page (SEO, Open Graph, Schema.org, FAQ)
llms.txt                     AI-agent bootstrap & file map (GEO / AEO)
robots.txt / sitemap.xml     crawler & AI-search discovery
favicon.svg / favicon.ico    site & browser icons (generated by scripts/build_logo.py)
SKILL.md                     game-master rules (English; play in any language)
modules/                     optional rules, loaded when needed
campaigns/                   predefined campaigns
templates/campaign-file.md   format of the campaign (save) file
techtree/core.yaml           schema, categories, knowledge levels
techtree/core/*.yaml         shared tech tree (510 entries in 17 category files)
techtree/eras/*.yaml         status per era/region (knowledge, use, producibility, acceptance)
techtree/generated/          pre-built static Markdown (era indices, era/category, tech/<id>.md, reference/)
scripts/                     contributor build + campaign progress visualization
assets/logo/                 logo SVGs — generated by scripts/build_logo.py
assets/fonts/                Allo, the wordmark typeface (SIL OFL)
docs/concept.md              original concept (German)
docs/campaign-scenarios.md   assessment of further campaign scenarios (German)
MIGRATIONS.md                step-by-step migration of campaign files between versions
```

---

## Scripts (contributors & visualization)

Players never need to run these. Use them if you contribute to `techtree/` or want to
visualize a finished campaign file:

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt    # Linux/macOS: .venv/bin/pip
python scripts/build_techtree.py                  # regenerate techtree/generated/
python scripts/build_techtree.py --check          # validate ids, enums, and dependencies
python scripts/visualize.py --era europe-1490-florence
python scripts/visualize.py --era europe-1490-florence --category medicine
python scripts/visualize.py my-campaign.md        # -> out/my-campaign.html (interactive) + .mmd
python scripts/build_logo.py                      # regenerate assets/logo/*.svg + root favicons
```

## Contributing

Pull requests welcome: new eras and regions, campaigns, and corrections to the tech
tree (please add sources). After editing `techtree/`, run `python scripts/build_techtree.py`
and commit the generated files.

## License

- **Content** (rules, campaigns, tech tree, documentation, artwork): [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- **Scripts & code** (`scripts/`, inline JS): [MIT](LICENSE)
- **Allo typeface** (`assets/fonts/`): [SIL OFL 1.1](assets/fonts/OFL.txt)

See [LICENSE](LICENSE) for full details.
