"""CVRP : tournées avec capacité, construction et amélioration.

Le problème : un dépôt (point 0), des clients avec une demande, des véhicules
de capacité identique. On cherche à minimiser la distance totale en respectant
la capacité de chaque véhicule.

Trois briques, dans l'ordre historique :
  1. Clarke-Wright (1964) — construction par économies, encore une référence ;
  2. recherche locale inter-tournées (relocate, swap, 2-opt intra) ;
  3. ALNS — destruction/réparation, état de l'art des métaheuristiques.
"""

from __future__ import annotations

import math
import random

import numpy as np

from ..instance import Instance


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #
def route_load(instance: Instance, route: list[int]) -> float:
    return float(sum(instance.demand[i] for i in route))


def routes_cost(instance: Instance, routes: list[list[int]]) -> float:
    return sum(instance.tour_cost(r) for r in routes if r)


def is_feasible(instance: Instance, routes: list[list[int]]) -> bool:
    seen: set[int] = set()
    for r in routes:
        if not r:
            continue
        if route_load(instance, r) > instance.capacity + 1e-9:
            return False
        for c in r:
            if c in seen or c == 0:
                return False
            seen.add(c)
    return len(seen) == instance.n - 1


# --------------------------------------------------------------------------- #
# 1. Clarke-Wright
# --------------------------------------------------------------------------- #
def clarke_wright(instance: Instance) -> list[list[int]]:
    """Économies : fusionne deux tournées si le gain dépasse le coût de liaison."""
    n, cap, d = instance.n, instance.capacity, instance.matrix
    routes: dict[int, list[int]] = {i: [i] for i in range(1, n)}
    loads = {i: float(instance.demand[i]) for i in range(1, n)}

    savings = []
    for i in range(1, n):
        for j in range(i + 1, n):
            s = d[0, i] + d[0, j] - d[i, j]
            if s > 0:
                savings.append((s, i, j))
    savings.sort(reverse=True)

    def find(customer: int) -> int | None:
        for key, r in routes.items():
            if customer in r:
                return key
        return None

    for _, i, j in savings:
        ri, rj = find(i), find(j)
        if ri is None or rj is None or ri == rj:
            continue
        if loads[ri] + loads[rj] > cap + 1e-9:
            continue
        # on ne fusionne qu'en extrémité
        if i == routes[ri][-1] and j == routes[rj][0]:
            merged = routes[ri] + routes[rj]
        elif j == routes[rj][-1] and i == routes[ri][0]:
            merged = routes[rj] + routes[ri]
        elif i == routes[ri][0] and j == routes[rj][0]:
            merged = list(reversed(routes[ri])) + routes[rj]
        elif i == routes[ri][-1] and j == routes[rj][-1]:
            merged = routes[ri] + list(reversed(routes[rj]))
        else:
            continue
        routes[ri] = merged
        loads[ri] += loads[rj]
        del routes[rj]
        loads.pop(rj)
    return [r for r in routes.values() if r]


# --------------------------------------------------------------------------- #
# 2. Recherche locale
# --------------------------------------------------------------------------- #
def two_opt_route(instance: Instance, route: list[int]) -> list[int]:
    """2-opt à l'intérieur d'une tournée, avec le dépôt aux deux bouts."""
    if len(route) < 3:
        return route[:]
    d = instance.matrix
    best = route[:]
    improved = True
    while improved:
        improved = False
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                a = 0 if i == 0 else best[i - 1]
                b, c = best[i], best[j]
                e = 0 if j == len(best) - 1 else best[j + 1]
                delta = d[a, c] + d[b, e] - d[a, b] - d[c, e]
                if delta < -1e-9:
                    best[i : j + 1] = reversed(best[i : j + 1])
                    improved = True
    return best


def improve(instance: Instance, routes: list[list[int]], max_rounds: int = 200) -> list[list[int]]:
    """Descente : 2-opt intra, puis déplacement de client entre tournées."""
    d = instance.matrix
    cap = instance.capacity
    best = [r[:] for r in routes]
    rounds = 0
    improved = True
    while improved and rounds < max_rounds:
        improved = False
        rounds += 1
        best = [two_opt_route(instance, r) for r in best]

        # relocate : déplacer un client vers une autre tournée
        for i, ri in enumerate(best):
            for pos_i, c in enumerate(ri):
                if c == 0:
                    continue
                for j, rj in enumerate(best):
                    if i == j:
                        continue
                    if route_load(instance, rj) + instance.demand[c] > cap + 1e-9:
                        continue
                    base = d[0, c] + d[c, 0]
                    if pos_i > 0:
                        base += d[ri[pos_i - 1], c]
                    if pos_i < len(ri) - 1:
                        base += d[c, ri[pos_i + 1]]
                    if pos_i > 0 and pos_i < len(ri) - 1:
                        base -= d[ri[pos_i - 1], ri[pos_i + 1]]

                    for pos_j in range(len(rj) + 1):
                        a = 0 if pos_j == 0 else rj[pos_j - 1]
                        b = 0 if pos_j == len(rj) else rj[pos_j]
                        cand = d[a, c] + d[c, b] - d[a, b]
                        if cand < base - 1e-9:
                            new_ri = ri[:pos_i] + ri[pos_i + 1 :]
                            new_rj = rj[:pos_j] + [c] + rj[pos_j:]
                            old = routes_cost(instance, [ri, rj])
                            new = routes_cost(instance, [new_ri, new_rj])
                            if new < old - 1e-9:
                                best[i], best[j] = new_ri, new_rj
                                improved = True
                                break
                    if improved:
                        break
                if improved:
                    break
            if improved:
                break
        best = [r for r in best if r]
    return best


# --------------------------------------------------------------------------- #
# 3. ALNS
# --------------------------------------------------------------------------- #
def _greedy_insert(instance: Instance, routes: list[list[int]], customer: int) -> None:
    """Insère le client à la position la moins coûteuse, en respectant la capacité."""
    d = instance.matrix
    best_delta, best_route, best_pos = math.inf, None, 0
    for r in routes:
        if route_load(instance, r) + instance.demand[customer] > instance.capacity + 1e-9:
            continue
        for pos in range(len(r) + 1):
            a = 0 if pos == 0 else r[pos - 1]
            b = 0 if pos == len(r) else r[pos]
            delta = d[a, customer] + d[customer, b] - d[a, b]
            if delta < best_delta:
                best_delta, best_route, best_pos = delta, r, pos
    if best_route is None:
        routes.append([customer])  # nouvelle tournée
    else:
        best_route.insert(best_pos, customer)


def alns(
    instance: Instance,
    start: list[list[int]] | None = None,
    iterations: int = 400,
    removal_fraction: float = 0.25,
    seed: int = 0,
    cooling: float = 0.995,
) -> list[list[int]]:
    """Adaptive Large Neighbourhood Search, recuit simulé comme acceptation.

    Cycle : détruire une fraction des clients (retrait aléatoire ou « pire »
    client), réinsérer gloutonnement, accepter si amélioration ou selon la
    température. Simple, mais redoutablement efficace sur le CVRP.
    """
    rng = random.Random(seed)
    d = instance.matrix
    current = improve(instance, start or clarke_wright(instance))
    best = [r[:] for r in current]
    best_cost = routes_cost(instance, best)
    current_cost = best_cost
    temperature = 0.05 * best_cost

    customers = list(range(1, instance.n))
    for _ in range(iterations):
        candidate = [r[:] for r in current]
        k = max(1, int(removal_fraction * len(customers)))
        mode = rng.random()

        if mode < 0.5:
            removed = rng.sample(customers, k)
        else:  # retrait des clients au plus fort gain de suppression
            gains = []
            for r in candidate:
                for idx, c in enumerate(r):
                    a = 0 if idx == 0 else r[idx - 1]
                    b = 0 if idx == len(r) - 1 else r[idx + 1]
                    gains.append((d[a, c] + d[c, b] - d[a, b], c))
            gains.sort(reverse=True)
            removed = [c for _, c in gains[:k]]

        for c in removed:
            for r in candidate:
                if c in r:
                    r.remove(c)
        candidate = [r for r in candidate if r]

        rng.shuffle(removed)
        for c in removed:
            _greedy_insert(instance, candidate, c)

        candidate = improve(instance, candidate)
        cost = routes_cost(instance, candidate)

        if cost < current_cost - 1e-9 or rng.random() < math.exp(-(cost - current_cost) / max(temperature, 1e-9)):
            current, current_cost = candidate, cost
            if cost < best_cost - 1e-9:
                best, best_cost = [r[:] for r in candidate], cost
        temperature *= cooling

    return best
