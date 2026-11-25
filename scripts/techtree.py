"""Shared loading and validation for the Blueprints from Tomorrow tech tree."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "techtree" / "core.yaml"
CORE_DIR = ROOT / "techtree" / "core"
ERAS = ROOT / "techtree" / "eras"

KNOWLEDGE_DEFAULT = 0


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_core() -> dict:
    core = load_yaml(CORE)
    core["technologies"] = [
        t for path in sorted(CORE_DIR.glob("*.yaml")) for t in load_yaml(path)["technologies"]
    ]
    core["by_id"] = {t["id"]: t for t in core["technologies"]}
    return core


def load_era(era_id: str) -> dict:
    path = ERAS / f"{era_id}.yaml"
    if not path.exists():
        available = ", ".join(p.stem for p in sorted(ERAS.glob("*.yaml")))
        sys.exit(f"Unknown era '{era_id}'. Available: {available}")
    return load_yaml(path)


def era_status(era: dict, tech_id: str) -> dict:
    status = dict(era.get("default") or {})
    status.update(era.get("status", {}).get(tech_id) or {})
    status.setdefault("knowledge", KNOWLEDGE_DEFAULT)
    status.setdefault("use", "none")
    return status


VALID_USE = {"none", "wrong", "partial", "correct"}
VALID_PRODUCIBILITY = {"easy", "medium", "hard", "very-hard", "impossible"}
VALID_ACCEPTANCE = {"low", "medium", "high"}


def validate(core: dict, era: dict | None = None) -> list[str]:
    """Return a list of problems (empty if everything is consistent)."""
    problems: list[str] = []
    ids = core["by_id"]
    if len(ids) != len(core["technologies"]):
        seen: set[str] = set()
        dups: set[str] = set()
        for t in core["technologies"]:
            if t["id"] in seen:
                dups.add(t["id"])
            seen.add(t["id"])
        problems.append(f"duplicate technology ids in core: {', '.join(sorted(dups))}")
    categories = core["categories"]
    for t in core["technologies"]:
        if t.get("category") not in categories:
            problems.append(f"{t['id']}: unknown category {t.get('category')!r}")
        for key in ("requires", "helps"):
            for dep in t.get(key) or []:
                if dep not in ids:
                    problems.append(f"{t['id']}: {key} unknown id {dep!r}")
        for region in t.get("history") or {}:
            if region not in core["regions"]:
                problems.append(f"{t['id']}: unknown history region {region!r}")
    if era is not None:
        for tech_id, st in (era.get("status") or {}).items():
            if tech_id not in ids:
                problems.append(f"era {era['era']}: unknown id {tech_id!r}")
            st = st or {}
            k = st.get("knowledge", 0)
            if k not in core["knowledge_levels"]:
                problems.append(f"era {era['era']}: {tech_id} invalid knowledge {k!r}")
            if "use" in st and st["use"] not in VALID_USE:
                problems.append(f"era {era['era']}: {tech_id} invalid use {st['use']!r}")
            if "producibility" in st and st["producibility"] not in VALID_PRODUCIBILITY:
                problems.append(f"era {era['era']}: {tech_id} invalid producibility {st['producibility']!r}")
            if "acceptance" in st and st["acceptance"] not in VALID_ACCEPTANCE:
                problems.append(f"era {era['era']}: {tech_id} invalid acceptance {st['acceptance']!r}")
    return problems
