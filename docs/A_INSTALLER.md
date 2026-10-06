# À faire demain matin — installation et tests

Aucun **plugin** à ajouter. Côté **mods** : les 16 mods décoratifs que tu m'as envoyés sont maintenant utilisés par la
ville (section 6) : à mettre sur le serveur et dans le pack des joueurs, avec le mod client `za_modeles` 1.6.0.

**Nouveau monde de 10 000 × 10 000 entièrement généré par moi** (pas de Lost Cities) : section 9. C'est la plus grosse
étape de demain matin : environ 15-60 minutes selon ton PC, à faire serveur arrêté.

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
2. Regarde la console au démarrage : Skript affiche `Loaded 88 scripts`. S'il y a des lignes **error**, copie-les
   moi dans la prochaine session : je corrige.
3. MythicMobs se recharge au démarrage (sinon `/mm reload`) : 6 nouveaux zombies (`ZA_Policier_Infecte`,
   `ZA_Medecin_Infecte`, `ZA_Ouvrier_Infecte`, `ZA_Ouvrier_Brule`, `ZA_Pompier_Infecte`, `ZA_Prisonnier_Infecte`).
4. Java : le serveur exige Java 17 ou 21 (pas 25).

## 3. Mettre à jour le pack des joueurs (CurseForge)

1. Dans ton projet de modpack CurseForge, dossier `overrides/mods` : **remplace** l'ancien `za_modeles-1.x.jar` par
   `pack_joueurs/za_modeles-1.8.0.jar` (dans le dépôt).
2. Monte la version du pack (ex. 1.4), exporte, publie. Les joueurs mettent à jour leur pack.
   Sans la 1.6.0, les nouveaux zombies ont l'apparence de base et les nouveaux sons sont muets (pas de plantage).

## 4. Poser Saint-Aurèle en ruines (une seule fois)

> **Avec le nouveau monde (section 9), saute cette section** : le générateur pose déjà les ruines au centre de la carte,
> et `/zasites installer` les branche. Cette section ne sert que si tu gardes l'ancien monde.

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
| Zombies | `/mm mobs spawn ZA_Policier_Infecte` | uniforme, yeux qui luisent dans le noir (mod 1.6.0) |
| Scènes rares | `/zazv scene regard <toi>` | un zombie te fixe |
| Ruines | marcher dans la ville | titre « Population : 0 », souvenirs, mot de Maman dans le coffre du 2A |
| Lampes | `/zaville lampes hopital on` | les lampadaires de l'hôpital s'allument |
| Dossier Arel | clic droit sur le menu du Café du Coin, puis la porte de la chambre 104, etc. | documents datés, casier 0731 |
| Factions | `/faction diplomatie`, `/zadiplo stock milice munitions 0`, `/zadiplo jour`, `/faction contrats` | contrat publié |
| Cours | `/cours`, `/zacours set munitions 1.5`, ouvrir le Trafiquant | prix x1,5 |
| Téléphone | `/zatel <toi> donner`, `/telephone` | menu, SMS, appels |
| Chroniques | `/zasaison enregistrer`, `/chroniques <n> 2` | lignes Personnages / Réseau / Saint-Aurèle |

## 6. Ville « full custom » : les 16 mods décoratifs (FAIT le 30 sept.)

Tu m'as envoyé 16 mods : Macaw's (Doors, Windows, Fences, Roofs, Furniture, Paths, Lights, Bridges, Stairs,
Trapdoors, Paintings), Create Deco, Handcrafted (+ Resourceful Lib), Supplementaries (+ Moonlight). Les dépendances
sont toutes présentes et Create Deco accepte ton Create 6.0.8. Liste exacte + SHA-1 : `JARS.txt`.

**Saint-Aurèle utilise maintenant ces blocs** (prologue, ruines, Hall des survivants) :
- intérieurs : chaises, tables, canapés, bureaux, commodes, lits, fours de **Handcrafted** ; éviers, armoires de
  cuisine, tabourets de **Macaw's Furniture** ; portes modernes / vitrées / d'hôpital de **Macaw's Doors** ;
- extérieur : toits **Macaw's Roofs**, clôtures à piquets **Macaw's Fences**, trottoirs en pavés et allées du parc en
  dalles **Macaw's Paths**, grilles industrielles **Create Deco**.

**Donc ces mods deviennent obligatoires, sur le serveur ET dans le pack des joueurs** :
1. Copie les 16 jars dans `mods/` du serveur (tu les as déjà sur ton PC).
2. Ajoute-les au modpack CurseForge (même versions), avec `za_modeles-1.8.0.jar`, puis publie.
3. Redémarre le serveur. Dans la console, cherche **« BlockData invalide »** (ZAMonde) : s'il y en a, copie-les moi.
4. **Reconstruis la ville du prologue** (elle a été posée avant les mods) : `/zamonde construire` puis attends la fin
   (`/zamonde etat`). Les joueurs en plein prologue verront la nouvelle ville au chapitre suivant.
5. Le Hall des survivants et les ruines prennent la nouvelle version à leur prochaine pose (`/zaville installer`).

**Retour arrière** si un mod pose problème avec Arclight : dans `ZA_sources/ville`, `ZA_VANILLE=1 python3
gen_ville.py --sans-apercus` régénère la ville 100 % vanilla (identique à l'ancienne, vérifié octet pour octet),
puis recopie `town.json.gz`, `layers.json` et `hall.json.gz` dans `plugins/ZAMonde/` — ou demande-le moi.

Pas encore utilisés (disponibles pour la suite) : Macaw's Lights, Bridges, Stairs, Trapdoors, Paintings,
Supplementaries. Les lampadaires restent vanilla car le blackout du prologue les éteint un par un.

Côté joueurs seulement (ambiance, facultatif) : **Sound Physics Remastered**, **AmbientSounds** (+ CreativeCore).
À éviter : **Fresh Animations** (écraserait les modèles de zombies de `za_modeles`).

## 6 bis. Add-ons Create (vérifiés le 30 sept.)

J'ai comparé chaque jar à ceux du serveur (SHA-1), lu ses dépendances et vérifié qu'il n'utilise aucune classe de
Create disparue dans **Create 6.0.8** (ta version).

**✅ À installer (serveur ET pack des joueurs)** — compatibles Create 6.0.8 :
Create Big Cannons 5.11.4 (+ Ritchie's Projectile Lib 2.1.1), Copycats+ 3.0.10, Create Connected 1.2.3,
Create Diesel Generators 1.3.12, Slice and Dice 3.6.0, Create Enchantment Industry 1.4.1, Create Central Kitchen
1.5.1, Bells & Whistles 0.4.5, Interiors 0.6.0, Create New Age 1.2.0.

**⚠️ Il manque 2 bibliothèques** (sinon le serveur refuse de démarrer) :
- **Kotlin for Forge** ≥ 4.3.0 (pour Slice and Dice) — la version 4.x pour 1.20.1 ;
- **Energy Storage Lib 1.1.3** (modId `esl`, Antarctic Gardens) pour Create New Age — version **exactement** 1.1.3.

**❌ À NE PAS installer** — faits pour l'ancien Create 0.5, ils feraient planter le serveur au démarrage :
- **Design Decor 0.4.0b** (28 classes de Create introuvables dans 6.0.8) ;
- **Create: Dreams & Desires 0.1b Early Dev** (49 classes introuvables). Cherche des versions « pour Create 6 ».

**Doublons dans ce que tu m'as envoyé** (même fichier exact, n'en garde qu'un) : Ritchie's Projectile Lib (×2),
Create Big Cannons (×2), Slice and Dice (×2), Create Deco (×2). Déjà sur le serveur, rien à faire :
Create 6.0.8, Steam 'n' Rails 1.7.3, Create Crafts & Additions 1.3.3. ⚠️ Deux jars du même mod dans `mods/`
= le serveur ne démarre pas.

**Intégration au jeu (faite)** :
- Moteurs diesel (Diesel Generators) et générateurs / énergiseurs / moteurs (Create New Age) comptent comme vraies
  machines pour les sous-stations (`/electricite`) et pour le bruit des usines (`za_p17`).
- Toute explosion (obus de Create Big Cannons, TNT, creeper) s'entend de loin : activité + bruit pour les joueurs à
  60 blocs → les morts convergent. Un canon défend une base, mais il appelle la horde.

**Conseil Arclight** : ajoute ces mods **par petits groupes** et redémarre entre chaque, pour savoir lequel pose
problème s'il y en a un. Create Big Cannons : dans `world/serverconfig/createbigcannons-server.toml` (créé au premier
démarrage), pense à limiter la destruction de blocs si tu ne veux pas voir les ruines de Saint-Aurèle rasées.

## 6 ter. Zombies plus effrayants (mod 1.6.0)

- **Apparence** : peau cadavérique marbrée, ecchymoses, veines, plaies ouvertes, sang séché qui coule vers le bas,
  crasse aux jambes, orbites creuses, bouches arrachées. Les 15 zombies humains (citoyens, soldats, policier...) ont
  des **pupilles laiteuses qui luisent dans le noir**, une larme de sang, une joue ouverte et une morsure au cou.
- **Silhouettes (1.5.0)** : mâchoire qui pend et claque à l'attaque (citoyen, soldat, médecin, prisonnier, Dumas...),
  côtes à l'air, colonne vertébrale qui sort du dos (patient, Dumas), bras gauche cassé qui pend à l'envers avec l'os
  qui perce (citoyen, soldat, policier, pompier). Mme Gagnon reste reconnaissable.
- **Animations** : le cou **craque d'un coup** sur le côté, la tête part en avant pour **mordre**, recul quand il
  prend un coup, bras qui s'agitent en mourant ; un humain immobile te **fixe** sans bouger la tête.
- **Capacités** (`plugins/MythicMobs/Skills/ZA_Horreur.yml`) : des mains t'**agrippent** (shambler, citoyen,
  patient), le rampant t'**attrape la cheville** (impossible de sauter), **frénésie** sous 30 % de vie, **charge** du
  soldat et de la brute, **bond** du prisonnier, **sprint** du runner, **murmure** du stalker (+ obscurité),
  matraque du policier (sonné), **seringue** du médecin (poison + risque d'infection), clé à molette de l'ouvrier
  (projeté), hache du pompier (qui ne brûle plus).
- À faire : `/mm reload` (ou redémarrage) et mettre `za_modeles-1.8.0.jar` dans le pack des joueurs (section 3).

## 6 quater. Le jour : les morts ne brûlent pas, ils rentrent au nid

- **Aucun monstre ne brûle au soleil** : zombies MythicMobs (`PreventSunburn`), et `za_p32_soleil.sk` couvre
  maintenant tous les monstres vanilla (zombies, noyés, squelettes...).
- **À l'aube** (5 h à 7 h du jeu, `za_p74_aube.sk`) : les zombies ordinaires à ciel ouvert et loin des joueurs
  (plus de 24 blocs) disparaissent dans un nuage de fumée et **rentrent au nid** le plus proche. Ceux qui sont près
  d'un joueur restent, **éblouis** (lents et faibles 5 min). Ceux qui chassent quelqu'un ne lâchent pas. Ceux qui sont
  **à l'abri** (bâtiments, grottes) restent : explorer de jour reste dangereux. Boss, nids, PNJ, Phototropes : jamais.
- **Au crépuscule** (18 h 30) : chaque nid relâche ceux qui y ont dormi (8 max par soir), Léa prévient à la radio.
- Test : `/time set 23500` (juste avant l'aube) près de quelques zombies dehors, attends ~30 s, puis `/zaaube`
  (compteur). `/zaaube aube` et `/zaaube crepuscule` forcent chaque moment.

## 6 quinquies. Défendre sa base : soldats et tourelles

- **Soldats de la milice** (`za_p75_defense.sk`, `MythicMobs/Mobs/ZA_Defense.yml`) : `/garde recruter [arbalete|hache]`
  à ta base (40 ou 30 jetons, 3 max). Ils tiennent leur poste (`/garde poste`), tirent sur tous les morts (zombies
  MythicMobs, vanilla, zombie_extreme), jamais sur les joueurs, se soignent lentement. S'ils tombent, tu es prévenu.
  `/garde liste`, `/garde renvoyer <n°>`.
- **Tourelles** (`za_p16_tourelles.sk`) : visent le mort le plus proche ; **niveaux** (accroupi + clic droit avec
  2 Composants électroniques : niveau 2 = 18 blocs, 2 cibles ; niveau 3 = 22 blocs, 3 cibles, 6 dégâts) ;
  **alimentées** par une sous-station à 48 blocs : plus besoin de flèches.
- Test : `/base definir`, `/jetons` si besoin, `/garde recruter`, puis `/mm mobs spawn ZA_Shambler` à 15 blocs.
- À vérifier en jeu : la faction `ZA_Milice` et le sélecteur `otherfactionmonsters` de MythicMobs 5.7.2 (si les
  soldats restent passifs, me le dire : je passerai à `monsters`).

## 6 sexies. Le monde s'agrandit (villages, routes, souterrains, hiver) et l'histoire se referme

Tout ce qui suit est dans le générateur (section 9) ou dans les scripts : rien à installer en plus, sauf le mod 1.6.0.
- **Villages** : chaque village a maintenant une **école** (enfants infectés), une **clinique** (patients, médecin),
  une **caserne de pompiers** (camion rouge, pompiers), une église, un dépanneur, un casse-croûte, un garage : chacun
  a son nom à l'entrée et ses zombies.
- **Routes** : **l'exode** (200 blocs de bouchon vers Montréal sur la 40), 9 **carambolages** (panneaux ACCIDENT),
  3 **convois militaires** (camions, caisses de butin militaire, sacs de sable). **La nuit**, des files de morts
  arrivent par la route et foncent sur les joueurs proches (`za_p76_routes.sk`, test : `/zaroute horde <joueur>`).
- **Souterrains** (`za_p77_souterrains.sk`) : **NORDA — niveau -2** (kiosque « ACCÈS TECHNIQUE » à l'est du campus :
  labos, cellules de confinement du programme Z-01), **bunker de commandement Bravo** (kiosque à l'est de la base :
  commandement, dortoir, armurerie, infirmerie), **tunnels de service de Saint-Aurèle** (6 bouches d'égout = trappes
  en fer dans les rues des ruines, canal d'eau, station de pompage). Dans le noir, les morts naissent dans les couloirs.
- **Hiver** (`za_p78_hiver.sk`, avec Serene Seasons) : neige qui s'accumule (3 à 5 couches), **rivière Blanche qui
  gèle** (on la traverse à pied), morts ralentis dehors, froid dans la température corporelle, Léa annonce la première
  neige et le dégel. `/zahiver` (état), `/zahiver forcer 10` (tester le cœur de l'hiver), `/zahiver forcer` (annuler).
  À vérifier : la commande `season set early_winter` de Serene Seasons (si la console dit « unknown », me le dire).
- **La meute** (`za_p79_meute.sk`) : les morts **cognent aux portes** jusqu'à ce qu'elles cèdent (une porte renforcée
  tient plus longtemps), **montent les uns sur les autres** si tu es en hauteur, **convergent** quand l'un d'eux mord.
- **Fin de saison** (`za_p80_fin_norda.sk`) : après la cérémonie, cinématique + **vote de tous les joueurs** (`/choix
  detruire|verite|remede`, 10 min) avec de vraies conséquences (NORDA scellé et moins de mutants / titre « Témoin » /
  morsures moins contagieuses et un antidote chacun). Test : `/zafin test`, puis `/choix ...`, puis `/zafin resultat`.
- **Les dix premières minutes** (`za_p81_guide.sk`) : un fil discret en barre d'action (flèche + distance + boussole)
  de l'autobus jusqu'à l'appartement 2A, puis vers un abri. `/fil off` pour le couper.

## 6 septies. Le niveau supérieur (scripts p82 à p91, mod 1.7.0)

Après `/mm reload` (ou redémarrage) et la mise à jour du pack joueurs en **1.7.0** :
- **Évolution du virus** (`za_p82`) : `/evolution` ; admin `/zaevo etat|niveau <1-5>|points`. Variants mutés et Colosse.
- **Boss régionaux** (`za_p83`) : Boucher (parc industriel), Matriarche (hôpital), Gardien (bunker Bravo), Brûlé
  (barrage). `/lieutenants` ; admin `/zaregboss etat|reveiller <id>|oublier <id>`. Objets légendaires en récompense.
- **Refuges** (`za_p84`) : `/refuges` ; admin `/zarefuge etat`. **Radio** (`za_p85`) : `/frequence <valeur>|liste|off`,
  silence radio dans les souterrains, zones mortes et NORDA ; admin `/zafreq <joueur> tout|reset`.
- **Stress et poids** (`za_p86`) : `/stress`, `/poids`. **Territoires** (`za_p87`) : `/zones` ; admin `/zamorts`.
- **Cimetière** (`za_p88`) : `/cimetiere`, `/epitaphe <texte>`. **Familles** (`za_p89`) : `/monhistoire [2]` ;
  admin `/zafamille <id survivant>`.
- **Infrastructures** (`za_p90`) : `/infra construire mirador|tour|infirmerie|antenne`, `/ligne couper|retablir|saboter|deriver|liste`.
- **Ambiances et cinématiques** (`za_p91`) : `/ambiance on|off` ; admin `/zacine tue|horde|alpha|norda <joueur>`.
- **Apparences (1.7.0)** : 4 boss avec modèle et peau propres, zombies mutés aux veines qui luisent, et les zombies
  humains tirés au hasard entre 4 états (décomposé, frais, très décomposé, mutilé). Nécessite ETF (déjà requis par EMF).

## 6 octies. Équipe, destins, enquêtes, ombre, carte, quartiers, époques, musée (scripts p92 à p102, mod 1.8.0)

- **Équipe** (`za_p92`) : clic droit sur un survivant de ta base -> « Donner une tâche » / « Sa fiche ». `/equipe`
  (liste), `/equipe tache <nom> bois|nourriture|plantes|materiaux|minerais|recon|recup|cherche|suivre|rentrer [zone]`,
  `/equipe ou <nom>`, `/equipe zone <nom>`, `/equipe priorite <nom> bois nourriture`. Postes : scierie (scie mécanique
  Create à 16 blocs du centre de la base), ferme, mine, entretien électrique, radio, patrouille, cuisine, intendance.
  Admin : `/zaequipe liste|fin <id>|incident <id>`. Nouveaux métiers : bûcheron, mineur, policier.
- **Destins** (`za_p93`) : `/destins`, `/destins accepter|refuser|payer`. Admin : `/zadestin lancer <frere|convoi|emilie|cache|dette> <joueur>`,
  `/zadestin suite <joueur>` (fait arriver les conséquences tout de suite).
- **Disparitions** (`za_p94`) : `/disparition`, `/disparition conclure <1-3>`. Admin : `/zadisp lancer <joueur> [fui|mort|enleve|norda|trahison]`.
- **L'Ombre** (`za_p95`) : `/ombre`, `/ombre prendre <n>`, `designer <n>`, `infiltrer <faction>`, `sortir`, `forger <faction>`,
  `enqueter`, `suspects`, `accuser <nom>`. Admin : `/zaombre offres <joueur>|taupe <id> <faction>`.
- **Carte** (`za_p96`) : `/macarte`, `/macarte large|liste|livre`.
- **Quartiers, incendies, éclairage** (`za_p97-99`) : `/quartiers`, `/incendies`, `/lumiere lier|delier`.
  Admin : `/zaquartier etat|set <zone> <état>|pression <zone> <n>|jour`, `/zafeu allumer|eteindre <id>`.
- **Apparences et sons** (`za_p100`) : `/sons off|on`. **Ajoute Sound Physics Remastered au pack des joueurs** : il donne
  l'écho des tunnels, les sons étouffés derrière les murs et la réverbération des rues à tous les sons.
- **Époques** (`za_p101`) : `/epoque`. Admin : `/zaepoque evenement|affiches|annonce`.
- **Musée** (`za_p102`) : l'admin le pose avec `/zamusee installer` (là où il se tient ; 21 x 15 vers l'est et le sud,
  terrain plat conseillé, par exemple près du parc de Saint-Aurèle). Joueurs : `/musee`, `/musee donner`.
- **Mod 1.8.0** : variantes de peau (contaminé, brûlé, blessé sous 40 % de vie, givre avec tuque, boue, chemise à
  carreaux à la campagne) et animations rares. Remplace la 1.7.0 dans le pack des joueurs.

## 7. Voix (FAIT : voix de synthèse)

Les entractes des jours 2, 4 et 6, les annonces de l'hiver et des nids, et toute la fin de saison ont maintenant une
**voix de Léa** (synthèse Piper, voix « siwis », passée dans un filtre radio : bande étroite, souffle). Elles sont dans le
mod 1.6.0 (`voix.radio_j2`, `voix.fin_intro`...). Si tu enregistres de vraies voix plus tard, garde les mêmes noms de
fichiers : `ZA_sources/modeles_generateur/extension_1_6.py` les remplace.

## 8. Ce qui n'a PAS été testé

Tout ce qui est en jeu : chargement réel des 109 scripts par Skript, les commandes, la pose des ruines, les modèles
et animations EMF du mod 1.6.0, les capacités MythicMobs de `Skills/ZA_Horreur.yml`, les soldats (`Mobs/ZA_Defense.yml`, faction
et sélecteur de cibles), les silhouettes 1.5.0 (sous-modèles mâchoire / avant-bras), la commande `season set` de Serene
Seasons, les poussées de la pyramide et les portes qui cèdent, les sons, la lecture de la redstone des machines Create/CCA/IE par Skript sur
Arclight. Le détail des risques est dans `docs/RAPPORTS_PHASES.md`, phase par phase.

## 9. Le nouveau monde : la région de Saint-Aurèle (10 000 × 10 000)

Tout le terrain est généré par un programme Python du dépôt (`generateur_monde/`) qui écrit **directement les fichiers
de région** (`world/region/r.X.Z.mca`). Minecraft ne génère rien : il lit ce qui est déjà là.

**Ce qu'il y a dedans** (carte : `docs/carte_region.png`) :
- **Relief québécois** : Laurentides au nord (sommets enneigés), plaines agricoles au sud, la **rivière
  Blanche** qui traverse la carte d'ouest en est, 11 lacs, le réservoir en amont du barrage. 11 biomes vanilla aux
  lisières naturelles, forêts d'épinettes, de bouleaux et de chênes, marais.
- **Sous terre** : grottes en tunnels, lave profonde, minerais vanilla + **zinc (Create)** + **aluminium, plomb, argent,
  nickel, uranium (Immersive Engineering)** pour que l'électricité (Create / IE) se construise avec ce qu'on trouve.
- **Routes** : l'autoroute 40 (4 voies, ligne jaune, ponts sur la rivière), la route 117, le Chemin du Lac, le
  Rang Saint-Aurèle et un chemin vers chaque lieu. Voitures abandonnées dans les villages.
- **Panneaux routiers** (47) : « SORTIE 117 » sur l'autoroute, « SAINT-AURÈLE — tout droit » à côté de l'autobus,
  « Bienvenue à Saint-Aurèle » suivi d'un avis de **QUARANTAINE** aux deux entrées de la ville, et un panneau avec le
  nom et la distance à l'entrée du chemin de chaque lieu (base Bravo « ACCÈS INTERDIT », NORDA, barrage, fermes...).
- **Lieux** (tous abandonnés, vitres brisées, lierre, lampes éteintes, coffres avec butin) :
  - au centre (0, 0) : **Saint-Aurèle en ruines** (la ville du prologue, 288 × 288) ;
  - l'**autobus du Jour 8** (point d'apparition, x 641 z 299) ;
  - la **base Bravo** (militaire) à l'ouest ; **NORDA Biotech** au nord-est ; le **barrage** de la Rivière-Blanche ;
  - le **parc industriel** ; l'**émetteur CKZA** dans les montagnes ; la **carrière** ; un **motel** ;
  - 3 villages (**Val-des-Pins**, **Rivière-Blanche**, **Sainte-Brigitte**), 4 stations-service, 2 barrages routiers ;
  - 18 fermes, 16 chalets au bord des lacs, 22 camps de chasse.
- En jeu (`za_p73_sites.sk`) : en entrant dans un lieu, son nom s'affiche (la 1re fois : titre + phrase d'ambiance +
  souvenir) ; chaque lieu a **ses zombies** (soldats à la base, blouses blanches à NORDA, ouvriers au barrage...).

### Marche à suivre (serveur ARRÊTÉ)

1. **Python 3** (3.10 ou plus) et **numpy** : `pip install numpy` (Pillow seulement pour l'image de la carte :
   `pip install pillow`).
2. Récupère les changements (section 1), puis extrais les sources : dans le dossier du serveur,
   `unzip -o ZA_sources_build.zip` (ou clic droit → Extraire ici). Il faut le dossier `ZA_sources/ville`.
3. **Sauvegarde puis mets de côté l'ancien monde** : renomme `world` en `world_ancien`, puis crée un dossier `world`
   vide et **recopie dedans** `world_ancien/datapacks` et `world_ancien/serverconfig` (butin, réglages des mods).
   Ne touche pas au monde `za_prologue` (le prologue, la ville « avant ») : normalement c'est un dossier
   `za_prologue` à côté de `world`. S'il était rangé dans `world` et disparaît avec le renommage, ZAMonde recrée
   le monde vide au démarrage : refais alors la ville avec `/zamonde construire` (à faire de toute façon, §6).
4. Lance le générateur depuis le dossier du serveur :
   ```
   python generateur_monde/generer.py
   ```
   Il affiche l'avancement (400 régions, ~8 s chacune par cœur de processeur : ~13 min sur 4 cœurs, ~7 min sur 8).
   Il faut ~1 Go de mémoire par cœur utilisé (limiter : `--processus 2`) et ~1,8 Go de disque.
   S'il s'arrête (erreur, PC éteint), **relance la même commande** : il reprend là où il en était.
   Il écrit aussi `plugins/ZAMonde/placements.yml` (position des ruines et de l'autobus, pour les POIs).
5. Démarre le serveur. Le Nether et l'End se recréent tout seuls.
6. En jeu (op) : **`/zasites installer`**. Il branche les ruines (lieux + 4 sous-stations endommagées), inscrit les
   73 lieux de la région dans la mémoire du monde (+ les 8 de la ville), met la **bordure à 10 000** (`worldborder`) et le **point d'apparition à
   l'autobus**. Vérifie : `/zasites` (état), `/zasites ici` (lieu où tu es), `/zaville` (ruines).
7. Lost Cities est **retiré de l'overworld** (`world/serverconfig/lostcities-server.toml` : `selectedProfile = ""`).
   Le mod reste installé (sa dimension séparée et la table de butin des coffres de ville restent).

**Attention aux anciennes données** : les joueurs qui avaient une partie gardent leurs coordonnées de l'ancien monde
(maisons, camps, bases dans `variables.csv`). Pour un vrai redémarrage, fais-le aussi pour eux (nouvelle saison).

**Retour arrière** : arrête le serveur, supprime `world`, renomme `world_ancien` en `world`, remets
`selectedProfile = "default"` dans `world/serverconfig/lostcities-server.toml`.

**Pas testé** : le générateur a été vérifié avec un **serveur Minecraft 1.20.1 vanilla** (régions chargées et
réenregistrées sans erreur, panneaux et coffres avec butin conservés), mais **pas avec Arclight et les mods** : les
blocs moddés (Macaw's, Handcrafted, Create, IE) sont écrits avec des identifiants que je n'ai pas pu tous vérifier
dans les jars (surtout les minerais d'IE). Un identifiant inconnu devient de l'air, sans planter. Regarde la console
au premier démarrage : des lignes « Unknown block » m'indiqueraient quoi corriger.

## 10. Le moteur du monde : ZAMoteur (bible de conception, F1 à F10, IA-1 à IA-16, S-3)

`docs/ZA_BIBLE_CONCEPTION.md` (version 2) décrit le serveur « extrême ». Sa fondation est un **plugin Java à part**,
`plugins/ZAMoteur.jar` (versionné dans le dépôt, sources dans `moteur/`). Il simule le monde **hors du fil principal**
(régions, hordes virtuelles, contamination, NORDA, factions, économie, informations, mémoire) et ne fait sur le fil
principal que les actions visibles, avec un budget par tick. Skript garde le contenu : les deux se parlent par la
console (`zam ...` vers le moteur, `zaevt ...` vers Skript, script `za_p103_moteur.sk`).

### Installation
1. `plugins/ZAMoteur.jar`, `plugins/ZAMoteur/graphe.yml` et `plugins/ZAMoteur/reactions.yml` arrivent avec le `git pull`.
   Rien à télécharger. Il faut MythicMobs (déjà là) ; Skript reste en 2.9.5.
2. Redémarre le serveur. Console : `ZAMoteur prêt : 100 régions, 95 lieux, 37 règles de réaction, 8 hordes.`
   Le plugin crée `plugins/ZAMoteur/config.yml` (systèmes on/off, budgets, plafonds, option Ω) et, toutes les
   5 minutes, `etat.yml`, `chronique.txt`, `informations.txt`, `memoire.txt`, `bases.txt`, `factions.txt`
   (copie de `etat.yml` chaque jour, sur 7 jours : `etat-jour0.yml` à `etat-jour6.yml`).
3. MythicMobs : `/mm reload` (nouveau fichier `Mobs/ZA_Norda.yml` : agents NORDA, zombies de saison, chiens infectés).
4. Si tu régénères le monde : `python3 generateur_monde/exporter_graphe.py` refait `plugins/ZAMoteur/graphe.yml`.
5. Pour recompiler le plugin (seulement si on modifie `moteur/src`) : `sh moteur/build.sh <chemin du spigot-api 1.20.1>`.

### Ce que les joueurs voient
- `/monde` : l'état de ta région (stable → perdue), l'eau, les nids, le courant, la quarantaine. `/zone` l'affiche aussi.
- **Rumeurs** : « [On dit] Une horde a attaqué près de Val-des-Pins (de bouche à oreille, il y a 40 min, 52 %) ».
  `/infos` (ce que tu sais, avec l'âge et la fiabilité), `/infos dire <joueur> <n°>`, `/signaler <ce que tu as vu>`.
- **Léa** choisit ses nouvelles dans la Chronique ; Bravo (104.2), la radio pirate et NORDA donnent leur version.
- **Némésis** : le zombie qui te tue prend ton casque, ton arme et un nom (« Shambler « le Faucheur de Val-des-Pins » »),
  et reviendra plus tard, ailleurs. L'abattre rend l'équipement et donne sa tête (titre « Le Revenant »).
- **NORDA** : `/norda` (ce que tu sens), drones qui tournent là où NORDA CROIT que tu es, barrages sur tes routes
  habituelles, contrôles, capture au palier 5 (cellule au niveau -2, `/interrogatoire verite|mentir|negocier`).
- **Bases vivantes** : `/communaute` (stocks, minimums, sorties, journal). Les survivants partent seuls quand un stock
  baisse (« J'irai demain matin »). À la connexion : « PENDANT TON ABSENCE ».
- **Factions** : convois sur les routes (qu'une horde peut attaquer : l'épave reste avec son chargement), blocus,
  traités, prix différents selon la région chez les marchands. `/regler` règle une affaire de vol (chaîne 14).

### Outils de Colin (`/zaadmin`, permission `za.admin`)
`directeur [joueur]` · `region [id|ici]` · `carte` · `hordes [creer N|attirer]` · `norda [joueur]` · `nemesis` ·
`simuler <jours> [fantômes]` (60 jours de monde en quelques secondes, test des freins) · `chaine <1-14>` (les chaînes
de la Partie 5) · `evt <type> [grav] [texte]` · `rapport` (télémétrie du jour) · `systeme <nom> on|off` ·
`reactions recharger` · `chronique [n]` · `sauver` · `cerveau` (regarde un zombie) · `memoire <clé>` ·
`relation <de> <envers>` · `savoir <clé>` · `legendes` · `base <joueur>` · `survivant <id>` ·
`factions [cycle|rompre <traître> <victime>]` · `prix [région]` · `omega`.

**Tester les chaînes** : place-toi quelque part et tape `/zaadmin chaine 1` (coup de feu → horde), puis suis avec
`/zaadmin chronique` et `/zaadmin region ici`. Les chaînes 9 à 14 : panne de génératrice, bûcheron (il faut une base,
une Réserve et des survivants), inondation, expédition d'hiver, blocus, rumeur.

**Régler sans programmer** : `plugins/ZAMoteur/reactions.yml` (« si tel événement, alors telle conséquence, avec telle
probabilité, après tel délai ») puis `/zaadmin reactions recharger`.

### Ω (facultatif, désactivé)
Léa peut écrire sa chronique du soir avec un vrai modèle de langage (bible IA-16). **Payant à l'usage**, séparé de tout
abonnement : il faut une clé d'API dans `plugins/ZAMoteur/config.yml` (`omega.cle`), puis `/zaadmin systeme omega on`.
Par défaut : Claude Haiku (`claude-haiku-4-5`), 40 appels par jour, 8 par joueur, réponses en cache. Option Gemini
(`omega.fournisseur: gemini`, version gratuite : Google utilise les échanges, serveur privé seulement). Seuls les
pseudos et les événements du jeu partent. Sans clé, rien ne sort du serveur.

### Pas testé
Rien de tout ça n'a tourné sur un vrai serveur (pas de serveur dans la session). Vérifié : compilation du plugin contre
l'API Spigot 1.20.1, simulateur hors ligne (60 jours, la carte se stabilise autour de 55 % de régions vertes), et le
vérificateur Skript (111 scripts). À surveiller en premier :
- que `/zaevt` et `/zam` passent bien par la console d'Arclight (s'il y a « Unknown command », me le dire) ;
- la matérialisation des hordes (`mm mobs spawn`) et le marquage des zombies apparus (tags `za_horde`) ;
- les leurres invisibles qui guident les zombies, les drones (Allay immobile, lumineux) ;
- `ProjectileLaunch`/`EntitySpawn` des balles TaCZ comme bruit ; la capture NORDA ;
- les performances : `/zaadmin rapport`, et `spark` si le serveur ralentit (`/zaadmin systeme cerveaux off` pour couper
  le plus gourmand).

## 11. Nouveaux lieux de la bible (points 28 à 31, 36, 86)

Le générateur ajoute **sans rien déplacer** (vérifié : les anciens lieux, routes et épaves sont identiques) :
l'**aéroport régional** (terminal où des survivants ont tenu, tour de contrôle avec sa radio, hangar à pièces de drones,
dépôt de carburant, avion écrasé au bout d'une traînée de débris, piste d'extraction), le **centre d'achat** Carrefour
Laurentides (boutiques, pharmacie, aire de restauration, cinéma plein de morts endormis, poste de sécurité, camp perdu),
l'**aréna** Gilles-Tremblay (patinoire avec des formes sous la glace, gradins), la **prison** (miradors, deux blocs
cellulaires, armurerie, levier qui ouvre toutes les cellules, traces de l'émeute des pillards), l'**université**
(labo de biologie civil, bibliothèque, résidences), le **port**, l'**hôtel**, trois **gares** reliées par la
**Ligne Laurentienne** (rails, tronçons arrachés), et des **ponts détruits** (route 117, voie ferrée, un chemin sur la
rivière) : passages obligés, aussi pour les hordes du moteur (`graphe.yml`, liens « pont_detruit »).
Chaque sous-lieu a son nom à l'entrée, sa phrase et ses zombies (za_p73 ; noyés au port, givrés sur la patinoire).

**À faire (serveur ARRÊTÉ, avant que les joueurs construisent dans ces zones)** : régénérer seulement les 47 régions
touchées (≈ 5 minutes) :
```
python3 generateur_monde/generer.py --forcer --regions=-8,-2/-8,-1/-8,0/-8,1/-7,-1/-7,0/-4,-5/-4,-4/-4,-3/-4,-2/-3,-2/-3,-1/-2,-2/-2,-1/-1,-2/-1,-1/-1,0/-1,1/0,-2/0,-1/0,0/0,1/0,2/0,3/1,-3/1,-2/1,-1/1,0/1,1/1,2/1,3/2,-3/2,-2/2,0/2,1/2,3/3,3/4,0/4,1/4,2/4,3/5,0/5,1/7,0/7,1/7,2/7,3
```
⚠️ Une région régénérée perd ce que les joueurs y ont construit. Ensuite, en jeu : `/zasites installer` (les nouveaux
lieux rejoignent la mémoire du monde). **Testé** : les dix structures se construisent sans erreur, deux régions
(gare de Saint-Aurèle + rails, pont détruit de la voie ferrée) générées sans erreur. **Pas testé** : le rendu en jeu, la
forme des rails dans les virages et les pentes, l'accès aux étages (échafaudages).
