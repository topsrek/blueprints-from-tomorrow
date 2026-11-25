"""Generate static HTML scenario subpages in scenarios/*.html from campaigns/*.md
and techtree/eras/*.yaml (plus scenarios/custom.html for custom eras).

Usage:
    python scripts/build_pages.py
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from techtree import ROOT, era_status, load_core, load_era

OUT = ROOT / "scenarios"
SITE_URL = "https://blueprintsfromtomorrow.com"

SCENARIOS = [
    {
        "slug": "florence-1490",
        "campaign": "florence-1490",
        "era": "europe-1490-florence",
        "art": "../assets/eras/florence-1490.svg",
        "title": "Florence 1490",
        "subtitle": "High Renaissance · Workshops, Medici & Lenses",
        "prompt_place": "Florence 1490",
    },
    {
        "slug": "florence-1347",
        "campaign": "florence-1347",
        "era": "europe-1347-florence",
        "art": "../assets/eras/florence-1347.svg",
        "title": "Florence 1347 – Before the Plague",
        "subtitle": "Eve of the Black Death · Hygiene & Trust Test",
        "prompt_place": "Florence 1347",
    },
    {
        "slug": "vienna-1683",
        "campaign": "vienna-1683",
        "era": "europe-1683-vienna",
        "art": "../assets/eras/vienna-1683.svg",
        "title": "Vienna 1683 – The Siege",
        "subtitle": "Ottoman Siege · Time Pressure & Early Science",
        "prompt_place": "Vienna 1683",
    },
    {
        "slug": "rome-46bc",
        "campaign": "rome-46bc",
        "era": "europe-46bc-rome",
        "art": "../assets/eras/rome-46bc.svg",
        "title": "Rome 46 BC – The Longest Year",
        "subtitle": "Late Republic · Caesar's 445-Day Calendar Reform",
        "prompt_place": "Rome 46 BC",
    },
    {
        "slug": "baghdad-830",
        "campaign": "baghdad-830",
        "era": "islamic-830-baghdad",
        "art": "../assets/eras/baghdad-830.svg",
        "title": "Baghdad 830 – The House of Wisdom",
        "subtitle": "Abbasid Golden Age · Ahead of Medieval Europe",
        "prompt_place": "Baghdad 830",
    },
]

CUSTOM_IDEAS = [
    ("Berlin, 1750", "Frederick the Great, Euler, the Academy of Sciences, and early Prussia."),
    ("Kyoto, 1600", "The eve of the Tokugawa shogunate — Sekigahara, steelcraft, woodblock print, and strict hierarchy."),
    ("Babylon, 590 BC", "Nebuchadnezzar II, astronomy, brick engineering, bronze and early iron."),
    ("Tenochtitlan, 1450", "Floating chinampas, obsidian craftsmanship, causeways — no iron, no draft animals, 70 years before Cortés."),
    ("Alexandria, 250 BC", "The Great Library, Eratosthenes measuring the Earth, Hero's predecessors, and Ptolemaic patronage."),
    ("Bell Labs, 1947", "Months before the transistor — can you explain anything a room full of modern physicists doesn't already know?"),
]


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def md_inline(text: str) -> str:
    """Convert minimal inline markdown (*italic*, **bold**) safely to HTML."""
    s = esc(text)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    return s


def extract_campaign_meta(campaign_id: str) -> tuple[str, list[str]]:
    """Extract start date and Premise paragraphs from campaigns/<id>.md (spoiler-free)."""
    text = (ROOT / "campaigns" / f"{campaign_id}.md").read_text(encoding="utf-8")
    m_date = re.search(r"-\s*\*\*start date:\*\*\s*(.+)", text)
    start_date = m_date.group(1).strip() if m_date else ""
    m_prem = re.search(r"## Premise\s*\n(.*?)(?:\n## |\Z)", text, re.S)
    paragraphs: list[str] = []
    if m_prem:
        raw = m_prem.group(1).strip()
        for chunk in re.split(r"\n\s*\n", raw):
            joined = " ".join(line.strip() for line in chunk.splitlines() if line.strip())
            if joined:
                paragraphs.append(joined)
    return start_date, paragraphs


SHARED_CSS = """
    @font-face {
      font-family: "Allo";
      src: url("../assets/fonts/allo-web.woff2") format("woff2");
      font-weight: 400 800;
      font-style: normal;
      font-display: swap;
    }
    :root {
      --bg-deep: #0b2554;
      --bg-mid: #133c84;
      --bg-card: rgba(8, 24, 58, 0.56);
      --ink: #f3efe4;
      --ink-soft: rgba(243, 239, 228, 0.78);
      --ink-faint: rgba(243, 239, 228, 0.54);
      --line: rgba(243, 239, 228, 0.18);
      --line-strong: rgba(243, 239, 228, 0.42);
      --grid: rgba(243, 239, 228, 0.055);
      --amber: #f5b83d;
      --gutter: 20px;
    }
    *, *::before, *::after { box-sizing: border-box; }
    html { -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }
    body {
      margin: 0;
      font-family: "Allo", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      font-size: 1.0625rem;
      line-height: 1.58;
      color: var(--ink);
      background-color: var(--bg-deep);
      background-image:
        linear-gradient(to right, var(--grid) 1px, transparent 1px),
        linear-gradient(to bottom, var(--grid) 1px, transparent 1px),
        linear-gradient(155deg, #0a224d 0%, var(--bg-mid) 52%, #0d2b63 100%);
      background-size: 40px 40px, 40px 40px, 100% 100%;
      background-attachment: fixed;
      -webkit-font-smoothing: antialiased;
      overflow-wrap: break-word;
    }
    img { max-width: 100%; height: auto; display: block; }
    a { color: var(--ink); text-underline-offset: 0.2em; text-decoration-color: rgba(243,239,228,0.42); }
    a:hover { color: var(--amber); text-decoration-color: var(--amber); }
    :focus-visible { outline: 3px solid var(--amber); outline-offset: 3px; border-radius: 6px; }
    .wrap { width: 100%; max-width: 1020px; margin: 0 auto; padding: 0 var(--gutter); }
    @media (min-width: 720px) { :root { --gutter: 36px; } }

    header { padding: 28px 0 44px; }
    @media (min-width: 720px) { header { padding: 40px 0 56px; } }
    .topbar {
      display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
      gap: 14px 20px;
    }
    .back-link {
      display: inline-flex; align-items: center; gap: 10px;
      font-weight: 700; font-size: 0.98rem; text-decoration: none; min-height: 44px;
    }
    .genre-badge {
      font-size: 0.9rem; font-weight: 750; letter-spacing: 0.02em; line-height: 1.3;
      padding: 8px 16px; border-radius: 6px;
      border: 1.5px solid var(--line-strong); background: var(--bg-card);
      font-variation-settings: "ROND" 10;
      max-width: 100%;
    }

    .hero-grid {
      margin-top: 32px;
      display: grid; gap: 28px; align-items: center;
      grid-template-columns: 1fr;
    }
    @media (min-width: 820px) {
      .hero-grid { grid-template-columns: 1.1fr 0.9fr; gap: 40px; margin-top: 44px; }
    }
    .hero-grid > * { min-width: 0; }
    .kicker {
      margin: 0 0 10px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.86rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
      color: var(--amber);
    }
    h1 {
      margin: 0 0 12px;
      font-size: clamp(2rem, 5.4vw, 3.35rem);
      line-height: 1.09; font-weight: 800; letter-spacing: 0.015em;
      font-variation-settings: "ROND" 8;
      text-wrap: balance;
    }
    .hero-sub { margin: 0; font-size: 1.12rem; color: var(--ink-soft); }
    .hero-art {
      border-radius: 14px; overflow: hidden;
      border: 1.5px solid var(--line-strong);
      background: #0d2c66;
    }

    .start-strip {
      margin-top: 32px;
      display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
      gap: 16px 22px;
      padding: 18px 22px; border-radius: 8px;
      background: rgba(7, 21, 52, 0.74);
      border: 1.5px solid var(--line-strong);
    }
    .start-left { display: flex; align-items: center; gap: 16px; min-width: 0; flex: 1 1 300px; }
    .voice-btn {
      flex: none; width: 52px; height: 52px; border-radius: 50%;
      background: var(--ink); color: var(--bg-deep);
      display: flex; align-items: center; justify-content: center;
    }
    .voice-btn svg { width: 28px; height: 28px; }
    .start-label { margin: 0 0 2px; font-size: 0.94rem; font-weight: 600; color: var(--ink-soft); font-variation-settings: "ROND" 10; }
    .start-prompt {
      margin: 0; font-size: clamp(1.08rem, 2.4vw, 1.45rem);
      line-height: 1.24; font-weight: 800; letter-spacing: 0.012em;
      font-variation-settings: "ROND" 8;
      overflow-wrap: anywhere;
    }
    .start-prompt .domain { color: var(--amber); }
    .copy-btn {
      font: inherit; font-size: 0.96rem; font-weight: 750;
      display: inline-flex; align-items: center; justify-content: center; gap: 8px;
      min-height: 46px; padding: 0 20px; border-radius: 6px;
      border: 1.5px solid var(--amber); cursor: pointer;
      background: var(--amber); color: #0a224d;
      font-variation-settings: "ROND" 10;
      transition: filter 0.15s ease, background-color 0.15s ease, color 0.15s ease;
      white-space: nowrap;
    }
    .copy-btn:hover { filter: brightness(1.08); }
    .copy-btn.done { background: transparent; color: var(--amber); border-color: var(--amber); filter: none; }
    .copy-btn svg { width: 17px; height: 17px; flex: none; }
    @media (max-width: 639px) { .copy-btn { width: 100%; } }

    section { padding: 44px 0; border-top: 1px solid var(--line); }
    @media (min-width: 720px) { section { padding: 56px 0; } }
    h2 {
      margin: 0 0 18px;
      font-size: clamp(1.4rem, 3.2vw, 1.85rem);
      font-weight: 800;
    }
    .prose { max-width: 68ch; color: var(--ink-soft); }
    .prose p { margin: 0 0 14px; }
    .prose p:last-child { margin-bottom: 0; }
    .prose strong { color: var(--ink); }

    .two-col {
      display: grid; gap: 28px 36px; grid-template-columns: 1fr;
    }
    @media (min-width: 760px) { .two-col { grid-template-columns: 1fr 1fr; } }

    .col-block { padding-top: 14px; border-top: 1.5px solid var(--line-strong); }
    .col-block h3 { margin: 0 0 12px; font-size: 1.08rem; font-weight: 750; color: var(--ink); }
    .col-block .count { color: var(--amber); font-weight: 700; font-size: 0.9rem; margin-left: 6px; }

    ul.clean {
      margin: 0; padding: 0; list-style: none;
      display: grid; gap: 10px;
    }
    ul.clean li {
      padding-left: 16px; position: relative;
      font-size: 0.96rem; color: var(--ink-soft);
    }
    ul.clean li::before {
      content: "·"; position: absolute; left: 0; top: 0;
      color: var(--amber); font-weight: 800;
    }
    ul.clean li strong { color: var(--ink); }

    .people-grid {
      display: grid; gap: 16px 28px; grid-template-columns: 1fr;
    }
    @media (min-width: 680px) { .people-grid { grid-template-columns: repeat(2, 1fr); } }
    .person {
      padding-top: 12px; border-top: 1px solid var(--line);
    }
    .person-name { margin: 0 0 3px; font-size: 1.02rem; font-weight: 750; color: var(--ink); }
    .person-role { margin: 0; font-size: 0.92rem; color: var(--ink-soft); line-height: 1.45; }

    .other-scenarios {
      display: flex; flex-wrap: wrap; gap: 10px 18px;
      font-weight: 650; font-size: 0.96rem;
    }
    .other-scenarios a { display: inline-flex; align-items: center; min-height: 40px; }

    footer {
      border-top: 1px solid var(--line);
      padding: 24px 0 40px;
      font-size: 0.88rem; color: var(--ink-faint);
    }
    .foot-inner {
      display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
      gap: 10px 24px;
    }
    .foot-inner nav { display: flex; flex-wrap: wrap; gap: 0 18px; }
    .foot-inner nav a {
      display: inline-flex; align-items: center; min-height: 40px;
      color: var(--ink-soft); font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.84rem;
    }
"""

COPY_SCRIPT = """
  <script>
    (function () {
      var btn = document.getElementById("copyBtn");
      var label = document.getElementById("copyLabel");
      var text = btn.getAttribute("data-prompt");
      var timer;
      function done(ok) {
        clearTimeout(timer);
        if (ok) {
          btn.classList.add("done");
          label.textContent = "Copied!";
          timer = setTimeout(function () { btn.classList.remove("done"); label.textContent = "Copy"; }, 1800);
        }
      }
      btn.addEventListener("click", function () {
        if (navigator.clipboard && window.isSecureContext) {
          navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(false); });
        } else {
          var ta = document.createElement("textarea");
          ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
          document.body.appendChild(ta); ta.select();
          var ok = false; try { ok = document.execCommand("copy"); } catch (e) {}
          document.body.removeChild(ta); done(ok);
        }
      });
    })();
  </script>
"""

VOICE_SVG = """<svg viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="14" width="4.5" height="10" rx="2.25" fill="currentColor"/><rect x="10" y="8" width="4.5" height="22" rx="2.25" fill="currentColor"/><rect x="17" y="4" width="4.5" height="30" rx="2.25" fill="currentColor"/><rect x="24" y="10" width="4.5" height="18" rx="2.25" fill="currentColor"/><rect x="31" y="15" width="4.5" height="8" rx="2.25" fill="currentColor"/></svg>"""


def other_links(current_slug: str) -> str:
    links = []
    for s in SCENARIOS:
        if s["slug"] != current_slug:
            links.append(f'<a href="{s["slug"]}.html">{esc(s["title"])}</a>')
    if current_slug != "custom":
        links.append('<a href="custom.html">Any place, any year</a>')
    return "\n          ".join(links)


def render_scenario(core: dict, sc: dict) -> str:
    era = load_era(sc["era"])
    start_date, premise_paras = extract_campaign_meta(sc["campaign"])
    people = (era.get("people") or [])[:12]
    events = (era.get("events") or [])[:12]

    known_techs = []
    missing_buildable = []
    for t in core["technologies"]:
        st = era_status(era, t["id"])
        if st["knowledge"] >= 3:
            known_techs.append(t)
        elif st["knowledge"] == 0 and st.get("producibility") in ("easy", "medium"):
            missing_buildable.append(t)

    known_sample = known_techs[:10]
    missing_sample = missing_buildable[:10]

    prompt_text = f"Start a game of blueprintsfromtomorrow.com in {sc['prompt_place']} (read https://blueprintsfromtomorrow.com/llms.txt)"
    canonical = f"{SITE_URL}/scenarios/{sc['slug']}"  # Cloudflare serves pages without .html
    page_title = f"{sc['prompt_place']} — Blueprints from Tomorrow"
    desc = f"{sc['prompt_place']}: {sc['subtitle']}. Play this free time-travel AI RPG in ChatGPT, Claude, or Gemini."
    og_desc = f"{sc['prompt_place']} — {sc['subtitle']}. Free single-player time-travel AI RPG."

    premise_html = "\n          ".join(f"<p>{md_inline(p)}</p>" for p in premise_paras)
    people_html = "\n          ".join(
        f'<div class="person"><p class="person-name">{esc(p["name"])}</p>'
        f'<p class="person-role">{esc(" ".join(str(p["role"]).split()))}</p></div>'
        for p in people
    )
    events_html = "\n          ".join(f"<li>{esc(e)}</li>" for e in events)
    known_html = "\n            ".join(f"<li><strong>{esc(t['name'])}</strong></li>" for t in known_sample)
    missing_html = "\n            ".join(f"<li><strong>{esc(t['name'])}</strong></li>" for t in missing_sample)

    kicker_parts = [era["region"], f"Year {era['year']}"]
    if start_date:
        kicker_parts.append(f"Start: {start_date.split('(')[0].strip()}")
    kicker = " · ".join(kicker_parts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(page_title)}</title>
  <meta name="description" content="{esc(desc)}">
  <meta name="robots" content="index, follow">
  <meta name="theme-color" content="#0F3577">
  <link rel="canonical" href="{canonical}">
  <link rel="icon" type="image/svg+xml" href="../favicon.svg">
  <link rel="icon" href="../favicon.ico" sizes="any">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{esc(page_title)}">
  <meta property="og:description" content="{esc(og_desc)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{SITE_URL}/assets/og-image.png">
  <meta name="twitter:card" content="summary_large_image">
  <style>{SHARED_CSS}</style>
</head>
<body>
  <header>
    <div class="wrap">
      <div class="topbar">
        <a class="back-link" href="../index.html">← Blueprints from Tomorrow</a>
        <span class="genre-badge">Free Single-Player AI Role-Playing Game</span>
      </div>

      <div class="hero-grid">
        <div>
          <p class="kicker">{esc(kicker)}</p>
          <h1>{esc(sc['title'])}</h1>
          <p class="hero-sub">{esc(sc['subtitle'])}</p>
        </div>
        <div class="hero-art">
          <img src="{esc(sc['art'])}" alt="Blueprint illustration of {esc(sc['title'])}" width="640" height="360">
        </div>
      </div>

      <div class="start-strip">
        <div class="start-left">
          <div class="voice-btn" aria-hidden="true">{VOICE_SVG}</div>
          <div>
            <p class="start-label">Play this scenario in ChatGPT, Claude or Gemini (best in voice mode):</p>
            <p class="start-prompt">“Start a game of <span class="domain">blueprintsfromtomorrow.com</span> in {esc(sc['prompt_place'])}”</p>
          </div>
        </div>
        <button class="copy-btn" id="copyBtn" type="button" data-prompt="{esc(prompt_text)}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>
          <span id="copyLabel">Copy</span>
        </button>
      </div>
    </div>
  </header>

  <main>
    <section>
      <div class="wrap">
        <h2>Why this era?</h2>
        <div class="prose">
          {premise_html}
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <h2>How people think here</h2>
        <div class="prose">
          <p>{esc(" ".join(str(era["worldview"]).split()))}</p>
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <h2>Technologies in {esc(sc['prompt_place'])}</h2>
        <div class="two-col">
          <div class="col-block">
            <h3>Already in use <span class="count">({len(known_techs)} of {len(core['technologies'])})</span></h3>
            <ul class="clean">
              {known_html}
            </ul>
          </div>
          <div class="col-block">
            <h3>Unknown &amp; buildable locally <span class="count">({len(missing_buildable)} opportunities)</span></h3>
            <ul class="clean">
              {missing_html}
            </ul>
          </div>
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <h2>People you may encounter</h2>
        <div class="people-grid">
          {people_html}
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <h2>Significant events around this time</h2>
        <ul class="clean">
          {events_html}
        </ul>
      </div>
    </section>

    <section>
      <div class="wrap">
        <h2>Explore other scenarios</h2>
        <div class="other-scenarios">
          {other_links(sc['slug'])}
        </div>
      </div>
    </section>
  </main>

  <footer>
    <div class="wrap foot-inner">
      <span><a href="../index.html">← Back to home</a> · Made by <a href="https://topsrek.top" rel="noopener">@topsrek</a> in Austria</span>
      <nav aria-label="Raw agent files">
        <a href="https://github.com/topsrek/blueprints-from-tomorrow" rel="noopener">GitHub</a>
        <a href="../campaigns/{sc['campaign']}.md">campaigns/{sc['campaign']}.md</a>
        <a href="../techtree/generated/{sc['era']}.md">era guide (.md)</a>
        <a href="../techtree/generated/{sc['era']}/briefing.md">briefing (.md)</a>
        <a href="../llms.txt">llms.txt</a>
      </nav>
    </div>
  </footer>
  {COPY_SCRIPT}
</body>
</html>
"""


def render_custom(core: dict) -> str:
    canonical = f"{SITE_URL}/scenarios/custom"
    prompt_text = "Start a game of blueprintsfromtomorrow.com in Kyoto 1600 (read https://blueprintsfromtomorrow.com/llms.txt)"
    region_labels = [
        (v if isinstance(v, str) else str(v)).replace("_", " ").title()
        for v in (core["regions"].values() if isinstance(core["regions"], dict) else core["regions"])
    ]
    regions_html = "\n            ".join(
        f"<li><strong>{esc(r)}</strong></li>" for r in region_labels
    )
    cats_html = "\n            ".join(
        f"<li><strong>{esc(v)}</strong></li>" for v in core["categories"].values()
    )
    ideas_html = "\n          ".join(
        f'<div class="person"><p class="person-name">{esc(name)}</p><p class="person-role">{esc(desc)}</p></div>'
        for name, desc in CUSTOM_IDEAS
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Any Place, Any Year — Blueprints from Tomorrow</title>
  <meta name="description" content="Play Blueprints from Tomorrow in any city and century. 510 historical technologies across 12 world regions keep custom eras grounded.">
  <meta name="robots" content="index, follow">
  <meta name="theme-color" content="#0F3577">
  <link rel="canonical" href="{canonical}">
  <link rel="icon" type="image/svg+xml" href="../favicon.svg">
  <link rel="icon" href="../favicon.ico" sizes="any">
  <meta property="og:type" content="article">
  <meta property="og:title" content="Any Place, Any Year — Blueprints from Tomorrow">
  <meta property="og:description" content="Pick any city, culture, and century in history. Backed by 510 technologies across 12 world regions.">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{SITE_URL}/assets/og-image.png">
  <meta name="twitter:card" content="summary_large_image">
  <style>{SHARED_CSS}</style>
</head>
<body>
  <header>
    <div class="wrap">
      <div class="topbar">
        <a class="back-link" href="../index.html">← Blueprints from Tomorrow</a>
        <span class="genre-badge">Free Single-Player AI Role-Playing Game</span>
      </div>

      <div class="hero-grid">
        <div>
          <p class="kicker">12 World Regions · {len(core['technologies'])} Technologies · Any Century</p>
          <h1>Any place, any year</h1>
          <p class="hero-sub">Drop yourself into any city and century in human history — your AI grounds it using real regional dates and prerequisites.</p>
        </div>
        <div class="hero-art">
          <img src="../assets/eras/custom-era.svg" alt="Blueprint illustration of a globe and hourglass" width="640" height="360">
        </div>
      </div>

      <div class="start-strip">
        <div class="start-left">
          <div class="voice-btn" aria-hidden="true">{VOICE_SVG}</div>
          <div>
            <p class="start-label">Example custom start in ChatGPT, Claude or Gemini (best in voice mode):</p>
            <p class="start-prompt">“Start a game of <span class="domain">blueprintsfromtomorrow.com</span> in Kyoto 1600”</p>
          </div>
        </div>
        <button class="copy-btn" id="copyBtn" type="button" data-prompt="{esc(prompt_text)}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>
          <span id="copyLabel">Copy</span>
        </button>
      </div>
    </div>
  </header>

  <main>
    <section>
      <div class="wrap">
        <h2>Ideas to try</h2>
        <div class="people-grid">
          {ideas_html}
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <h2>How custom eras stay historically grounded</h2>
        <div class="prose">
          <p>When you pick a place and year without a dedicated campaign file, your AI loads the complete <strong>{len(core['technologies'])}-technology reference</strong> with hard prerequisites and first-appearance dates across <strong>{len(core['regions'])} world regions</strong>. That prevents anachronisms (like paper in ancient Rome or printing in 1347 Florence) and lets craftsmen challenge every missing step realistically.</p>
        </div>
        <div class="two-col" style="margin-top:28px">
          <div class="col-block">
            <h3>12 World Regions</h3>
            <ul class="clean">
              {regions_html}
            </ul>
          </div>
          <div class="col-block">
            <h3>17 Technology Categories</h3>
            <ul class="clean">
              {cats_html}
            </ul>
          </div>
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <h2>Verified historical campaigns</h2>
        <div class="other-scenarios">
          {other_links("custom")}
        </div>
      </div>
    </section>
  </main>

  <footer>
    <div class="wrap foot-inner">
      <span><a href="../index.html">← Back to home</a> · Made by <a href="https://topsrek.top" rel="noopener">@topsrek</a> in Austria</span>
      <nav aria-label="Raw agent files">
        <a href="https://github.com/topsrek/blueprints-from-tomorrow" rel="noopener">GitHub</a>
        <a href="../techtree/generated/all-techs.md">all-techs.md</a>
        <a href="../llms.txt">llms.txt</a>
        <a href="../SKILL.md">SKILL.md</a>
      </nav>
    </div>
  </footer>
  {COPY_SCRIPT}
</body>
</html>
"""


def main() -> None:
    core = load_core()
    OUT.mkdir(parents=True, exist_ok=True)
    for sc in SCENARIOS:
        path = OUT / f"{sc['slug']}.html"
        path.write_text(render_scenario(core, sc), encoding="utf-8", newline="\n")
        print(f"wrote {path.relative_to(ROOT)}")
    custom_path = OUT / "custom.html"
    custom_path.write_text(render_custom(core), encoding="utf-8", newline="\n")
    print(f"wrote {custom_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
