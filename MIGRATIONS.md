# Migrations

Campaign files store the `skill_version` they were started with. When a newer skill
loads an older campaign file, apply the steps below **one version at a time**, in
order, from the file's version up to the current one. Each step lists only breaking
changes to the campaign file or the tech-tree ids.

Versioning: `MAJOR.MINOR.PATCH`. Breaking changes to the campaign file format or to
tech ids bump MINOR while < 1.0, MAJOR afterwards.

## 0.1.0
Initial version. Nothing to migrate.

## 0.1.0 → 0.2.0
- No tech id of 0.1.0 was renamed or removed; `tech_progress` keys stay valid.
- The tech tree is now loaded as an index plus per-category files (see SKILL.md §1);
  load `techtree/generated/<era>.md` again instead of relying on the 0.1.0 file.
- Then set `skill_version: 0.2.0`.

<!--
Template for future steps:

## 0.1.x → 0.2.0
- Renamed tech id `foo` → `bar`: in `tech_progress`, rename the key.
- New required field `settings.xyz` (default: ...).
- Then set `skill_version: 0.2.0`.
-->
