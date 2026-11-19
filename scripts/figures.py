"""Génère les figures du projet dans docs/figures/.

Usage :
    python scripts/figures.py
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402

from vrp.data.load import load_instance  # noqa: E402
from vrp.instance import Instance  # noqa: E402
from vrp.solvers.cvrp import alns, clarke_wright, routes_cost  # noqa: E402
from vrp.solvers.exact import held_karp  # noqa: E402
from vrp.solvers.ga import genetic_algorithm  # noqa: E402
from vrp.solvers.heuristics import local_search, nearest_neighbor, tour_cost  # noqa: E402
from vrp.viz.figures import bars, convergence, route_map  # noqa: E402

OUT = pathlib.Path("docs/figures")  # valeur par défaut
UNIT = "s"


def main() -> None:
    ap = argparse.ArgumentParser(description="Génère les figures du projet")
    ap.add_argument("--instance", default="data/instances/abidjan_communes_12.json")
    ap.add_argument("--out", default="docs/figures")
    args = ap.parse_args()

    out = pathlib.Path(args.out)
    inst = load_instance(args.instance)
    print(f"instance : {inst.name} ({inst.n} points)")

    # 1. optimum exact et tournée optimale
    opt, opt_tour = held_karp(inst)
    p1 = route_map(
        inst, [opt_tour], out / "tournee_optimale.png",
        title="Tournée optimale sur le réseau OSRM d'Abidjan", unit=UNIT,
    )
    print(f"tournée optimale : {opt:.0f} s")

    # 2. convergence de l'AG sans recherche locale (montre la progression réelle)
    histories, finals = [], []
    for seed in range(5):
        cost_seed, _, hist_seed = genetic_algorithm(
            inst, pop_size=80, generations=250, mutation_rate=0.3, seed=seed, local_search_every=0
        )
        histories.append(hist_seed)
        finals.append(cost_seed)
    p2 = convergence(
        histories, opt, out / "convergence.png",
        title="Convergence de l'AG sur cinq graines", unit=UNIT,
    )
    print(f"AG 5 graines : {min(finals):.0f} a {max(finals):.0f} s | optimum {opt:.0f} s")

    # 3. CVRP sur les mêmes points, demandes déterministes
    # demande proportionnelle a la population du quartier (RGPH 2021) si disponible
    pts = inst.meta.get("points") or []
    pops = [p.get("population") for p in pts]
    if len(pops) == inst.n and all(isinstance(v, int) and v > 0 for v in pops[1:]):
        raw = np.array([0.0] + [p / max(min(pops[1:]), 1) for p in pops[1:]])
        demand = np.round(np.clip(raw * 4, 1, 5)).astype(float)
        demand[0] = 0.0
        print("demandes derivees de la population RGPH 2021")
    else:
        rng = np.random.default_rng(3)
        demand = np.concatenate([[0.0], rng.integers(1, 5, inst.n - 1).astype(float)])
    cv = Instance(
        name="abidjan_cvrp", lat=inst.lat, lon=inst.lon, matrix=inst.matrix,
        demand=demand, capacity=14.0, cost_unit=UNIT, source=inst.source, meta=inst.meta,
    )
    base = clarke_wright(cv)
    best = alns(cv, start=base, iterations=250, seed=2)
    p3 = route_map(
        cv, best, out / "tournees_cvrp.png",
        title=f"CVRP : {len(best)} tournées sur le réseau réel", unit=UNIT,
    )
    print(f"CVRP : Clarke-Wright {routes_cost(cv, base):.0f} s -> ALNS {routes_cost(cv, best):.0f} s")

    # 4. comparaison des méthodes
    nn = nearest_neighbor(inst.matrix)
    ls = local_search(inst.matrix, nn)
    cost_ga, _, _ = genetic_algorithm(inst, pop_size=120, generations=300, seed=7)
    p4 = bars(
        ["Plus proche voisin", "2-opt / Or-opt", "AG mémétique", "Held-Karp"],
        [tour_cost(inst.matrix, nn), tour_cost(inst.matrix, ls), cost_ga, opt],
        out / "comparaison.png",
        title="Coût de la tournée selon la méthode (secondes)", unit=UNIT,
    )

    for p in (p1, p2, p3, p4):
        print(f"  {p} : {p.stat().st_size} octets")


if __name__ == "__main__":
    main()
