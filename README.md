<h1>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo/logo.svg">
    <img src="assets/logo/logo-on-light.svg" alt="Blueprints from Tomorrow" width="370">
  </picture>
</h1>

A text and voice role-playing game that runs inside an AI chatbot. You travel into the
past as yourself and try to explain science, medicine, engineering or institutions well
enough that people of that era can build or adopt them. The AI acts as game master,
following the rules in [`SKILL.md`](SKILL.md), and uses a tech tree of 510
technologies to judge what people know, what they believe, and what they can build
with local means.

The game is plain static Markdown, with no app and no server-side code. Website:
[blueprintsfromtomorrow.com](https://blueprintsfromtomorrow.com).

## Playing

Tell any web-enabled AI chat or voice agent:

```text
Start a game of blueprintsfromtomorrow.com (read https://blueprintsfromtomorrow.com/llms.txt)
```

Add a place and year to skip the first question ("… in Florence 1490"). Offline, give
the agent `SKILL.md`, `techtree/generated/<era>.md` and `campaigns/<campaign>.md`. To
continue a saved game, paste your campaign file and say "continue".

Included campaigns: Florence 1490, Florence 1347, Vienna 1683, Rome 46 BC and
Baghdad 830. Any other place and year works through the generic tech tree.

---

## How it fits together

```text
techtree/core.yaml          schema, 17 categories, 12 regions, knowledge levels
techtree/core/*.yaml        the 510 technologies, one file per category    ─┐
techtree/eras/*.yaml        status of every technology in one era & place  ─┤ scripts/build_techtree.py
                                                                            ▼
techtree/generated/         pre-built Markdown the game master reads (committed)
  <era>.md                    era index, loaded once at campaign start (~32k tokens)
  <era>/briefing.md           compact fallback for small context windows
  <era>/<category>.md         era status per category, loaded on demand
  all-techs.md                all techs + first appearances by region, for custom eras
  catalog/<category>.md       per-category list linking to …
  tech/<id>.md                one ~2 KB file per tech: explain, pitfalls, sources
  reference/<category>.md     full per-category reference

campaigns/*.md              premise, opening scene, arc, people, evaluation focus
SKILL.md                    game-master rules (English; the AI plays in any language)
modules/*.md                optional rules: voice mode, language barrier, social layer, content
templates/campaign-file.md  save-file format

index.html, scenarios/*.html, llms.txt, sitemap.xml, robots.txt   the website
scripts/build_pages.py      generates scenarios/*.html from campaigns + era files
assets/                     logo, era illustrations, Allo typeface
docs/                       original concept and scenario assessment (German)
```

Generated files are committed on purpose: chatbots fetch them over HTTP, and players
never run any scripts.

---

## Contributing

Pull requests are welcome, especially:

- **Corrections** to the tech tree or era files: a wrong date, an anachronism, a
  missing pitfall, a better source.
- **New era files** for regions and periods the tree does not cover yet.
- **New campaigns** built on an era file.
- **Rule improvements** to `SKILL.md` or the modules, e.g. after a playtest where the
  game master was too lenient or broke immersion.

Playtest reports help too. Open an issue with the model you used, the campaign, and
what went wrong. Paste the relevant part of the transcript if you can.

### Setup

Only contributors need this. You need Python 3; the commands below install the packages in `requirements.txt`.

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt    # Linux/macOS: .venv/bin/pip
python scripts/build_techtree.py --check          # validate without writing files
```

### Editing a technology

Entries live in `techtree/core/<category>.yaml`. The field reference is in the header
of [`techtree/core.yaml`](techtree/core.yaml):

| Field | Meaning |
|---|---|
| `id` | unique `snake_case` id; **never rename or remove** without a migration (see below) |
| `name`, `category` | English name; one of the 17 category keys |
| `requires` / `helps` | hard prerequisites / ids that make it easier or more convincing |
| `explain` | the core idea the player must get across; the GM judges explanations against it |
| `pitfalls` | typical mistakes when explaining or building it; these drive in-game failures |
| `history` | first occurrences per region (`region: "year – note"`) |
| `sources` | real literature for the final evaluation |

### Adding or fixing an era

An era file (`techtree/eras/<region>-<year>-<place>.yaml`) sets the status of each
technology in one place and time:

- `knowledge` is 0–4 (unknown → widespread). `use` is `none | wrong | partial | correct`.
- `producibility` is `easy | medium | hard | very-hard | impossible`, with local means
  within about a year. `acceptance` is `low | medium | high`.
- `note` is what the world believes. `local` lists the people, places and materials
  to connect to. `elsewhere` says where the technology already exists, which is useful
  as quest material.
- The top-level `worldview`, `people`, `events` and `quest_hooks` give the game master
  its setting.

Technologies the file leaves out default to knowledge 0 and use `none`, or to the
file's `default:`. Use [`europe-1490-florence.yaml`](techtree/eras/europe-1490-florence.yaml)
as the model.

### Adding a campaign

1. Write the era file and run `build_techtree.py`.
2. Write `campaigns/<id>.md` with the same sections as
   [`florence-1490.md`](campaigns/florence-1490.md): header with id, era guide and
   start date, then Premise, Opening scene, Arc, hint examples, People, and Evaluation
   focus.
3. To list it on the website, add an entry to `SCENARIOS` in `scripts/build_pages.py`
   and an illustration in `assets/eras/`, then run `build_pages.py`. Also add it to
   the campaign list in `SKILL.md` §2, to `llms.txt`, and to `sitemap.xml`. Add an era
   card to `index.html`, with its strings in all six languages. The maintainer can do
   the website part if you only send the era file and campaign.

### Sources and accuracy

The content was drafted with AI help and fact-checked by a second model. Sources were
checked for existence, not page by page, so careful corrections are among the most
useful contributions. Please:

- cite something a reader can find (book, paper, edition, or a primary source with its
  location), not just a link to a summary;
- keep era files to what people **in that place and year** could know. Use
  `elsewhere` for knowledge that exists in other parts of the world;
- note real uncertainty in the text ("probably", "c. 1490") instead of picking one
  side silently.

### Changing the rules or save format

- `SKILL.md` carries the skill `version` in its front matter, and campaign files store
  the version they were started with.
- Renaming or removing a tech id, or changing the campaign-file format, is a breaking
  change. Bump the version and add a step to [`MIGRATIONS.md`](MIGRATIONS.md).
- Record notable changes in [`CHANGELOG.md`](CHANGELOG.md) under *Unreleased*.

### Before opening a pull request

```bash
python scripts/build_techtree.py --check   # must print no PROBLEM lines
python scripts/build_techtree.py           # regenerate techtree/generated/
python scripts/build_pages.py              # if you touched campaigns or era files
```

Commit the source YAML/Markdown **and** the regenerated files together. If you are
unsure about the facts in your change, play a few turns with your change loaded.

### Other scripts

```bash
python scripts/visualize.py --era europe-1490-florence             # interactive tech-tree explorer -> out/
python scripts/visualize.py --era europe-1490-florence --category medicine
python scripts/visualize.py my-campaign.md                         # progress of a finished save file
python scripts/build_logo.py                                       # assets/logo/*.svg + favicons
python scripts/build_font.py                                       # web subset of the Allo typeface
python scripts/deploy_cloudflare.py                                # maintainer only: deploy the site
```

## Contact

Issues and pull requests on GitHub, or
[hello@blueprintsfromtomorrow.com](mailto:hello@blueprintsfromtomorrow.com).

## License

- **Content** (rules, campaigns, tech tree, documentation, artwork): [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- **Scripts & code** (`scripts/`, inline JS): [MIT](LICENSE)
- **Allo typeface** (`assets/fonts/`): [SIL OFL 1.1](assets/fonts/OFL.txt)

By contributing you agree that your contribution is published under these licenses.
See [LICENSE](LICENSE) for details.
