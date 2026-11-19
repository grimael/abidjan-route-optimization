"""Test du generateur de carte (aucune dependance navigateur)."""
import sys, pathlib, shutil
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from vrp.instance import Instance
from vrp.solvers.cvrp import clarke_wright
from vrp.viz.map import solution_map

TMP = pathlib.Path(__file__).resolve().parent / "_tmpmap"


def test_map_generation():
    TMP.mkdir(exist_ok=True)
    try:
        inst = Instance.random_cvrp(n=12, seed=2, capacity=15)
        routes = clarke_wright(inst)
        out = solution_map(inst, routes, TMP / "c.html", title="Test")
        html = out.read_text(encoding="utf-8")
        assert "leaflet" in html.lower()
        assert "openstreetmap" in html
        assert html.count("Véhicule") == len(routes)
        assert out.stat().st_size > 2000
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    print(f"OK  carte generee ({len(routes)} tournees)")


if __name__ == "__main__":
    test_map_generation()
    print("Test carte: OK")
