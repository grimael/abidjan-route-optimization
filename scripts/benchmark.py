"""Compare les solveurs sur une instance et écrit un tableau de résultats.

Usage :
    python scripts/benchmark.py --instance data/instances/abidjan_communes_12.json
    python scripts/benchmark.py --instance ... --seeds 10 --generations 300
"""

from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from vrp.data.load import load_instance  # noqa: E402
from vrp.solvers.exact import held_karp  # noqa: E402
from vrp.solvers.ga import genetic_algorithm  # noqa: E402
from vrp.solvers.heuristics import local_search, nearest_neighbor, tour_cost  # noqa: E402


def run(instance, seeds: int, generations: int) -> list[dict]:
    matrix = instance.matrix
    rows: list[dict] = []

    t0 = time.perf_counter()
    nn = nearest_neighbor(matrix)
    rows.append({"solver": "plus proche voisin", "cost": tour_cost(matrix, nn), "time_s": time.perf_counter() - t0})

    t0 = time.perf_counter()
    ls = local_search(matrix, nn)
    rows.append({"solver": "voisin + 2-opt/Or-opt", "cost": tour_cost(matrix, ls), "time_s": time.perf_counter() - t0})

    ga_costs, ga_times = [], []
    for seed in range(seeds):
        t0 = time.perf_counter()
        cost, _, _ = genetic_algorithm(instance, pop_size=120, generations=generations, seed=seed)
        ga_times.append(time.perf_counter() - t0)
        ga_costs.append(cost)
    rows.append(
        {
            "solver": f"AG mémétique ({seeds} graines)",
            "cost": min(ga_costs),
            "mean": statistics.fmean(ga_costs),
            "std": statistics.pstdev(ga_costs),
            "time_s": statistics.fmean(ga_times),
        }
    )

    if instance.n <= 16:
        t0 = time.perf_counter()
        opt, _ = held_karp(instance)
        rows.append({"solver": "Held-Karp (optimum)", "cost": opt, "time_s": time.perf_counter() - t0})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", required=True)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--generations", type=int, default=200)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    inst = load_instance(args.instance)
    unit = "s" if inst.cost_unit == "s" else inst.cost_unit
    print(f"Instance : {inst.name} — {inst.n} points — source : {inst.source}\n")

    rows = run(inst, args.seeds, args.generations)
    ref = max(r["cost"] for r in rows)
    print(f"{'Solveur':<30} {'Coût':>10} {'Écart':>8} {'Temps':>9}")
    print("-" * 62)
    for r in rows:
        gap = (r["cost"] - min(x["cost"] for x in rows)) / min(x["cost"] for x in rows) * 100
        extra = f"{r['mean']:.1f} ±{r['std']:.1f}" if "mean" in r else ""
        print(f"{r['solver']:<30} {r['cost']:>10.1f} {gap:>7.1f}% {r['time_s']:>8.2f}s {extra}")
    print(f"\nUnité : {unit}")

    if args.json_out:
        pathlib.Path(args.json_out).write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"Résultats écrits dans {args.json_out}")


if __name__ == "__main__":
    main()
