"""Chargement et sauvegarde d'instances au format JSON.

Format volontairement simple et lisible, pour que les données puissent être
versionnées dans le dépôt et relues sans dépendre d'OSRM à l'exécution.

Exemple de fichier :
    {
      "name": "abidjan_communes_12",
      "cost_unit": "s",
      "source": "OSRM public, 2026-11-19",
      "points": [{"name": "Plateau", "lat": 5.3247, "lon": -4.0197}, ...],
      "durations": [[0, 524.7, ...], ...],
      "distances": [[0, 6754.3, ...], ...]
    }
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ..instance import Instance


def load_instance(path: str | Path) -> Instance:
    """Charge une instance depuis un fichier JSON versionné."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    points = data["points"]
    lat = np.array([p["lat"] for p in points], dtype=float)
    lon = np.array([p["lon"] for p in points], dtype=float)

    matrix = data.get("durations") or data.get("matrix")
    if matrix is None:
        raise ValueError(f"{path}: ni 'durations' ni 'matrix' dans le fichier")

    instance = Instance(
        name=data.get("name", Path(path).stem),
        lat=lat,
        lon=lon,
        matrix=np.array(matrix, dtype=float),
        cost_unit=data.get("cost_unit", "s"),
        source=data.get("source", ""),
        meta={"points": points, "distances": data.get("distances")},
    )
    return instance


def save_instance(instance: Instance, path: str | Path, durations: bool = True) -> None:
    """Écrit une instance au format JSON (matrice de durée par défaut)."""
    payload = {
        "name": instance.name,
        "cost_unit": instance.cost_unit,
        "source": instance.source,
        "points": instance.meta.get(
            "points",
            [{"name": f"p{i}", "lat": float(a), "lon": float(b)} for i, (a, b) in enumerate(zip(instance.lat, instance.lon))],
        ),
        "durations": np.round(instance.matrix, 1).tolist(),
    }
    if instance.meta.get("distances") is not None:
        payload["distances"] = instance.meta["distances"]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
