"""Algorithme génétique pour le TSP, avec recherche locale optionnelle.

Améliorations par rapport à la version d'origine du projet :
  - croisement OX (Ordered Crossover) conservant l'ordre relatif,
  - mutation par inversion de segment, plus efficace que le swap simple,
  - élitisme explicite (les k meilleurs survivent),
  - recherche locale appliquée périodiquement au meilleur individu (version
    mémétique), qui transforme un AG scolaire en solveur compétitif,
  - graine aléatoire explicite et historique de convergence renvoyé.
"""

from __future__ import annotations

import random

import numpy as np

from ..instance import Instance
from .heuristics import local_search, nearest_neighbor, tour_cost


def ordered_crossover(parent1: list[int], parent2: list[int], rng: random.Random) -> list[int]:
    """OX : copie un segment du parent 1, remplit le reste dans l'ordre du parent 2."""
    n = len(parent1)
    a, b = sorted(rng.sample(range(n), 2))
    child: list[int | None] = [None] * n
    child[a:b] = parent1[a:b]
    fill = [city for city in parent2 if city not in child]
    idx = 0
    for i in range(n):
        if child[i] is None:
            child[i] = fill[idx]
            idx += 1
    return [int(c) for c in child]


def invert_mutation(tour: list[int], rng: random.Random) -> list[int]:
    n = len(tour)
    i, j = sorted(rng.sample(range(n), 2))
    return tour[:i] + list(reversed(tour[i : j + 1])) + tour[j + 1 :]


def tournament(population: list[list[int]], costs: list[float], k: int, rng: random.Random) -> list[int]:
    contenders = rng.sample(range(len(population)), k)
    best = min(contenders, key=lambda i: costs[i])
    return population[best]


def genetic_algorithm(
    instance: Instance,
    pop_size: int = 120,
    generations: int = 400,
    mutation_rate: float = 0.25,
    elite: int = 4,
    tournament_k: int = 3,
    local_search_every: int = 25,
    seed: int = 42,
) -> tuple[float, list[int], list[float]]:
    """Renvoie (meilleur coût, meilleure tournée, historique du meilleur coût)."""
    rng = random.Random(seed)
    matrix = instance.matrix
    n = instance.n

    population = [nearest_neighbor(matrix)]
    while len(population) < pop_size:
        tour = list(range(n))
        rng.shuffle(tour)
        population.append(tour)
    costs = [tour_cost(matrix, t) for t in population]

    history: list[float] = []
    for gen in range(generations):
        order = sorted(range(pop_size), key=lambda i: costs[i])
        new_pop = [population[i][:] for i in order[:elite]]
        new_costs = [costs[i] for i in order[:elite]]

        while len(new_pop) < pop_size:
            p1 = tournament(population, costs, tournament_k, rng)
            p2 = tournament(population, costs, tournament_k, rng)
            child = ordered_crossover(p1, p2, rng)
            if rng.random() < mutation_rate:
                child = invert_mutation(child, rng)
            new_pop.append(child)
            new_costs.append(tour_cost(matrix, child))

        # version mémétique : on polit le meilleur individu régulièrement
        if local_search_every and gen % local_search_every == 0:
            best_i = int(np.argmin(new_costs))
            polished = local_search(matrix, new_pop[best_i])
            polished_cost = tour_cost(matrix, polished)
            if polished_cost < new_costs[best_i]:
                new_pop[best_i] = polished
                new_costs[best_i] = polished_cost

        population, costs = new_pop, new_costs
        history.append(min(costs))

    best_i = int(np.argmin(costs))
    return costs[best_i], population[best_i], history
