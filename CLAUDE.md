# ZombieApocalypse — serveur Minecraft (Arclight 1.20.1)

Serveur de survie zombie francophone (Québec). Propriétaire : Colin. Tout le texte vu par les joueurs est en
**français avec accents** ; commentaires de code en français, courts.

## Mission en cours
Lire **[MISSION.md](MISSION.md)** en entier avant tout travail. Elle fixe l'objectif (Saint-Aurèle : une ville normale
qui tombe sous les yeux du joueur), l'ordre obligatoire des 15 phases et le format du rapport de fin de phase.
Phase 1 = analyse seule, aucune modification.

## Pile technique
- `arclight-5dc8683.jar` : Forge 1.20.1 + API Bukkit/Spigot dans le même serveur.
- Skript 2.9.5 : presque toute la logique de jeu (`plugins/Skript/scripts/za_*.sk`, 136 fichiers).
- MythicMobs 5.7.2 : zombies et PNJ (`plugins/MythicMobs/Mobs|Skills|Items|RandomSpawns/`).
- Plugin maison `plugins/ZAMonde.jar` : ville, PNJ, props, HUD, caméras (données dans `plugins/ZAMonde/`).
- ~64 mods Forge (liste et SHA-1 dans [JARS.txt](JARS.txt), dont 16 mods décoratifs Macaw's / Handcrafted / Supplementaries / Create Deco utilisés par la ville, et des add-ons Create : voir docs/A_INSTALLER.md §6 bis ; Design Decor 0.4.0b et Create D&D 0.1b sont INCOMPATIBLES avec Create 6), configs dans `config/`, `defaultconfigs/`, `world/serverconfig/`.
- Datapacks : `world/datapacks/za_*`.

## Moteur du monde ZAMoteur (bible `docs/ZA_BIBLE_CONCEPTION.md`, v2)
- Plugin Java séparé (ZAMonde ne peut pas être recompilé ici) : sources `moteur/src/za/moteur/`, jar versionné
  `plugins/ZAMoteur.jar`, données `plugins/ZAMoteur/` (`graphe.yml` généré par `generateur_monde/exporter_graphe.py`,
  `reactions.yml` = règles de réaction lisibles). Compilation : `sh moteur/build.sh <spigot-api-1.20.1.jar>`
  (javac --release 17, aucune autre dépendance). Paquet `za.moteur.coeur` sans Bukkit : simulateur hors ligne
  `java -cp moteur/build/classes za.moteur.coeur.Simulateur plugins/ZAMoteur/graphe.yml 60 4 plugins/ZAMoteur/reactions.yml`.
- Pont : Skript → moteur par `zam ...` (console), moteur → Skript par `zaevt ...` (`za_p103_moteur.sk`) ; le moteur écrit
  `{za::mot::<clé>}` par `zaevt set`. `za_mot_actif()` avant tout envoi. `za_mot_evt(type, lieu, grav, acteurs, texte)`
  publie dans la Chronique (`za_monde_evt` de p62 le fait déjà).
- Contenu : Chronique (F2, importance 0-100), graphe et régions (F3), hordes virtuelles + matérialisation (F4),
  télémétrie (F5), simulateur (F6), information (F9 : /infos, /signaler), mémoire et relations (F10), Directeur (IA-1),
  cerveaux des zombies (IA-2/3/5), Némésis (IA-4), génome régional (IA-6), NORDA (IA-11), Léa (IA-12), écosystème (IA-13),
  bases vivantes + cerveau des survivants (IA-15/IA-8, `za_p104_bases_vivantes.sk`, /communaute), factions + économie
  (IA-10/S-3), Ω facultatif (IA-16, désactivé, clé d'API). Admin : `/zaadmin`.
- MythicMobs `Mobs/ZA_Norda.yml` : agents NORDA (tag `za_norda`), zombies de saison, chiens infectés.
- Systèmes de jeu v2 : `za_p105_corps` (/etat), `za_p106_compagnons` (/garde), `za_p107_social` (/promesse, /accord,
  /avis, /station), `za_p108_terrain`, `za_p109_science` (/recherche, /marchenoir, /plans), `za_p110_defense_soins`
  (barricades `{za::barr::*}`, /sang), `za_p111_secrets` (infecté caché, /proie, /deserteurs), `za_p112_reconquete`
  (/reprise `{za::reprise::*}` — pas `{za::rep::*}` qui est la réputation ; /base abandonner `{za::aband::*}`),
  `za_p113_commerce_ombre` (faux remèdes = donnée de modèle 7, /frigo, /peage), `za_p114_aide` (aide adaptative),
  `za_p115_justice` (prison, /proces), `za_p116_campagne` (chapitres, décisions `za_cmpg_decision`, poids du vote p80 ;
  `{za::cmpg::*}`, pas `{za::camp::*}` qui est aux camps), `za_p117_camps_politique` (disputes, quarantaine des camps),
  `za_p118_cassettes` (textes en attendant les voix de za_modeles), `za_p119_barrage_colonnes` (`{za::digue::*}`, colonnes
  `{za::col::*}` ; `za_elec_pres` de p61 consulte le barrage), `za_p120_semer` (fumigène, tag `za_fumee`),
  `za_p121_offensives` (offensives de territoire `{za::off::*}`, JcJ permis entre les camps), `za_p122_ville_classement`
  (/ville, /classement, /zaredemarrer), `za_p123_ombres` (témoins `{za::tem::*}`, filature `{za::filat::*}`, opérations
  NORDA `{za::nop::*}`), `za_p124_chairs` (démembrement, mutation : tags `za_rampant`, `za_sansbras`, `za_odeur_morte`,
  `za_camouflage`), `za_p125_catastrophes2` (effondrements, dépôt de carburant), `za_p126_liens` (branchements :
  convois escortés ou pillés, faction détruite, hôpital et médicaments), `za_p127_societe_base` (liens entre survivants
  `{za::soc::*}`, /liens).
- **Règle de l'équipe** : un système n'est pas fini tant qu'il n'interagit pas avec les autres. Tout événement publié
  (`za_mot_evt`) doit avoir une conséquence (règle de `reactions.yml`, règle de mémoire ou traitement du moteur).
  Vérifier : `python3 docs/outils/verif_liens.py` (liste les impasses). Liste et tests : docs/A_INSTALLER.md §12.

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
- LISEZMOI.txt annonce 41 scripts : il y en a 136.
- Colin utilise Java 25 en local, alors que le serveur exige Java 17 ou 21.
- Erreurs vues sur le vrai serveur (Skript 2.9.5), détectées par `verif_skript.py` :
  - `loop-index-N` n'existe pas (« There's no loop that matches ») : `loop indices of {_x::*}:` puis
    `set {_i} to loop-value-N` et lire `{_x::%{_i}%}`.
  - `push X horizontally towards Y` n'est pas compris : calculer dx/dz, normaliser, puis
    `add vector(dx * v, 0, dz * v) to velocity of X`.
  - Argument `<number>` comparé à du texte (`if arg-2 is "hache"`) : « Can't compare a number with a text ».
    Déclarer `<text>` et utiliser `(arg-2 parsed as number) ? 0` là où il sert de nombre.

## Travail des phases 2 à 15 (voir docs/RAPPORTS_PHASES.md)
- Nouveaux modules : `za_p61_electricite` (sous-stations Create/CCA/IE), `za_p63_echos` (personnages du prologue),
  `za_p65_zombies_vivants`, `za_p66_ruines` (+ `_donnees`, généré), `za_p67_diplomatie`, `za_p68_cours`,
  `za_p69_exploration` (dossier Arel), `za_p70_ondes` (bulletin de Léa, téléphone), `za_p71_chronique`, `za_p72_archives`, `za_p73_sites` (lieux du monde généré), `za_p74_aube` (retraite au nid à l'aube, réveil
  au crépuscule ; aucun monstre ne brûle : `za_p32_soleil` ; infectés de zombie_extreme : datapack `za_aube`),
  `za_p75_defense` (soldats de la milice, `MythicMobs/Mobs/ZA_Defense.yml`), `za_p76_routes` (hordes de la nuit sur les
  routes), `za_p77_souterrains`, `za_p78_hiver` (Serene Seasons), `za_p79_meute` (portes, pyramide, ralliement),
  `za_p80_fin_norda` (vote de fin de saison /choix), `za_p81_guide` (/fil, dix premières minutes),
  `za_p82_evolution` (niveaux du virus 1-5, `Mobs/ZA_Evolution.yml`), `za_p83_boss_regionaux` (Boucher, Matriarche,
  Gardien, Brûlé : `Mobs/ZA_BossRegionaux.yml`, `Items/ZA_Legendaires.yml`), `za_p84_refuges`, `za_p85_radio`
  (fréquences cachées, silence radio : `za_sans_signal`), `za_p86_stress` (stress, poids), `za_p87_territoires_morts`
  (`{za::tmort::*}`, pas `{za::terr::*}` qui est aux factions p45 ; nature qui reprend), `za_p88_cimetiere`,
  `za_p89_familles` (/monhistoire), `za_p90_infra` (/infra, /ligne, panne en cascade), `za_p91_ambiances`
  (particules régionales, cinématiques « première fois »), `za_p92_equipe` (survivants commandables : fiches
  `{za::surv::<id>::st::*}`, missions réelles `{za::eq::m::<id>::*}`, postes ; branché dans za_p43 et za_p61),
  `za_p93_destins` (quêtes à conséquences différées), `za_p94_disparitions`, `za_p95_ombre` (espionnage, double jeu,
  taupes), `za_p96_carte` (/macarte ; `{za::carte::<uuid>::*}` ; /carte reste la chasse au trésor de p54),
  `za_p97_quartiers` (états des zones), `za_p98_incendies`, `za_p99_eclairage` (/lumiere ; p66 appelle
  `za_lum_quartier_on`), `za_p100_apparences` (équipes ETF za_contamine/za_brule/za_givre, sons positionnés),
  `za_p101_epoques` (identité des saisons), `za_p102_musee`.
- Mod client : `pack_joueurs/za_modeles-1.8.0.jar` = `extension_1_8.py` (variantes ETF selon équipe, santé, biome ;
  animations rares) sur le jar 1.7.0 = `extension_1_7.py` (boss `zamodels_boss.py`, zombies mutés, états
  ETF des humains frais/décomposé/mutilé, voix `lea_evo_*`) sur le jar 1.6.0 = `extension_1_6.py` (voix de synthèse, `voix_generer.py` : Piper
  + filtre radio) sur le jar 1.5.0 = `extension_1_5.py` (silhouettes : mâchoire, côtes, vertèbres,
  bras cassé ; peaux humaines 64x96) sur le jar 1.4.0 (git) = `build.py` (16 zombies de base, peintre `zagen_lib.py`) +
  `extension_1_4.py` sur le jar 1.3.0 (passe horreur des peaux humaines, animations, sons).
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
  Aussi : `epaves.py` (exode, carambolages, convois), `souterrains.py` (NORDA -2, bunker Bravo, tunnels ; vide de
  structure), `signalisation.py` (panneaux), bâtiments de village dans `batisse.py` (école, clinique, caserne).
- **Villes** (`ville.py`, conseil des 4) : ville → quartiers → routes hiérarchisées (avenues décalées, T, impasses,
  rail, rond-point, métro) → îlots → recettes → bâtiments (`ville_bat.py` + `batisse.py`) → sort d'apocalypse par quartier.
  `VILLES` (6) : Laurentia (métropole, -1800/3600, A-20 surélevée), Saint-Rémi-de-la-Voie (industrielle, passage
  inférieur), Sainte-Agathe-des-Champs (résidentielle), Fort-Laflèche (garnison, 3400/3100), Mont-Lévis (universitaire,
  -3000/3100), Saint-Jacques-des-Ponts (rivière Blanche, 1900/1300, `y` forcé à 64 : eau locale 61 = 62 du monde ;
  sites `garder_riviere` dans `terrain.py`). `AUTOROUTES` : autoroute 20 (z 3600). Construite une fois puis découpée en
  sites `ville_tuile` de 240 ; quartiers dans `plan['quartiers']` (lignes `quartier` de p73, zones p97 `v_<id>`, lieux
  `quartier_<genre>` du graphe). `generer.py` écrit `za_p128_villes_donnees.sk`. Jeu : `za_p128_villes.sk` (`/zavilles`).
  Aperçus : `docs/apercus/`. Installation : A_INSTALLER §13.
- Lost Cities retiré de l'overworld : `world/serverconfig/lostcities-server.toml` `selectedProfile = ""`.
- Ville moddée : `ZA_sources/ville/blocs_mods.json.gz` (extrait des jars par `extraire_blocs_mods.py`) permet à
  `za_blocs.S()` d'accepter les blocs moddés (propriétés partielles) ; `za_meubles.py` (meubles) et `za_moderne.py`
  (toits, clôtures, grilles, pavés). `ZA_VANILLE=1` = ville vanilla d'origine. Après régénération : recopier dans
  `plugins/ZAMonde/` puis relancer `gen_ruines.py`.

## Façon de travailler
- Commits petits et clairs, en français, poussés sur GitHub pour que Colin puisse récupérer et tester.
- Avant de créer une commande, variable, fonction ou événement : grep dans tous les `.sk` et les `.yml` MythicMobs.
