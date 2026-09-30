# ZombieApocalypse — serveur Minecraft (Arclight 1.20.1)

Serveur de survie zombie francophone (Québec). Propriétaire : Colin. Tout le texte vu par les joueurs est en
**français avec accents** ; commentaires de code en français, courts.

## Mission en cours
Lire **[MISSION.md](MISSION.md)** en entier avant tout travail. Elle fixe l'objectif (Saint-Aurèle : une ville normale
qui tombe sous les yeux du joueur), l'ordre obligatoire des 15 phases et le format du rapport de fin de phase.
Phase 1 = analyse seule, aucune modification.

## Pile technique
- `arclight-5dc8683.jar` : Forge 1.20.1 + API Bukkit/Spigot dans le même serveur.
- Skript 2.9.5 : presque toute la logique de jeu (`plugins/Skript/scripts/za_*.sk`, 78 fichiers).
- MythicMobs 5.7.2 : zombies et PNJ (`plugins/MythicMobs/Mobs|Skills|Items|RandomSpawns/`).
- Plugin maison `plugins/ZAMonde.jar` : ville, PNJ, props, HUD, caméras (données dans `plugins/ZAMonde/`).
- ~64 mods Forge (liste et SHA-1 dans [JARS.txt](JARS.txt), dont 16 mods décoratifs Macaw's / Handcrafted / Supplementaries / Create Deco utilisés par la ville, et des add-ons Create : voir docs/A_INSTALLER.md §6 bis ; Design Decor 0.4.0b et Create D&D 0.1b sont INCOMPATIBLES avec Create 6), configs dans `config/`, `defaultconfigs/`, `world/serverconfig/`.
- Datapacks : `world/datapacks/za_*`.

## Ce que le dépôt ne contient pas
- **Les jars publics** : exclus par `.gitignore`, voir JARS.txt. Seuls `ZAMonde.jar`, `ZAPaperCompat.jar` et
  `zombie_extreme-0.2.6.5-za2.jar` sont versionnés (introuvables ailleurs).
- **Pas de serveur de test ici** : impossible de lancer le serveur dans cette session. Validation = relecture statique
  rigoureuse (syntaxe Skript, références, doublons). Colin teste lui-même en jeu. Dire clairement ce qui n'a pas été testé.
- Monde et données joueurs (`variables.csv`, LuckPerms, CoreProtect).

## Sources complémentaires
`ZA_sources_build.zip` contient les sources : plugin ZAMonde (Java), générateurs Python de la ville, générateur du mod
client de modèles `za_modeles`, specs et **BRIEF_AGENTS.md** (règles Skript + fonctions partagées : à lire).
Extraire avec `unzip -o ZA_sources_build.zip` : crée `ZA_sources/`, qui est ignoré par git.
- Les chemins cités dans BRIEF_AGENTS.md (`/home/claude/za_build`, serveur de test `arc`) viennent d'un ancien
  environnement et n'existent pas ici.
- La vérité pour les scripts est `plugins/Skript/scripts/` (version déployée). `ZA_sources/skript/` peut être plus ancien.

## À ne jamais casser (sinon le serveur gèle ou tue les joueurs)
- `plugins/MythicMobs/config/config-spawning.yml` : `Generator` doit rester `NONE`. Les apparitions aléatoires sont
  gérées par `za_p36_apparitions.sk`.
- Ne pas remplacer `mods/zombie_extreme-0.2.6.5-za2.jar` par l'original (biome radioactif mortel).
- MythicMobs reste en 5.7.2 avec `ZAPaperCompat.jar`. **Pas de MythicMobs 5.11 ni de ModelEngine** (incompatibles
  Arclight). Les apparences custom des zombies/PNJ passent par le mod client `za_modeles` (pack CurseForge des joueurs) :
  toute modif visuelle implique de régénérer ce mod et de mettre à jour le pack joueurs.

## Règles Skript essentielles (détails dans BRIEF_AGENTS.md)
- Tout événement joueur/entité commence par `if za_pro(player) is true: stop` : le monde `za_prologue` est une
  instance d'histoire privée que les systèmes de survie ne doivent pas toucher.
- `za_monde_joueurs()` au lieu de `all players`, `za_diffuser("...")` au lieu de `broadcast`.
- Variables globales `{za::<module>::...}`, données joueur indexées par UUID. Chercher (grep) avant de créer un nom.
- `%` s'écrit `%%` dans les chaînes. `every N seconds` ≥ 5 s, jamais de boucle sur toutes les entités.
- Une fonction qui atteint un `wait` rend la main tout de suite à l'appelant.
- Objets nommés via `za_item(...)`, menus via `za_menu(...)`, radio via `za_radio(...)`.
- Ne jamais recommander `sk reload all` (gèle ~60 s) : `sk reload <fichier>`.

## Pièges connus
- Numéros en double : `za_p7_economie` / `za_p7_progression`, `za_p38_lieux` / `za_p38_prologue`.
- LISEZMOI.txt annonce 41 scripts : il y en a 81.
- Colin utilise Java 25 en local, alors que le serveur exige Java 17 ou 21.

## Travail des phases 2 à 15 (voir docs/RAPPORTS_PHASES.md)
- Nouveaux modules : `za_p61_electricite` (sous-stations Create/CCA/IE), `za_p63_echos` (personnages du prologue),
  `za_p65_zombies_vivants`, `za_p66_ruines` (+ `_donnees`, généré), `za_p67_diplomatie`, `za_p68_cours`,
  `za_p69_exploration` (dossier Arel), `za_p70_ondes` (bulletin de Léa, téléphone), `za_p71_chronique`, `za_p72_archives`, `za_p73_sites` (lieux du monde généré), `za_p74_aube` (retraite au nid à l'aube, réveil
  au crépuscule ; aucun monstre ne brûle : `za_p32_soleil`).
- Mod client : `pack_joueurs/za_modeles-1.4.0.jar` = `build.py` (16 zombies de base, peintre `zagen_lib.py`) +
  `extension_1_4.py` appliqué au jar 1.3.0 (git) : passe horreur des peaux humaines, animations, sons.
  1.3.0 venait de `extension_1_3.py` sur le jar 1.2.0. Capacités « horreur » : `MythicMobs/Skills/ZA_Horreur.yml`.
- Ruines de Saint-Aurèle : `ZA_sources/ville/gen_ruines.py` -> `plugins/ZAMonde/ruines.json.gz` + `za_p66_ruines_donnees.sk`.
- Vérification statique : `python3 docs/outils/verif_skript.py plugins/Skript/scripts/*.sk` (à lancer après chaque modif).
- Ce qu'il faut installer / tester : `docs/A_INSTALLER.md`.

## Monde généré (10 000 x 10 000, sans Lost Cities)
- `generateur_monde/` écrit directement les `.mca` (Anvil 1.20.1, DataVersion 3465) : `plan.py` (lieux, routes, lacs,
  graine 1250), `terrain.py` (relief, rivière, biomes), `monde.py` (remplissage, minerais, grottes, routes, végétation),
  `sites.py` + `batisse.py` (structures : ruines/autobus depuis `plugins/ZAMonde`, le reste construit avec
  `ZA_sources/ville`), `generer.py` (lanceur multiprocessus, reprise, `--vanille` pour tester sur un serveur vanilla).
- `generer.py` produit aussi `plugins/ZAMonde/placements.yml` (fichier du serveur, non versionné) et
  `za_p73_sites_donnees.sk` (versionné, généré : ne pas modifier à la main). Module de jeu : `za_p73_sites.sk`.
- Lost Cities retiré de l'overworld : `world/serverconfig/lostcities-server.toml` `selectedProfile = ""`.
- Ville moddée : `ZA_sources/ville/blocs_mods.json.gz` (extrait des jars par `extraire_blocs_mods.py`) permet à
  `za_blocs.S()` d'accepter les blocs moddés (propriétés partielles) ; `za_meubles.py` (meubles) et `za_moderne.py`
  (toits, clôtures, grilles, pavés). `ZA_VANILLE=1` = ville vanilla d'origine. Après régénération : recopier dans
  `plugins/ZAMonde/` puis relancer `gen_ruines.py`.

## Façon de travailler
- Commits petits et clairs, en français, poussés sur GitHub pour que Colin puisse récupérer et tester.
- Avant de créer une commande, variable, fonction ou événement : grep dans tous les `.sk` et les `.yml` MythicMobs.
