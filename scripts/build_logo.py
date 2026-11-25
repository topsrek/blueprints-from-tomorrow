"""Build the logo SVGs in assets/logo/. The wordmark is set in Allo (assets/fonts/,
SIL OFL) and converted to outlines, so the SVGs do not need the font.

Usage:
    python scripts/build_logo.py
"""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "assets" / "fonts" / "AlloVariable.ttf"
OUT = ROOT / "assets" / "logo"

ROUNDNESS = 50  # Allo's ROND axis: 0 sharp, 100 round
TRACKING = 0.02  # extra letter spacing, in em
PAPER, AMBER, BLUE, DEEP, AMBER_DARK = "#F3EFE4", "#F5B83D", "#17489A", "#0F3577", "#D98E0B"

_face = hb.Face(hb.Blob.from_file_path(str(FONT)))
_instances: dict = {}


def axes(weight: int) -> dict:
    return {"wght": weight, "ROND": ROUNDNESS, "opsz": 12}


def instance(weight: int):
    if weight not in _instances:
        font = instancer.instantiateVariableFont(TTFont(FONT), axes(weight))
        _instances[weight] = (font, font.getGlyphSet(), font.getGlyphOrder())
    return _instances[weight]


def outline(text: str, weight: int, size: float, x: float = 0.0, y: float = 0.0):
    """Return (path data, width, cap height) for text with its baseline starting at (x, y)."""
    font, glyphs, order = instance(weight)
    upem = font["head"].unitsPerEm
    scale = size / upem
    shaper = hb.Font(_face)
    shaper.set_variations(axes(weight))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(shaper, buf, {"kern": True, "liga": False})
    pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    cursor = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        place = (scale, 0, 0, -scale, x + (cursor + pos.x_offset) * scale, y - pos.y_offset * scale)
        glyphs[order[info.codepoint]].draw(TransformPen(pen, place))
        cursor += pos.x_advance + TRACKING * upem
    width = (cursor - TRACKING * upem) * scale
    return pen.getCommands(), width, font["OS/2"].sCapHeight * scale


def mark(fg: str, accent: str) -> str:
    """Clock on a 120x120 canvas; the hands start at the centre and point to 2 and 4."""
    return (
        f'<g fill="none" stroke-linecap="round" stroke-linejoin="round">'
        f'<circle cx="60" cy="60" r="42" stroke="{fg}" stroke-width="9"/>'
        f'<path d="M60 27V33M60 87V93M27 60H33" stroke="{fg}" stroke-width="7"/>'
        f'<path d="M85.1 45.5L60 60L85.1 74.5" stroke="{accent}" stroke-width="10"/>'
        f"</g>"
    )


def svg(width: float, height: float, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:g} {height:g}" '
        f'width="{width:g}" height="{height:g}" '
        f'role="img" aria-label="Blueprints from Tomorrow">{body}</svg>\n'
    )


def lockup(fg: str, accent: str) -> str:
    """Mark plus two-line wordmark; the second line is sized to the width of the first."""
    size1, x, gap = 50, 132, 17
    _, width, cap1 = outline("Blueprints", 700, size1)
    size2 = 100 * width / outline("from Tomorrow", 500, 100)[1]
    cap2 = outline("from Tomorrow", 500, size2)[2]
    top = 60 - (cap1 + gap + cap2) / 2
    line1 = outline("Blueprints", 700, size1, x, top + cap1)[0]
    line2 = outline("from Tomorrow", 500, size2, x, top + cap1 + gap + cap2)[0]
    body = mark(fg, accent) + f'<path d="{line1}" fill="{fg}"/><path d="{line2}" fill="{accent}"/>'
    return svg(round(x + width + 4), 120, body)


def icon() -> str:
    body = (
        f'<rect width="120" height="120" rx="26" fill="{BLUE}"/>'
        f'<g transform="translate(8.4 8.4) scale(.86)">{mark(PAPER, AMBER)}</g>'
    )
    return svg(120, 120, body)


def _hex_rgb(code: str) -> tuple[int, int, int]:
    h = code.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _dist_seg(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / l2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def _render_icon_png(size: int) -> bytes:
    """Rasterize the icon mark directly with 4x4 supersampling (zero extra deps)."""
    bg = _hex_rgb(BLUE)
    paper = _hex_rgb(PAPER)
    amber = _hex_rgb(AMBER)
    samples = 4
    inv_s = 1.0 / samples
    rows = bytearray()
    for py in range(size):
        rows.append(0)  # PNG filter type 0
        for px in range(size):
            ar = ag = ab = aa = 0.0
            for sy in range(samples):
                vy = (py + (sy + 0.5) * inv_s) * (120.0 / size)
                for sx in range(samples):
                    vx = (px + (sx + 0.5) * inv_s) * (120.0 / size)
                    # Rounded rect [0,120]^2 with rx=26
                    qx = abs(vx - 60.0) - 34.0
                    qy = abs(vy - 60.0) - 34.0
                    in_rect = math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - 26.0 <= 0.0
                    if not in_rect:
                        continue
                    # Inverse of translate(8.4, 8.4) scale(0.86)
                    mx = (vx - 8.4) / 0.86
                    my = (vy - 8.4) / 0.86
                    # Amber hands (stroke-width 10 -> radius 5)
                    d_hand = min(
                        _dist_seg(mx, my, 85.1, 45.5, 60.0, 60.0),
                        _dist_seg(mx, my, 60.0, 60.0, 85.1, 74.5),
                    )
                    if d_hand <= 5.0:
                        r, g, b = amber
                    else:
                        # Paper circle (r=42, stroke-width 9 -> half 4.5) and ticks (stroke-width 7 -> half 3.5)
                        d_ring = abs(math.hypot(mx - 60.0, my - 60.0) - 42.0)
                        d_tick = min(
                            _dist_seg(mx, my, 60.0, 27.0, 60.0, 33.0),
                            _dist_seg(mx, my, 60.0, 87.0, 60.0, 93.0),
                            _dist_seg(mx, my, 27.0, 60.0, 33.0, 60.0),
                        )
                        if d_ring <= 4.5 or d_tick <= 3.5:
                            r, g, b = paper
                        else:
                            r, g, b = bg
                    ar += r
                    ag += g
                    ab += b
                    aa += 1.0
            n = samples * samples
            if aa > 0:
                rows.extend((round(ar / aa), round(ag / aa), round(ab / aa), round(255 * aa / n)))
            else:
                rows.extend((0, 0, 0, 0))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(rows), 9))
        + chunk(b"IEND", b"")
    )


def build_ico(sizes: tuple[int, ...] = (16, 32, 48)) -> bytes:
    """Wrap PNG icons in a standard multi-size .ico container."""
    images = [(s, _render_icon_png(s)) for s in sizes]
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries = bytearray()
    blobs = bytearray()
    for s, png in images:
        dim = 0 if s >= 256 else s
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset)
        blobs += png
        offset += len(png)
    return header + bytes(entries) + bytes(blobs)


def main() -> None:
    icon_svg = icon()
    files = {
        "mark.svg": svg(120, 120, mark(PAPER, AMBER)),
        "mark-on-light.svg": svg(120, 120, mark(DEEP, AMBER_DARK)),
        "icon.svg": icon_svg,
        "logo.svg": lockup(PAPER, AMBER),
        "logo-on-light.svg": lockup(DEEP, AMBER_DARK),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8", newline="\n")
        print(f"wrote {(OUT / name).relative_to(ROOT)}")

    (ROOT / "favicon.svg").write_text(icon_svg, encoding="utf-8", newline="\n")
    print("wrote favicon.svg")
    (ROOT / "favicon.ico").write_bytes(build_ico())
    print("wrote favicon.ico")


if __name__ == "__main__":
    main()
