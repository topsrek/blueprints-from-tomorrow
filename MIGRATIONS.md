# Migrations

Campaign files store the `skill_version` they were started with. When a newer skill
loads an older campaign file, apply the steps below **one version at a time**, in
order, from the file's version up to the current one. Each step lists only breaking
changes to the campaign file or the tech-tree ids.

Versioning: `MAJOR.MINOR.PATCH`. Breaking changes to the campaign file format or to
tech ids bump MAJOR.

## 1.0.0
Initial public version. Nothing to migrate.

<!--
Template for future steps:

## 1.x → 2.0.0
- Renamed tech id `foo` → `bar`: in `tech_progress`, rename the key.
- New required field `settings.xyz` (default: ...).
- Then set `skill_version: 2.0.0`.
-->
