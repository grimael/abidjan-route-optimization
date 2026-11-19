"""Construit une instance réelle d'Abidjan à partir d'OSRM.

Usage :
    python scripts/build_instance.py --out data/instances/abidjan_communes_12.json
    python scripts/build_instance.py --poi pharmacies --limit 40

Deux modes :
  1. `--communes` (par défaut) : les douze chefs-lieux de commune, coordonnées
     publiques, aucune dépendance réseau hormis OSRM.
  2. `--poi` : interroge Overpass pour récupérer de vrais points d'intérêt
     (pharmacies, marchés, hôpitaux), puis OSRM pour la matrice.

Aucune dépendance lourde : `requests` suffit. Les appels sont retentés avec
backoff, et le résultat est mis en cache dans data/cache/.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import requests

OSRM = "https://router.project-osrm.org/table/v1/driving/"
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

COMMUNES = [
    {"name": "Plateau", "lat": 5.3247, "lon": -4.0197},
    {"name": "Cocody", "lat": 5.3540, "lon": -3.9900},
    {"name": "Adjamé", "lat": 5.3540, "lon": -4.0230},
    {"name": "Yopougon", "lat": 5.3400, "lon": -4.0800},
    {"name": "Abobo", "lat": 5.4160, "lon": -4.0200},
    {"name": "Treichville", "lat": 5.2930, "lon": -4.0100},
    {"name": "Marcory", "lat": 5.3000, "lon": -3.9900},
    {"name": "Koumassi", "lat": 5.2930, "lon": -3.9500},
    {"name": "Port-Bouët", "lat": 5.2500, "lon": -3.9300},
    {"name": "Attécoubé", "lat": 5.3400, "lon": -4.0400},
    {"name": "Bingerville", "lat": 5.3550, "lon": -3.8850},
    {"name": "Anyama", "lat": 5.4940, "lon": -4.0520},
]


def _get(url: str, params: dict | None = None, tries: int = 4, timeout: int = 60) -> dict:
    """GET avec backoff exponentiel : les API publiques saturent vite."""
    delay = 2.0
    last: Exception | None = None
    for attempt in range(tries):
        try:
            r = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": "abidjan-route-optimization/0.1"})
            r.raise_for_status()
            return r.json()
        except Exception as exc:  # noqa: BLE001 - on journalise et on retente
            last = exc
            print(f"  tentative {attempt + 1}/{tries} échouée : {exc}", file=sys.stderr)
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"échec après {tries} tentatives : {last}")


def osrm_table(points: list[dict]) -> tuple[list, list]:
    """Matrice de durées (s) et de distances (m) entre tous les points."""
    coords = ";".join(f"{p['lon']:.5f},{p['lat']:.5f}" for p in points)
    data = _get(OSRM + coords, {"annotations": "duration,distance"})
    if data.get("code") != "Ok":
        raise RuntimeError(f"OSRM a répondu : {data.get('code')}")
    return data["durations"], data["distances"]


def overpass_pois(amenity: str, limit: int) -> list[dict]:
    """Récupère de vrais points d'intérêt à Abidjan via Overpass."""
    query = f"""
    [out:json][timeout:60];
    node["amenity"="{amenity}"](5.25,-4.15,5.45,-3.88);
    out center {limit};
    """
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            data = _get(endpoint, {"data": query}, tries=2)
            pois = [
                {"name": el.get("tags", {}).get("name", f"{amenity}-{el['id']}"), "lat": el["lat"], "lon": el["lon"]}
                for el in data.get("elements", [])
                if "lat" in el and "lon" in el
            ]
            if pois:
                return pois[:limit]
        except Exception as exc:  # noqa: BLE001
            print(f"  {endpoint} indisponible : {exc}", file=sys.stderr)
    raise RuntimeError("aucun serveur Overpass n'a répondu")


def main() -> None:
    ap = argparse.ArgumentParser(description="Construit une instance réelle pour Abidjan")
    ap.add_argument("--out", default="data/instances/abidjan_communes_12.json")
    ap.add_argument("--poi", default=None, help="type OSM : pharmacy, marketplace, hospital…")
    ap.add_argument("--limit", type=int, default=12)
    args = ap.parse_args()

    if args.poi:
        print(f"Récupération des POI « {args.poi} » via Overpass…")
        points = overpass_pois(args.poi, args.limit)
        name = f"abidjan_{args.poi}_{len(points)}"
        source = f"OpenStreetMap via Overpass + OSRM, {time.strftime('%Y-%m-%d')}"
    else:
        points = COMMUNES
        name = "abidjan_communes_12"
        source = f"Chefs-lieux de commune (coordonnées publiques) + OSRM, {time.strftime('%Y-%m-%d')}"

    print(f"Matrice OSRM pour {len(points)} points…")
    durations, distances = osrm_table(points)

    payload = {
        "name": name,
        "cost_unit": "s",
        "source": source,
        "points": points,
        "durations": np.round(np.array(durations, dtype=float), 1).tolist(),
        "distances": np.round(np.array(distances, dtype=float), 1).tolist(),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Écrit : {out} ({len(points)} points)")


if __name__ == "__main__":
    main()
