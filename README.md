# Abidjan Route Optimization

**Optimisation de tournées sur le réseau routier réel d'Abidjan.**

Ce projet ne simule plus des villes au hasard : il travaille sur les **temps de trajet réels** entre les communes d'Abidjan, calculés par OSRM sur le réseau OpenStreetMap. Il compare des solveurs — heuristique gloutonne, recherche locale, algorithme génétique mémétique — et mesure l'écart à l'optimum exact quand la taille le permet.

| | |
|---|---|
| **Problème** | TSP, puis CVRP avec fenêtres de temps |
| **Données** | OpenStreetMap + OSRM, chefs-lieux des 12 communes d'Abidjan |
| **Métrique** | Durée de trajet (secondes), matrice **asymétrique** |
| **Solveurs** | Plus proche voisin · 2-opt/Or-opt · AG mémétique · Held-Karp (optimum) |
| **Tests** | 7 tests, exécutables sans dépendance lourde |

## Pourquoi ce projet n'est pas un exercice

La version initiale générait quinze points aléatoires et calculait des distances euclidiennes. Aucune route, aucun client, aucune référence. Ici :

- les points sont les **chefs-lieux réels des communes** d'Abidjan ;
- la matrice vient d'**OSRM**, qui route sur le graphe OSM et respecte les sens uniques — Plateau → Cocody prend 525 s, le retour 770 s ;
- chaque résultat est comparé à l'**optimum exact** (Held-Karp) sur les petites instances, ce qui permet de dire « à 0,4 % de l'optimum » au lieu de « la courbe monte ».

## Démarrage

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS : source .venv/bin/activate
pip install -r requirements.txt

# 1. Construire l'instance réelle (appels OSRM, ~2 s)
python scripts/build_instance.py --out data/instances/abidjan_communes_12.json

# 2. Comparer les solveurs
python scripts/benchmark.py --instance data/instances/abidjan_communes_12.json --seeds 5

# 3. Tests
python tests/test_solvers.py
python tests/test_data.py
```

Pour des points d'intérêt réels (pharmacies, marchés, hôpitaux) plutôt que des chefs-lieux :

```bash
python scripts/build_instance.py --poi pharmacy --limit 40 --out data/instances/abidjan_pharmacies_40.json
```

Overpass sature régulièrement : le script essaie trois miroirs avec backoff exponentiel.

## Structure

```
src/vrp/
  instance.py          # modèle d'instance, distances haversine
  data/
    load.py            # lecture/écriture JSON des instances
  solvers/
    exact.py           # force brute, Held-Karp (optimum)
    heuristics.py      # plus proche voisin, 2-opt, Or-opt, descente
    ga.py              # AG mémétique (OX, inversion, élitisme)
scripts/
  build_instance.py    # OSRM + Overpass → JSON
  benchmark.py         # comparaison des solveurs
notebooks/
  01_baseline_ga.ipynb # notebook d'origine, conservé pour l'historique
docs/
  methodes_selection.md # théorie des cinq opérateurs de sélection
```

## Résultats reproductibles

Chaque exécution fixe sa graine. Le banc d'essai répète l'AG sur plusieurs graines et rapporte moyenne et écart-type, au lieu d'une courbe unique.

```bash
python scripts/benchmark.py --instance data/instances/abidjan_communes_12.json --seeds 10 --json-out results/bench_communes.json
```

## Limites assumées

- Les chefs-lieux sont des points approximatifs : ce sont des centres de commune, pas des adresses de clients.
- OSRM public applique des vitesses moyennes par type de voie, pas le trafic réel d'Abidjan à 17 h.
- Held-Karp plafonne à 16 points ; au-delà, la référence devient OR-Tools (à exécuter dans Colab, l'installation locale étant bloquée sur certaines machines).
- Le CVRP et les fenêtres de temps sont la prochaine étape, pas encore implémentés.

## Sources et licences

- Données cartographiques : © contributeurs OpenStreetMap, licence **ODbL**.
- Routage : serveur public OSRM (usage raisonnable, pas de production).
- Code : licence MIT.

## Auteur

Michaël SIPTOUA GRIMA — [grimael.dev](https://grimael.dev) · [GitHub](https://github.com/grimael)
