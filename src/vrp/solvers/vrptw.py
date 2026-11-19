"""VRPTW : tournées avec capacité ET fenêtres de temps.

Chaque client doit être servi dans un intervalle [ouverture, fermeture]. Le
véhicule peut arriver avant l'ouverture et attendre ; il ne peut pas arriver
après la fermeture. Le coût reste la durée de trajet — l'attente n'est pas
facturée, mais elle est mesurée et affichée.

Méthode : insertion gloutonne (à la Solomon, simplifiée) puis ALNS avec
destruction/réparation, chaque insertion étant validée par le calcul des
horaires réels.
"""

from __future__ import annotations

import math
import random

import numpy as np

from ..instance import Instance


# --------------------------------------------------------------------------- #
# Horaires
# --------------------------------------------------------------------------- #
def route_schedule(instance: Instance, route: list[int], start_time: float = 0.0) -> tuple[bool, float, float]:
    """Simule une tournée. Renvoie (faisable, heure de retour, attente totale)."""
    if not instance.has_time_windows:
        raise ValueError("instance sans fenêtres de temps")
    t = start_time
    wait = 0.0
    prev = 0
    for c in route:
        t += float(instance.matrix[prev, c])
        open_, close = instance.tw[c]
        if t < open_:
            wait += open_ - t
            t = open_
        if t > close + 1e-9:
            return False, math.inf, math.inf
        t += float(instance.service[c])
        prev = c
    t += float(instance.matrix[prev, 0])
    return True, t, wait


def is_feasible_tw(instance: Instance, routes: list[list[int]]) -> bool:
    seen: set[int] = set()
    for r in routes:
        if not r:
            continue
        if sum(instance.demand[i] for i in r) > instance.capacity + 1e-9:
            return False
        ok, _, _ = route_schedule(instance, r)
        if not ok:
            return False
        for c in r:
            if c in seen or c == 0:
                return False
            seen.add(c)
    return len(seen) == instance.n - 1


# --------------------------------------------------------------------------- #
# Insertion
# --------------------------------------------------------------------------- #
def _best_insertion(instance: Instance, routes: list[list[int]], customer: int) -> tuple[int, int, float] | None:
    """Meilleure position faisable pour `customer` : (index de tournée, position, coût)."""
    d = instance.matrix
    best: tuple[int, int, float] | None = None
    for ri, route in enumerate(routes):
        if sum(instance.demand[i] for i in route) + instance.demand[customer] > instance.capacity + 1e-9:
            continue
        for pos in range(len(route) + 1):
            a = 0 if pos == 0 else route[pos - 1]
            b = 0 if pos == len(route) else route[pos]
            cost = float(d[a, customer] + d[customer, b] - d[a, b])
            candidate = route[:pos] + [customer] + route[pos:]
            ok, _, _ = route_schedule(instance, candidate)
            if not ok:
                continue
            if best is None or cost < best[2]:
                best = (ri, pos, cost)
    return best


def solomon_insertion(instance: Instance, seed_customer: int | None = None) -> list[list[int]]:
    """Construction par insertion successive, en respectant capacité et horaires.

    Les clients les plus contraints (fermeture la plus précoce) sont insérés
    d'abord : c'est la règle qui évite de se peindre dans un coin.
    """
    n = instance.n
    customers = sorted(range(1, n), key=lambda c: instance.tw[c][1])
    routes: list[list[int]] = []

    if seed_customer is None:
        seed_customer = customers[0]
    routes.append([seed_customer])
    if not route_schedule(instance, routes[0])[0]:
        routes[0] = [seed_customer]

    for c in customers:
        if any(c in r for r in routes):
            continue
        best = _best_insertion(instance, routes, c)
        if best is None:
            routes.append([c])
        else:
            ri, pos, _ = best
            routes[ri].insert(pos, c)
    return [r for r in routes if r]


# --------------------------------------------------------------------------- #
# ALNS avec fenêtres de temps
# --------------------------------------------------------------------------- #
def alns_tw(
    instance: Instance,
    start: list[list[int]] | None = None,
    iterations: int = 300,
    removal_fraction: float = 0.2,
    seed: int = 0,
    cooling: float = 0.995,
) -> list[list[int]]:
    """ALNS adapté au VRPTW : toute réinsertion est validée par les horaires."""
    rng = random.Random(seed)
    current = [r[:] for r in (start or solomon_insertion(instance))]
    if not is_feasible_tw(instance, current):
        current = [[c] for c in range(1, instance.n)]

    def cost(routes: list[list[int]]) -> float:
        return sum(instance.tour_cost(r) for r in routes if r)

    best = [r[:] for r in current]
    best_cost = current_cost = cost(current)
    temperature = 0.05 * max(best_cost, 1.0)
    customers = list(range(1, instance.n))

    for _ in range(iterations):
        candidate = [r[:] for r in current]
        k = max(1, int(removal_fraction * len(customers)))
        removed = rng.sample(customers, k)
        for c in removed:
            for r in candidate:
                if c in r:
                    r.remove(c)
        candidate = [r for r in candidate if r]

        rng.shuffle(removed)
        for c in removed:
            best_ins = _best_insertion(instance, candidate, c)
            if best_ins is None:
                candidate.append([c])
            else:
                ri, pos, _ = best_ins
                candidate[ri].insert(pos, c)

        cand_cost = cost(candidate)
        if cand_cost < current_cost - 1e-9 or rng.random() < math.exp(-(cand_cost - current_cost) / max(temperature, 1e-9)):
            current, current_cost = candidate, cand_cost
            if cand_cost < best_cost - 1e-9:
                best, best_cost = [r[:] for r in candidate], cand_cost
        temperature *= cooling

    return best


def summary(instance: Instance, routes: list[list[int]]) -> dict:
    """Indicateurs de synthèse d'une solution VRPTW."""
    total_travel = sum(instance.tour_cost(r) for r in routes if r)
    waits, returns = [], []
    for r in routes:
        ok, ret, wait = route_schedule(instance, r)
        returns.append(ret if ok else math.inf)
        waits.append(wait if ok else math.inf)
    return {
        "vehicles": len([r for r in routes if r]),
        "travel": round(total_travel, 1),
        "wait_total": round(float(np.sum(waits)), 1),
        "makespan": round(float(np.max(returns)), 1),
        "feasible": is_feasible_tw(instance, routes),
    }
