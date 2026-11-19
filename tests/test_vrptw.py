"""Tests VRPTW : horaires, insertion, ALNS."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from vrp.instance import Instance
from vrp.solvers.vrptw import alns_tw, is_feasible_tw, route_schedule, solomon_insertion, summary


def test_schedule_detects_late_arrival():
    """Une fenetre fermee avant l'arrivee doit rendre la tournee infaisable."""
    inst = Instance.random_vrptw(n=4, seed=1, width=60)
    inst.tw[2] = [0.0, 1.0]  # ferme presque immediatement
    ok, _, _ = route_schedule(inst, [2])
    assert not ok, "une arrivee apres fermeture doit etre detectee"
    print("OK  retard detecte")


def test_insertion_feasible():
    inst = Instance.random_vrptw(n=20, seed=3, width=2400)
    routes = solomon_insertion(inst)
    assert is_feasible_tw(inst, routes), "l'insertion doit produire une solution faisable"
    s = summary(inst, routes)
    print(f"OK  insertion faisable : {s['vehicles']} vehicules, trajet {s['travel']} s, attente {s['wait_total']} s")


def test_alns_improves_or_equals():
    inst = Instance.random_vrptw(n=20, seed=5, width=2400)
    base = solomon_insertion(inst)
    best = alns_tw(inst, start=base, iterations=60, seed=1)
    assert is_feasible_tw(inst, best), "ALNS doit rester faisable"
    c_base = sum(inst.tour_cost(r) for r in base)
    c_best = sum(inst.tour_cost(r) for r in best)
    assert c_best <= c_base + 1e-6, f"ALNS degrade : {c_base:.1f} -> {c_best:.1f}"
    print(f"OK  ALNS VRPTW : {c_base:.1f} -> {c_best:.1f}")


if __name__ == "__main__":
    test_schedule_detects_late_arrival()
    test_insertion_feasible()
    test_alns_improves_or_equals()
    print("Tests VRPTW: OK")
