"""Modèle d'instance pour un problème de tournées (TSP / CVRP).

Une instance est décrite par des coordonnées géographiques réelles (WGS84) et,
si on le souhaite, une matrice de temps de trajet issue d'un graphe routier.
Le module ne dépend que de numpy : il tourne partout, y compris sans accès réseau.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

EARTH_RADIUS_KM = 6371.0088


def haversine_matrix(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """Matrice de distances orthodromiques (km) entre tous les points.

    Ce n'est pas une distance routière : c'est une borne inférieure, utile
    comme repli quand aucun graphe routier n'est disponible. Les solveurs
    travaillent indifféremment sur cette matrice ou sur une matrice de temps.
    """
    lat_r = np.radians(lat)
    lon_r = np.radians(lon)
    dlat = lat_r[:, None] - lat_r[None, :]
    dlon = lon_r[:, None] - lon_r[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(lat_r)[:, None] * np.cos(lat_r)[None, :] * np.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


@dataclass
class Instance:
    """Jeu de points à visiter, avec dépôt optionnel et demandes optionnelles.

    Attributes:
        name: identifiant lisible de l'instance.
        lat: latitudes (degré décimal), forme (n,).
        lon: longitudes (degré décimal), forme (n,).
        demand: demande de chaque point (CVRP). Le premier point est le dépôt.
        capacity: capacité d'un véhicule (CVRP).
        matrix: matrice de coût (n, n). Si absente, calculée par haversine.
        cost_unit: unité de la matrice, pour l'affichage.
        source: provenance des données, conservée pour la traçabilité.
    """

    name: str
    lat: np.ndarray
    lon: np.ndarray
    demand: np.ndarray | None = None
    capacity: float | None = None
    tw: np.ndarray | None = None
    service: np.ndarray | None = None
    matrix: np.ndarray | None = None
    cost_unit: str = "km"
    source: str = ""
    meta: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.lat = np.asarray(self.lat, dtype=float)
        self.lon = np.asarray(self.lon, dtype=float)
        if self.lat.shape != self.lon.shape:
            raise ValueError("lat et lon doivent avoir la même forme")
        if self.lat.ndim != 1:
            raise ValueError("lat et lon doivent être des vecteurs 1D")
        if self.matrix is None:
            self.matrix = haversine_matrix(self.lat, self.lon)
        else:
            self.matrix = np.asarray(self.matrix, dtype=float)
            if self.matrix.shape != (len(self.lat), len(self.lat)):
                raise ValueError("matrice de taille incompatible avec les points")
        np.fill_diagonal(self.matrix, 0.0)
        if self.tw is not None:
            self.tw = np.asarray(self.tw, dtype=float)
            if self.tw.shape != (self.n, 2):
                raise ValueError("tw doit être de forme (n, 2)")
        if self.service is not None:
            self.service = np.asarray(self.service, dtype=float)
            if self.service.shape != (self.n,):
                raise ValueError("service doit être de forme (n,)")

    @property
    def has_time_windows(self) -> bool:
        return self.tw is not None


    @property
    def n(self) -> int:
        return len(self.lat)

    @property
    def is_cvrp(self) -> bool:
        return self.demand is not None and self.capacity is not None

    def tour_cost(self, tour: list[int], closed: bool = True) -> float:
        """Coût d'une tournée. `closed=True` ajoute le retour au dépôt."""
        if not tour:
            return 0.0
        total = float(self.matrix[tour[-1], tour[0]]) if closed else 0.0
        for a, b in zip(tour, tour[1:]):
            total += float(self.matrix[a, b])
        return total

    def routes_cost(self, routes: list[list[int]]) -> float:
        """Coût total d'une solution multi-tours (CVRP), dépôt = point 0."""
        return sum(self.tour_cost(r) for r in routes if r)

    @classmethod
    def random(cls, n: int = 15, seed: int = 42, name: str = "random") -> "Instance":
        """Instance aléatoire, conservée pour reproduire l'ancien notebook."""
        rng = np.random.default_rng(seed)
        lat = rng.uniform(5.30, 5.42, n)
        lon = rng.uniform(-4.08, -3.95, n)
        return cls(name=name, lat=lat, lon=lon, source="aléatoire (seed=%d)" % seed)

    @classmethod
    def random_cvrp(cls, n: int = 30, seed: int = 42, capacity: float = 20.0, name: str = "random_cvrp") -> "Instance":
        """Instance CVRP synthétique : demande entière 1..5 par client."""
        rng = np.random.default_rng(seed)
        lat = rng.uniform(5.28, 5.40, n)
        lon = rng.uniform(-4.08, -3.94, n)
        demand = np.concatenate([[0.0], rng.integers(1, 6, n - 1).astype(float)])
        return cls(name=name, lat=lat, lon=lon, demand=demand, capacity=capacity,
                   source="synthétique (seed=%d)" % seed)

    @classmethod
    def random_vrptw(cls, n: int = 25, seed: int = 0, capacity: float = 20.0,
                     horizon: float = 3600.0, width: float = 1200.0) -> "Instance":
        """Instance VRPTW synthétique : fenêtre de temps de largeur fixe par client."""
        rng = np.random.default_rng(seed)
        lat = rng.uniform(5.28, 5.40, n)
        lon = rng.uniform(-4.08, -3.94, n)
        demand = np.concatenate([[0.0], rng.integers(1, 5, n - 1).astype(float)])
        start = rng.uniform(0, max(1.0, horizon - width), n)
        start[0] = 0.0
        tw = np.column_stack([start, np.minimum(start + width, horizon)])
        service = np.concatenate([[0.0], rng.integers(60, 300, n - 1).astype(float)])
        # 120 s/km : vitesse urbaine moyenne de 30 km/h, pour des horaires cohérents
        travel = np.round(haversine_matrix(lat, lon) * 120.0, 1)
        return cls(
            name=f"vrptw_{n}",
            lat=lat,
            lon=lon,
            demand=demand,
            capacity=capacity,
            matrix=travel,
            tw=tw,
            service=service,
            cost_unit="s",
            source="synthétique VRPTW (seed=%d)" % seed,
        )
