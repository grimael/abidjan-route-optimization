"""Tests du CVRP : faisabilité, amélioration, ALNS."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from vrp.instance import Instance
from vrp.solvers.cvrp import alns, clarke_wright, improve, is_feasible, route_load, routes_cost


def test_savings_feasible():
    inst = Instance.random_cvrp(n=40, seed=3, capacity=18)
    routes = clarke_wright(inst)
    assert is_feasible(inst, routes), "Clarke-Wright doit respecter la capacite"
    for r in routes:
        assert route_load(inst, r) <= inst.capacity + 1e-9
    print(f"OK  Clarke-Wright faisable : {len(routes)} tournees, cout {routes_cost(inst, routes):.1f}")


def test_improve_not_worse():
    inst = Instance.random_cvrp(n=40, seed=5, capacity=18)
    base = clarke_wright(inst)
    improved = improve(inst, base)
    assert is_feasible(inst, improved), "la recherche locale doit preserver la faisabilite"
    assert routes_cost(inst, improved) <= routes_cost(inst, base) + 1e-6
    print(f"OK  amelioration : {routes_cost(inst, base):.1f} -> {routes_cost(inst, improved):.1f}")


def test_alns_beats_or_equals_savings():
    inst = Instance.random_cvrp(n=50, seed=9, capacity=20)
    base = clarke_wright(inst)
    best = alns(inst, start=base, iterations=150, seed=1)
    assert is_feasible(inst, best), "ALNS doit rendre une solution faisable"
    ratio = routes_cost(inst, best) / routes_cost(inst, base)
    assert ratio <= 1.0 + 1e-6, f"ALNS moins bon que Clarke-Wright : ratio {ratio:.3f}"
    print(f"OK  ALNS : {routes_cost(inst, base):.1f} -> {routes_cost(inst, best):.1f} ({ratio:.1%})")


if __name__ == "__main__":
    test_savings_feasible()
    test_improve_not_worse()
    test_alns_beats_or_equals_savings()
    print("Tests CVRP: OK")
