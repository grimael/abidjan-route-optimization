Explication des méthodes de sélection pour les algorithmes génétiques

Dans un algorithme génétique (AG), la sélection consiste à choisir des individus (solutions candidates, ici des chemins pour le TSP) parmi la population pour créer la prochaine génération. Chaque méthode de sélection utilise le score de fitness (ici, 1 / distance_totale, où un fitness plus élevé indique un chemin plus court) pour favoriser les meilleurs individus tout en maintenant une certaine diversité. Voici une explication claire de cinq méthodes de sélection utilisées dans notre TP.

### **1. Sélection par roulette (Roulette Wheel Selection)**

Définition

La sélection par roulette attribue à chaque individu une probabilité de sélection proportionnelle à son score de fitness. C'est comme une roulette de casino : les individus avec un fitness élevé occupent une plus grande part de la "roue", augmentant leurs chances d'être choisis.

Fonctionnement

Calcule le fitness de chaque chemin (par exemple, fitness = 1 / distance_totale).

Somme tous les fitness pour obtenir une valeur totale.

Normalise les fitness pour créer des probabilités (fitness de chaque chemin divisé par la somme totale).

Choisit un chemin aléatoirement en fonction de ces probabilités, comme tirer un numéro sur une roulette.

Dans le TSP, un chemin avec une distance courte (fitness élevé) a plus de chances d'être sélectionné, mais même les chemins moins performants ont une petite chance.

Avantages

Simple à comprendre et à implémenter.

Permet à tous les chemins d'avoir une chance, ce qui favorise la diversité.

Bien adapté lorsque les fitness varient beaucoup.

Inconvénients

Si un chemin a un fitness beaucoup plus élevé, il peut dominer la sélection, réduisant la diversité.

Sensible aux différences d'échelle des fitness (par exemple, si les fitness sont très proches, la sélection devient presque aléatoire).

Exemple

Dans une population de 100 chemins avec des fitness entre 0.001 et 0.003 :

Chemin A : fitness = 0.002 (distance = 500).

Chemin B : fitness = 0.001 (distance = 1000).

La somme des fitness est, disons, 0.2. Les probabilités sont 0.002/0.2 = 1% pour A, 0.001/0.2 = 0.5% pour B.

Chemin A a deux fois plus de chances d'être choisi que B.

## **2. Sélection par rang (Rank-Based Selection)**

Définition

La sélection par rang classe les individus par ordre de fitness (du meilleur au moins bon) et attribue des probabilités de sélection basées sur leur rang plutôt que leur fitness brut. Les meilleurs individus (rangs élevés) ont une plus grande chance d'être choisis.

Fonctionnement

Calcule le fitness de chaque chemin et trie les chemins par fitness décroissant.

Assigne un rang à chaque chemin : le meilleur a le rang 1, le deuxième a le rang 2, etc.

Calcule des probabilités linéaires basées sur le rang (le rang 1 a la plus haute probabilité).

Choisit un chemin aléatoirement selon ces probabilités.

Dans le TSP, cela donne une chance aux chemins corrects, mais évite qu'un chemin exceptionnel ne domine trop.

Avantages

Moins sensible aux grandes différences de fitness (par exemple, un chemin avec un fitness très élevé n'écrase pas les autres).

Favorise une sélection équilibrée, maintenant une bonne diversité.

Utile lorsque les fitness varient beaucoup dans la population.

Inconvénients

Ignore les différences relatives de fitness (un chemin légèrement meilleur qu’un autre a le même avantage qu’un chemin beaucoup meilleur).

Peut réduire la pression sélective, ralentissant la convergence.

Exemple

Dans une population de 100 chemins :

Chemin A : fitness = 0.003 (rang 1).

Chemin B : fitness = 0.002 (rang 2).

Chemin C : fitness = 0.001 (rang 100).

Probabilité pour le rang 1 = 100/(100*101/2) ≈ 0.0198, rang 2 ≈ 0.0196, ..., rang 100 ≈ 0.0002.

Chemin A a une probabilité légèrement plus élevée que B, mais C a une petite chance.

## **3. Sélection par échantillonnage stochastique universel (SUS)**

Définition

La sélection par échantillonnage stochastique universel (SUS) est une variante de la sélection par roulette. Elle utilise plusieurs "pointeurs" régulièrement espacés pour sélectionner des individus en une seule passe, assurant une sélection proportionnelle au fitness.

Fonctionnement

Calcule le fitness de chaque chemin et leur somme totale.

Définit un intervalle (pas) égal à la somme des fitness divisée par le nombre d'individus.

Choisit un point de départ aléatoire dans le premier intervalle.

Parcourt les fitness cumulés et sélectionne le premier chemin dont le fitness cumulé dépasse le point de départ.

Dans le TSP, SUS garantit que les chemins courts sont sélectionnés proportionnellement à leur fitness, tout en étant plus stable que la roulette.

Avantages

Plus stable que la roulette : garantit une sélection proportionnelle sans trop de variance.

Efficace pour sélectionner plusieurs parents en une passe (bien que notre code sélectionne un seul parent à la fois).

Bonne diversité, car tous les chemins ont une chance proportionnelle.

Inconvénients

Légèrement plus complexe à implémenter que la roulette.

Sensible aux grandes différences de fitness, comme la roulette.

Exemple

Dans une population de 100 chemins, somme des fitness = 0.2 :

Pas = 0.2/100 = 0.002.

Point de départ aléatoire = 0.0015.

Chemin A : fitness = 0.002 (cumulé = 0.002).

Chemin B : fitness = 0.001 (cumulé = 0.003).

Le cumulé dépasse 0.0015 au chemin A, donc A est sélectionné.

## **4. Sélection élitiste (Elitist Selection)**

Définition

La sélection élitiste choisit systématiquement l'individu avec le meilleur fitness de la population, sans aucune composante aléatoire.

Fonctionnement

Calcule le fitness de chaque chemin.

Retourne directement le chemin avec le fitness le plus élevé (distance la plus courte dans le TSP).

Dans le TSP, cela garantit que le meilleur chemin connu est toujours utilisé comme parent.

Avantages

Très simple et rapide (une seule comparaison).

Garantit que la meilleure solution est utilisée, ce qui peut accélérer la convergence.

Utile pour préserver les meilleures solutions (souvent combinée avec d'autres méthodes).

Inconvénients

Réduit fortement la diversité, car seuls les meilleurs chemins sont choisis.

Risque de convergence prématurée vers un optimum local.

Ne convient pas comme méthode unique, car elle ignore les autres chemins.

Exemple

Dans une population de 100 chemins :

Chemin A : fitness = 0.003 (distance = 333, le meilleur).

Chemin B : fitness = 0.002 (distance = 500).

La sélection élitiste choisit toujours Chemin A, ignorant B et les autres.

1. Sélection par troncature (Truncation Selection)

Définition

La sélection par troncature trie les individus par fitness et choisit aléatoirement parmi les k% meilleurs (par exemple, les 50% meilleurs). Les individus les moins performants sont complètement ignorés.

Fonctionnement

Calcule le fitness de chaque chemin et trie les chemins par fitness décroissant.

Sélectionne les proportion * taille_population meilleurs chemins (par exemple, 50% si proportion=0.5).

Choisit un chemin aléatoirement parmi ce sous-ensemble.

Dans le TSP, cela concentre la sélection sur les chemins les plus courts, mais donne une chance égale à tous les chemins dans le sous-ensemble sélectionné.

Avantages

Simple et rapide (tri et choix aléatoire).

Forte pression sélective, favorisant les bons chemins.

Utile pour accélérer la convergence dans des problèmes complexes.

Inconvénients

Réduit fortement la diversité, car les chemins moins performants sont exclus.

Risque de convergence prématurée si la proportion est trop faible.

Néglige des chemins moyens qui pourraient contenir des segments utiles.

Exemple

Dans une population de 100 chemins, avec proportion=0.5 :

Les 50 chemins avec les meilleurs fitness (par exemple, fitness > 0.002) sont retenus.

Un chemin est choisi aléatoirement parmi ces 50, par exemple, un chemin avec fitness = 0.0025.

Les 50 chemins restants (fitness < 0.002) n'ont aucune chance d'être sélectionnés.

Intégration dans le TP

Ces méthodes peuvent être testées dans le TP en remplaçant la méthode de sélection dans la fonction genetic_algorithm. Par exemple, pour utiliser roulette_selection :

parent1 = roulette_selection(population)

parent2 = roulette_selection(population)

Chaque méthode influence :

La courbe de fitness (fitness_evolution.png) : Une méthode avec forte pression sélective (comme élitiste) peut converger plus vite, mais risque de stagner.

La distance finale (tsp_solution.png) : Une méthode équilibrée (comme rang ou SUS) peut trouver de meilleures solutions en évitant les optima locaux.

La diversité des chemins : Les méthodes comme roulette et SUS produisent des chemins plus variés, visibles dans route_gen_X.png.

Pour comparer, exécutez le TP avec chaque méthode et analysez les résultats (fitness, distance, graphiques).
