# Module: Social Layer

Default: **on**. If off, the game becomes a pure technology test: patrons, money and
workshops are available on request, and events concern only nature, materials and
time, not people.

## Favour
Track the player's standing with key persons and factions in the campaign file
(`people[].attitude` and `factions[].standing`), on a scale from -3 (hostile) to +3
(devoted). Change it based on actions, not on single lines of dialogue.

Typical factions: the ruler/patron, the guilds, the Church, the physicians'
guild/university, rival families, the common people.

## Access
The player starts with no status. Getting to powerful people is a ladder:
street → craftsman/innkeeper → merchant/scholar → household of a patron → the patron.
Each step needs a reason: a demonstration, a service, a recommendation, a bribe,
luck. Skipping steps is possible with spectacular proof (pocket items), but attracts
attention: envy, suspicion, the Inquisition.

## Intrigue
Rivals exist. Someone always loses if the player wins: the physician whose remedies
are questioned, the guild whose monopoly is threatened, the court astrologer. They act
off-screen. Report their moves as events.

## Quests
NPCs give tasks in return for help: cure a relative, find a better dye, win a bet,
make the cannons more reliable, explain a comet. Quests are the natural way to apply
knowledge. Use the era file's `quest_hooks` and `elsewhere` entries (technology that
exists in other regions — e.g. porcelain in China — can become an expedition or
trade quest).

## Money
Track money roughly (e.g. in florins) only when it matters. Workshops, materials,
assistants and bribes cost money. Patrons pay for results or promises.
