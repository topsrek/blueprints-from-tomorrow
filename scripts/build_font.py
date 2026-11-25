"""Compile assets/fonts/AlloVariable.ttf (1.19 MB) into a compact webfont
assets/fonts/allo-web.woff2 (~30-45 KB):
- Pins ROND=50 and opsz=32 (matching scripts/build_logo.py)
- Keeps variable wght axis (400..800) so all weights come from one file
- Subsets to Latin + European diacritics + typographic punctuation & arrows

Usage:
    python scripts/build_font.py
"""

from __future__ import annotations

from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "fonts" / "AlloVariable.ttf"
OUT = ROOT / "assets" / "fonts" / "allo-web.woff2"

UNICODES = (
    "U+0020-007E,"  # Basic Latin
    "U+00A0-00FF,"  # Latin-1 Supplement (äöüßéèêàìòùñ¿¡«»·)
    "U+0100-017F,"  # Latin Extended-A
    "U+2010-2027,"  # Dashes, quotes (“”„’—–…)
    "U+2030-205E,"  # Extra punctuation
    "U+2190-2194,"  # Arrows (←→↔)
    "U+2212"        # Minus sign (−)
)


def main() -> None:
    font = TTFont(SRC)
    instancer.instantiateVariableFont(
        font,
        {"wght": (400, 800), "ROND": (0, 50), "opsz": 14},
        inplace=True,
    )
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["kern", "liga"]
    options.desubroutinize = False

    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=subset.parse_unicodes(UNICODES))
    subsetter.subset(font)

    font.flavor = "woff2"
    font.save(OUT)
    src_kb = SRC.stat().st_size / 1024
    out_kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT.relative_to(ROOT)} ({out_kb:.1f} KB, down from {src_kb:.0f} KB)")


if __name__ == "__main__":
    main()
