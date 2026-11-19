"""Genere une carte HTML des tournees a partir d'une instance.

Usage :
    python scripts/make_map.py --instance data/instances/abidjan_communes_12.json --out results/carte.html
"""
from __future__ import annotations
import argparse, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from vrp.data.load import load_instance
from vrp.solvers.cvrp import alns, clarke_wright, routes_cost
from vrp.viz.map import solution_map


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", required=True)
    ap.add_argument("--out", default="results/carte.html")
    ap.add_argument("--iterations", type=int, default=300)
    args = ap.parse_args()

    inst = load_instance(args.instance)
    if not inst.is_cvrp:
        from vrp.solvers.ga import genetic_algorithm
        cost, tour, _ = genetic_algorithm(inst, generations=200, seed=1)
        routes = [tour]
    else:
        base = clarke_wright(inst)
        routes = alns(inst, start=base, iterations=args.iterations, seed=1)
        print(f"Clarke-Wright : {routes_cost(inst, base):.0f} | ALNS : {routes_cost(inst, routes):.0f}")

    out = solution_map(inst, routes, args.out, title=inst.name)
    print(f"Carte ecrite : {out}")


if __name__ == "__main__":
    main()
