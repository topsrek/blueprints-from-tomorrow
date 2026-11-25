# Campaign File – Template

The GM keeps this file up to date (see SKILL.md §6). It is Markdown with one YAML
block, so humans can read it and `scripts/visualize.py` can parse it. Keep it short:
facts, not prose. Only the YAML block is machine-read; the "Journal" below it is free
text.

```yaml
campaign_file_version: 1
skill_version: 0.2.0          # version of SKILL.md when the campaign started
campaign: florence-1490       # predefined campaign id, or "custom"
era: europe-1490-florence     # era file used for the tech tree
title: "Florence 1490"
language: de                  # language of play

settings:
  difficulty: medium
  hints: medium
  resistance: medium
  language: none              # none | no-terms | related | interpreter | none-at-all
  social_layer: on
  duration: 1 year
  hook: accident

time:
  start: 1490-03-12
  now: 1490-03-14
  end: 1491-03-12

location: "Florence, Oltrarno, inn near Santo Spirito"

pockets:                      # carried items and their state
  - item: smartphone
    state: "battery 71 %, flight mode, offline photos and maps"
  - item: car key with remote
    state: ok
  - item: wallet
    state: "2 bank cards, 35 euros in coins and notes, ID card"

people:                       # everyone who matters; attitude -3..+3
  - name: Marsilio Ficino
    role: philosopher, physician
    attitude: 1
    knows: "player claims to come from the future; saw the phone light"
    asked: ["where do you come from?", "what causes the plague?"]
    promised: "introduction to Lorenzo if the player helps with the plague"

factions:
  - name: Medici household
    standing: 0
  - name: Physicians' guild
    standing: -1

tech_progress:                # only technologies the player has touched
  contagion_theory:
    explained_to: [Marsilio Ficino]
    level_before: 1
    level_now: 2              # knowledge level in the game world now
    built: false
    notes: "Ficino links it to Varro but remains unconvinced without proof"

quests:
  - name: "Plague in San Frediano"
    status: active            # active | done | failed | abandoned
    notes: ""

events_done:
  - "1490-03-13: Fire in a dyer's workshop"

errors_for_evaluation:         # private GM notes, ROT13-encoded so mid-game saves do not spoil the player (decoded in §7)
  - "Cynlre fnvq syrnf ner pneevrq ol pngf (npghnyyl engf/oynpx eng syrn)."

ending: null                  # filled in at the end: summary of impact
```

## Journal

- **1490-03-12** – Arrival at the Ponte Vecchio. Found note: return in one year.
- **1490-03-13** – Met Ficino at Careggi; showed the phone's flashlight.
