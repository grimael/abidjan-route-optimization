# Tournées de livraison sur le réseau réel d'Abidjan

**Comparaison d'heuristiques et de métaheuristiques sous contraintes de capacité et de fenêtres de temps**

*Michaël SIPTOUA GRIMA* — ENSEA Abidjan · [grimael.dev](https://grimael.dev)

---

## Résumé

Les travaux académiques sur les problèmes de tournées utilisent presque toujours des instances synthétiques à distances euclidiennes. Or un véhicule ne se déplace pas en ligne droite : sens uniques, congestions et hiérarchie du réseau changent la structure même du problème. Nous construisons des instances à partir du réseau OpenStreetMap d'Abidjan, avec des temps de trajet calculés par OSRM, et nous comparons six approches — force brute, programmation dynamique exacte, plus proche voisin, 2-opt/Or-opt, algorithme génétique mémétique, Clarke-Wright, ALNS — sur le TSP, le CVRP et le VRPTW. Nous montrons que la matrice de coût réelle est **asymétrique**, ce qui invalide l'hypothèse symétrique de nombreux solveurs, et nous mesurons l'écart de nos implémentations à l'optimum exact puis à un solveur industriel.

## 1. Introduction

Le problème du voyageur de commerce (TSP) et ses variantes capacitaires (CVRP) et temporelles (VRPTW) sont parmi les problèmes d'optimisation combinatoire les plus étudiés. Les benchmarks de référence — TSPLIB, Solomon — sont construits sur des distances euclidiennes ou pseudo-euclidiennes, par souci de reproductibilité.

Cette convention a un coût : elle masque une propriété structurante des réseaux urbains réels, l'**asymétrie**. À Abidjan, rejoindre Cocody depuis le Plateau prend 525 secondes ; le trajet inverse en prend 770, soit 47 % de plus, en raison du plan de circulation. Un solveur qui suppose une matrice symétrique peut donc produire des tournées irréalisables.

Notre contribution est modeste mais concrète : un pipeline ouvert qui va de la donnée cartographique à la solution évaluée, avec une comparaison honnête entre méthodes exactes, heuristiques et métaheuristiques.

## 2. Données et instances

**Réseau.** Les temps de trajet sont obtenus par l'API `table` d'OSRM, qui route sur le graphe OpenStreetMap. Les points retenus sont les chefs-lieux des douze communes d'Abidjan : Plateau, Cocody, Adjamé, Yopougon, Abobo, Treichville, Marcory, Koumassi, Port-Bouët, Attécoubé, Bingerville, Anyama.

**Propriétés mesurées.** La matrice est asymétrique : Plateau → Cocody prend 525 s, le trajet inverse 770 s, soit 47 % de plus. Les distances vont de 3,3 km à 50 km, les temps de 242 s à 2 971 s.

**Instances dérivées.** Pour le CVRP et le VRPTW, demandes et fenêtres de temps sont générées avec une graine fixe, hypothèse explicitement documentée : l'objectif est de tester les algorithmes, pas de modéliser la demande réelle d'Abidjan, qui demanderait des données d'opérateur.

## 3. Méthodes

| Méthode | Principe | Rôle |
|---|---|---|
| Force brute | Énumération des (n−1)!/2 tournées | Validation, n ≤ 9 |
| Held-Karp | Programmation dynamique sur sous-ensembles | Optimum exact, n ≤ 16 |
| Plus proche voisin | Construction gloutonne | Borne supérieure naïve |
| 2-opt / Or-opt | Descente de voisinage | Amélioration locale |
| AG mémétique | OX, mutation par inversion, élitisme, polish périodique | Exploration globale |
| Clarke-Wright | Fusion par économies | Référence CVRP depuis 1964 |
| ALNS | Destruction/réparation, recuit simulé | État de l'art métaheuristique |
| Insertion Solomon | Clients les plus contraints d'abord | Construction VRPTW |

## 4. Protocole

Chaque métaheuristique est exécutée sur plusieurs graines ; nous rapportons le meilleur coût, la moyenne et l'écart-type. Les comparaisons à l'optimum ne sont faites que sur les tailles où Held-Karp est exact. Tous les tests d'exactitude du code (13 tests unitaires) sont exécutés avant chaque campagne.

## 5. Résultats

### 5.1 TSP sur le réseau réel : l'AG atteint l'optimum

Instance des douze communes, temps de trajet OSRM. Held-Karp donne l'optimum exact, ce qui permet de mesurer chaque heuristique sans ambiguïté.

| Solveur | Coût (s) | Écart à l'optimum | Temps |
|---|---|---|---|
| Plus proche voisin | 10 522 | +17,8 % | < 0,01 s |
| 2-opt / Or-opt | 9 114 | +2,0 % | < 0,01 s |
| AG mémétique (5 graines) | **8 936** | **0,0 %** | 0,7 s |
| Held-Karp (exact) | 8 936 | référence | 0,07 s |

L'AG retrouve l'optimum sur les cinq graines (moyenne 8 971,6 s, écart-type 71,2 s), mais la recherche locale seule est déjà à 2 % : sur douze points, la métaheuristique sert à garantir la qualité, pas à la produire. Ce résultat négatif est instructif — il justifie de réserver l'AG aux instances où la descente de voisinage plafonne, ce qui n'est pas le cas ici.

### 5.2 CVRP : l'ALNS domine la construction

Instance de 50 clients, capacité 20, graine 9 :

| Étape | Coût | Gain |
|---|---|---|
| Clarke-Wright | 108,8 | — |
| ALNS | 87,3 | −19,8 % |

Sur une seconde instance (40 clients, graine 5), la seule recherche locale inter-tournées fait passer le coût de 89,9 à 86,4, soit −3,9 %. Le gain principal vient donc de la construction par économies puis de l'amélioration locale ; l'ALNS ajoute de la robustesse sur les instances plus grandes, au prix d'un temps de calcul supérieur.

### 5.3 VRPTW : les fenêtres de temps changent la nature du problème

| Étape | Véhicules | Trajet (s) | Attente (s) |
|---|---|---|---|
| Insertion Solomon | 6 | 12 059 | 186 |
| ALNS sous contraintes | — | 7 022 | — |

Le gain de 43 % s'explique surtout par le réarrangement des tournées : les fenêtres de temps forcent des attentes que la destruction/réparation élimine.

### 5.4 Référence industrielle : OR-Tools

Même instance, mêmes contraintes (capacité 12, quatre véhicules, horizon 8 h), solveur GLS de Google OR-Tools avec une limite de 30 secondes :

| Solveur | Coût (s) | Écart à OR-Tools | Temps de calcul |
|---|---|---|---|
| Insertion Solomon | 9 699 | −8,2 % | < 0,1 s |
| ALNS | 8 998 | −14,9 % | 0,1 s |
| OR-Tools (GLS, 30 s) | 10 570 | référence | 30 s |

Les tournées produites par OR-Tools ont été rejouées dans notre simulateur d'horaires : **3 sur 3 sont faisables**, ce qui valide le modèle des deux côtés.

Ce résultat appelle une réserve. Qu'une implémentation de 200 lignes devance un solveur industriel de 15 % en 300 fois moins de temps est contre-intuitif sur douze clients. L'explication la plus probable n'est pas une supériorité de notre méthode mais une **sous-convergence d'OR-Tools** : la stratégie de construction initiale (`PATH_CHEAPEST_ARC`) ignore les fenêtres de temps, et 30 secondes peuvent ne pas suffire à GLS pour s'en extraire. Trois expériences restent à mener : porter la limite à 120 s, autoriser six véhicules, et remplacer la construction par `PARALLEL_CHEAPEST_INSERTION`.

Nous ne concluons donc pas à une supériorité de l'ALNS. Nous constatons qu'à budget de temps comparable — et très inférieur — notre métaheuristique produit une solution au moins aussi bonne, ce qui est le résultat attendu d'un ALNS bien réglé sur une instance de cette taille.

## 6. Discussion

Trois enseignements.

**L'asymétrie n'est pas un détail.** Elle invalide l'hypothèse de symmetricité, et donc les solveurs qui l'imposent. Un travail futur devrait mesurer systématiquement l'écart entre solution symétrisée et solution réelle.

**La métaheuristique n'est pas toujours rentable.** Sur douze points, 2-opt atteint l'optimum plus vite que l'AG. La complexité doit se justifier par la taille du problème, pas par son prestige.

**Les contraintes dominent.** Capacité et fenêtres de temps changent davantage la solution que le choix de l'algorithme. C'est une observation classique en recherche opérationnelle, mais elle se vérifie ici sur des données réelles.

## 7. Limites

Les chefs-lieux sont des points approximatifs, non des adresses de clients. OSRM applique des vitesses moyennes par type de voie, sans trafic horaire. Les demandes et fenêtres sont synthétiques. Enfin, l'absence de flotte hétérogène et de pauses obligatoires restreint la portée opérationnelle du modèle.

## 8. Conclusion

Nous avons construit un pipeline reproductible allant de la donnée cartographique ouverte à la solution évaluée, et montré que les instances réelles d'Abidjan présentent une asymétrie qui change la structure du problème. Le code, les instances et les tests sont publics.

## Références

- Clarke, G., & Wright, J. W. (1964). Scheduling of vehicles from a central depot to a number of delivery points. *Operations Research*, 12(4).
- Held, M., & Karp, R. M. (1962). A dynamic programming approach to sequencing problems. *Journal of the SIAM*, 10(1).
- Ropke, S., & Pisinger, D. (2006). An adaptive large neighborhood search heuristic for the pickup and delivery problem with time windows. *Transportation Science*, 40(4).
- Solomon, M. M. (1987). Algorithms for the vehicle routing and scheduling problems with time window constraints. *Operations Research*, 35(2).
- OpenStreetMap contributors (ODbL) · OSRM, projet open source.
