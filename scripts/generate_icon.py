"""Generiert die Brand-Icons (icon.png 256px, icon@2x.png 512px) ohne Pillow.

Motiv passend zur Dashboard-Karte: Amortisations-Donut (blauer Bogen auf
grauem Ring) mit grünen Wachstumsbalken in der Mitte. Transparenter Hintergrund.

Aufruf:  python scripts/generate_icon.py
"""

from __future__ import annotations

import math
import os
import struct
import zlib

BLUE = (3, 169, 244)      # Bogen (#03a9f4, Karten-Primärfarbe)
GREY = (215, 221, 226)    # Rest-Ring
GREEN = (76, 175, 80)     # Balken (#4caf50)


def _write_png(path: str, size: int, pixels: list[tuple[int, int, int, int]]) -> None:
    """Schreibt RGBA-Pixel als PNG (minimaler Writer, kein Pillow nötig)."""
    raw = b"".join(
        b"\x00" + bytes(c for px in pixels[y * size:(y + 1) * size] for c in px)
        for y in range(size)
    )

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)  # 8-bit RGBA
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )
    with open(path, "wb") as f:
        f.write(png)


def _sample(x: float, y: float, size: float) -> tuple[float, float, float, float]:
    """Farbe (r,g,b,a je 0..1) an Subpixel-Position – Donut + Balken."""
    s = size / 256.0  # Skalierungsfaktor relativ zum 256er-Design
    cx = cy = size / 2.0
    dx, dy = x - cx, y - cy
    dist = math.hypot(dx, dy)

    outer, inner = 118.0 * s, 86.0 * s
    edge = 1.5 * s  # weiche Kante

    def cov(d_in: float, d_out: float) -> float:
        """Abdeckung im Ringband [d_in, d_out] mit weicher Kante."""
        a_out = min(1.0, max(0.0, (d_out - dist) / edge))
        a_in = min(1.0, max(0.0, (dist - d_in) / edge))
        return a_out * a_in

    ring = cov(inner, outer)
    if ring > 0.0:
        # Winkel: -90° = oben; Bogen läuft 270° im Uhrzeigersinn (bis 180°).
        ang = math.degrees(math.atan2(dy, dx))
        color = BLUE if ang >= -90.0 else GREY
        return (color[0] / 255, color[1] / 255, color[2] / 255, ring)

    # Wachstumsbalken in der Mitte (3 Stück, ansteigend)
    bar_w = 20.0 * s
    gap = 9.0 * s
    bottom = cy + 42.0 * s
    heights = [32.0 * s, 52.0 * s, 72.0 * s]
    total_w = 3 * bar_w + 2 * gap
    x0 = cx - total_w / 2.0
    for i, h in enumerate(heights):
        bx = x0 + i * (bar_w + gap)
        if bx <= x <= bx + bar_w and bottom - h <= y <= bottom:
            return (GREEN[0] / 255, GREEN[1] / 255, GREEN[2] / 255, 1.0)
    return (0.0, 0.0, 0.0, 0.0)


def render(size: int) -> list[tuple[int, int, int, int]]:
    """Rendert mit 2x2-Supersampling für glatte Kanten."""
    pixels: list[tuple[int, int, int, int]] = []
    offsets = [0.25, 0.75]
    for py in range(size):
        for px in range(size):
            r = g = b = a = 0.0
            for oy in offsets:
                for ox in offsets:
                    sr, sg, sb, sa = _sample(px + ox, py + oy, float(size))
                    r += sr * sa
                    g += sg * sa
                    b += sb * sa
                    a += sa
            n = len(offsets) ** 2
            a /= n
            if a > 0:
                pixels.append((
                    round(r / n / a * 255), round(g / n / a * 255),
                    round(b / n / a * 255), round(a * 255),
                ))
            else:
                pixels.append((0, 0, 0, 0))
    return pixels


if __name__ == "__main__":
    out_dir = os.path.join(
        os.path.dirname(__file__), "..", "custom_components", "roi_tracker", "brand"
    )
    os.makedirs(out_dir, exist_ok=True)
    for name, size in (("icon.png", 256), ("icon@2x.png", 512)):
        path = os.path.join(out_dir, name)
        _write_png(path, size, render(size))
        print(f"OK  {path} ({size}x{size})")
