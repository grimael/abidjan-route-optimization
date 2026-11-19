"""Tests du noyau algorithmique (exécutables sans pytest : python tests/test_solvers.py)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import numpy as np
from vrp.instance import Instance
from vrp.solvers.exact import brute_force, held_karp
from vrp.solvers.heuristics import nearest_neighbor, two_opt, local_search, tour_cost
from vrp.solvers.ga import genetic_algorithm, ordered_crossover


def test_exact_matches_brute_force():
    for seed in (1, 2, 3):
        inst = Instance.random(n=8, seed=seed)
        c1, _ = brute_force(inst)
        c2, _ = held_karp(inst)
        assert abs(c1 - c2) < 1e-6, f"seed {seed}: {c1} != {c2}"
    print("OK  held_karp == brute_force (3 instances)")


def test_tour_cost_consistency():
    inst = Instance.random(n=6, seed=7)
    tour = [0, 2, 3, 1, 4, 5]
    manual = sum(inst.matrix[a, b] for a, b in zip(tour, tour[1:] + tour[:1]))
    assert abs(tour_cost(inst.matrix, tour) - manual) < 1e-9
    print("OK  tour_cost coherent")


def test_two_opt_never_worse():
    inst = Instance.random(n=40, seed=11)
    nn = nearest_neighbor(inst.matrix)
    improved = two_opt(inst.matrix, nn)
    assert tour_cost(inst.matrix, improved) <= tour_cost(inst.matrix, nn) + 1e-9
    print(f"OK  2-opt ameliore : {tour_cost(inst.matrix, nn):.2f} -> {tour_cost(inst.matrix, improved):.2f}")


def test_local_search_beats_nearest_neighbor():
    inst = Instance.random(n=60, seed=5)
    nn = nearest_neighbor(inst.matrix)
    ls = local_search(inst.matrix, nn)
    assert tour_cost(inst.matrix, ls) < tour_cost(inst.matrix, nn)
    print(f"OK  recherche locale : {tour_cost(inst.matrix, nn):.2f} -> {tour_cost(inst.matrix, ls):.2f}")


def test_crossover_is_permutation():
    import random
    rng = random.Random(0)
    p1 = list(range(12)); rng.shuffle(p1)
    p2 = list(range(12)); rng.shuffle(p2)
    child = ordered_crossover(p1, p2, rng)
    assert sorted(child) == list(range(12)), "OX doit produire une permutation"
    print("OK  OX produit une permutation valide")


def test_ga_close_to_optimum():
    inst = Instance.random(n=10, seed=3)
    opt, _ = held_karp(inst)
    cost, tour, _ = genetic_algorithm(inst, pop_size=60, generations=120, seed=3)
    gap = (cost - opt) / opt
    assert gap < 0.05, f"AG trop loin de l'optimum : gap {gap:.1%}"
    print(f"OK  AG a moins de 5% de l'optimum (gap {gap:.2%})")


if __name__ == "__main__":
    test_tour_cost_consistency()
    test_exact_matches_brute_force()
    test_crossover_is_permutation()
    test_two_opt_never_worse()
    test_local_search_beats_nearest_neighbor()
    test_ga_close_to_optimum()
    print("\nTous les tests passent.")
