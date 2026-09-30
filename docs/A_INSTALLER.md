# À faire demain matin — installation et tests

Bonne nouvelle : **aucun nouveau plugin ni mod serveur n'est obligatoire** pour ce qui a été ajouté cette nuit.
Tout passe par ce que tu as déjà (Skript, MythicMobs, ZAMonde, Create, CCA, IE, TaCZ). La seule chose à distribuer
aux joueurs est la nouvelle version du mod client `za_modeles` (1.3.0).

Rien n'a pu être testé en jeu (pas de serveur dans la session cloud) : tout a été vérifié « à la lecture » et par un
petit vérificateur automatique. Il faut donc tester avant d'ouvrir aux joueurs.

---

## 1. Récupérer les changements (git, pas à pas)

Mes changements sont sur la branche **`main-eoee6l`** de ton dépôt GitHub (pas encore sur `main`).

**Le plus simple (sur le site GitHub)** :
1. Va sur `github.com/colinbo1219/ZombieApocalypse_Serveur`.
2. Un bandeau jaune propose « main-eoee6l had recent pushes » → clique **Compare & pull request**, puis
   **Create pull request**, puis **Merge pull request** → **Confirm merge**. Tes changements sont maintenant sur `main`.
3. Sur ton PC, dans le dossier du serveur (clic droit → « Open Git Bash here ») : `git pull`

**Sans passer par le site** (dans Git Bash, dans le dossier du serveur) :
```
git fetch origin
git checkout main-eoee6l
git pull
```
(Pour revenir ensuite à `main` : `git checkout main`.)

> Avant tout : fais une **copie de sauvegarde** du dossier `world` et de `plugins/Skript/variables.csv`.

## 2. Mettre à jour le serveur

1. Arrête le serveur, récupère les fichiers (étape 1), relance-le (`start.bat`).
   Un redémarrage est plus sûr que 11 `sk reload` (et **jamais** `sk reload all`).
2. Regarde la console au démarrage : Skript affiche `Loaded 78 scripts`. S'il y a des lignes **error**, copie-les
   moi dans la prochaine session : je corrige.
3. MythicMobs se recharge au démarrage (sinon `/mm reload`) : 6 nouveaux zombies (`ZA_Policier_Infecte`,
   `ZA_Medecin_Infecte`, `ZA_Ouvrier_Infecte`, `ZA_Ouvrier_Brule`, `ZA_Pompier_Infecte`, `ZA_Prisonnier_Infecte`).
4. Java : le serveur exige Java 17 ou 21 (pas 25).

## 3. Mettre à jour le pack des joueurs (CurseForge)

1. Dans ton projet de modpack CurseForge, dossier `overrides/mods` : **remplace** `za_modeles-1.2.0.jar` par
   `pack_joueurs/za_modeles-1.3.0.jar` (dans le dépôt).
2. Monte la version du pack (ex. 1.4), exporte, publie. Les joueurs mettent à jour leur pack.
   Sans la 1.3.0, les nouveaux zombies ont l'apparence de base et les nouveaux sons sont muets (pas de plantage).

## 4. Poser Saint-Aurèle en ruines (une seule fois)

1. Choisis un endroit **plat, sans construction de joueur**, idéalement à 150-300 blocs de l'autobus d'arrivée.
2. Pré-génère la zone : `/chunky center <x> <z>`, `/chunky radius 250`, `/chunky start` (attends la fin).
3. Mets-toi debout au centre voulu (la rue Principale sera sous tes pieds) et tape **`/zaville installer`**.
4. Suis la pose avec `/zamonde etat` (288 × 48 × 288 blocs, quelques minutes). Puis `/zaville` pour l'état.
5. Les 4 sous-stations de la ville sont créées **endommagées** : c'est voulu (objectifs de réparation).

## 5. Tests rapides (dans cet ordre)

| Test | Commande / action | Attendu |
|---|---|---|
| Prologue | `/prologue lancer <toi>` | barre d'action « Saint-Aurèle · VILLE NORMALE », entractes Jour 2/4/6, alerte « QUELQUE CHOSE vient de se relever » |
| Échos | `/zaecho lancer ginette <toi>` | indice radio, en t'approchant : Ginette te reconnaît |
| Électricité | accumulateur CCA chargé → comparateur → fil → bloc ; regarder le bloc, `/electricite installer` ; attendre 15 s ; `/electricite` | sous-station qui produit 1 à 5 unités |
| Réparation | `/zaelec panne <id>` puis `/electricite reparer` (2 Composants + 4 cuivre) | 20 s, des zombies arrivent, radio |
| Zombies | `/mm mobs spawn ZA_Policier_Infecte` | uniforme (avec le mod 1.3.0) |
| Scènes rares | `/zazv scene regard <toi>` | un zombie te fixe |
| Ruines | marcher dans la ville | titre « Population : 0 », souvenirs, mot de Maman dans le coffre du 2A |
| Lampes | `/zaville lampes hopital on` | les lampadaires de l'hôpital s'allument |
| Dossier Arel | clic droit sur le menu du Café du Coin, puis la porte de la chambre 104, etc. | documents datés, casier 0731 |
| Factions | `/faction diplomatie`, `/zadiplo stock milice munitions 0`, `/zadiplo jour`, `/faction contrats` | contrat publié |
| Cours | `/cours`, `/zacours set munitions 1.5`, ouvrir le Trafiquant | prix x1,5 |
| Téléphone | `/zatel <toi> donner`, `/telephone` | menu, SMS, appels |
| Chroniques | `/zasaison enregistrer`, `/chroniques <n> 2` | lignes Personnages / Réseau / Saint-Aurèle |

## 6. Optionnel : pour une ville « full custom » (pas vanilla)

Ce qui suit n'est **pas nécessaire** au fonctionnement. Ce sont des mods Forge 1.20.1 qui donneraient à Saint-Aurèle
un vrai look de ville moderne. **À installer sur le serveur ET dans le pack des joueurs**, et à tester d'abord sur une
copie du serveur (Arclight n'est pas compatible avec tous les mods).

| Mod | Pourquoi | Dépendance |
|---|---|---|
| Macaw's Roofs, Windows, Doors, Lights and Lamps, Fences and Walls, Furniture, Paths and Pavings, Bridges | toits, fenêtres, lampadaires, trottoirs, mobilier : l'essentiel d'une ville moderne | aucune |
| Create: Deco | lampes industrielles, passerelles, grilles, parfait pour la centrale et les sous-stations | Create (déjà là) |
| Supplementaries | panneaux indicateurs, tableaux d'affichage, bocaux, sacs : décor de ruines | Moonlight Lib |
| Handcrafted | meubles de maison (appartements, dépanneur) | Resourceful Lib |

Côté joueurs seulement (ambiance, facultatif) : **Sound Physics Remastered** (échos, réverbération : génial pour
l'horreur), **AmbientSounds** (ambiance sonore ; demande CreativeCore).

À éviter : **Fresh Animations** (pack de ressources) : il remplace le modèle `zombie` et écraserait les modèles
custom de `za_modeles`.

Quand ces mods seront installés, dans une prochaine session je peux adapter le générateur de la ville
(`ZA_sources/ville/`) pour utiliser leurs blocs (il faudra me donner la liste exacte des mods installés, pour valider
les noms de blocs) et régénérer la ville du prologue **et** les ruines.

## 7. Facultatif : voix

Les entractes des jours 2, 4 et 6 sont en texte seul. Si tu enregistres des voix, dépose des `.ogg` et je les
branche (clés prévues : `voix.radio_j2`, `voix.radio_j4`, `voix.radio_j6`).

## 8. Ce qui n'a PAS été testé

Tout ce qui est en jeu : chargement réel des 78 scripts par Skript, les commandes, la pose des ruines, les modèles
et animations EMF du mod 1.3.0, les sons, la lecture de la redstone des machines Create/CCA/IE par Skript sur
Arclight. Le détail des risques est dans `docs/RAPPORTS_PHASES.md`, phase par phase.
