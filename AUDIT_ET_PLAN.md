# Audit et refonte — abidjan-route-optimization

## 1. État actuel, factuel

**Ce que contient le dépôt** : un notebook de 26 cellules, un `methodes.md` de 9 Ko (théorie des cinq opérateurs de sélection), huit figures PNG, un README de 4 Ko — et **222,7 Mo d'environnement virtuel Python** (`grim/`, 11 850 fichiers), sans `.gitignore`.

**Ce que fait le notebook** : il génère **15 villes aux coordonnées aléatoires**, calcule des **distances euclidiennes**, puis lance un algorithme génétique (tournoi, croisement OX, mutation). Cinq opérateurs de sélection sont définis — roulette, rang, SUS, élitisme, troncature — mais l'algorithme principal n'en utilise qu'un.

## 2. Les limites, par ordre de gravité

### Critiques — celles qui font fermer l'onglet

1. **Les données sont inventées.** Quinze points tirés au hasard dans un carré. Aucun rapport avec Abidjan, aucune route, aucun client. Le titre du projet ment sur son contenu : c'est un TSP jouet, pas une optimisation de tournées urbaines.
2. **Distance euclidienne.** Un véhicule ne vole pas à travers les immeubles. Sans graphe routier, la métrique n'a aucun sens opérationnel.
3. **Aucun point de comparaison.** Un algorithme génétique seul ne prouve rien : sans solveur exact ni heuristique de référence, on ne sait pas si le résultat est bon, médiocre ou catastrophique.
4. **222 Mo de venv dans Git.** C'est le premier signal envoyé à un recruteur ou à un professeur : le projet n'a pas été relu.

### Méthodologiques

5. **Une seule exécution, une seule graine.** Aucune répétition, aucun écart-type, aucune garantie que la courbe observée ne soit pas un artefact du hasard.
6. **15 nœuds.** L'espace de recherche fait 14!/2 ≈ 4·10¹⁰ — impressionnant à l'écrit, mais un solveur moderne le résout à l'optimum en millisecondes. L'instance ne justifie pas la métaheuristique.
7. **Objectif unique.** Distance seule. Ni capacité, ni fenêtres de temps, ni flotte hétérogène — donc aucun des problèmes que rencontrent réellement les opérateurs logistiques.
8. **Pas de généralisation.** Rien ne dit si l'algorithme tient sur 50, 200 ou 1 000 clients.

### Ingénierie

9. Pas de package, pas de tests, pas de CLI, pas de reproductibilité (pas d'environnement figé, pas de configuration).
10. `methodes.md` explique la théorie mais ne documente aucun résultat.
11. Les sorties sont des PNG statiques ; aucune carte interactive, alors qu'on parle de géographie.

## 3. La cible

Faire passer le projet de « TP de L3 » à « travail de niveau master, publiable en atelier ».

| Axe | Aujourd'hui | Cible |
|---|---|---|
| Données | 15 points aléatoires | Graphe routier réel d'Abidjan (OpenStreetMap) + points d'intérêt réels + population WorldPop |
| Métrique | Euclidienne | Temps de trajet réel par type de voie, ou distance réseau |
| Problème | TSP 15 nœuds | **CVRP avec fenêtres de temps (VRPTW)** sur 50 à 500 clients |
| Méthodes | 1 AG | OR-Tools (référence) · AG + recherche locale (2-opt, Or-opt) · ALNS · comparaison statistique |
| Évaluation | 1 figure | 30 répétitions, intervalles de confiance, test de Wilcoxon, écart au meilleur connu |
| Visualisation | PNG matplotlib | Carte interactive folium sur fond OSM, itinéraires, isochrones |
| Ingénierie | notebook | Package `src/`, CLI, tests pytest, CI, `requirements.txt`, Dockerfile, licence |

## 4. Plan d'exécution

**Phase 0 — Hygiène (aujourd'hui)**
Supprimer le venv du suivi Git, ajouter `.gitignore`, structurer le dépôt, licence, déplacer le notebook dans `notebooks/`.

**Phase 1 — Données réelles**
Téléchargement du graphe OSM d'Abidjan via OSMnx, mise en cache locale, extraction des temps de trajet, sélection de clients réels (marchés, pharmacies, hôpitaux) et génération d'instances reproductibles.

**Phase 2 — Solveurs**
Formulation VRPTW, baseline OR-Tools, AG amélioré avec recherche locale, ALNS.

**Phase 3 — Expériences**
Protocole multi-graines, benchmarks Solomon, comparaison statistique, figures.

**Phase 4 — Restitution**
Carte interactive, README de niveau publication, article court (4 pages).

## 5. Sources de données ouvertes à mobiliser

- **OpenStreetMap** via l'API Overpass et les extraits Geofabrik — réseau routier, commerces, santé. Licence ODbL, à citer.
- **WorldPop** — grille de population 100 m, pour pondérer la demande.
- **HDX (Humanitarian Data Exchange)** — découpages administratifs d'Abidjan, données de population.
- **OpenStreetMap POI** — marchés, pharmacies, hôpitaux, stations-service comme points de livraison réels.
- **ANSUT / Open Data Côte d'Ivoire** — à vérifier, les portails nationaux sont souvent incomplets.
