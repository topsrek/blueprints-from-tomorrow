"""Visualize the tech tree of an era, optionally with a campaign's progress.

Writes:
  1. A standalone, offline-capable interactive HTML explorer (.html) containing all
     technologies, filters, dependency inspection, and a layered SVG graph view.
  2. A guaranteed-renderable Mermaid diagram (.mmd, renders on GitHub inside a
     ```mermaid block):
       - For a campaign with progress: the touched technologies + 1-hop dependencies
         and unlocks (override with --category or --all).
       - With --category: the technologies in those categories (+ external prereqs).
       - For an era overview (no filter): a 17-category summary graph so Mermaid
         never exceeds its node/edge limits.

Usage:
    python scripts/visualize.py --era europe-1490-florence
    python scripts/visualize.py --era europe-1490-florence --category medicine
    python scripts/visualize.py path/to/my-campaign.md        # era taken from file
    python scripts/visualize.py my-campaign.md -o out/mine     # -> out/mine.mmd/.html
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

from techtree import ROOT, era_status, load_core, load_era

YAML_BLOCK = re.compile(r"```ya?ml\s*\n(.*?)```", re.S)

# colour per knowledge level 0..4 (light fill, readable dark text)
LEVEL_STYLE = {
    0: "fill:#eeeeee,stroke:#9e9e9e,color:#333",
    1: "fill:#fff3cd,stroke:#c9a227,color:#333",
    2: "fill:#ffe0b2,stroke:#e08a00,color:#333",
    3: "fill:#c8e6c9,stroke:#388e3c,color:#1b3d1d",
    4: "fill:#a5d6a7,stroke:#1b5e20,color:#10300f",
}


def load_campaign(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = YAML_BLOCK.search(text)
    data = yaml.safe_load(m.group(1) if m else text)
    if not isinstance(data, dict) or "era" not in data:
        sys.exit(f"{path}: no campaign YAML with an 'era' field found")
    return data


def label(text: str) -> str:
    return text.replace('"', "'")


def build_mermaid_overview(core: dict, era: dict, campaign: dict | None) -> str:
    """Compact 17-category overview diagram that always fits Mermaid limits."""
    progress = (campaign or {}).get("tech_progress") or {}
    by_id = core["by_id"]
    cat_techs: dict[str, list[dict]] = defaultdict(list)
    for t in core["technologies"]:
        cat_techs[t["category"]].append(t)

    out = ["flowchart LR"]
    avg_level: dict[str, int] = {}
    for cat_id, cat_name in core["categories"].items():
        techs = cat_techs.get(cat_id) or []
        if not techs:
            continue
        known = 0
        easy_wins = 0
        touched = 0
        built = 0
        k_sum = 0
        for t in techs:
            st = era_status(era, t["id"])
            p = progress.get(t["id"]) or {}
            now = p.get("level_now", st["knowledge"])
            k_sum += now
            if now >= 3:
                known += 1
            if now <= 1 and st.get("producibility") == "easy":
                easy_wins += 1
            if t["id"] in progress:
                touched += 1
                if p.get("built"):
                    built += 1
        avg_level[cat_id] = min(4, round(k_sum / len(techs)))
        meta = f"{known}/{len(techs)} known · {easy_wins} easy K0-K1"
        if touched:
            meta += f"<br/>{touched} touched" + (f" · {built} built ★" if built else "")
        out.append(f'  {cat_id}["<b>{label(cat_name)}</b><br/><small>{meta}</small>"]')

    cross_req: dict[tuple[str, str], int] = defaultdict(int)
    for t in core["technologies"]:
        dst = t["category"]
        for dep in t.get("requires") or []:
            src = by_id[dep]["category"]
            if src != dst:
                cross_req[(src, dst)] += 1
    for (src, dst), count in sorted(cross_req.items()):
        if count >= 2:
            out.append(f"  {src} -->|{count} req| {dst}")

    for k, style in LEVEL_STYLE.items():
        out.append(f"  classDef k{k} {style}")
    out.append("  classDef touched stroke-width:4px,stroke:#17489A")
    for cat_id, k in avg_level.items():
        out.append(f"  class {cat_id} k{k}")
        if any(t["id"] in progress for t in cat_techs[cat_id]):
            out.append(f"  class {cat_id} touched")
    return "\n".join(out) + "\n"


def select_mermaid_ids(
    core: dict,
    campaign: dict | None,
    categories: list[str] | None,
    touched_only: bool,
    full_all: bool,
) -> tuple[set[str] | None, set[str]]:
    """Return (primary_ids, external_stub_ids), or (None, set()) for category overview."""
    by_id = core["by_id"]
    progress = (campaign or {}).get("tech_progress") or {}

    if full_all:
        return set(by_id.keys()), set()

    if categories:
        primary = {t["id"] for t in core["technologies"] if t["category"] in categories}
        stubs = {
            dep
            for tid in primary
            for dep in (by_id[tid].get("requires") or [])
            if dep not in primary
        }
        return primary, stubs

    if touched_only or progress:
        if not progress:
            return None, set()
        primary = set(tid for tid in progress if tid in by_id)
        # Include 1-hop hard prerequisites and direct unlocks so progress has context
        unlocks: dict[str, list[str]] = defaultdict(list)
        for t in core["technologies"]:
            for dep in t.get("requires") or []:
                unlocks[dep].append(t["id"])
        stubs: set[str] = set()
        for tid in list(primary):
            for dep in by_id[tid].get("requires") or []:
                if dep not in primary:
                    stubs.add(dep)
            for nxt in unlocks.get(tid) or []:
                if nxt not in primary:
                    stubs.add(nxt)
        return primary, stubs

    return None, set()


def build_mermaid_subgraph(
    core: dict,
    era: dict,
    campaign: dict | None,
    primary_ids: set[str],
    stub_ids: set[str],
    include_helps: bool,
) -> str:
    progress = (campaign or {}).get("tech_progress") or {}
    levels = core["knowledge_levels"]
    visible = primary_ids | stub_ids
    out = ["flowchart LR"]

    for cat_id, cat_name in core["categories"].items():
        techs = [t for t in core["technologies"] if t["category"] == cat_id and t["id"] in visible]
        if not techs:
            continue
        out.append(f'  subgraph {cat_id}["{label(cat_name)}"]')
        out.append("    direction TB")
        for t in techs:
            st = era_status(era, t["id"])
            before = st["knowledge"]
            p = progress.get(t["id"]) or {}
            now = p.get("level_now", before)
            status = f"K{before}" if now == before else f"K{before} → K{now}"
            status += f" · {levels[now]}"
            if p.get("built"):
                status += " · built ★"
            out.append(f'    {t["id"]}["{label(t["name"])}<br/><small>{status}</small>"]')
        out.append("  end")

    for t in core["technologies"]:
        tid = t["id"]
        if tid not in visible:
            continue
        for dep in t.get("requires") or []:
            if dep in visible and (tid in primary_ids or dep in primary_ids):
                out.append(f"  {dep} --> {tid}")
        if include_helps:
            for dep in t.get("helps") or []:
                if dep in primary_ids and tid in primary_ids:
                    out.append(f"  {dep} -.-> {tid}")

    for k, style in LEVEL_STYLE.items():
        out.append(f"  classDef k{k} {style}")
    out.append("  classDef touched stroke-width:4px,stroke:#17489A")
    out.append("  classDef context stroke-dasharray:5 4")

    for t in core["technologies"]:
        tid = t["id"]
        if tid not in visible:
            continue
        p = progress.get(tid) or {}
        now = p.get("level_now", era_status(era, tid)["knowledge"])
        out.append(f"  class {tid} k{now}")
        if tid in progress:
            out.append(f"  class {tid} touched")
        elif tid in stub_ids:
            out.append(f"  class {tid} context")
    return "\n".join(out) + "\n"


def build_payload(
    core: dict,
    era: dict,
    campaign: dict | None,
    initial_categories: list[str] | None,
    initial_touched: bool,
) -> dict:
    progress = (campaign or {}).get("tech_progress") or {}
    techs = []
    for t in core["technologies"]:
        st = era_status(era, t["id"])
        p = progress.get(t["id"]) or None
        before = st["knowledge"]
        now = p.get("level_now", before) if p else before
        techs.append(
            {
                "id": t["id"],
                "name": t["name"],
                "category": t["category"],
                "requires": t.get("requires") or [],
                "helps": t.get("helps") or [],
                "knowledge_before": before,
                "knowledge": now,
                "use": st.get("use", "none"),
                "producibility": st.get("producibility", "?"),
                "acceptance": st.get("acceptance", "?"),
                "note": st.get("note", ""),
                "local": st.get("local") or [],
                "elsewhere": st.get("elsewhere") or [],
                "touched": p is not None,
                "built": bool(p and p.get("built")),
                "explained_to": (p.get("explained_to") or []) if p else [],
                "campaign_notes": (p.get("notes") or "") if p else "",
            }
        )
    return {
        "era": era["era"],
        "eraTitle": era["title"],
        "region": era.get("region", ""),
        "year": era.get("year", ""),
        "worldview": era.get("worldview", ""),
        "hasCampaign": campaign is not None,
        "categories": [{"id": cid, "name": cname} for cid, cname in core["categories"].items()],
        "levels": {str(k): v for k, v in core["knowledge_levels"].items()},
        "initialCategory": initial_categories[0] if initial_categories and len(initial_categories) == 1 else "all",
        "initialPreset": "touched" if (initial_touched or bool(progress)) else "all",
        "technologies": techs,
    }


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ – Blueprints from Tomorrow</title>
<style>
  :root {
    --bg: #f6f4ee;
    --surface: #ffffff;
    --ink: #1b2230;
    --muted: #5a6475;
    --border: #dcd8cc;
    --blue: #17489a;
    --blue-soft: #e8effa;
    --amber: #d98e0b;
    --k0-bg: #eeeeee; --k0-bd: #9e9e9e; --k0-fg: #333333;
    --k1-bg: #fff3cd; --k1-bd: #c9a227; --k1-fg: #4a3900;
    --k2-bg: #ffe0b2; --k2-bd: #e08a00; --k2-fg: #543100;
    --k3-bg: #c8e6c9; --k3-bd: #388e3c; --k3-fg: #1b3d1d;
    --k4-bg: #a5d6a7; --k4-bd: #1b5e20; --k4-fg: #10300f;
  }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: system-ui, -apple-system, Segoe UI, sans-serif; background: var(--bg); color: var(--ink); line-height: 1.4; }
  header { background: var(--blue); color: #f3efe4; padding: 18px 24px 16px; border-bottom: 3px solid #f5b83d; }
  header h1 { margin: 0 0 4px; font-size: 22px; letter-spacing: -0.01em; }
  header p { margin: 0; opacity: 0.88; font-size: 13px; }
  .stats { display: flex; flex-wrap: wrap; gap: 10px; padding: 12px 24px; background: var(--surface); border-bottom: 1px solid var(--border); }
  .stat { background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 6px 12px; min-width: 110px; }
  .stat b { display: block; font-size: 18px; color: var(--blue); }
  .stat span { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
  .toolbar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; padding: 12px 24px; background: var(--surface); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 20; }
  .toolbar input[type="search"], .toolbar select { padding: 7px 10px; border: 1px solid var(--border); border-radius: 6px; font-size: 13px; background: #fff; color: var(--ink); }
  .toolbar input[type="search"] { width: 230px; }
  .btn { padding: 7px 11px; border: 1px solid var(--border); border-radius: 6px; background: #fff; color: var(--ink); font-size: 13px; cursor: pointer; }
  .btn:hover { background: var(--blue-soft); border-color: var(--blue); }
  .btn.active { background: var(--blue); color: #fff; border-color: var(--blue); }
  .spacer { flex: 1; }
  .layout { display: grid; grid-template-columns: 1fr 340px; min-height: calc(100vh - 180px); }
  @media (max-width: 960px) { .layout { grid-template-columns: 1fr; } .inspector { border-left: none; border-top: 1px solid var(--border); } }
  main { padding: 18px 24px 40px; min-width: 0; }
  .legend { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-bottom: 14px; font-size: 12px; color: var(--muted); }
  .chip { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 999px; border: 1px solid; font-size: 11px; font-weight: 600; }
  .k0 { background: var(--k0-bg); border-color: var(--k0-bd); color: var(--k0-fg); }
  .k1 { background: var(--k1-bg); border-color: var(--k1-bd); color: var(--k1-fg); }
  .k2 { background: var(--k2-bg); border-color: var(--k2-bd); color: var(--k2-fg); }
  .k3 { background: var(--k3-bg); border-color: var(--k3-bd); color: var(--k3-fg); }
  .k4 { background: var(--k4-bg); border-color: var(--k4-bd); color: var(--k4-fg); }
  .cat-block { margin-bottom: 22px; }
  .cat-head { display: flex; align-items: baseline; justify-content: space-between; margin: 0 0 8px; padding-bottom: 4px; border-bottom: 1px solid var(--border); }
  .cat-head h2 { margin: 0; font-size: 15px; color: var(--blue); }
  .cat-head span { font-size: 12px; color: var(--muted); }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(215px, 1fr)); gap: 8px; }
  .card { text-align: left; width: 100%; border: 1px solid; border-radius: 8px; padding: 8px 10px; cursor: pointer; transition: transform .08s, box-shadow .08s; font: inherit; }
  .card:hover { transform: translateY(-1px); box-shadow: 0 3px 10px rgba(0,0,0,.08); }
  .card.selected { outline: 3px solid var(--amber); outline-offset: 1px; }
  .card.touched { box-shadow: inset 0 0 0 2.5px var(--blue); }
  .card-title { font-size: 13px; font-weight: 600; margin-bottom: 3px; }
  .card-meta { font-size: 11px; opacity: 0.85; display: flex; justify-content: space-between; gap: 6px; }
  .graph-wrap { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
  .graph-bar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; padding: 10px 12px; border-bottom: 1px solid var(--border); background: #faf9f5; font-size: 12px; color: var(--muted); }
  .graph-stage { overflow: auto; max-height: 72vh; padding: 12px; background: #fff; }
  .graph-notice { padding: 28px 20px; text-align: center; color: var(--muted); font-size: 14px; }
  .inspector { background: var(--surface); border-left: 1px solid var(--border); padding: 18px; overflow-y: auto; }
  .inspector h3 { margin: 0 0 4px; font-size: 17px; color: var(--ink); }
  .inspector .tid { font-family: ui-monospace, Consolas, monospace; font-size: 12px; color: var(--muted); margin-bottom: 10px; }
  .kv { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
  .sec-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); margin: 14px 0 5px; font-weight: 700; }
  .dep-list { display: flex; flex-wrap: wrap; gap: 5px; }
  .dep-btn { border: 1px solid; border-radius: 6px; padding: 3px 7px; font-size: 12px; cursor: pointer; font-family: inherit; }
  .dep-btn:hover { filter: brightness(0.95); }
  .note-box { font-size: 13px; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 9px 10px; }
  .empty { color: var(--muted); font-size: 13px; }
  svg text { font-family: system-ui, -apple-system, Segoe UI, sans-serif; user-select: none; }
  .svg-node { cursor: pointer; }
  .svg-node:hover rect { filter: brightness(0.96); }
  .toast { position: fixed; bottom: 18px; right: 18px; background: var(--ink); color: #fff; padding: 8px 14px; border-radius: 8px; font-size: 13px; opacity: 0; pointer-events: none; transition: opacity .2s; z-index: 50; }
  .toast.show { opacity: 1; }
</style>
</head>
<body>
<header>
  <h1>__TITLE__</h1>
  <p>__SUBTITLE__</p>
</header>
<div class="stats" id="stats"></div>
<div class="toolbar">
  <input type="search" id="q" placeholder="Search tech, id, person, note...">
  <select id="cat"></select>
  <select id="kfilter">
    <option value="all">All K levels</option>
    <option value="0">K0 unknown</option>
    <option value="1">K1 idea / rumour</option>
    <option value="2">K2 theory</option>
    <option value="3">K3 specialist</option>
    <option value="4">K4 widespread</option>
  </select>
  <select id="make">
    <option value="all">All producibility</option>
    <option value="easy">make: easy</option>
    <option value="medium">make: medium</option>
    <option value="hard">make: hard</option>
    <option value="very-hard">make: very-hard</option>
    <option value="impossible">make: impossible</option>
  </select>
  <button class="btn" id="presetEasy" title="Unknown or rumour (K0-K1) and easy to build locally">Easy wins</button>
  <button class="btn" id="presetTouched" style="display:none">Touched</button>
  <button class="btn" id="resetBtn">Reset</button>
  <span class="spacer"></span>
  <button class="btn active" id="viewMatrix">Matrix</button>
  <button class="btn" id="viewGraph">Dependency Graph</button>
</div>
<div class="layout">
  <main>
    <div class="legend" id="legend"></div>
    <div id="content"></div>
  </main>
  <aside class="inspector" id="inspector">
    <p class="empty">Click any technology to inspect local beliefs, materials, prerequisites, and what it unlocks.</p>
  </aside>
</div>
<div class="toast" id="toast"></div>
<script id="data" type="application/json">__JSON__</script>
<script>
const DATA = JSON.parse(document.getElementById("data").textContent);
const byId = Object.fromEntries(DATA.technologies.map(t => [t.id, t]));
const unlocksMap = Object.fromEntries(DATA.technologies.map(t => [t.id, []]));
const helpedByMap = Object.fromEntries(DATA.technologies.map(t => [t.id, []]));
for (const t of DATA.technologies) {
  for (const r of t.requires) if (unlocksMap[r]) unlocksMap[r].push(t.id);
  for (const h of t.helps) if (helpedByMap[h]) helpedByMap[h].push(t.id);
}
const catName = Object.fromEntries(DATA.categories.map(c => [c.id, c.name]));

const state = {
  q: "",
  cat: DATA.initialCategory || "all",
  k: "all",
  make: "all",
  easyOnly: false,
  touchedOnly: DATA.initialPreset === "touched" && DATA.technologies.some(t => t.touched),
  view: DATA.initialPreset === "touched" && DATA.technologies.some(t => t.touched) ? "graph" : "matrix",
  selected: null,
  focusTreeId: null,
  showHelps: false,
};

const K_COLORS = {
  0: { fill: "#eeeeee", stroke: "#9e9e9e", text: "#333333" },
  1: { fill: "#fff3cd", stroke: "#c9a227", text: "#4a3900" },
  2: { fill: "#ffe0b2", stroke: "#e08a00", text: "#543100" },
  3: { fill: "#c8e6c9", stroke: "#388e3c", text: "#1b3d1d" },
  4: { fill: "#a5d6a7", stroke: "#1b5e20", text: "#10300f" },
};

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c]));
}

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.remove("show"), 2200);
}

function initChrome() {
  const total = DATA.technologies.length;
  const known = DATA.technologies.filter(t => t.knowledge >= 3).length;
  const theory = DATA.technologies.filter(t => t.knowledge === 1 || t.knowledge === 2).length;
  const unknown = DATA.technologies.filter(t => t.knowledge === 0).length;
  const easy = DATA.technologies.filter(t => t.knowledge <= 1 && t.producibility === "easy").length;
  const touched = DATA.technologies.filter(t => t.touched).length;
  const built = DATA.technologies.filter(t => t.built).length;
  const stats = [
    [total, "Technologies"],
    [known, "Known (K3–K4)"],
    [theory, "Idea / Theory (K1–K2)"],
    [unknown, "Unknown (K0)"],
    [easy, "Easy wins (K0–K1)"],
  ];
  if (DATA.hasCampaign) stats.unshift([built, "Built ★"], [touched, "Touched"]);
  document.getElementById("stats").innerHTML = stats
    .map(([v, l]) => `<div class="stat"><b>${v}</b><span>${l}</span></div>`).join("");

  const catSel = document.getElementById("cat");
  catSel.innerHTML = `<option value="all">All 17 categories (${total})</option>` +
    DATA.categories.map(c => {
      const n = DATA.technologies.filter(t => t.category === c.id).length;
      return `<option value="${esc(c.id)}">${esc(c.name)} (${n})</option>`;
    }).join("");
  catSel.value = state.cat;

  if (DATA.hasCampaign && touched > 0) {
    document.getElementById("presetTouched").style.display = "";
  }

  document.getElementById("legend").innerHTML =
    "<span>Knowledge:</span>" +
    Object.entries(DATA.levels).map(([k, v]) => `<span class="chip k${k}">K${k} ${esc(v)}</span>`).join("") +
    (DATA.hasCampaign ? ` <span class="chip" style="border-color:#17489a;color:#17489a;background:#e8effa">blue ring = touched</span>` : "");
}

function getFiltered() {
  const q = state.q.trim().toLowerCase();
  return DATA.technologies.filter(t => {
    if (state.cat !== "all" && t.category !== state.cat) return false;
    if (state.k !== "all" && String(t.knowledge) !== state.k) return false;
    if (state.make !== "all" && t.producibility !== state.make) return false;
    if (state.easyOnly && !(t.knowledge <= 1 && t.producibility === "easy")) return false;
    if (state.touchedOnly && !t.touched) return false;
    if (q) {
      const hay = `${t.id} ${t.name} ${t.note} ${t.local.join(" ")} ${t.elsewhere.join(" ")}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}

function statusText(t) {
  const kStr = t.touched && t.knowledge !== t.knowledge_before
    ? `K${t.knowledge_before}→K${t.knowledge}` : `K${t.knowledge}`;
  return `${kStr} · make ${t.producibility}` + (t.built ? " · ★" : "");
}

function renderMatrix(list) {
  if (!list.length) {
    return `<div class="graph-notice">No technologies match the current filter.</div>`;
  }
  const byCat = new Map();
  for (const t of list) {
    if (!byCat.has(t.category)) byCat.set(t.category, []);
    byCat.get(t.category).push(t);
  }
  let html = "";
  for (const c of DATA.categories) {
    const items = byCat.get(c.id);
    if (!items || !items.length) continue;
    items.sort((a, b) => (b.touched - a.touched) || (b.knowledge - a.knowledge) || a.name.localeCompare(b.name));
    html += `<section class="cat-block">
      <div class="cat-head">
        <h2>${esc(c.name)}</h2>
        <span>${items.length} shown · <a href="#" data-graph-cat="${esc(c.id)}" style="color:var(--blue)">graph category</a></span>
      </div>
      <div class="grid">` +
      items.map(t => `<button class="card k${t.knowledge}${t.touched ? " touched" : ""}${state.selected === t.id ? " selected" : ""}" data-id="${esc(t.id)}">
        <div class="card-title">${esc(t.name)}</div>
        <div class="card-meta"><span>${esc(statusText(t))}</span><span>use ${esc(t.use)}</span></div>
      </button>`).join("") +
      `</div></section>`;
  }
  return html;
}

function getGraphSubset(filtered) {
  if (state.focusTreeId && byId[state.focusTreeId]) {
    const primary = new Set([state.focusTreeId]);
    const stubs = new Set();
    // Walk all ancestors via requires
    const qUp = [state.focusTreeId];
    while (qUp.length) {
      const cur = qUp.shift();
      for (const r of byId[cur].requires) {
        if (!primary.has(r) && !stubs.has(r)) { stubs.add(r); qUp.push(r); }
      }
    }
    // Walk 2 hops downstream via requires
    let frontier = [state.focusTreeId];
    for (let depth = 0; depth < 2; depth++) {
      const next = [];
      for (const cur of frontier) {
        for (const u of (unlocksMap[cur] || [])) {
          if (!primary.has(u) && !stubs.has(u)) { stubs.add(u); next.push(u); }
        }
      }
      frontier = next;
    }
    return { primary, stubs, title: `Dependency tree: ${byId[state.focusTreeId].name}` };
  }
  if (state.touchedOnly) {
    const primary = new Set(filtered.map(t => t.id));
    const stubs = new Set();
    for (const id of primary) {
      for (const r of byId[id].requires) if (!primary.has(r)) stubs.add(r);
      for (const u of (unlocksMap[id] || [])) if (!primary.has(u)) stubs.add(u);
    }
    return { primary, stubs, title: `Campaign progress & 1-hop unlocks (${primary.size} touched)` };
  }
  const primary = new Set(filtered.map(t => t.id));
  const stubs = new Set();
  for (const id of primary) {
    for (const r of byId[id].requires) if (!primary.has(r)) stubs.add(r);
  }
  const title = state.cat !== "all" ? `Category graph: ${catName[state.cat]}` : `Filtered graph (${primary.size} nodes)`;
  return { primary, stubs, title };
}

function buildMermaidForSubset(primary, stubs, includeHelps) {
  const vis = new Set([...primary, ...stubs]);
  const lines = ["flowchart LR"];
  for (const c of DATA.categories) {
    const items = DATA.technologies.filter(t => t.category === c.id && vis.has(t.id));
    if (!items.length) continue;
    lines.push(`  subgraph ${c.id}["${c.name.replace(/"/g, "'")}"]`);
    lines.push("    direction TB");
    for (const t of items) {
      const kStr = t.touched && t.knowledge !== t.knowledge_before ? `K${t.knowledge_before} → K${t.knowledge}` : `K${t.knowledge}`;
      const st = `${kStr} · ${DATA.levels[String(t.knowledge)]}${t.built ? " · built ★" : ""}`;
      lines.push(`    ${t.id}["${t.name.replace(/"/g, "'")}<br/><small>${st}</small>"]`);
    }
    lines.push("  end");
  }
  for (const id of vis) {
    const t = byId[id];
    for (const r of t.requires) if (vis.has(r) && (primary.has(id) || primary.has(r))) lines.push(`  ${r} --> ${id}`);
    if (includeHelps) {
      for (const h of t.helps) if (primary.has(id) && primary.has(h)) lines.push(`  ${h} -.-> ${id}`);
    }
  }
  for (const [k, c] of Object.entries(K_COLORS)) {
    lines.push(`  classDef k${k} fill:${c.fill},stroke:${c.stroke},color:${c.text}`);
  }
  lines.push("  classDef touched stroke-width:4px,stroke:#17489A");
  lines.push("  classDef context stroke-dasharray:5 4");
  for (const id of vis) {
    const t = byId[id];
    lines.push(`  class ${id} k${t.knowledge}`);
    if (t.touched) lines.push(`  class ${id} touched`);
    else if (stubs.has(id)) lines.push(`  class ${id} context`);
  }
  return lines.join("\\n");
}

function renderGraph(filtered) {
  const { primary, stubs, title } = getGraphSubset(filtered);
  const visIds = [...new Set([...primary, ...stubs])];

  const bar = `<div class="graph-bar">
    <b>${esc(title)}</b> · ${visIds.length} nodes
    ${state.focusTreeId ? `<button class="btn" id="clearFocusBtn">Exit tree focus</button>` : ""}
    <label style="margin-left:8px;cursor:pointer"><input type="checkbox" id="toggleHelps" ${state.showHelps ? "checked" : ""}> dotted helps</label>
    <span class="spacer"></span>
    <button class="btn" id="copyMmdBtn">Copy Mermaid</button>
  </div>`;

  if (visIds.length === 0) {
    return `<div class="graph-wrap">${bar}<div class="graph-notice">No technologies in current selection.</div></div>`;
  }
  if (visIds.length > 90) {
    const catLinks = DATA.categories.map(c =>
      `<button class="btn" data-graph-cat="${esc(c.id)}" style="margin:3px">${esc(c.name)}</button>`
    ).join("");
    return `<div class="graph-wrap">${bar}<div class="graph-notice">
      <p><b>${visIds.length} nodes</b> is too dense for a single flowchart. Pick a category below, enable <b>Easy wins</b>, or click any tech in Matrix view and press <b>Focus dependency tree</b>.</p>
      <div style="margin-top:12px">${catLinks}</div>
    </div></div>`;
  }

  // Compute DAG layers via longest path from visible prerequisites
  const visSet = new Set(visIds);
  const memo = new Map();
  const visiting = new Set();
  function layerOf(id) {
    if (memo.has(id)) return memo.get(id);
    if (visiting.has(id)) return 0;
    visiting.add(id);
    let maxP = -1;
    for (const r of byId[id].requires) {
      if (visSet.has(r)) maxP = Math.max(maxP, layerOf(r));
    }
    visiting.delete(id);
    const lvl = maxP + 1;
    memo.set(id, lvl);
    return lvl;
  }
  const cols = new Map();
  for (const id of visIds) {
    const l = layerOf(id);
    if (!cols.has(l)) cols.set(l, []);
    cols.get(l).push(id);
  }
  const sortedLayers = [...cols.keys()].sort((a, b) => a - b);
  const NODE_W = 205, NODE_H = 52, GAP_X = 64, GAP_Y = 16, PAD = 22;
  const pos = new Map();
  let maxH = 0;
  for (const l of sortedLayers) {
    const list = cols.get(l).sort((a, b) => {
      const ta = byId[a], tb = byId[b];
      return ta.category.localeCompare(tb.category) || ta.name.localeCompare(tb.name);
    });
    const colH = list.length * (NODE_H + GAP_Y) - GAP_Y;
    maxH = Math.max(maxH, colH);
    list.forEach((id, idx) => {
      pos.set(id, {
        x: PAD + l * (NODE_W + GAP_X),
        y: PAD + idx * (NODE_H + GAP_Y),
      });
    });
  }
  const svgW = PAD * 2 + sortedLayers.length * (NODE_W + GAP_X) - GAP_X;
  const svgH = Math.max(220, PAD * 2 + maxH);

  let edgesSvg = "";
  for (const id of visIds) {
    const t = byId[id];
    const dst = pos.get(id);
    for (const r of t.requires) {
      if (!visSet.has(r) || (!primary.has(id) && !primary.has(r))) continue;
      const src = pos.get(r);
      const x1 = src.x + NODE_W, y1 = src.y + NODE_H / 2;
      const x2 = dst.x, y2 = dst.y + NODE_H / 2;
      const mx = (x1 + x2) / 2;
      const hi = state.selected === id || state.selected === r;
      edgesSvg += `<path d="M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}" fill="none" stroke="${hi ? "#17489a" : "#64748b"}" stroke-width="${hi ? 2.4 : 1.4}" marker-end="url(#${hi ? "arr-hi" : "arr"})"/>`;
    }
    if (state.showHelps) {
      for (const h of t.helps) {
        if (!primary.has(id) || !primary.has(h)) continue;
        const src = pos.get(h);
        const x1 = src.x + NODE_W, y1 = src.y + NODE_H / 2;
        const x2 = dst.x, y2 = dst.y + NODE_H / 2;
        const mx = (x1 + x2) / 2;
        edgesSvg += `<path d="M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}" fill="none" stroke="#94a3b8" stroke-width="1.1" stroke-dasharray="4 4" marker-end="url(#arr-soft)"/>`;
      }
    }
  }

  let nodesSvg = "";
  for (const id of visIds) {
    const t = byId[id];
    const { x, y } = pos.get(id);
    const c = K_COLORS[t.knowledge];
    const isSel = state.selected === id;
    const isStub = stubs.has(id) && !primary.has(id);
    const stroke = isSel ? "#d98e0b" : (t.touched ? "#17489a" : c.stroke);
    const sw = isSel ? 3.2 : (t.touched ? 3 : 1.4);
    const dash = isStub ? ' stroke-dasharray="5 3"' : "";
    const shortName = t.name.length > 29 ? t.name.slice(0, 28) + "…" : t.name;
    nodesSvg += `<g class="svg-node" data-id="${esc(id)}" transform="translate(${x},${y})">
      <rect width="${NODE_W}" height="${NODE_H}" rx="7" fill="${c.fill}" stroke="${stroke}" stroke-width="${sw}"${dash}/>
      <text x="9" y="21" font-size="12" font-weight="600" fill="${c.text}">${esc(shortName)}</text>
      <text x="9" y="39" font-size="10.5" fill="${c.text}" opacity="0.82">${esc(statusText(t))}${isStub ? " · context" : ""}</text>
    </g>`;
  }

  const svg = `<svg width="${svgW}" height="${svgH}" viewBox="0 0 ${svgW} ${svgH}" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 1 L9 5 L0 9 z" fill="#64748b"/></marker>
      <marker id="arr-hi" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 1 L9 5 L0 9 z" fill="#17489a"/></marker>
      <marker id="arr-soft" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 1 L9 5 L0 9 z" fill="#94a3b8"/></marker>
    </defs>
    ${edgesSvg}${nodesSvg}
  </svg>`;

  renderGraph._lastMmd = () => buildMermaidForSubset(primary, stubs, state.showHelps);
  return `<div class="graph-wrap">${bar}<div class="graph-stage">${svg}</div></div>`;
}

function depChips(ids) {
  if (!ids.length) return `<span class="empty">None</span>`;
  return `<div class="dep-list">` + ids.map(id => {
    const t = byId[id];
    if (!t) return "";
    return `<button class="dep-btn k${t.knowledge}" data-id="${esc(id)}">${esc(t.name)} (K${t.knowledge})</button>`;
  }).join("") + `</div>`;
}

function renderInspector() {
  const el = document.getElementById("inspector");
  const t = state.selected ? byId[state.selected] : null;
  if (!t) {
    el.innerHTML = `<p class="empty">Click any technology to inspect local beliefs, materials, prerequisites, and what it unlocks.</p>` +
      (DATA.worldview ? `<div class="sec-label">Era Worldview</div><div class="note-box">${esc(DATA.worldview)}</div>` : "");
    return;
  }
  const kBadge = t.touched && t.knowledge !== t.knowledge_before
    ? `K${t.knowledge_before} → K${t.knowledge} (${DATA.levels[String(t.knowledge)]})`
    : `K${t.knowledge} (${DATA.levels[String(t.knowledge)]})`;
  el.innerHTML = `
    <h3>${esc(t.name)}</h3>
    <div class="tid">${esc(t.id)} · ${esc(catName[t.category])}</div>
    <div class="kv">
      <span class="chip k${t.knowledge}">${esc(kBadge)}</span>
      <span class="chip" style="border-color:var(--border);background:var(--bg)">use: ${esc(t.use)}</span>
      <span class="chip" style="border-color:var(--border);background:var(--bg)">make: ${esc(t.producibility)}</span>
      <span class="chip" style="border-color:var(--border);background:var(--bg)">accept: ${esc(t.acceptance)}</span>
      ${t.built ? `<span class="chip" style="border-color:#17489a;background:#e8effa;color:#17489a">built ★</span>` : ""}
    </div>
    <div style="margin-bottom:10px">
      <button class="btn" id="focusTreeBtn">Focus dependency tree</button>
    </div>
    ${t.touched ? `<div class="sec-label">Campaign progress</div><div class="note-box">
      ${t.explained_to.length ? `<b>Explained to:</b> ${esc(t.explained_to.join(", "))}<br>` : ""}
      ${t.campaign_notes ? esc(t.campaign_notes) : "No notes recorded."}
    </div>` : ""}
    ${t.note ? `<div class="sec-label">Local status in ${esc(DATA.eraTitle)}</div><div class="note-box">${esc(t.note)}</div>` : ""}
    ${t.local.length ? `<div class="sec-label">Local hooks</div><div class="note-box">${esc(t.local.join("; "))}</div>` : ""}
    ${t.elsewhere.length ? `<div class="sec-label">Exists elsewhere</div><div class="note-box">${esc(t.elsewhere.join("; "))}</div>` : ""}
    <div class="sec-label">Requires (${t.requires.length})</div>
    ${depChips(t.requires)}
    <div class="sec-label">Unlocks directly (${(unlocksMap[t.id] || []).length})</div>
    ${depChips(unlocksMap[t.id] || [])}
    <div class="sec-label">Helped by (${t.helps.length})</div>
    ${depChips(t.helps)}
  `;
  document.getElementById("focusTreeBtn").onclick = () => {
    state.focusTreeId = t.id;
    state.view = "graph";
    render();
  };
  el.querySelectorAll("[data-id]").forEach(btn => {
    btn.onclick = () => { state.selected = btn.dataset.id; render(); };
  });
}

function render() {
  document.getElementById("presetEasy").classList.toggle("active", state.easyOnly);
  document.getElementById("presetTouched").classList.toggle("active", state.touchedOnly);
  document.getElementById("viewMatrix").classList.toggle("active", state.view === "matrix");
  document.getElementById("viewGraph").classList.toggle("active", state.view === "graph");
  document.getElementById("cat").value = state.cat;

  const filtered = getFiltered();
  const content = document.getElementById("content");
  content.innerHTML = state.view === "matrix" ? renderMatrix(filtered) : renderGraph(filtered);

  content.querySelectorAll("[data-id]").forEach(el => {
    el.onclick = () => { state.selected = el.dataset.id; render(); };
  });
  content.querySelectorAll("[data-graph-cat]").forEach(el => {
    el.onclick = e => {
      e.preventDefault();
      state.cat = el.dataset.graphCat;
      state.focusTreeId = null;
      state.touchedOnly = false;
      state.view = "graph";
      render();
    };
  });
  const clearBtn = document.getElementById("clearFocusBtn");
  if (clearBtn) clearBtn.onclick = () => { state.focusTreeId = null; render(); };
  const toggleHelps = document.getElementById("toggleHelps");
  if (toggleHelps) toggleHelps.onchange = () => { state.showHelps = toggleHelps.checked; render(); };
  const copyBtn = document.getElementById("copyMmdBtn");
  if (copyBtn && renderGraph._lastMmd) {
    copyBtn.onclick = async () => {
      try {
        await navigator.clipboard.writeText(renderGraph._lastMmd());
        toast("Mermaid diagram copied to clipboard");
      } catch {
        toast("Clipboard unavailable; use the .mmd file");
      }
    };
  }
  renderInspector();
}

initChrome();
document.getElementById("q").oninput = e => { state.q = e.target.value; state.focusTreeId = null; render(); };
document.getElementById("cat").onchange = e => { state.cat = e.target.value; state.focusTreeId = null; render(); };
document.getElementById("kfilter").onchange = e => { state.k = e.target.value; state.focusTreeId = null; render(); };
document.getElementById("make").onchange = e => { state.make = e.target.value; state.focusTreeId = null; render(); };
document.getElementById("presetEasy").onclick = () => { state.easyOnly = !state.easyOnly; state.focusTreeId = null; render(); };
document.getElementById("presetTouched").onclick = () => { state.touchedOnly = !state.touchedOnly; state.focusTreeId = null; render(); };
document.getElementById("viewMatrix").onclick = () => { state.view = "matrix"; render(); };
document.getElementById("viewGraph").onclick = () => { state.view = "graph"; render(); };
document.getElementById("resetBtn").onclick = () => {
  state.q = ""; state.cat = "all"; state.k = "all"; state.make = "all";
  state.easyOnly = false; state.touchedOnly = false; state.focusTreeId = null;
  document.getElementById("q").value = "";
  document.getElementById("kfilter").value = "all";
  document.getElementById("make").value = "all";
  render();
};
render();
</script>
</body>
</html>
"""


def build_html(payload: dict, title: str, subtitle: str) -> str:
    raw_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return (
        HTML_TEMPLATE.replace("__TITLE__", html.escape(title))
        .replace("__SUBTITLE__", html.escape(subtitle))
        .replace("__JSON__", raw_json)
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("campaign", nargs="?", type=Path, help="campaign file (Markdown with YAML block)")
    ap.add_argument("--era", help="era id, if no campaign file is given")
    ap.add_argument("-o", "--out", type=Path, help="output path without extension")
    ap.add_argument(
        "--category",
        nargs="+",
        help="filter .mmd (and initial HTML view) to one or more category ids",
    )
    ap.add_argument(
        "--touched",
        action="store_true",
        help="filter .mmd to campaign-touched technologies and 1-hop prerequisites/unlocks",
    )
    ap.add_argument(
        "--no-helps",
        action="store_true",
        help="omit dotted 'helps' edges from .mmd output",
    )
    ap.add_argument(
        "--all",
        action="store_true",
        help="force all technologies into .mmd (warning: may exceed Mermaid size/edge limits)",
    )
    args = ap.parse_args()

    campaign = load_campaign(args.campaign) if args.campaign else None
    era_id = campaign["era"] if campaign else args.era
    if not era_id:
        ap.error("give a campaign file or --era")

    core = load_core()
    era = load_era(era_id)

    categories: list[str] | None = None
    if args.category:
        categories = [c.strip() for item in args.category for c in item.split(",") if c.strip()]
        unknown = [c for c in categories if c not in core["categories"]]
        if unknown:
            ap.error(f"unknown category: {', '.join(unknown)}. Valid: {', '.join(core['categories'])}")

    primary, stubs = select_mermaid_ids(core, campaign, categories, args.touched, args.all)
    if primary is None:
        mermaid = build_mermaid_overview(core, era, campaign)
        mmd_mode = "17-category overview"
    else:
        mermaid = build_mermaid_subgraph(
            core, era, campaign, primary, stubs, include_helps=not args.no_helps
        )
        mmd_mode = f"{len(primary)} primary + {len(stubs)} context nodes"
        if len(mermaid) > 50_000:
            print(
                f"note: .mmd is {len(mermaid)} bytes (> Mermaid's 50 KB default limit); "
                "use --category or --touched for GitHub-safe Mermaid diagrams.",
                file=sys.stderr,
            )

    if campaign:
        title = campaign.get("title", era["title"])
        t = campaign.get("time") or {}
        subtitle = f"Campaign progress · {t.get('start', '?')} → {t.get('now', '?')} · skill {campaign.get('skill_version', '?')}"
        default_out = ROOT / "out" / args.campaign.stem
    else:
        title = era["title"]
        subtitle = f"Technology status in {era['region']}, {era['year']}"
        suffix = f"-{categories[0]}" if categories and len(categories) == 1 else ""
        default_out = ROOT / "out" / f"{era_id}{suffix}"
    out = args.out or default_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".mmd").write_text(mermaid, encoding="utf-8")
    payload = build_payload(core, era, campaign, categories, args.touched)
    out.with_suffix(".html").write_text(build_html(payload, title, subtitle), encoding="utf-8")
    print(f"wrote {out.with_suffix('.mmd')} ({mmd_mode}) and {out.with_suffix('.html')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
