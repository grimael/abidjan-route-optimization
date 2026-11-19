"""Heuristiques constructives et de recherche locale.

Toutes les fonctions opèrent sur une matrice de coût symétrique et une tournée
représentée par une liste de points (le dépôt est le point 0, non répété).
"""

from __future__ import annotations

import numpy as np


def nearest_neighbor(matrix: np.ndarray, start: int = 0) -> list[int]:
    """Construction gloutonne : toujours le point non visité le plus proche."""
    n = matrix.shape[0]
    unvisited = set(range(n)) - {start}
    tour = [start]
    current = start
    while unvisited:
        nxt = min(unvisited, key=lambda v: matrix[current, v])
        tour.append(nxt)
        unvisited.remove(nxt)
        current = nxt
    return tour


def tour_cost(matrix: np.ndarray, tour: list[int]) -> float:
    total = float(matrix[tour[-1], tour[0]])
    for a, b in zip(tour, tour[1:]):
        total += float(matrix[a, b])
    return total


def two_opt(matrix: np.ndarray, tour: list[int], max_passes: int = 50) -> list[int]:
    """2-opt : inverse un segment dès que cela raccourcit la tournée.

    Implémentation first-improvement, qui converge plus vite que best-improvement
    sur les instances de taille moyenne.
    """
    n = len(tour)
    if n < 4:
        return tour[:]
    improved = True
    passes = 0
    best = tour[:]
    while improved and passes < max_passes:
        improved = False
        passes += 1
        for i in range(n - 2):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue  # inversion du cycle complet : sans effet
                a, b = best[i], best[i + 1]
                c, d = best[j], best[(j + 1) % n]
                delta = matrix[a, c] + matrix[b, d] - matrix[a, b] - matrix[c, d]
                if delta < -1e-12:
                    best[i + 1 : j + 1] = reversed(best[i + 1 : j + 1])
                    improved = True
    return best


def or_opt(matrix: np.ndarray, tour: list[int], max_segment: int = 3) -> list[int]:
    """Or-opt : déplace un segment de 1 à 3 points ailleurs s'il y gagne."""
    n = len(tour)
    if n < 4:
        return tour[:]
    best = tour[:]
    improved = True
    while improved:
        improved = False
        for seg in range(1, max_segment + 1):
            for i in range(n):
                if i + seg > n:
                    continue
                segment = best[i : i + seg]
                rest = best[:i] + best[i + seg :]
                if len(rest) < 2:
                    continue
                base = _cost_of(matrix, best, closed=True)
                for pos in range(len(rest) + 1):
                    if pos == i:
                        continue
                    cand = rest[:pos] + segment + rest[pos:]
                    if _cost_of(matrix, cand, closed=True) < base - 1e-12:
                        best = cand
                        improved = True
                        break
                if improved:
                    break
            if improved:
                break
    return best


def _cost_of(matrix: np.ndarray, tour: list[int], closed: bool = True) -> float:
    if not tour:
        return 0.0
    total = float(matrix[tour[-1], tour[0]]) if closed else 0.0
    for a, b in zip(tour, tour[1:]):
        total += float(matrix[a, b])
    return total


def local_search(matrix: np.ndarray, tour: list[int]) -> list[int]:
    """Alternance 2-opt / Or-opt jusqu'à stabilité (descente de voisinage)."""
    current = tour[:]
    while True:
        before = _cost_of(matrix, current)
        current = two_opt(matrix, current)
        current = or_opt(matrix, current)
        if _cost_of(matrix, current) >= before - 1e-9:
            return current
