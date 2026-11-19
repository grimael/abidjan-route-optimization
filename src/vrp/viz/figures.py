"""Génération de figures PNG avec Pillow uniquement.

Aucune dépendance graphique lourde : Pillow est présent partout où Python l'est,
et le rendu par suréchantillonnage (×3 puis réduction) donne des traits nets
sans antialiasing natif.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SCALE = 3
BG = (255, 255, 255)
INK = (26, 58, 92)
MUTED = (110, 118, 128)
GRID = (226, 230, 235)
PALETTE = [
    (31, 119, 180), (214, 39, 40), (44, 160, 44), (255, 127, 14),
    (148, 103, 189), (140, 86, 75), (227, 119, 194), (23, 190, 207),
]


_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def _font(size: int) -> ImageFont.ImageFont:
    """TrueType si disponible (accents corrects), sinon police par défaut.

    La police bitmap de Pillow ne gère pas les accents : elle rend « é » comme
    deux caractères (« Ã© »). On cherche donc une police système avant tout.
    """
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size * SCALE)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size * SCALE)
    except TypeError:  # Pillow < 10
        return ImageFont.load_default()


def _canvas(w: int, h: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (w * SCALE, h * SCALE), BG)
    return img, ImageDraw.Draw(img)


def _save(img: Image.Image, path: Path, w: int, h: int) -> Path:
    out = img.resize((w, h), Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path, "PNG", optimize=True)
    return path


def _project(lat: np.ndarray, lon: np.ndarray, w: int, h: int, pad: int) -> np.ndarray:
    """Projette lat/lon en pixels, en conservant le ratio et en centrant."""
    x = (lon - lon.min()) / max(lon.max() - lon.min(), 1e-9)
    y = (lat - lat.min()) / max(lat.max() - lat.min(), 1e-9)
    span = min(w - 2 * pad, h - 2 * pad)
    ox = (w - span) / 2
    oy = (h - span) / 2
    # latitude croissante vers le haut : on inverse y
    return np.column_stack([ox + x * span, oy + (1 - y) * span])


def route_map(
    instance,
    routes: list[list[int]],
    path: str | Path,
    title: str = "",
    width: int = 900,
    height: int = 700,
    unit: str = "s",
) -> Path:
    """Carte des tournées : points, dépôt, arêtes colorées, étiquettes."""
    w, h = width, height
    img, d = _canvas(w, h)
    pad = 105
    pts = _project(instance.lat, instance.lon, w, h, pad) * SCALE

    if title:
        d.text((pad * SCALE, 24 * SCALE), title, font=_font(20), fill=INK)
    sub = f"{len(routes)} tournées · {instance.n} points · coût total {sum(instance.tour_cost(r) for r in routes):.0f} {unit}"
    d.text((pad * SCALE, 52 * SCALE), sub, font=_font(12), fill=MUTED)

    for i, route in enumerate(routes):
        color = PALETTE[i % len(PALETTE)]
        seq = [0, *route, 0]
        for a, b in zip(seq, seq[1:]):
            d.line([tuple(pts[a]), tuple(pts[b])], fill=color, width=2 * SCALE)
        # arrêts numérotés
        for k, node in enumerate(route, start=1):
            x, y = pts[node]
            r = 9 * SCALE
            d.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=BG, width=SCALE)
            label = str(k)
            fb = _font(9)
            tw = d.textlength(label, font=fb)
            d.text((x - tw / 2, y - 5 * SCALE), label, font=fb, fill=BG)

    # dépôt
    x, y = pts[0]
    r = 13 * SCALE
    d.ellipse([x - r, y - r, x + r, y + r], fill=(17, 17, 17), outline=BG, width=2 * SCALE)
    fb = _font(11)
    tw = d.textlength("D", font=fb)
    d.text((x - tw / 2, y - 7 * SCALE), "D", font=fb, fill=BG)

    # noms des points, sur un fond blanc pour rester lisibles au-dessus des traits
    f = _font(9)
    names = instance.meta.get("points") or [{"name": f"P{i}"} for i in range(instance.n)]
    for i, p in enumerate(names):
        if i == 0:
            continue
        x, y = pts[i]
        label = p.get("name", f"P{i}")
        tw = d.textlength(label, font=f)
        d.rectangle([x + 10 * SCALE, y - 6 * SCALE, x + 14 * SCALE + tw, y + 6 * SCALE], fill=BG)
        d.text((x + 12 * SCALE, y - 5 * SCALE), label, font=f, fill=MUTED)

    # légende
    ly = h - 40
    for i, route in enumerate(routes):
        color = PALETTE[i % len(PALETTE)]
        x0 = (pad + i * 150) * SCALE
        d.rectangle([x0, (ly - 6) * SCALE, x0 + 18 * SCALE, (ly + 6) * SCALE], fill=color)
        d.text((x0 + 26 * SCALE, (ly - 6) * SCALE),
               f"Véhicule {i + 1} · {instance.tour_cost(route):.0f} {unit}",
               font=_font(10), fill=INK)

    return _save(img, Path(path), w, h)


def convergence(
    histories: list[list[float]],
    optimum: float | None,
    path: str | Path,
    title: str = "Convergence de l'algorithme génétique",
    width: int = 800,
    height: int = 450,
    unit: str = "s",
) -> Path:
    """Courbes de convergence (une par graine) avec ligne d'optimum."""
    w, h = width, height
    img, d = _canvas(w, h)
    left, right, top, bottom = 95, 40, 70, 70

    if histories and isinstance(histories[0], (int, float)):
        histories = [histories]  # appel avec une seule courbe

    all_values = np.array([v for hst in histories for v in hst], dtype=float)
    y_min = min(all_values.min(), optimum if optimum is not None else all_values.min())
    y_max = all_values.max()
    span = max(y_max - y_min, 1e-9)
    y_min -= span * 0.06
    y_max += span * 0.06
    n_gen = max(len(hst) for hst in histories)

    def px(i: int, v: float) -> tuple[float, float]:
        x = left + (right - left) * (i / max(n_gen - 1, 1))
        y = h - bottom - (h - top - bottom) * (v - y_min) / (y_max - y_min)
        return x * SCALE, y * SCALE

    d.text((left * SCALE, 22 * SCALE), title, font=_font(18), fill=INK)

    for k in range(5):
        v = y_min + (y_max - y_min) * k / 4
        _, y = px(0, v)
        d.line([(left * SCALE, y), ((w - right) * SCALE, y)], fill=GRID, width=SCALE)
        d.text((10 * SCALE, y - 6 * SCALE), f"{v:.0f}", font=_font(9), fill=MUTED)

    if optimum is not None:
        _, yo = px(0, optimum)
        for x in range(left, w - right, 12):
            d.line([(x * SCALE, yo), ((x + 6) * SCALE, yo)], fill=(214, 39, 40), width=SCALE)
        d.text(((w - right - 160) * SCALE, yo - 17 * SCALE),
               f"optimum {optimum:.0f} {unit}", font=_font(9), fill=(214, 39, 40))

    for idx, hst in enumerate(histories):
        colour = PALETTE[idx % len(PALETTE)]
        pts = [px(i, v) for i, v in enumerate(hst)]
        d.line(pts, fill=colour, width=2 * SCALE, joint="curve")

    d.text((left * SCALE, (h - 42) * SCALE), "générations", font=_font(10), fill=MUTED)
    d.text((10 * SCALE, (top - 22) * SCALE), f"coût ({unit})", font=_font(10), fill=MUTED)
    d.text(((w - right - 190) * SCALE, (h - 42) * SCALE),
           f"{len(histories)} graines", font=_font(10), fill=MUTED)
    return _save(img, Path(path), w, h)


def bars(
    labels: list[str],
    values: list[float],
    path: str | Path,
    title: str = "",
    width: int = 800,
    height: int = 380,
    unit: str = "",
) -> Path:
    """Histogramme horizontal, valeurs décroissantes."""
    w, h = width, height
    img, d = _canvas(w, h)
    left, right, top, bottom = 190, 90, 60, 40
    vmax = max(values) * 1.05

    d.text((24 * SCALE, 20 * SCALE), title, font=_font(17), fill=INK)
    bar_h = (h - top - bottom) / len(values) * 0.62
    step = (h - top - bottom) / len(values)

    for i, (label, v) in enumerate(zip(labels, values)):
        y = top + i * step + step * 0.18
        length = (w - left - right) * v / vmax
        color = PALETTE[i % len(PALETTE)]
        d.rectangle([left * SCALE, y * SCALE, (left + length) * SCALE, (y + bar_h) * SCALE], fill=color)
        d.text(((left - 8) * SCALE - d.textlength(label, font=_font(10)), (y + bar_h / 2 - 6) * SCALE),
               label, font=_font(10), fill=INK)
        d.text(((left + length + 8) * SCALE, (y + bar_h / 2 - 6) * SCALE),
               f"{v:.0f} {unit}".strip(), font=_font(10), fill=MUTED)

    return _save(img, Path(path), w, h)
