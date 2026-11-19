# Reproduction complète du projet, en quatre commandes.
# macOS / Linux : `make <cible>`. Windows : `make` via Git Bash ou WSL.

PY ?= python
INSTANCE := data/instances/abidjan_communes_12.json

.PHONY: help setup data test bench map all clean

help:
	@echo "setup  : installe les dependances"
	@echo "data   : construit l'instance reelle depuis OSRM"
	@echo "test   : lance les 13 tests"
	@echo "bench  : compare les solveurs"
	@echo "map    : genere la carte HTML"
	@echo "all    : data + test + bench + map"

setup:
	$(PY) -m pip install -r requirements.txt

data:
	$(PY) scripts/build_instance.py --out $(INSTANCE)

test:
	$(PY) tests/test_solvers.py
	$(PY) tests/test_data.py
	$(PY) tests/test_cvrp.py
	$(PY) tests/test_vrptw.py
	$(PY) tests/test_map.py

bench: $(INSTANCE)
	$(PY) scripts/benchmark.py --instance $(INSTANCE) --seeds 10 --json-out results/bench_communes.json

map: $(INSTANCE)
	$(PY) scripts/make_map.py --instance $(INSTANCE) --out results/carte.html

all: data test bench map

clean:
	rm -rf __pycache__ .pytest_cache results/*.html results/*.json
