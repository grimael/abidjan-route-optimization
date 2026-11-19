"""Solveurs exacts : force brute et programmation dynamique de Held-Karp.

Servent de référence : c'est seulement en connaissant l'optimum qu'on peut
dire qu'une métaheuristique est bonne. Réservés aux petites instances.
"""

from __future__ import annotations

from itertools import permutations

import numpy as np

from ..instance import Instance


def brute_force(instance: Instance, max_n: int = 9) -> tuple[float, list[int]]:
    """Énumère toutes les tournées. Complexité (n-1)!/2 : n <= 9 seulement."""
    n = instance.n
    if n > max_n:
        raise ValueError(f"force brute limitée à {max_n} points, reçu {n}")
    if n <= 2:
        return instance.tour_cost(list(range(n))), list(range(n))

    best_cost = float("inf")
    best_tour: list[int] = []
    first, rest = 0, list(range(1, n))
    for perm in permutations(rest):
        tour = [first, *perm]
        cost = instance.tour_cost(tour)
        if cost < best_cost:
            best_cost, best_tour = cost, tour
    return best_cost, best_tour


def held_karp(instance: Instance, max_n: int = 16) -> tuple[float, list[int]]:
    """Programme dynamique exact pour le TSP symétrique (bitmask).

    Complexité O(2^n · n²) en temps, O(2^n · n) en mémoire. Au-delà de 16
    points, la mémoire explose : utiliser un solveur MIP (OR-Tools) à la place.
    """
    n = instance.n
    if n > max_n:
        raise ValueError(f"Held-Karp limité à {max_n} points, reçu {n}")
    if n <= 3:
        return instance.tour_cost(list(range(n))), list(range(n))

    dist = instance.matrix
    full = 1 << (n - 1)  # sous-ensembles des points 1..n-1
    inf = np.inf

    # dp[mask, j] = coût du plus court chemin partant de 0, visitant mask, finissant en j+1
    dp = np.full((full, n - 1), inf)
    parent = np.full((full, n - 1), -1, dtype=np.int16)

    for j in range(n - 1):
        dp[1 << j, j] = dist[0, j + 1]

    for mask in range(full):
        for j in range(n - 1):
            if not (mask & (1 << j)):
                continue
            curr = dp[mask, j]
            if curr == inf:
                continue
            for k in range(n - 1):
                if mask & (1 << k):
                    continue
                nxt = mask | (1 << k)
                cand = curr + dist[j + 1, k + 1]
                if cand < dp[nxt, k]:
                    dp[nxt, k] = cand
                    parent[nxt, k] = j

    last = np.argmin(dp[full - 1] + dist[1:, 0])
    best_cost = float(dp[full - 1, last] + dist[last + 1, 0])

    # reconstruction : on remonte les parents depuis le dernier point
    path: list[int] = []
    mask = full - 1
    j = int(last)
    while j != -1:
        path.append(j + 1)
        prev = int(parent[mask, j])
        mask ^= 1 << j
        j = prev
    path.reverse()
    tour = [0, *path]
    return best_cost, tour
