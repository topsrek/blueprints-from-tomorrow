# Module: Language Barrier

Active at difficulty **hard** automatically; otherwise only if the player asks.
Store the chosen level in the campaign file (`settings.language`).

| Level | Effect |
|---|---|
| `none` | Everyone understands the player perfectly. |
| `no-terms` | Normal conversation works, but modern technical terms do not exist. "Bacteria", "pressure", "voltage", "oxygen" mean nothing. The player must describe, draw or demonstrate. If they use a modern term, the NPC asks what it means or misunderstands it in a period way ("pressure" → the weight of a stone, a moral burden). |
| `related` | The player speaks a related or older form of the language (e.g. modern Italian or German vs. 1490 Tuscan). Fragments are understood, false friends cause misunderstandings, idioms fail. Show this by having NPCs repeat back a distorted version of what they understood. |
| `interpreter` | The player cannot communicate directly. An in-world interpreter (a merchant, a monk, a Jewish or Greek scholar, a sailor) translates — with their own interests, gaps in technical vocabulary and occasional deliberate "softening". The interpreter is an NPC with goals. |
| `none-at-all` | No shared language. Gestures, drawings, numbers, demonstrations. Learning the language is a quest in itself (progress per month of immersion). |

Rules:
- Never translate silently for the player at levels above `none`. Show what the NPC
  understood, not what the player meant.
- Numbers, drawings and physical demonstrations work at every level. Mathematics is
  the strongest bridge.
- At `related` and above, the player gradually improves. After roughly one in-game
  month of daily contact, move one level towards `none` (but never past `no-terms`).
