"""Carte interactive des tournées, sans dépendance Python.

Génère un fichier HTML autonome : Leaflet et les tuiles OpenStreetMap sont
chargés depuis un CDN, les tournées sont dessinées en polylignes colorées.
Aucune bibliothèque à installer — le fichier s'ouvre dans n'importe quel
navigateur, et reste lisible dans un dépôt Git.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..instance import Instance

PALETTE = [
    "#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd",
    "#8c564b", "#e377c2", "#17becf", "#bcbd22", "#7f7f7f",
]

TEMPLATE = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
  html, body { margin: 0; height: 100%; font-family: system-ui, sans-serif; }
  #map { height: 100%; }
  .legend { background: #fff; padding: 10px 12px; border-radius: 6px; box-shadow: 0 1px 6px rgba(0,0,0,.25); font-size: 12px; line-height: 1.5; max-height: 70vh; overflow: auto; }
  .legend h3 { margin: 0 0 6px; font-size: 13px; }
  .swatch { display: inline-block; width: 13px; height: 13px; border-radius: 2px; margin-right: 6px; vertical-align: -2px; }
  .total { margin-top: 8px; font-weight: 600; }
</style>
</head>
<body>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const data = __DATA__;
const map = L.map('map');
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; contributeurs OpenStreetMap'
}).addTo(map);

function marker(latlng, html, size) {
  return L.marker(latlng, { icon: L.divIcon({ className: '', html: html, iconSize: size }) });
}

const depot = data.points[0];
marker([depot.lat, depot.lon], '<div style="background:#111;color:#fff;border-radius:50%;width:26px;height:26px;display:flex;align-items:center;justify-content:center;font:600 12px sans-serif;">D</div>', [26, 26])
  .addTo(map).bindPopup('Dépôt : ' + depot.name);

const bounds = [[depot.lat, depot.lon]];
data.routes.forEach((route, idx) => {
  const color = data.colors[idx % data.colors.length];
  const pts = [[depot.lat, depot.lon]];
  route.stops.forEach((s, k) => {
    const p = data.points[s];
    pts.push([p.lat, p.lon]);
    bounds.push([p.lat, p.lon]);
    marker([p.lat, p.lon], '<div style="background:' + color + ';color:#fff;border-radius:50%;width:20px;height:20px;display:flex;align-items:center;justify-content:center;font:600 10px sans-serif;">' + (k + 1) + '</div>', [20, 20])
      .addTo(map).bindPopup(data.routes[idx].label + '<br>arrêt ' + (k + 1) + ' : ' + p.name);
  });
  pts.push([depot.lat, depot.lon]);
  L.polyline(pts, { color: color, weight: 3, opacity: 0.85 }).addTo(map);
});

const legend = L.control({ position: 'topright' });
legend.onAdd = function () {
  const div = L.DomUtil.create('div', 'legend');
  let html = '<h3>' + data.title + '</h3>';
  data.routes.forEach((r, i) => {
    html += '<div><span class="swatch" style="background:' + data.colors[i % data.colors.length] + '"></span>' + r.label + ' — ' + r.stops.length + ' arrêts, ' + r.cost + '</div>';
  });
  html += '<div class="total">Total : ' + data.total + '</div>';
  div.innerHTML = html;
  return div;
};
legend.addTo(map);
map.fitBounds(bounds, { padding: [30, 30] });
</script>
</body>
</html>
"""


def solution_map(
    instance: Instance,
    routes: list[list[int]],
    path: str | Path,
    title: str | None = None,
    unit: str | None = None,
) -> Path:
    """Écrit une carte HTML des tournées et renvoie le chemin du fichier."""
    points = instance.meta.get(
        "points",
        [{"name": f"Point {i}", "lat": float(a), "lon": float(b)} for i, (a, b) in enumerate(zip(instance.lat, instance.lon))],
    )
    unit = unit or ("s" if instance.cost_unit == "s" else instance.cost_unit)
    total = sum(instance.tour_cost(r) for r in routes if r)

    payload = {
        "title": title or instance.name,
        "points": points,
        "routes": [
            {"stops": r, "label": f"Véhicule {i + 1}", "cost": f"{instance.tour_cost(r):.0f} {unit}"}
            for i, r in enumerate(routes)
        ],
        "colors": PALETTE,
        "total": f"{total:.0f} {unit}",
    }

    html = TEMPLATE.replace("__TITLE__", title or instance.name).replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out
