# ZA — Bible de conception extrême

> Ce document décrit jusqu'où chaque système du serveur ZombieApocalypse peut aller.
> Il dit **quoi** construire. La feuille de route dira **dans quel ordre**.
>
> Version 1 — 1er octobre 2026. Écrit pour Colin et pour Claude Code.

## Comment lire ce document

- Les **117 points** gardent leur numéro pour toujours. On ne renumérote jamais : un point fusionné garde son numéro et renvoie à l'autre.
- Chaque point suit le même modèle :
  - **Aujourd'hui** : ce qui existe déjà dans les 88 scripts, les mods ou ZAMonde ;
  - **Extrême** : la version poussée au maximum ;
  - 🔗 : les systèmes avec lesquels il interagit ;
  - ⚠️ : la limite ou le risque à surveiller.
- Symboles :

| Symbole | Sens |
|---|---|
| 🧠 | IA, détaillée dans la Partie 2 |
| ⚙️ | Moteur du monde (Java, ZAMonde 2.0) |
| 📦 | Mise à jour du pack joueurs (`za_modeles`) |
| 🗺️ | Changement du monde (générateur ou structures ZAMonde) |
| ✍️ | Surtout de l'écriture (textes, dialogues, voix) |
| 🔍 | À vérifier avant de construire (mod, compatibilité Arclight) |

- Tous les chiffres (rayons, durées, plafonds) sont des **valeurs de départ**, à régler en jeu avec la télémétrie (F5).

## Les 12 grands bonds

Si on ne retient que douze choses de ce document, ce sont celles-ci :

1. **ZAMonde 2.0, le moteur du monde** (F1) : la simulation passe en Java, hors du fil principal. C'est la fondation de tout le reste.
2. **La Chronique** (F2) : tous les systèmes publient et écoutent les mêmes événements. C'est ce qui fait naître les chaînes de conséquences sans les écrire.
3. **Virtuel ↔ réel** (F4) : les hordes, PNJ et convois vivent comme des données partout sur la carte et n'apparaissent que près des joueurs.
4. **Le Directeur** (IA-1) : une IA invisible qui dose la peur de chaque joueur, comme un metteur en scène.
5. **Les sens et le cerveau des zombies** (IA-2, IA-3) : ils voient, entendent, sentent, cherchent, abandonnent.
6. **La Némésis** (IA-4) : le zombie qui t'a tué porte ton équipement, porte un nom et revient te chercher.
7. **L'évolution régionale** (IA-6) : chaque région a son propre « génome » de zombies, qui s'adapte à la façon de jouer des joueurs.
8. **Les hordes-agents** (IA-7) : chaque horde a un but, une mémoire et un moral.
9. **Les cerveaux des PNJ et le mensonge lisible** (IA-8, IA-9) : personnalité, mémoire, secrets, et des mensonges qu'on peut démasquer.
10. **NORDA, une IA qui croit des choses** (IA-11) : un adversaire intelligent mais limité, qu'on peut tromper.
11. **Léa journaliste** (IA-12) : la radio raconte ce que les joueurs font vraiment, avec des sources plus ou moins fiables.
12. **Le simulateur accéléré** (F6) : 60 jours de monde simulés en quelques minutes pour vérifier que rien ne s'emballe.

## Partie 0 — Les 10 règles qui ne changent jamais

1. **La map guérit, l'histoire n'oublie pas.** Contamination, danger, nids, hordes, courant, contrôle territorial et état des villes sont réversibles. Les morts importantes, la chute d'une ville, les choix narratifs, les décisions de faction et la fin de saison restent gravés jusqu'à la saison suivante. Une ville redevenue verte garde sa plaque « Chute de X — Jour 43 ».
2. **Les actions ont des conséquences, pas l'absence.** Un joueur qui part une semaine ne perd rien. Les bases enregistrées (`/base`) et les territoires de faction ne sont jamais la cible d'une invasion automatique. Les sièges continuent de se déclencher seulement quand un joueur est à moins de 80 blocs (règle actuelle de p8). Les points 67 et 70 visent seulement les refuges improvisés et les constructions non enregistrées ou abandonnées volontairement.
3. **Chaque gain a un coût.** Rétablir le courant, c'est la chirurgie et les frigos, mais aussi la lumière qui se voit de loin, le bruit des génératrices et une signature électrique pour NORDA.
4. **Deux attentions séparées.** Les zombies remarquent ce qui se sent : bruit, lumière, odeurs, sang, cadavres. NORDA remarque ce qui se capte : électricité, radio, téléphone, antennes, labos, caméras, témoins.
5. **Ce qui ne se voit pas n'existe pas.** Chaque système a au moins un signal pour le joueur : un son, un visuel, une phrase de PNJ, une ligne radio, une entrée du bestiaire ou une commande.
6. **L'IA ne triche jamais devant le joueur.** Pas d'apparition dans le champ de vision, pas de téléportation visible, pas de cible connue sans raison. Les zombies et NORDA agissent seulement sur ce qu'ils ont réellement perçu.
7. **Toute boucle qui s'emballe a un frein et un plafond.** Voir le point 80.
8. **Équité.** Les nouveaux sont protégés leurs premières heures. Le Directeur baisse la pression après des morts répétées. Aucune perte définitive au-delà de la saison, sauf la légende.
9. **Budget de performance.** Ce qui est loin des joueurs est virtuel. Chaque système a un plafond d'entités et un budget de temps par tick.
10. **Tout se teste.** Chaque système a une commande pour le forcer et l'inspecter (`/zaadmin`), et les chaînes de la Partie 5 servent de tests.

## Partie 1 — Les fondations (ce qui rend l'extrême possible)

### F1. ZAMonde 2.0 — le moteur du monde ⚙️

**Aujourd'hui** : ZAMonde est déjà un plugin Java (sources dans `ZA_sources/plugin/src/za/monde/`). Il sait déjà faire beaucoup plus que construire la ville :

- `Cameras` : cinématiques fluides (le joueur regarde à travers une entité invisible déplacée sur une courbe) ;
- `Npcs` : PNJ et MythicMobs « privés », qui marchent, regardent et s'animent ;
- `Privacy` + `PacketHider` : des entités visibles par **un seul joueur** ;
- `Overlay` : des **blocs factices par joueur** (calques, lampes, clignotement) ;
- `Hud` : boussole d'objectif, écrans noirs, titres stylés ;
- `Mythic` : pont vers l'API de MythicMobs ; `Nms` : accès aux classes internes de Minecraft sur Arclight.

Ces outils servent directement à plusieurs points de ce document : hallucinations visibles par un seul joueur (39), imitateurs (22), cinématiques (53), graffitis (111), vision de l'infection.

**Extrême** : ZAMonde devient le cerveau du serveur. Skript est parfait pour le contenu, mais il tourne sur le fil principal et sauvegarde ses variables dans un fichier texte. Pour simuler 100 régions, des dizaines de hordes, des centaines de PNJ et NORDA, il faut du Java.

- **Ce qui va dans le moteur** :
  - le graphe du monde (F3) et la Chronique (F2) ;
  - les hordes-agents (IA-7), les cerveaux des PNJ (IA-8), les factions PNJ (IA-10), NORDA (IA-11) ;
  - le Directeur (IA-1) ;
  - la contamination et les deux jauges d'attention (108) ;
  - la télémétrie (F5).
- **Ce qui reste en Skript** : dialogues, commandes joueurs, menus, effets, événements scénarisés, et tout ce qui existe déjà. Les 88 scripts continuent de marcher.
- **Pont Skript ↔ Java** :
  - le plugin lit et écrit directement les variables Skript (`{za::...}`) avec l'API de Skript ;
  - Skript appelle le moteur par commandes console (`zam ...`) ; le moteur appelle Skript par commandes console (`zaevt ...`) ;
  - migration progressive : seulement les nouveaux systèmes au départ. Un ancien script migre seulement si spark montre qu'il coûte cher.
- **Cadences** :

| Rythme | Ce qui tourne |
|---|---|
| 1 seconde | Perception des zombies et PNJ près des joueurs, Directeur |
| 30 secondes | Régions, hordes virtuelles, contamination |
| 5 minutes | Vie des PNJ, économie, rumeurs |
| 1 jour serveur | Camps, factions, plans de NORDA, évolution des zombies, végétation |

- **Le calcul se fait hors du fil principal.** Le fil principal ne fait que les actions visibles (apparitions, blocs, effets), avec un budget. Départ : 3 ms par tick, 6 apparitions par tick, 200 blocs modifiés par tick.
- **Sauvegarde** : base SQLite `plugins/ZAMonde/monde.db`, copie chaque jour, export JSON pour les archives de saison (p72).
- **Contraintes à respecter** (voir `CLAUDE.md`) :
  - Arclight 1.20.1, MythicMobs 5.7.2 avec `ZAPaperCompat.jar`, jamais MythicMobs 5.11 ni ModelEngine ;
  - `Generator: NONE` dans `config-spawning.yml` : les apparitions passent par les fonctions existantes (`za_spawn_at`, p36) ou par l'API MythicMobs du pont `Mythic` ;
  - les messages et barres de boss de MythicMobs plantent sur Arclight : ils passent par Skript (p37).

### F2. La Chronique — le système nerveux ⚙️

Chaque système publie ce qui se passe dans une seule file d'événements :

`{type, lieu, région, coordonnées, acteurs (joueurs, PNJ, factions), gravité 1–5, vérité (vrai / faux / inconnu), témoins, sources, jour serveur}`

- **Qui publie** : tous les systèmes. `za_journal` (p21), `za_monde_evt` et `za_lieu_evt` (p62) deviennent des portes d'entrée de la Chronique.
- **Qui écoute** :
  - Léa et les radios (IA-12) ;
  - NORDA (IA-11) ;
  - la mémoire des PNJ et les rumeurs (IA-8) ;
  - les réputations (77, 112) ;
  - les graffitis (111), le bestiaire (116), les archives (p72) ;
  - le Directeur (IA-1) et la télémétrie (F5).
- **Pourquoi c'est la clé** : une chaîne comme « un tir → une horde → une barricade tombe → un PNJ meurt → la radio en parle → NORDA intercepte » n'est écrite nulle part. Elle arrive parce que chaque système écoute la Chronique et réagit avec une règle simple (point 20).
- **Le champ « vérité »** permet aux fausses informations d'exister proprement : un faux document (81) publie un événement « faux », NORDA peut le croire, Léa peut le répéter, et un témoin peut le contredire.
- **Règles de réaction en YAML** : les réactions (« si tel événement arrive à tel endroit, alors telle conséquence, avec telle probabilité, après tel délai ») sont écrites dans un fichier `reactions.yml` lisible par un humain. Colin peut créer ses propres chaînes sans programmer.

### F3. Le graphe du monde ⚙️

- **Nœuds** :
  - les 81 lieux de la région (p73) et les 8 de Saint-Aurèle ;
  - les quartiers, les camps (p44), les bases, les nids (p39), les infrastructures (106) ;
  - regroupés en **régions** d'environ 1 km × 1 km (une centaine sur la carte de 10 000 × 10 000).
- **Liens** : routes (autoroute 40, route 117, routes secondaires), rivières, rails (36), souterrains (p77). Chaque lien a un coût de passage, un danger et un état (pont détruit, route enneigée, péage, barrage NORDA).
- **État de chaque nœud** :
  - population civile et PNJ présents ;
  - zombies virtuels, nids, cadavres ;
  - contamination, eau, nourriture, courant, réseau cellulaire ;
  - sécurité, moral, panique, faction dominante ;
  - infrastructures, végétation, danger ;
  - attention des zombies et attention de NORDA ;
  - historique (les événements de la Chronique qui le concernent).
- `/zone` (p39), `/contamination` (p5), `/lieu` (p62) et la fiche de ville (7) lisent tous ce graphe.
- **Les rivières sont des liens à sens unique** pour la contamination : ce qui est sale en amont descend vers l'aval (18, 85). Ce n'est pas de la physique, juste une règle sur le graphe, donc ça ne coûte presque rien.

### F4. Virtuel ↔ réel (la matérialisation) ⚙️

- Les hordes, PNJ, convois, réfugiés, drones et animaux-indicateurs vivent comme des **données**.
- Ils apparaissent pour vrai à 96–128 blocs d'un joueur, **hors de son champ de vision**, et redeviennent virtuels quand plus personne n'est à moins de 160 blocs depuis 60 s. Ils gardent leur état : blessures, butin, souvenirs, équipement.
- **Plafonds de départ** : 350 zombies réels sur tout le serveur, 40 par joueur, 12 par chunk. À régler avec spark.
- **Renforts en continu** : une horde de 200 envoie 30 zombies réels à la fois. Quand ils tombent, d'autres arrivent par l'arrière, hors de vue.
- Le joueur ne voit jamais la différence. C'est ce qui permet au monde de vivre la nuit et loin des joueurs sans faire laguer.

### F5. Télémétrie et équilibrage 🧠

- **Le serveur note tout** :
  - morts (cause, lieu, heure, équipement, groupe) ;
  - zombies tués par arme et par type ;
  - temps passé par zone, munitions dépensées, soins ;
  - flux de jetons, prix, ventes ;
  - systèmes déclenchés, et ceux qui ne se déclenchent jamais.
- **Rapport quotidien admin** (`/zaadmin rapport`, et sur Discord si le point 59 est fait) :
  - zones les plus mortelles et joueurs en difficulté ;
  - systèmes jamais déclenchés : c'est un problème de lisibilité ou un bug ;
  - exploits suspects : farm AFK, pilier, piège à zombies, duplication (avec CoreProtect).
- **Réglage automatique borné** : taux d'apparition, butin et prix bougent seulement dans des limites fixées. Tout changement plus gros attend la validation de Colin.

### F6. Outils de test

- `/zaadmin` (63) : forcer, inspecter et annuler chaque système.
- **Simulateur accéléré** : le moteur fait tourner 60 jours de monde sans joueurs, ou avec des « joueurs fantômes » qui imitent des habitudes, en quelques minutes, puis sort un rapport. C'est le test obligatoire des freins (80) : si toute la carte est rouge au jour 40, un frein manque.
- **Chaînes de test** (Partie 5) : on force la première étape et on vérifie que la chaîne se rend au bout, avec les bons signaux pour le joueur.
- **Bots** : le testeur actuel (bots mineflayer sur le serveur local) sert aux commandes et aux événements. Le visuel et les sons se testent avec de vrais joueurs.

### F7. Pack joueurs groupé 📦

- Tous les nouveaux modèles, textures, sons, voix et éléments d'interface arrivent dans **une seule** mise à jour majeure, `za_modeles 2.0`, plutôt que dix petites.
- `za_modeles` est déjà un vrai mod Forge (une classe Java et beaucoup de ressources). Il peut recevoir du **code client** : effets d'écran (vision de l'infection, commotion), interface du bruit et des blessures, moteur de musique. Ça demande un environnement de compilation Forge, plus lourd que les ressources seules.

### F8. Variables Skript en SQLite 🔍

- Skript sait stocker ses variables dans une base SQLite au lieu de `variables.csv` (`plugins/Skript/config.sk`, section `databases`). C'est un changement de configuration, sans rien réécrire.
- À faire avant d'ajouter des milliers de données.
- 🔍 Le commentaire du fichier de configuration parle du plugin SQLibrary : vérifier si Skript 2.9.5 en a encore besoin.

## Partie 2 — L'IA poussée au maximum 🧠

> **Principe** : des règles simples, nombreuses et branchées entre elles donnent un comportement qui paraît intelligent. Rien ici n'est une vraie pensée, mais tout doit en donner l'impression. Et tout respecte la règle 6 : l'IA ne triche jamais devant le joueur.

### IA-1. Le Directeur (le metteur en scène invisible)

Inspiré de l'« AI Director » de Left 4 Dead : une IA qui regarde chaque joueur et dose la peur.

- **Intensité par joueur (0–100)** :
  - monte avec les dégâts reçus, les zombies proches, les morts frôlées, la vie basse, le noir, le bruit, les munitions basses, l'isolement ;
  - redescend avec le temps passé en sécurité (base, camp, groupe).
- **Le cycle** : Calme → Montée → Pic → Relâche.
  - **Calme** : il prépare. Sons lointains (113), signes avant-coureurs (105), une odeur, une porte entrouverte.
  - **Montée** : plus d'apparitions, une embuscade (102), un imitateur (22).
  - **Pic** : une horde déviée vers le joueur, un événement (2, 14), une Némésis (IA-4).
  - **Relâche** : interdiction des grosses menaces. C'est le moment des SMS, de la radio, des PNJ, des découvertes.
- **Il joue avec ce qu'il a, il ne crée rien de magique** : il choisit quelle horde virtuelle dévier (IA-7), quel événement déclencher, quand Léa parle (IA-12), quand l'horreur psychologique (p4) frappe, quelle musique jouer (57).
- **Lecture du groupe** : taille, niveau des armes (p49), armure, morts récentes, heures de jeu. Un groupe de 4 bien armés n'a pas la même nuit qu'un joueur seul.
- **Profil de joueur** : la télémétrie (F5) montre ce que chaque joueur aime (explorer, combattre, bâtir, parler aux autres). Le Directeur adapte ses moments forts : l'explorateur trouve plus de secrets, le combattant croise plus souvent sa Némésis, le bâtisseur vit plus de sièges, le joueur social a plus de drames de PNJ.
- **Quota de moments forts** : chaque joueur doit vivre au moins un moment mémorable par session (vétéran, crash, PNJ qui revient, découverte, sauvetage). Le Directeur note le dernier et en provoque un s'il manque.
- **Anti-routine** : si les dernières sessions d'un joueur se ressemblent, le Directeur change d'outil (une nuit sans horde mais pleine de bruits, une journée tranquille qui tourne mal).
- **Nuits de serveur** : en plus du rythme de chaque joueur, il garde un rythme commun pour créer de grandes nuits partagées (Blood Moon, Grande Migration) quand tout le monde est prêt.
- **Anti-frustration** : 3 morts en 30 minutes → intensité plafonnée, et parfois un coup de chance plausible (un survivant passe, une cache dans le coin).
- **Protection des nouveaux** : premières heures en douceur, en suivant le fil `/fil` (p81).
- **Directeur narratif** : en parallèle, il choisit les moments d'histoire selon la progression de chaque joueur (parcours p60, dossier Arel p69, NORDA 79), pour que l'histoire avance au bon rythme pour tout le monde.
- **Limites** : ne touche jamais aux bases enregistrées hors des sièges normaux (p8). Tout ce qu'il décide est noté dans un carnet visible avec `/zaadmin directeur`.

### IA-2. Les sens des zombies

Chaque zombie perçoit le monde avec ses sens, au lieu de juste viser le joueur le plus proche.

- **Vue** :
  - cône de 110° devant lui ;
  - portée selon la lumière : 24 blocs de jour, 8 la nuit, 32 si le joueur tient une torche ou une lampe (Dynamic Lights rend déjà la lumière visible) ;
  - accroupi : portée divisée par deux ; hautes herbes, buissons, brouillard (p55), pluie : portée réduite.
- **Ouïe** :
  - chaque bruit a une force et une portée (tableau du point 3) ;
  - les murs et les portes fermées étouffent, l'intérieur porte moins loin que l'extérieur, l'orage masque (p55) ;
  - Zombie Awareness et TSAZ gèrent déjà une partie ; le moteur ajoute la propagation et la mémoire.
- **Odorat** :
  - une carte d'odeurs par cases de 4 × 4 blocs ;
  - les joueurs laissent une piste faible, le sang une piste forte (26), la cuisine et l'élevage une odeur de fond (108), les cadavres une odeur qui grandit (1) ;
  - la pluie lave, le temps efface, l'eau coupe la piste.
- **Vibrations** (zombies aveugles seulement) : course, sauts, blocs cassés à proximité.
- **Camouflage** : se couvrir de sang de zombie (item fait à partir de restes, 24) masque l'odeur et trompe la vue de loin pendant 3 minutes. Coût : risque d'infection (p27) et les chiens te prennent pour un mort (44).
- **Alerte partagée** : un zombie qui perçoit quelque chose réveille ceux à 8 blocs ; le Screamer porte l'alerte à 48 blocs (existe déjà, p56) ; l'Observateur (`ZA_Observer`) voit loin et guide la horde.
- **Chaque zombie a ses sens à lui** (IA-4) : un aveugle n'a que l'ouïe et les vibrations, un sourd ne réagit qu'à la vue.
- **Ce que le joueur voit** : le zombie tourne la tête vers un bruit, renifle (animation 📦), change de démarche quand il passe en poursuite. Le joueur apprend à lire les zombies.

### IA-3. Le cerveau d'un zombie

Chaque zombie suit une machine à états, au lieu de foncer tout droit.

| État | Ce qu'il fait | Comment il en sort |
|---|---|---|
| Dormant | Immobile dans un nid ou un bâtiment, presque aucun calcul | Un bruit fort, une odeur, un congénère qui crie |
| Errance | Marche au hasard, suit les routes et les odeurs, revient vers les lieux où il a déjà trouvé des proies | Un stimulus |
| Alerte | S'arrête, tourne la tête, renifle 2 à 4 s | Stimulus confirmé → investigation ; rien → errance |
| Investigation | Va vers la source du bruit ou de l'odeur | Voit un joueur → poursuite ; rien → recherche |
| Poursuite | Chasse sa cible, alerte les autres | Perd la cible → recherche |
| Recherche | Fouille la dernière position connue en spirale pendant 20 à 40 s (104) | Retrouve → poursuite ; sinon abandon |
| Repas | Dévore un cadavre (le Charognard le fait déjà) | Dérangé ou rassasié |
| Panique | Fuit une explosion ou le feu (68) | Après 10 à 20 s |
| Retour | Rentre au nid à l'aube (p74) ou rejoint sa horde | Arrivé |

- **Mémoire de lieu** : un zombie se souvient des endroits où il a trouvé des proies et y retourne en errance. C'est la base du point 67 (refuges trop utilisés).
- **Portes et fenêtres** : il frappe les portes (p79), casse les vitres pour entrer, écoute derrière une porte avant de frapper.
- **Coincé** : s'il ne progresse plus depuis 10 s, il change de chemin ou tente une autre entrée.
- **Technique** : MythicMobs et l'IA de Minecraft font le déplacement ; le moteur choisit l'état et la destination. Pour envoyer un zombie à un endroit précis sans cible, on réutilise le leurre invisible de la migration (p33).
- Les états sont visibles : animation, son, vitesse (📦 pour les animations).

### IA-4. Individualité, vétérans et Némésis

Aucun zombie n'est une copie.

- **Traits tirés à l'apparition** : boiteux, aveugle, sourd, affamé, obstiné (ne lâche jamais une piste), craintif (fuit le feu plus longtemps). Visibles sur le modèle ou à la démarche quand c'est possible 📦.
- **Traits de son ancien métier** : le policier essaie les poignées de porte, le pompier ignore la fumée, le prisonnier traîne ses chaînes et fait du bruit, le soldat porte encore des munitions, le médecin du matériel médical (p65 donne déjà du butin par métier).
- **Souvenirs de sa vie** : les citoyens infectés du prologue retournent parfois à leur ancien appartement ou à leur lieu de travail (p63, p65). Un joueur peut reconnaître Mme Gagnon.
- **Vétérans (84)** : un zombie qui survit plusieurs jours serveur gagne un rang (Vétéran → Ancien → Légende locale). Chaque rang donne plus de vie, un trait de plus, un nom (« L'Éventreur du garage Tremblay »), une entrée au bestiaire (116) et une mention à la radio.
- **Némésis** (inspiré de Shadow of Mordor) :
  - un zombie qui **tue un joueur** devient automatiquement un vétéran nommé ;
  - il **porte l'équipement** pris sur sa victime (casque, arme en main) ;
  - il **se souvient** de sa victime : le Directeur organise une revanche plus tard, ailleurs ;
  - s'il est blessé et s'enfuit, il revient avec une cicatrice et une **résistance** au type d'arme qui l'a blessé ;
  - s'il tue encore, il monte en grade et son nom grandit (« … le Faucheur de la 117 ») ;
  - il a une **faiblesse cachée**, que l'autopsie d'un autre vétéran (19) ou le bestiaire révèle ;
  - le tuer donne un haut fait (p30), un surnom (16), sa tête comme relique, et rend l'équipement perdu ;
  - limite : 1 Némésis actif par joueur, 10 sur le serveur.
- **Persistance** : vétérans et Némésis restent dans la base de données, même virtuels. Ils peuvent changer de région avec leur horde (IA-7).

### IA-5. La tactique de groupe (5)

- **Rôles** :
  - l'Alpha repère et choisit la cible : le joueur le plus isolé, le plus blessé ou le plus bruyant ;
  - le Screamer relaie l'alerte ; l'Alpha le protège ;
  - les Brutes passent devant et frappent les barricades ;
  - les Crawlers se glissent sous les barricades et achèvent les joueurs au sol ;
  - les Leapers prennent les hauteurs ;
  - les Spitters délogent les campeurs ;
  - les Bloaters bouchent un passage avec leur nappe toxique ;
  - les Stalkers prennent à revers dans les bâtiments sombres ;
  - les FakeDead attendent sur les routes que les joueurs prennent souvent.
- **Encerclement simple** : quand un groupe poursuit un joueur, un tiers prend un second chemin (leurre sur un deuxième point de passage) pour couper la retraite.
- **Embuscade de sortie** : pendant qu'un joueur fouille un bâtiment, quelques zombies attendent près de la sortie au lieu d'entrer.
- **Moral de la horde** : chaque perte baisse le moral ; à 30 %, la horde recule, se regroupe et revient plus tard. C'est un frein naturel. Tuer l'Alpha disperse la meute (existe déjà, p56).
- **Les joueurs peuvent contrer chaque rôle** : abattre le Screamer en premier, viser l'Alpha, garder les hauteurs, tenir un passage étroit. C'est ce qui rend la horde intelligente sans la rendre injuste.
- ⚠️ Pas d'armée : les tactiques restent courtes et brutales. La horde reste une masse affamée.

### IA-6. L'évolution darwinienne par région (4, 66)

Chaque région a son propre « génome » de zombies : la proportion de chaque type, les traits fréquents, les résistances.

- **Sélection naturelle** : chaque jour serveur, les types et traits qui ont fait le plus de dégâts ou survécu le plus longtemps dans une région gagnent du poids ; ceux qui meurent facilement en perdent.
- **Pression des habitudes** (p56 + point 4) : le moteur compte les habitudes des joueurs dans chaque région et oriente l'évolution :

| Habitude des joueurs | Réponse de la région |
|---|---|
| Armes à feu | Plus de Screamers, hordes plus grosses |
| Mêlée | Zombies blindés, Bloaters |
| Lumière forte | Phototropes |
| Camper sur les toits | Grimpeurs, Leapers, Spitters |
| Feu | Peau carbonisée résistante au feu |
| Barricades | Brutes, attaques des murs |
| Toujours les mêmes routes | Embuscades de FakeDead |
| Toujours les mêmes refuges | Zombies qui apparaissent dedans (67) |
| Leurres sonores | Zombies qui ignorent les leurres bon marché (117) |
| Pièges à zombies (farm) | Les morts évitent le piège pendant un jour |

- **Mémoire qui s'efface** : si les joueurs changent de façon de jouer, les adaptations reculent en quelques jours. Ça devient une course aux armements qui tourne en rond, jamais un mur.
- **Toujours une réponse** : aucune adaptation ne rend une stratégie inutile, elle la rend seulement plus coûteuse.
- **Arbre de mutations** : quand un trait dépasse un seuil, une vraie nouvelle variante peut naître (📦 si elle a un modèle). Le premier joueur qui la voit est inscrit aux archives, et les joueurs votent son nom (116).
- **Épidémiologie** : les hordes migrantes (IA-7) **transportent le génome** de leur région. Une mutation née au nord peut descendre vers le sud. Intercepter une horde migrante empêche la propagation : une vraie raison stratégique de chasser les hordes.
- **Lisibilité** : le bestiaire (116) affiche « Secteur du barrage : les morts grimpent davantage ». Un scientifique (19) peut le prédire, Léa en parle, `/adaptation` existe déjà.
- **Freins** : plafond de puissance par région. Une région nettoyée (80) perd ses mutations.

### IA-7. Les hordes-agents (103)

- **Chaque horde est un personnage** :
  - identifiant, nom pour les grandes (« La Marée de la 40 »), taille, composition, génome (IA-6) ;
  - chef (Alpha) ou non, personnalité (agressive, prudente, nomade) ;
  - position, objectif, moral, faim, vitesse (selon la saison et la météo) ;
  - mémoire : zones où elle a trouvé des proies, sons récents, bases qui lui ont résisté.
- **Objectifs choisis par score** (on prend le plus utile au moment présent) :
  - suivre le son le plus fort entendu (3) ;
  - migrer le long des routes et des rivières (p33, p76) et migration saisonnière (11) ;
  - se nourrir aux cadavres (1) ;
  - faire un nid dans un bâtiment (25) ;
  - hiberner l'hiver (12) ;
  - fuir une zone trop dangereuse pour elle (tourelles, feu, explosions) ;
  - assiéger une base, seulement quand un joueur y est (règle 2).
- **Elles se divisent et fusionnent** : deux hordes qui se croisent fusionnent sous l'Alpha le plus fort ; une horde trop grosse ou sans chef se divise. Rarement, plusieurs fusions donnent une **Mégahorde**, avec une alerte sur tout le serveur.
- **Elles laissent des traces** : champs piétinés, portes défoncées, sang, ossements, corbeaux au-dessus (105). Les joueurs peuvent pister une horde ou l'éviter.
- **Après un échec** : une horde qui perd son nid cherche un nouveau bâtiment ; une horde qui perd trop de monde recule ; une horde qui a échoué contre une base s'en souvient et l'évite… ou revient plus grosse si son Alpha est obstiné.
- **Lisibilité** : la radio signale les grandes hordes (74), les scientifiques prédisent leur trajet (19), les oiseaux s'envolent avant leur arrivée (105).
- **Matérialisation** : voir F4.

### IA-8. Les cerveaux des PNJ (15)

Chaque PNJ important a un vrai dossier, et ses décisions en découlent.

- **Identité** : prénom, nom, âge, ancien métier (p43), famille, origine (Saint-Aurèle, campagne, militaire).
- **Personnalité (0–100)** : courage, honnêteté, loyauté, avidité, empathie, paranoïa.
- **Besoins** : manger, boire, dormir, être en sécurité, voir les siens. Un PNJ qui a faim pense d'abord à manger.
- **État** : santé, blessures, infection cachée (110), fatigue, moral, peur, deuil.
- **Émotions envers chaque joueur** : confiance, gratitude, peur, rancune. Elles montent et descendent selon ce que le joueur fait.
- **Mémoire** : les événements vécus avec chaque joueur (aidé, sauvé, abandonné, volé, trahi, menti, payé), avec une importance. Les petites choses s'oublient, les grandes jamais.
- **Il apprend tes habitudes** : « Tu passes toujours la nuit. Je t'ai gardé une soupe. »
- **Réseau social** : amitiés, rivalités et liens familiaux entre PNJ d'un camp. Quand un ami meurt, le PNJ fait son deuil et son moral baisse.
- **Traumatismes** : un PNJ peut refuser de retourner à l'hôpital où sa femme est morte.
- **Objectif personnel** : retrouver sa fille, venger son frère, quitter la région, devenir chef, rembourser une dette. Ces objectifs donnent des quêtes naturelles.
- **Secrets** : espion NORDA (98), infecté (110), ancien pillard, sait où se trouve un labo, a trahi quelqu'un.
- **Connaissances** : des faits sur le monde (lieux, ressources, hordes, joueurs), chacun avec un degré de certitude, venus de ce qu'il a vu ou entendu.
- **Décisions** : à chaque cycle, le PNJ choisit l'action au meilleur score selon sa personnalité, ses besoins et son état : travailler, manger, dormir, voyager, recruter, voler, fuir, dénoncer, mentir, quitter le camp, rejoindre une faction, partir chercher sa famille.
- **Horaires** : dort la nuit, travaille le jour, se réunit au feu le soir (simulé partout, visible autour des joueurs).
- **Vie et mort** : la mort d'un PNJ important est définitive pour la saison et change son camp. Sa famille peut chercher vengeance. Ses descendants peuvent apparaître la saison suivante (p72).
- **Voyages virtuels** : un PNJ peut quitter son camp, marcher vers un autre, se faire capturer, rejoindre des réfugiés (89) ou une faction. Un survivant abandonné au jour 10 peut être chef d'un camp ennemi au jour 40, et s'en souvenir.
- **Dialogues** : des centaines de gabarits avec variables et humeurs, qui citent ses souvenirs (« Tu m'as laissé à l'hôpital, Colin. »). Menus existants (`za_menu`, p42). Le niveau Ω (IA-15) permet la conversation libre.
- **Corps** : les PNJ de ZAMonde (`Npcs`) marchent, regardent et s'animent déjà. Les survivants MythicMobs existent (`ZA_Survivant_*`).

### IA-9. Le mensonge lisible (75, 76, 98, 110)

Les PNJ et les radios peuvent mentir, mais le joueur doit pouvoir s'en rendre compte.

- **La décision de mentir vient du cerveau** (IA-8), jamais du hasard : un PNJ ment s'il y a un intérêt (peur, avidité, loyauté envers une autre faction, secret à protéger) et si son honnêteté est basse.
- **Quatre sortes de réponses** :
  1. vraie ;
  2. fausse par erreur : il est sûr de lui, mais il se trompe ;
  3. mensonge pour protéger un secret ;
  4. mensonge pour envoyer le joueur dans un piège.
- **Les indices qui permettent de démasquer** :
  - deux témoins se contredisent ;
  - la version du PNJ ne colle pas avec la Chronique ou avec ce que le joueur a vu ;
  - le PNJ a des phrases nerveuses (« Pourquoi tu me demandes ça ? ») ;
  - un chien grogne contre un infecté qui se cache (44, 110) ;
  - un document (p69) dit autre chose ;
  - la radio corrige plus tard une fausse nouvelle (IA-12).
- **Conséquences** : un menteur démasqué perd la confiance du camp. Un joueur qui accuse à tort perd de la réputation (112).
- **Carnet de soupçons** : le joueur peut noter dans son journal qui lui a menti. Les PNJ se souviennent aussi de qui les a crus.

### IA-10. Les factions PNJ stratèges (45, 88, 92)

- **Les factions** : la Milice (`ZA_Milice`), les Déserteurs de Bravo (88), les Pillards (`ZA_Pillard`), les Marchands nomades, les réfugiés organisés (89), NORDA (IA-11). Les factions des joueurs sont des acteurs comme les autres dans leurs calculs.
- **Chaque faction a** : un chef avec une personnalité (agressif, prudent, diplomate, paranoïaque), une doctrine (militaire, marchande, communautaire, prédatrice), des ressources (production de p67), des besoins, des relations (p67), une mémoire des joueurs et des traités.
- **Plan quotidien** : elle évalue ses besoins et choisit un plan : commercer, envoyer un convoi (92), attaquer, défendre, négocier, demander de l'aide aux joueurs (contrats), se replier, poser un péage (109).
- **Politique interne** : un chef qui perd des batailles perd sa légitimité ; contestation, scission ou coup de force deviennent possibles (90). Une faction peut naître (des réfugiés qui s'organisent) ou disparaître.
- **Réaction aux joueurs** : elle se souvient des promesses tenues et brisées, des convois braqués, des renseignements volés (91).
- **Pourquoi c'est important** : avec 20 joueurs maximum, il y aura 2 ou 3 factions de joueurs. Les factions PNJ remplissent le monde pour que la diplomatie, l'économie et la guerre aient toujours des acteurs.

### IA-11. NORDA, une IA qui croit des choses (79, 81–83, 96, 98–101, 108)

NORDA n'est pas omniscient : il **croit** des choses, avec un degré de certitude, à partir de preuves.

- **Un dossier par joueur et par faction** :
  - soupçon (0–100) et certitude ;
  - identité supposée, affiliation supposée ;
  - dernière position connue, avec un rayon d'incertitude ;
  - habitudes connues : routes, heures, lieux.
- **Les preuves** :
  - signatures électriques (sous-stations, bases sous tension, antennes 96) ;
  - émissions radio triangulées (107) ;
  - cellulaire qui accroche le réseau (82) ;
  - caméras, drones (99), informateurs et agents infiltrés (98) ;
  - documents volés (p69), labos visités (p25), convois attaqués.
- **Les croyances peuvent être fausses** : chaque preuve a du bruit. Les fausses traces (81) ajoutent de fausses preuves, les faux papiers (83) brouillent l'identité, détruire des preuves baisse la certitude.
- **Hypothèses concurrentes** : NORDA peut hésiter (« le saboteur est Colin à 60 % ou la faction Rouge à 40 % »). Il agit sur la plus probable, donc il frappe parfois le mauvais groupe. Les joueurs voient que la tromperie marche.
- **Il apprend des tromperies** : s'il se fait avoir plusieurs fois par de fausses traces, il vérifie davantage pendant quelque temps. C'est le jeu du chat et de la souris.
- **Paliers (79)** : Inconnu → Intérêt → Surveillance → Identifié → Intervention → Priorité, calculés à partir du soupçon et de la certitude.
- **Ressources limitées** : chaque jour, NORDA a un nombre fixe de moyens (départ : 2 drones, 1 patrouille, 1 barrage, 1 équipe de chasse). Il les envoie là où la menace lui paraît la plus grande. NORDA est intelligent mais limité, donc lisible et contournable.
- **Prédiction** : il place ses barrages sur les routes que le joueur prend souvent (habitudes du point 4). Changer ses habitudes le déjoue.
- **Opérations (101)** : récupération d'un scientifique, nettoyage d'un labo détruit, capture (100), labo mobile, ratissage d'une région.
- **Contact** : SMS (API de p70), radio NORDA cryptée (93), appels inconnus, dossier physique trouvable (79).
- **Négociation** : quand les enjeux sont grands, NORDA propose un marché (livrer un scientifique contre une baisse de soupçon). Il se souvient des marchés… et peut trahir.
- **Mémoire de saison** : une partie de ce que NORDA sait passe à la saison suivante (p72).

### IA-12. Léa et les radios journalistes (17/74, 51/75, 93)

- **Choix des nouvelles** : chaque événement de la Chronique reçoit un score (gravité × nouveauté × proximité × implication des joueurs). Les meilleurs passent à l'antenne.
- **Sources et fiabilité** : Léa reçoit ses informations de témoins PNJ, de factions, de fuites NORDA, de la radio pirate et des **auditeurs** (les joueurs peuvent l'appeler avec le téléphone de p70). Chaque source a une fiabilité ; celle d'un joueur dépend de sa réputation. Elle dit « confirmé », « non confirmé » ou « rumeur », se trompe parfois et se corrige plus tard.
- **Quatre stations, quatre personnalités** :

| Station | Ton | Fiabilité |
|---|---|---|
| Léa (civile) | Chaleureuse, inquiète | Honnête, parfois mal informée |
| Bravo (militaire) | Sèche, codée | Fiable, mais cache des choses |
| Radio pirate | Paranoïaque, drôle | Variable, parfois tenue par des joueurs (107) |
| NORDA | Calme, rassurante | Menteuse |

- **Couverture en direct (74)** : perte de contact avec une ville, puis explosions signalées, puis évacuation, puis zone rouge le lendemain. Et à l'inverse : une ville reprise (8).
- **Léa a sa propre histoire** : si elle dit trop de vérités sur NORDA, NORDA la menace, puis fait taire sa station. Les joueurs peuvent la protéger ou réparer l'émetteur (106). Le silence de la radio devient lui-même un signal.
- **Signal réel** : la qualité dépend de la distance, des répéteurs réparés (106) et de la météo. Hors réseau, on entend la statique.
- **Voix** : le texte est toujours unique ; les voix viennent d'une banque de répliques (jingles, statique, phrases clés, point 50).

### IA-13. L'écosystème (23, 44, 105)

- **Les animaux sont des capteurs du monde** : ils fuient avant une horde, désertent les zones contaminées, reviennent quand la zone est nettoyée (80). Les poissons disparaissent de l'eau contaminée (85).
- **Les corbeaux** tournent au-dessus des cadavres et des nids, et croassent quand quelqu'un approche, ce qui peut réveiller une horde.
- **Les chiens infectés** chassent en meute ; les chiens de garde détectent les zombies et les infectés qui se cachent (44, 110).
- **Le silence** : quand les oiseaux et les insectes se taisent d'un coup, quelque chose arrive (113).
- Chaque animal est un signal : le joueur qui sait les lire voit le danger avant qu'il arrive.

### IA-14. Les compagnons et les soldats

Pour les survivants recrutés (p43) et les soldats de la milice (p75).

- **Ordres** (menu `/garde` existant, élargi) : suivre, garder un poste, patrouiller un trajet, couvrir, se replier, porter, réparer une barricade, soigner.
- **Comportement** : se met à couvert, recule quand sa vie baisse, protège le joueur blessé, appelle à l'aide.
- **Moral et loyauté** (IA-8) : un compagnon mal nourri, mal payé ou envoyé à la mort finit par désobéir, puis par déserter. Un ordre suicidaire peut être refusé.
- **Expérience** : un soldat qui survit à plusieurs sièges devient vétéran, avec un nom et de meilleures capacités. Sa mort est une vraie perte, gravée dans la Chronique.

### IA-15. Niveau Ω — l'IA générative (option, payante)

Le niveau maximal : brancher un vrai modèle de langage, comme Claude, au moteur.

- **Le cerveau décide, le modèle parle.** Le cerveau du PNJ (IA-8) choisit quoi dire, y compris un mensonge ; le modèle de langage transforme ça en phrase naturelle, en français québécois, dans la personnalité du PNJ. Le modèle ne décide jamais des règles du jeu et ne peut pas révéler un secret que le cerveau garde.
- **Usages** :
  - conversation libre avec les PNJ importants, dans le chat ;
  - bulletins de Léa écrits à partir des vrais événements de la Chronique ;
  - interrogatoires NORDA dynamiques (100) ;
  - journaux personnels, graffitis (111) et lettres trouvées.
- **Garde-fous** : personnage strict, 2 lignes maximum, filtre de contenu, aucun sujet hors du jeu, quota par joueur, réponses mises en cache, retour aux dialogues écrits si le service ne répond pas.
- **Limites** : la voix ne peut pas être générée en direct sur Apex (hébergement Java seulement), donc seulement le texte. Aucune donnée personnelle n'est envoyée : seulement les pseudos et les événements du jeu.
- ⚠️ **Coût** : ça passe par une API (celle d'Anthropic ou une autre), payée à l'usage, **séparément** de l'abonnement Claude. Il faut une clé API et un moyen de paiement. On fixe un plafond de dépenses d'avance. À chiffrer avant de décider, et à faire en tout dernier, quand tout le reste marche.

## Partie 3 — Les 117 points poussés à l'extrême

Les points sont regroupés par domaine. L'index complet par numéro est à la fin du document.

### A. Zombies

#### 1. Cadavres → nid ⚙️
- **Aujourd'hui** : les corps de joueurs (p13) attirent les zombies et se brûlent ou s'enterrent ; le Charognard les dévore (p56) ; les sièges laissent des ossements et de la contamination (p8).
- **Extrême** :
  - chaque zombie tué ajoute une « charge de cadavre » à sa case de 16 × 16 blocs. Les corps restent visibles quelques minutes (54), puis deviennent un simple compteur ;
  - paliers : mouches (particules) → odeur (IA-2) → corbeaux (105) → contamination (18) → naissance d'un nid (25) ;
  - nettoyer, avec un coût pour chaque méthode (règle 3) :
    - brûler : rapide, mais la fumée et le bruit attirent ;
    - enterrer : lent et silencieux ;
    - chaux vive (ancien point 40) : rapide et silencieuse, mais rare ;
    - transporter les corps hors de la ville : sûr, mais long et dangereux ;
  - un bâtiment nettoyé reçoit une marque « Nettoyé — Jour N » qui compte pour les points 69 et 80 ;
  - les Charognards sont attirés par les zones les plus chargées : un massacre attire des mangeurs.
- 🔗 18, 25, 69, 80, 105, 108, IA-2.
- ⚠️ Pas de vrais corps qui s'accumulent (lag) : un compteur par zone.

#### 4. Nouvelles adaptations 🧠
- **Aujourd'hui** : p56 note 5 habitudes sur 3 jours (armes à feu, mêlée, lumières, camping, explosifs) et change les apparitions ; `/adaptation` les montre.
- **Extrême** : voir IA-6. Le tableau passe de 5 à 10 habitudes, par région, avec une mémoire qui s'efface, des mutations qui naissent et voyagent avec les hordes.
- **Anti-exploit** : un piège à zombies ou une tour de farm détectés par la télémétrie (F5) font que les morts évitent l'endroit pendant un jour serveur.
- 🔗 66, 67, 116, IA-6, F5.

#### 5. Rôles dans la horde 🧠
- **Aujourd'hui** : le Screamer appelle la horde, l'Alpha renforce les zombies proches et partage sa cible, la meute fait des pyramides et défonce les portes (p56, p79).
- **Extrême** : voir IA-5. Neuf rôles qui se complètent, encerclement, embuscade de sortie, moral de horde qui recule à 30 %.
- 🔗 IA-5, IA-7.

#### 6. Un boss par région ⚙️📦🗺️
- **Aujourd'hui** : Undead Overlord (barre de vie par p37), Alpha Z-01, Garde Z-01.
- **Extrême** :
  - un boss par grande zone (8 à 10), chacun lié à son lieu : la Directrice de l'hôpital, le Contremaître de la carrière, le Capitaine du convoi, la Chose du barrage ;
  - une **arène construite** avec une mécanique propre : à l'hôpital, couper le courant le rend vulnérable ; au barrage, ouvrir les vannes l'emporte ;
  - **trois phases**, et il appelle des renforts tirés du génome de sa région (IA-6) ;
  - **il vit dans le monde** : il se déplace (boss itinérant), apparaît à la radio, renforce les zombies de son territoire ;
  - le tuer fait baisser le danger de la région d'un niveau (80), donne une relique unique (p30) et libère son arène, qu'une faction peut ensuite occuper ;
  - **il apprend d'une saison à l'autre** : s'il est tombé trop vite, sa version de la saison suivante corrige sa faiblesse (archives p72) ;
  - sa vie s'ajuste au nombre de joueurs présents.
- 🔗 80, 116, p30, p72, IA-6.

#### 13. Zombies de saison 📦
- **Extrême** :
  - **Noyé** (printemps) : dans les zones inondées, agrippe et tire vers le fond ;
  - **Brûlé** (été) : enflammé, il propage le feu s'il meurt dans l'herbe sèche ;
  - **Moisi** (automne) : relâche des spores dans le brouillard qui brouillent la vision ;
  - **Givré** (hiver) : lent et résistant aux coups, il éclate sous le feu. Au printemps, il dégèle d'un coup et devient rapide pendant une minute (ancien point 9).
  - Chaque type entre dans le génome des régions (IA-6) et a sa page au bestiaire (116).
- 🔗 9 à 12, IA-6, 116.

#### 22. Imitateurs 📦🧠
- **Extrême** :
  - il crie « À l'aide ! », frappe à une porte, fait sonner un téléphone au moment où tu as du réseau (p70), imite la statique d'une radio, imite des pas ;
  - il imite la voix de PNJ connus, tirée de la banque de voix (50) ;
  - il répète la dernière phrase qu'il a entendue près des joueurs, et ton pseudo apparaît dans les sous-titres, prononcé d'une voix qui n'est pas tout à fait humaine ;
  - **toujours un indice** (IA-9) : la voix est légèrement fausse, elle a de l'écho, elle répète exactement la même phrase. Le bestiaire l'apprend aux joueurs ;
  - ZAMonde peut le rendre visible **par un seul joueur** (`Privacy`) : tes coéquipiers n'entendent rien.
- 🔗 50, 70, 113, IA-9.

#### 23. Chiens infectés et corbeaux 📦
- **Extrême** :
  - chiens infectés en meutes de 3 à 6, rapides, qui suivent le sang (26) ; le chien dominant hurle la nuit et appelle la horde ;
  - ils fuient le feu ; tuer le dominant disperse la meute ;
  - les corbeaux forment des nuées au-dessus des cadavres et des nids (105). Surpris, ils croassent et alertent les zombies proches (IA-2) ;
  - un joueur attentif utilise les corbeaux comme éclaireurs : là où ils tournent, il y a des morts.
- 🔗 26, 44, 105, IA-13.

#### 24. Démembrement 📦
- **Extrême** :
  - trois zones touchées, selon la hauteur de l'impact (comme les blessures de p53) :
    - **jambes** : il devient rampant, lent, et agrippe les chevilles (lenteur) ;
    - **bras** : il ne peut plus casser les portes, mais il mord, avec plus de risque d'infection ;
    - **tête** : mort immédiate, sauf avec un casque (zombies blindés) ;
  - le modèle change, parce que `za_modeles` choisit déjà le modèle d'après le nom de l'entité ;
  - les membres tombés servent à l'autopsie (19), au camouflage (IA-2) ou comme appât (117).
- ⚠️ Chaque variante est un modèle de plus : seulement pour les humains principaux.

#### 25. Nids qui grandissent 🗺️📦
- **Aujourd'hui** : nids de p39 (un cœur vivant ; le détruire rapporte et baisse le danger).
- **Extrême** :
  - quatre stades : **Germe** (un bloc) → **Foyer** (le sculk s'étend sur 8 blocs) → **Ruche** (l'intérieur d'un bâtiment couvert, plusieurs cœurs, des gardiens) → **Matrice** (une seule par région, de niveau boss, qui fait naître des mutants) ;
  - le nid grandit en se nourrissant de cadavres (1), de contamination (18) et de noir ; la lumière (42), le feu et la chaux le ralentissent ;
  - visible de loin : ciel teinté (p31), spores, corbeaux (105) ;
  - chaque stade se détruit autrement : feu, explosifs, ou chaux plus un échantillon pour le scientifique ;
  - les hordes peuvent transporter des spores et fonder des nids-fils ailleurs (IA-7), avec un plafond par région ;
  - réversible : le moteur garde la liste des blocs posés par le nid et les retire quand il meurt.
- 🔗 1, 18, 42, 80, IA-7.

#### 26. Trace de sang
- **Aujourd'hui** : saignement du torse (p53) avec particules rouges. Zombie Awareness suit déjà une forme de piste de sang 🔍.
- **Extrême** :
  - des taches de sang restent au sol (bloc mince de `za_modeles` 📦), plus grosses selon la blessure, effacées par la pluie ;
  - zombies, chiens infectés et chiens de garde suivent la piste (IA-2) ;
  - un bandage arrête la piste ;
  - tactique : faire saigner de la viande crue pour tendre un piège (117) ;
  - en JcJ, on peut pister un ennemi blessé (48).
- 🔗 23, 44, 117, IA-2.

#### 27. Noyés et zombies sous la glace 📦
- **Extrême** :
  - des noyés cachés dans les rivières (que les hordes longent déjà, p33) agrippent les nageurs et les tirent vers le fond ;
  - ils peuvent renverser les bateaux ;
  - l'hiver, des zombies figés sont visibles sous la glace. La glace mince **craque d'abord** (son d'alerte), puis cède sous le joueur ;
  - au printemps, la débâcle les libère (9).
- 🔗 9, 12, 13.

#### 66. Adaptation par région 🧠
- Voir IA-6 : chaque région a son génome et sa mémoire d'habitudes. Une région de montagne et une zone urbaine ne développent pas les mêmes menaces.
- 🔗 4, 116, IA-6.

#### 84. Zombies vétérans 🧠
- Voir IA-4 : rangs Vétéran → Ancien → Légende locale, et le système de Némésis (le zombie qui t'a tué porte ton équipement et revient te chercher).
- 🔗 16, 116, p30, IA-1, IA-4.

#### 102. Embuscades dans le décor 🗺️
- **Aujourd'hui** : FakeDead (fait le mort), Stalker (attaque de dos).
- **Extrême** :
  - le générateur place des « points d'embuscade » : voitures, toilettes, armoires, sous des débris, plafonds effondrés, tas de cadavres ;
  - le Directeur (IA-1) les active pendant la montée de tension ;
  - **chaque embuscade a un indice** : une porte entrouverte qui grince, des mouches, une odeur, une goutte de sang ;
  - les embuscades se placent sur les routes et dans les bâtiments que les joueurs utilisent souvent (IA-6) ;
  - au palier 4, NORDA pose aussi ses embuscades, humaines celles-là (79).
- 🔗 4, 79, IA-1, IA-6.

#### 104. Semer ses poursuivants 🧠
- **Extrême** :
  - les zombies fouillent ta dernière position connue, puis abandonnent (état Recherche, IA-3) ;
  - **empreintes** dans la neige et la boue, que la pluie efface : les zombies peuvent les suivre, les joueurs aussi ;
  - **outils** :
    - traverser l'eau coupe la piste d'odeur ;
    - fumigène artisanal : bloque la vue pendant 20 s ;
    - camouflage au sang de zombie (IA-2) ;
    - leurres sonores (117) ;
    - fermer une porte derrière soi : le zombie doit l'entendre ou la sentir pour continuer.
- 🔗 117, IA-2, IA-3.

#### 116. Bestiaire ✍️📦
- **Extrême** :
  - un livre (`/bestiaire` et un exemplaire physique dans les labos) qui se remplit au fil des rencontres :
    - silhouette tant que le type n'a pas été vu, puis son nom ;
    - statistiques après 10, 50 puis 200 éliminations ;
    - faiblesses après une autopsie (19) ;
  - les variantes régionales et les mutations, avec le nom du joueur qui les a découvertes et le nom voté par la communauté ;
  - les **avis de recherche** des vétérans et des Némésis (« Recherché : l'Éventreur du garage Tremblay ») ;
  - une page par région : « ce que la région apprend » (IA-6).
- 🔗 4, 19, 66, 84, IA-6.

#### 117. Leurres sonores
- **Extrême** :
  - **réveille-matin** : sonne après un délai réglable ;
  - **radio portative** : joue de la statique ou de la musique pendant 60 s ; les zombies finissent par la détruire ;
  - **pétards** : bruit court qui provoque la panique (68) ;
  - **fusée de détresse** : lumière et bruit, attire de loin (sert aussi à l'extraction de p39) ;
  - **sirène portable** : énorme, attire une horde de toute la région… et l'attention de NORDA (règle 3) ;
  - à lancer ou à poser ; la fronde de Supplementaries permet de lancer loin 🔍 ;
  - techniquement, on réutilise le leurre invisible de la migration (p33) ;
  - si une région abuse des leurres, ses zombies ignorent les leurres bon marché (IA-6) ;
  - fabrication dans les ateliers (p52), certains avec un plan (114).
- 🔗 3, 68, 104, 114, IA-6.

### B. Hordes et bruit

#### 3. Bruit qui voyage ⚙️
- **Aujourd'hui** : jauge `/bruit` (p24), Zombie Awareness, TSAZ pour les tirs TaCZ, génératrices (p14) et usines (p17) bruyantes.
- **Extrême** : un tableau de bruit (portée de départ, en blocs), puis les règles ci-dessous.

| Source | Portée |
|---|---|
| Marcher / courir | 4 / 8 |
| Porte, bloc cassé, mêlée | 10 à 12 |
| Pistolet / avec silencieux | 48 / 16 |
| Fusil de chasse / fusil | 64 / 80 |
| Mitrailleuse | 120 |
| Explosion | 160 |
| Canon Create Big Cannons | 300 |
| Génératrice (en continu) | 24 |
| Sirène | 200 |

- **Modifié par le lieu** : intérieur × 0,5, sous terre × 0,3, orage × 0,5, pluie × 0,8, neige × 0,7, nuit × 1,2.
- **Mémoire sonore** : chaque gros bruit laisse une trace de 10 minutes dans la région. Les hordes virtuelles (IA-7) l'entendent jusqu'à 300 blocs et décident d'y aller. Quand plusieurs bruits se mélangent, le plus fort et le plus récent gagne.
- **Signaux** : `/bruit` montre aussi jusqu'où tu t'es fait entendre ; Léa signale « des coups de feu entendus près de… ».
- **La voix des joueurs** 🔍 : si l'API de Simple Voice Chat (déjà installé) est accessible sur Arclight, la voix devient du bruit. Chuchoter près des zombies, crier les attire.
- 🔗 68, 71, 108, 117, IA-2, IA-7.

#### 68. Panique
- **Extrême** :
  - une explosion, le feu ou une fusée font fuir les zombies proches pendant 10 à 20 s (état Panique, IA-3) et baissent le moral de la horde (IA-5) ;
  - **mais** l'explosion est aussi un gros bruit qui attire ceux de plus loin (règle 3) : elle te sauve maintenant et te coûte plus tard ;
  - les Alphas et les vétérans résistent mieux ;
  - si une région abuse des explosifs, ses zombies s'endurcissent (IA-6).
- 🔗 3, 117, IA-3, IA-5, IA-6.

#### 103. Hordes virtuelles 🧠⚙️
- Voir IA-7 (hordes-agents) et F4 (virtuel ↔ réel). Les hordes vivent, migrent, se divisent et fusionnent même quand personne n'est en ligne, et n'apparaissent que près des joueurs.

#### 105. Signes avant-coureurs
- **Extrême** :
  - des oiseaux s'envolent et des animaux fuient avant une horde (IA-13) ;
  - un **silence soudain** : les sons d'ambiance s'arrêtent (113) ;
  - des chiens hurlent au loin ;
  - un grondement sourd pour les très grosses hordes ;
  - un nuage de poussière à l'horizon ;
  - des corbeaux qui tournent au-dessus des cadavres et des nids ;
  - des animaux qui **reviennent** dans une zone nettoyée : la preuve que le point 80 a marché.
- 🔗 80, 113, IA-7, IA-13.

### C. Monde vivant et contamination

#### 7. Fiche d'état de chaque lieu ⚙️
- **Aujourd'hui** : les camps ont déjà population, nourriture, sécurité, moral, électricité et contamination (p44) ; `/zone` donne le danger (p39) ; `/lieu` raconte l'histoire du lieu (p62).
- **Extrême** :
  - `/ville <nom>` et un **panneau dynamique** à l'entrée de chaque lieu (ou un tableau d'affichage de Supplementaries 🔍) ;
  - on y voit : population, contamination, courant, eau, nourriture, sécurité, moral et panique, faction, hordes proches, infrastructures, végétation, état (🟢 à ☣️), et l'histoire datée ;
  - **brouillard d'information** : un joueur ne voit que ce qu'il sait. Un lieu jamais visité affiche des « ? » ou des rumeurs, avec leur date. L'information vaut quelque chose : on peut la vendre, l'acheter, la fausser (91) ;
  - l'information vieillit : « Dernières nouvelles : il y a 3 jours ».
- 🔗 74, 80, 91, F3.

#### 8. Reprendre une ville ⚙️🗺️
- **Extrême** :
  - **six étapes** : nettoyer (zombies, cadavres 1, nids 25) → sécuriser (barricades 41, lumière 42) → rétablir (courant p61, eau 85, réseau 106) → repeupler (des PNJ arrivent, réfugiés 89) → tenir (la région contre-attaque une fois : une horde-test) → fêter ;
  - la **fête** : moral en hausse, Léa en parle, un banquet au camp. Trente jours serveur plus tard, la radio rappelle l'anniversaire de la chute, puis celui de la reprise ;
  - la ville devient contrôlée par une faction : production (p67), marché, péage possible (109) ;
  - **reconstruction visible** : ZAMonde pose des versions réparées des bâtiments, étape par étape. La ville se reconstruit sous les yeux des joueurs ;
  - la végétation recule (115), les animaux reviennent (IA-13) ;
  - réversible : la ville peut retomber (74). Irréversible : sa plaque et ses anniversaires (règle 1).
- 🔗 1, 25, 41, 42, 69, 74, 80, 89, 106, 115.

#### 18. La contamination se propage ⚙️
- **Aujourd'hui** : contamination par chunk (p5), pluie toxique (p55), nappes des Bloaters (p56), traces après les sièges (p8).
- **Extrême** :
  - un champ de contamination par région et par chunk, qui **diffuse** vers les régions voisines par les liens du graphe (F3) ;
  - **les rivières transportent vers l'aval** (lien à sens unique) : ce qui est sale en amont salit l'eau en bas (85). Pas de physique, juste une règle sur le graphe ;
  - **sources** : nids, cadavres, labos détruits, pluie toxique, Bloaters, joueurs infectés qui meurent, hordes de passage ;
  - **effets** : eau impropre (85), végétation grise (115), animaux qui partent (IA-13), maladies (p27) ;
  - **mesure** : un biocapteur artisanal ; les scientifiques (19) produisent des cartes ; Léa fait un bulletin sanitaire ;
  - freins : point 80.
- 🔗 1, 19, 25, 80, 85, 115, F3.

#### 20. Chaînes d'événements ⚙️
- **Extrême** :
  - les chaînes ne sont **pas écrites d'avance** : elles naissent de la Chronique (F2), où chaque système publie et écoute ;
  - les réactions sont décrites dans `reactions.yml`, un fichier lisible qu'on peut modifier sans programmer : « si un labo est détruit, alors la contamination monte de 30 dans la région, puis une pluie toxique locale 1 à 3 heures plus tard, avec 60 % de chances » ;
  - chaque réaction a un **délai**, une **probabilité**, une **condition** et un **plafond**, pour éviter les avalanches ;
  - la Partie 5 donne huit chaînes complètes qui servent de tests.
- 🔗 F2, Partie 5.

#### 21. Freins anti-cercle vicieux
- Fusionné avec le point 80.

#### 67. Refuges trop utilisés
- **Règle** : ne vise **que** les lieux non enregistrés. Une base `/base` n'est jamais concernée (règle 2).
- **Extrême** :
  - le moteur compte le temps passé par des joueurs dans chaque bâtiment non enregistré ;
  - après un seuil (départ : 3 jours serveur cumulés), les morts « connaissent » l'endroit (mémoire de lieu, IA-3) : ils rôdent autour, puis une embuscade apparaît dedans (102), puis un risque de nid (25) ;
  - **signaux** : griffures sur les portes, zombies qui reniflent les murs, un PNJ qui prévient : « Les morts tournent autour de l'hôpital depuis que vous y dormez » ;
  - **solutions** : enregistrer une base (avec son entretien), changer de refuge, nettoyer régulièrement.
- 🔗 25, 102, IA-3, IA-6.

#### 69. Ville nettoyée = période calme
- **Extrême** :
  - après un nettoyage réussi, les apparitions baissent de 70 % pendant un nombre de jours proportionnel à l'effort ;
  - **visible** : les oiseaux reviennent, les sons d'ambiance reprennent (113), des PNJ s'installent, Léa l'annonce ;
  - le calme s'use si personne n'entretient : lumière, patrouilles, milice (p75).
- 🔗 1, 8, 80, 113, IA-13.

#### 70. Constructions abandonnées ⚙️
- **Règle** : une base enregistrée n'est **jamais** envahie automatiquement (règle 2).
- **Extrême** :
  - concerne les constructions non enregistrées, et les bases qu'un joueur abandonne volontairement (`/base abandonner`) ;
  - une construction abandonnée devient un **lieu du monde** : les morts s'y installent, son butin reste, d'autres joueurs peuvent la piller ou la reprendre. Les joueurs fabriquent ainsi des donjons pour les autres ;
  - une plaque rappelle « Ancienne base de X » ;
  - entre deux saisons, les bases des joueurs inactifs toute la saison deviennent des ruines explorables dans la saison suivante (archives p72). Ce n'est pas une punition, puisque le monde repart de toute façon.
- 🔗 25, 102, p72.

#### 71. Une faction qui tue beaucoup attire les hordes ⚙️
- **Extrême** :
  - l'attention des zombies (108) se calcule aussi par territoire : tirs, éliminations, génératrices, lumière ;
  - les hordes virtuelles convergent vers les frontières du territoire (IA-7), mais les sièges n'ont lieu que quand un membre est présent (règle 2) ;
  - `/faction` affiche une « réputation de proie » ;
  - **contre-mesures** : silencieux, mêlée, nettoyage des cadavres, moins de lumière ;
  - les factions PNJ le remarquent : certaines demandent de l'aide, d'autres ont peur (IA-10).
- 🔗 3, 108, IA-7, IA-10.

#### 80. Rouge → vert (et freins anti-cercle vicieux) ⚙️
- **Extrême** :
  - **cinq états** : 🟢 Stable, 🟡 Contaminée, 🟠 Dangereuse, 🔴 Critique, ☣️ Perdue, calculés à partir de la contamination, des nids, des hordes, des cadavres et de l'activité ;
  - **ce qui fait redescendre** : détruire des nids, tuer un boss, brûler ou enterrer les cadavres, rétablir le courant, aider les survivants, éclairer ;
  - **décontamination en trois échelles** : une pièce (combinaison et pulvérisateur), un bâtiment (douche de décontamination, chaux), une zone (station de décontamination militaire, scientifique) ;
  - **freins naturels** : chaque région revient lentement vers l'équilibre, avec un plafond par région ;
  - **réaction immunitaire du monde** : quand trop de régions sont rouges, l'armée, NORDA ou les factions PNJ interviennent (quarantaine 33, frappe incendiaire). Ça empêche le monde de mourir, et ça crée du contenu ;
  - **signaux** : couleur dans `/zone`, la radio, les animaux qui reviennent (IA-13), la végétation (115), la musique (57) ;
  - **test obligatoire** : le simulateur accéléré (F6) vérifie qu'en 60 jours, la carte ne devient pas toute rouge.
- 🔗 1, 18, 25, 33, 69, 115, F6.

#### 85. Eau contaminée et puits
- **Aujourd'hui** : soif et eau potable (p11), Tough As Nails.
- **Extrême** :
  - **sources d'eau** : rivières (contaminées par l'amont, 18), lacs, puits à réparer (106), station d'eau (106), eau de pluie (récupérateur 🔍) ;
  - boire de l'eau contaminée donne une maladie (p27) et un petit risque d'infection ;
  - **purifier** : faire bouillir (feu de camp), pastilles (rares), filtre (fabriqué, s'use) ;
  - une station d'eau réparée rend l'eau saine dans toute une région ;
  - **signal** : les poissons disparaissent de l'eau contaminée et reviennent quand elle se nettoie (IA-13).
- 🔗 18, 106, p11, p27, IA-13.

#### 111. Graffitis dynamiques 🗺️✍️
- **Extrême** :
  - quand la Chronique annonce un événement (ville tombée, nid, opération NORDA, mort d'un PNJ), des messages apparaissent sur les murs proches : « ILS SONT DANS L'HÔPITAL », « NORDA MENT », « Léa a vu des soldats ici » ;
  - certains sont **faux** (IA-9) ;
  - les joueurs peuvent écrire leurs propres graffitis avec un aérosol (nombre limité, modération admin) ;
  - NORDA lit les graffitis signés : une preuve de plus (IA-11) ;
  - ils restent comme mémoire, même quand la zone guérit (règle 1) ;
  - ZAMonde peut aussi afficher des graffitis **visibles par un seul joueur** (`Overlay`) : les hallucinations d'un joueur infecté (39).
- 🔗 39, 74, IA-9, IA-11, F2.

#### 115. La végétation reprend 🗺️
- **Extrême** :
  - chaque jour serveur, dans les zones sans passage depuis longtemps : vignes et mousse sur les murs, herbe qui perce les routes, arbustes ;
  - près des nids et dans les zones contaminées, la végétation est **grise et morte** ; dans les zones propres, des fleurs : la nature devient un signal ;
  - dans une ville reprise (8), les PNJ coupent la végétation et elle recule ;
  - réversible : le moteur garde la liste des blocs posés ;
  - budget très faible : 50 blocs par région et par jour.
- 🔗 8, 18, 80, 105.

### D. Événements et saisons

#### 2. Crash sans annonce 🗺️📦
- **Extrême** :
  - **aucune annonce** : le Directeur choisit le moment (IA-1). On entend un hélicoptère passer bas, le moteur qui toussote, une traînée de fumée, puis le crash ;
  - une **colonne de fumée** visible à 500 blocs : course entre joueurs et entre factions ;
  - **l'épave** (structure ZAMonde) contient, selon le cas :
    - du matériel militaire ou NORDA ;
    - une boîte noire (indice de l'histoire, p69) ;
    - un survivant blessé à sauver (triage, 72) ;
    - un scientifique de NORDA, que NORDA viendra récupérer (101) ;
    - un conteneur scellé : un échantillon (19)… ou un mutant ;
  - **minuterie** : le bruit du crash attire une horde qui arrive en 5 minutes environ (3, IA-7) ;
  - **variantes** : hélicoptère militaire, avion de ligne (rare, immense, lié à l'aéroport 28), drone NORDA (99), largage raté (14) ;
  - l'épave reste comme repère, avec sa plaque (règle 1).
- 🔗 3, 19, 28, 72, 99, 101, IA-1, IA-7.

#### 9. Printemps 🗺️
- **Extrême** :
  - la fonte : des zones inondables marquées par le générateur se remplissent d'eau ;
  - la boue ralentit sur certains terrains et garde les empreintes (104) ;
  - les égouts débordent (souterrains p77 partiellement inondés) ;
  - la débâcle libère les zombies pris sous la glace (27), et les Givrés dégèlent (13) ;
  - rhumes et grippes (p27) ;
  - les hordes reprennent leurs migrations (11) ;
  - les crues peuvent endommager un pont (86).
- 🔗 13, 27, 86, p27, p77.

#### 10. Été
- **Extrême** :
  - canicule (existe dans p55) : soif × 1,5, nourriture qui pourrit deux fois plus vite (p11) ;
  - feux de forêt possibles après un orage, dans des zones limitées et avec un plafond (32) ;
  - la fumée réduit la vision (55) ;
  - plus de mouches autour des cadavres (1) ;
  - zombies Brûlés (13) ;
  - nuits courtes : le Directeur concentre les événements au crépuscule.
- 🔗 1, 13, 32, 55.

#### 11. Automne
- **Extrême** :
  - brouillard plus fréquent (p55) ;
  - **la Grande Migration** : un événement saisonnier où les hordes descendent vers les villes (IA-7), annoncé par les oiseaux et la radio ;
  - les récoltes : c'est le moment de faire des réserves pour l'hiver ;
  - zombies Moisis (13) ;
  - pluies froides et risque d'hypothermie (Tough As Nails).
- 🔗 13, IA-7, IA-1.

#### 12. Hiver
- **Aujourd'hui** : p78 (neige qui s'accumule, eau qui gèle, morts ralentis, froid ajouté à la température).
- **Extrême** :
  - **blizzard** : vision très réduite, sons étouffés (3) ;
  - **routes enneigées** : le coût de passage monte sur le graphe (F3), les convois ralentissent ;
  - les génératrices brûlent 50 % de carburant en plus ; les batteries des cellulaires se vident plus vite (82) ;
  - **hibernation** : les hordes dorment dans les bâtiments (état Dormant, IA-3). Dehors, c'est le froid qui tue ; dedans, ce sont les nids endormis qu'on réveille ;
  - les lacs gelés deviennent des raccourcis, mais avec des zombies sous la glace (27) ;
  - les traces dans la neige trahissent tout le monde (104) ;
  - les camps souffrent du manque de nourriture (p44) ;
  - tempêtes qui arrachent les barricades faibles (41) et abîment les lignes électriques (106) ;
  - zombies Givrés (13).
- ⚠️ Équilibrer pour que l'hiver soit dangereux, pas pénible.
- 🔗 3, 13, 27, 41, 82, 104, 106, IA-3.

#### 14. Événements sans annonce variés
- **Extrême** : le Directeur (IA-1) pioche selon la tension et la région :
  - largage perdu, tombé en zone contaminée ;
  - convoi attaqué en cours : deux factions PNJ se battent, à toi de choisir ton camp ;
  - signal radio inconnu : des coordonnées en morse (93) ;
  - survivant poursuivi qui court vers toi avec une horde derrière ;
  - **vieille alarme** d'un bâtiment déclenchée par une surtension : elle attire une horde, il faut aller la couper (106) ;
  - incendie qui démarre (32) ;
  - chien qui te guide vers son maître blessé (IA-13) ;
  - patrouille NORDA qui passe (79) ;
  - fausse alerte (75).
- 🔗 32, 75, 79, 93, 106, IA-1.

#### 32. Catastrophes physiques ⚙️🗺️
- **Extrême** :
  - **incendie de quartier** : le feu se propage dans une zone délimitée, avec un plafond de blocs ; les bâtiments en bois deviennent des ruines ; des cendres restent au sol (Supplementaries 🔍) ;
  - **effondrement** : un bâtiment s'effondre en partie et ouvre de nouveaux passages ;
  - **dépôt de carburant** : une explosion en chaîne ;
  - **grue** qui tombe sur un chantier ;
  - **barrage** qui cède (87), inondation (9), crash (2), tempête (12) ;
  - **sécurité** : jamais sur une base enregistrée ; 200 blocs par tick au maximum ; une « photo » de la zone avant les dégâts permet la reconstruction (8) et les retours en arrière admin.
- 🔗 2, 8, 9, 12, 87.

#### 33. Zones de quarantaine militaire 🗺️
- **Extrême** :
  - déclenchées quand une région passe au rouge ou après la destruction d'un labo ;
  - l'armée ou NORDA pose un périmètre : barbelés, panneaux, points de contrôle gardés ;
  - **dedans** : beaucoup de butin et beaucoup de danger ; **en sortir infecté** peut mener à une arrestation (95, 100) ;
  - durée : quelques jours ;
  - **frappe incendiaire** possible : elle tue les morts et brûle la zone, mais détruit le butin. Les joueurs peuvent l'empêcher ou la retarder en livrant des échantillons (19) ;
  - c'est aussi un frein du point 80.
- 🔗 19, 79, 80, 95, 100.

### E. PNJ et société

#### 15. PNJ avec personnalité 🧠
- Voir IA-8 (cerveaux des PNJ) et IA-14 (compagnons). Le survivant abandonné qui revient dans une faction ennemie et se souvient de toi en est un exemple direct.

#### 16. Surnoms automatiques ✍️
- **Aujourd'hui** : titres de chasseur à 50, 200 et 500 éliminations (p20) ; hauts faits gravés (p30) ; succès secrets (p57).
- **Extrême** :
  - des surnoms tirés de la Chronique et des statistiques (`za_stat`) :
    - Le Médecin (joueurs soignés, la statistique existe déjà) ;
    - Le Fantôme (longtemps sans être vu, NORDA ne le retrouve pas) ;
    - Le Fossoyeur (corps enterrés) ;
    - Le Bâtisseur (villes reconstruites) ;
    - La Voix de Léa (missions pour la radio) ;
    - Le Revenant (a tué sa propre Némésis) ;
    - Le Traître (trahisons, p29) ;
    - Le Menteur (pris à mentir, 112) ;
    - L'Ombre de NORDA (a survécu au palier 5) ;
  - plusieurs surnoms possibles ; ils se gagnent et se perdent ;
  - Léa les utilise, les PNJ appellent le joueur par son surnom, le Hall les garde (p72).
- 🔗 77, 84, 112, IA-8, IA-12.

#### 76. Survivants qui mentent 🧠
- Voir IA-9 (mensonge lisible). Quatre sortes de réponses, toujours des indices pour démasquer.

#### 88. Les Déserteurs de Bravo 🧠✍️
- **Aujourd'hui** : l'escouade Bravo-3 du Sergent Vega et le Caporal Dumas existent dans l'histoire (plaques d'identité, promesse).
- **Extrême** :
  - une faction PNJ (IA-10) d'anciens soldats de Bravo, retranchée dans une station-service fortifiée ou un poste militaire ;
  - bien armés (TaCZ militaire), ils connaissent des secrets de NORDA (p69, p80) et vendent de l'équipement militaire (78) ;
  - **leur relation avec Vega** change les options : si Vega est vivant et que le joueur l'a aidé, ils écoutent ;
  - ils peuvent devenir des alliés… ou être chassés par NORDA (101) : le joueur choisit de les protéger ou de les livrer.
- 🔗 78, 101, p40, p69, IA-10.

#### 89. Colonnes de réfugiés 🧠
- **Extrême** :
  - des groupes de 5 à 20 PNJ voyagent sur le graphe entre les camps et les villes, et apparaissent près des joueurs (F4) ;
  - **escorte** : risquée, parce qu'une colonne fait du bruit et sent fort (3, 108) ;
  - récompense : de la population pour un camp ou une ville reprise (8), de la réputation civile (77) ;
  - attaques de pillards ;
  - **dilemmes** : un infecté dans la colonne (110, quarantaine 95), un agent NORDA caché (98).
- 🔗 8, 77, 95, 98, 110, F4.

#### 90. Conflits dans les camps 🧠
- **Extrême** :
  - la politique interne des camps (IA-8) crée des disputes : vol de nourriture, infecté soupçonné, chef contesté, quelqu'un qui veut partir ;
  - le joueur peut arbitrer par menu ; le moral et la loyauté changent selon son choix ;
  - un conflit laissé sans réponse mène à une scission, à des départs ou à de la violence ;
  - élection du chef : les joueurs de confiance peuvent voter.
- 🔗 95, 110, IA-8, IA-10.

#### 95. Quarantaine dans les camps
- **Extrême** :
  - les camps testent les arrivants avec un kit qui **peut se tromper** (110) ;
  - un infecté est refusé ou isolé (cellule de quarantaine jusqu'au traitement) ;
  - des PNJ cachent leur propre infection ;
  - un faux certificat de santé (marché noir, 78) permet d'entrer… si le chien ne grogne pas (44).
- 🔗 44, 78, 83, 110.

#### 110. Infection cachée 🧠
- **Extrême** :
  - **tests** : faux positifs et faux négatifs, selon la qualité du kit et le stade de l'infection ;
  - **PNJ qui cachent leur infection** : ils toussent, portent des bandages, évitent les chiens ;
  - un chien de garde sent les infectés (44) ;
  - au labo, une analyse de sang est fiable (19) ;
  - **le moment de la bascule** : un PNJ infecté se transforme la nuit, à l'intérieur du camp. C'est une épidémie dans le camp, et le début d'une chaîne (Partie 5).
- 🔗 19, 44, 90, 95, IA-9.

#### 112. Réputation avec témoins 🧠
- **Extrême** :
  - un crime ou un exploit compte seulement s'il a été vu : joueurs à portée de vue, PNJ avec une ligne de vue, caméras SecurityCraft 🔍, drones (99) ;
  - les témoins peuvent être soudoyés (78), intimidés, éliminés (un autre crime) ou mentir (IA-9) ;
  - les rumeurs partent des témoins vers les camps, avec un **délai** et une **déformation** (IA-8). La réputation change plus tard, et par région (77) ;
  - certaines choses forment une **réputation secrète**, connue seulement de NORDA ou du milieu criminel.
- 🔗 48, 77, 78, 99, IA-8, IA-9.

### F. NORDA

Toute la logique de NORDA est dans IA-11. Les points ci-dessous décrivent ce que le joueur vit.

#### 79. NORDA en paliers 🧠
- **Ce que chaque palier fait vivre au joueur** :

| Palier | Ce que le joueur vit |
|---|---|
| 0. Inconnu | Rien |
| 1. Intérêt | SMS étranges ; la radio NORDA parle d'« activité inhabituelle » dans sa région |
| 2. Surveillance | Drones qui observent (99) ; ses messages radio parfois interceptés (93) ; des PNJ posent des questions sur lui |
| 3. Identifié | SMS avec son nom ; avis de recherche dans les zones NORDA (48) ; cellulaire traçable (82) ; fouilles aux points de contrôle (109) |
| 4. Intervention | Patrouilles sur ses routes habituelles, barrages, embuscades humaines, chasseurs |
| 5. Priorité | Équipe de capture (100) ; la signature électrique de sa base est suivie (96) ; la radio NORDA l'interpelle publiquement |

- **Branches action → réaction** :

| Ce que fait le joueur | Ce que fait NORDA |
|---|---|
| Détruit des preuves | Baisse de certitude |
| Utilise son cellulaire avec du réseau | Obtient sa position (rayon selon les tours, 82) |
| Montre de faux papiers | Identité brouillée (83) |
| Diffuse une fausse transmission | Enquête sur une autre piste (81) |
| Attaque un convoi NORDA | Intervention renforcée |
| Sauve un scientifique | Opération pour le récupérer (101) |
| Détruit un labo | Opération de nettoyage et quarantaine (33, 101) |
| Trouve un dossier secret | Nouvelle branche d'histoire, soupçon en hausse |
| Change ses habitudes de route | Les barrages tombent à côté |

- **Redescendre** : détruire des preuves, changer ses habitudes, utiliser de faux papiers, créer de fausses pistes, ou simplement rester tranquille un moment. La baisse avec le temps profite au joueur, donc elle respecte la règle 2.
- **Le dossier physique** : quelque part dans une archive NORDA (bunker, labo), il y a un dossier sur chaque joueur. Le trouver montre **exactement** ce que NORDA croit, erreurs comprises. On peut le voler, le détruire (grosse baisse) ou y glisser de fausses informations (81).
- 🔗 81 à 83, 96, 98 à 101, 108, IA-11.

#### 81. Fausses traces 🧠
- **Extrême** :
  - **faux documents** : fabriqués à l'atelier avec un plan (114) ;
  - **fausses transmissions** : émettre sur la fréquence d'une autre faction en imitant son indicatif (107) ;
  - **preuves plantées** : les armes ont déjà un numéro de série (p49). Laisser l'arme d'une autre faction sur les lieux d'un sabotage, et NORDA l'accuse ;
  - NORDA peut détecter une fausse trace, selon sa qualité. Démasqué, le faussaire voit son propre soupçon exploser ;
  - un agent NORDA retourné (98) peut porter de fausses informations directement à NORDA.
- 🔗 49, 98, 107, 114, IA-11.

#### 82. Cellulaire traçable 🧠
- **Aujourd'hui** : le cellulaire de p70 n'a du réseau que près de la centrale ou d'une sous-station qui produit.
- **Extrême** :
  - **pas de réseau = pas de traçage** : les zones mortes deviennent des cachettes ;
  - avec du réseau, chaque SMS, appel ou connexion automatique laisse un « ping » ;
  - à partir du palier 3, NORDA reçoit une position, avec un rayon qui dépend du **nombre de tours** réparées (106). Plus il y a de tours, plus c'est précis : réparer le réseau aide tout le monde… y compris NORDA (règle 3) ;
  - on peut éteindre son cellulaire, mais on ne reçoit plus les messages des alliés ;
  - le froid vide la batterie plus vite (12).
- 🔗 12, 79, 106, p70, IA-11.

#### 83. Faux papiers
- **Extrême** :
  - un item fabriqué ou acheté au marché noir (78), avec une **qualité** ;
  - il baisse la certitude de NORDA sur ton identité, pas son soupçon ;
  - usage unique ;
  - un point de contrôle (109) peut repérer des papiers de mauvaise qualité ;
  - au palier 5, ils servent beaucoup moins.
- 🔗 78, 79, 109.

#### 96. Antenne de base
- **Extrême** :
  - construire une antenne donne à la base du réseau cellulaire et une meilleure portée radio (93) ;
  - mais elle crée une signature électrique et radio : NORDA s'intéresse à l'emplacement de la base (108) ;
  - on peut la **camoufler** : moins de portée, moins de signature. C'est un réglage, pas une solution parfaite.
- 🔗 82, 93, 108, IA-11.

#### 98. Agents NORDA infiltrés 🧠
- **Extrême** :
  - certains PNJ des camps ont un secret : ils travaillent pour NORDA (IA-8) ;
  - ils rapportent la présence et les actions des joueurs (preuves pour IA-11) ;
  - **indices** : questions inhabituelles, sorties la nuit vers une boîte aux lettres morte (on peut les **filer**), badge NORDA caché ;
  - une fois démasqué : interrogatoire par menu, puis le **retourner** (agent double qui livre de fausses informations, 81), le livrer au camp ou l'éliminer (avec témoins ou pas, 112).
- 🔗 81, 89, 112, IA-8, IA-9, IA-11.

#### 99. Drones NORDA 📦
- **Extrême** :
  - une entité volante MythicMobs avec un modèle `za_modeles` (base à choisir : allay ou phantom 🔍) ;
  - elle tourne à 30 blocs d'altitude, avec une petite lumière rouge et un bourdonnement ;
  - elle enregistre ce qu'elle voit : des preuves pour NORDA ;
  - **abattue** (TaCZ) : elle s'écrase et laisse des **données** (un extrait du dossier NORDA ou la carte de ses opérations), mais le soupçon monte dans la zone ;
  - une impulsion EMP (p34) la fait tomber ; brouiller la radio (107) l'aveugle un moment.
- 🔗 34, 79, 107, 112, IA-11.

#### 100. Capture par NORDA
- **Extrême** :
  - au palier 5, une embuscade NORDA capture au lieu de tuer : écran noir (`Hud`), réveil dans une cellule ;
  - l'équipement est confisqué dans un casier du même complexe ;
  - **interrogatoire** par menu : mentir, dire la vérité ou négocier. Les réponses changent le dossier ;
  - **sorties possibles** :
    - s'évader : conduits, gardes, récupérer son équipement ;
    - être libéré par sa faction : un événement pour les coéquipiers ;
    - accepter un marché avec NORDA (79) ;
    - sinon, transfert par convoi (101), avec une chance de sauvetage en route ;
  - jamais de mort définitive (règle 8).
- 🔗 48, 79, 101, IA-11, IA-15.

#### 101. Opérations NORDA 🧠
- **Extrême** :
  - **récupération** d'un scientifique ou d'un échantillon après un crash (2) ;
  - **nettoyage** d'un labo détruit, avec mise en quarantaine (33) ;
  - **labo mobile** : un campement scientifique qui se déplace virtuellement sur le graphe ;
  - **ratissage** d'une région pour trouver un joueur de palier 5 ;
  - **campagne de désinformation** à la radio (75) ;
  - **convoi de prisonniers** (100) ;
  - **faux vaccin** distribué aux camps (94), qui sert en réalité à suivre ceux qui le prennent ;
  - chaque opération est publiée dans la Chronique. Les joueurs peuvent l'apprendre à l'avance en décryptant la radio NORDA (93).
- 🔗 2, 33, 75, 93, 94, 100, IA-11.

#### 108. Deux jauges d'attention ⚙️
- **Extrême** :
  - **attention des zombies** : bruit, lumière, odeurs (cuisine, élevage, sang, cadavres), mouvement. Elle sert aux hordes (IA-7) et au Directeur (IA-1) ;
  - **attention de NORDA** : électricité, radio, cellulaire, antennes, labos, caméras, témoins. Elle sert à NORDA (IA-11) ;
  - **ce que le joueur voit** : `/bruit` montre l'attention des zombies ; `/signal` montre son empreinte électronique (cellulaire allumé, antenne, courant). Le palier NORDA reste caché : on le devine aux signes (79).
- 🔗 3, 79, 82, 96, IA-2, IA-7, IA-11.

### G. Radio et communications

#### 17. La radio le soir même
- Fusionné avec le point 74.

#### 51. Propagande contradictoire
- Fusionné avec le point 75.

#### 74. La radio en direct 🧠
- **Aujourd'hui** : chaque matin, Léa lit ce qui s'est vraiment passé la veille (p70).
- **Extrême** : voir IA-12. Les nouvelles arrivent le soir même, avec des sources et des degrés de certitude, et Léa suit en direct la chute d'une ville : perte de contact, explosions, évacuation, zone rouge. Elle annonce aussi les reprises (8).
- 🔗 8, IA-12.

#### 75. La radio qui ment 🧠
- **Extrême** :
  - la station NORDA ment ; la radio pirate exagère ; Léa se trompe parfois et se corrige (IA-12) ;
  - les prévisions météo sont parfois fausses ;
  - la propagande se contredit : l'armée, NORDA et la radio pirate racontent trois versions du même événement ;
  - le joueur décide qui croire ; la Chronique (F2) garde la vérité, et les indices (IA-9) permettent de la retrouver.
- 🔗 93, 101, IA-9, IA-12.

#### 93. Radio à fréquences
- **Extrême** :
  - un poste de radio avec un menu pour choisir la fréquence ;
  - **stations** : Léa (civile), Bravo (militaire, codée), radio pirate (variable), NORDA (cryptée) ;
  - **stations mortes** : messages automatiques d'avant (p31) ;
  - **stations de nombres** : des suites en morse qui donnent les coordonnées de caches ;
  - **carnets de codes** trouvés en exploration (p54, p69) pour décoder Bravo et NORDA ;
  - la force du signal dépend de la distance, des répéteurs (106) et de la météo ;
  - un poste avec haut-parleur fait du bruit (3) ; avec des écouteurs, non ;
  - **voix réelles** 🔍 : un module radio pour Simple Voice Chat permettrait aux joueurs de se parler par fréquence. Les autres peuvent écouter la même fréquence (renseignement, 91), et NORDA aussi.
- 🔗 3, 91, 106, 107, IA-12.

#### 106. Infrastructures à réparer
- **Aujourd'hui** : sous-stations électriques (p61), centrale (p39), réseau par quartier (p50).
- **Extrême** :
  - **répéteurs radio** : portée des radios ;
  - **tours cellulaires** : zones de réseau (82) ;
  - **station météo** : prévisions exactes des catastrophes (p55) et des saisons ;
  - **station d'eau** : eau saine dans la région (85) ;
  - **ponts** (86), **barrage** (87), **ascenseurs** des grands bâtiments et des bunkers, **signaux ferroviaires** (36), **éclairage public** ;
  - chaque réparation se fait en plusieurs étapes (pièces, plans 114, composants électroniques) ;
  - chaque infrastructure donne un avantage régional **et** un risque (bruit, signature NORDA, attraction des hordes) ;
  - elles peuvent être sabotées par une faction (p45) ou abîmées par les tempêtes (12). Les contrôler devient un enjeu entre factions (IA-10).
- 🔗 36, 82, 85, 86, 87, 93, 114, IA-10.

#### 107. Radio des joueurs
- **Extrême** :
  - un joueur peut émettre ses propres messages : en direct, enregistrés pour plus tard, ou en boucle (balise) ;
  - mode morse, pour les énigmes entre joueurs ;
  - portée selon l'équipement et les répéteurs (106) ;
  - **chaque émission donne une position approximative** à NORDA (82) et aux factions qui écoutent (91) ;
  - **brouilleurs** : bloquer une fréquence dans une zone ; c'est la guerre des ondes entre factions ;
  - une station pirate construite par des joueurs devient un lieu du monde ;
  - Léa peut citer les émissions des joueurs (IA-12).
- 🔗 81, 82, 91, 93, 106, IA-12.

#### 113. Ambiance sonore au loin 📦
- **Extrême** :
  - **échos d'événements réels** : quand il se passe quelque chose entre 300 et 800 blocs (combat, explosion, horde, crash), les joueurs à portée entendent un son lointain, étouffé, **dans la bonne direction**. Le monde vit ailleurs ;
  - pendant le calme, le Directeur peut ajouter des sons lointains, mais toujours plausibles ;
  - **des sons qui veulent dire quelque chose** : des coups derrière une porte = il y a vraiment un mort derrière ; des cris lointains = un PNJ en danger (SOS) ; le silence = danger (105) ;
  - ambiance propre à chaque zone (ville, forêt, souterrains, zones contaminées).
- 🔗 3, 105, IA-1.

### H. Médecine et infection

#### 19. Science ⚙️
- **Aujourd'hui** : le Dr Lefort, des labos scellés (p25), un remède possible en fin de saison (p80).
- **Extrême** :
  - **échantillons** : tissu de zombie, nid, eau, sang. Ils se gâtent sans frigo (97) ;
  - **autopsies** de zombies spéciaux (membres 24, vétérans 84) : elles révèlent les faiblesses au bestiaire (116) ;
  - **analyses** qui produisent des prédictions : carte de contamination (18), trajet des hordes (IA-7), prochaine mutation (IA-6) ;
  - **vaccin expérimental** avec des effets secondaires ;
  - **expérience qui tourne mal** : un mutant s'échappe, accident de labo (32) ;
  - **recherche collective** : une progression commune à tout le serveur, nourrie par les échantillons de tous les joueurs, qui débloque des traitements, des détecteurs et la décontamination pour tout le monde ; NORDA veut cette recherche (101) ;
  - **deux scientifiques, deux théories** : les joueurs choisissent qui financer, et ça change ce qui se débloque.
- 🔗 18, 24, 84, 97, 101, 116, IA-6, IA-7.

#### 37. Chirurgie et bloc opératoire
- Fusionné avec le point 72.

#### 39. Mutation visible du joueur infecté 📦
- **Aujourd'hui** : stades d'infection (`za_infection`), fièvre (p26, p27).
- **Extrême** :
  - **vision** : effets d'écran (vignette verte, veines, flou) grâce au code client de `za_modeles` (F7) ;
  - **sons** : battements de cœur, chuchotements au stade avancé ;
  - **hallucinations** : des zombies, des graffitis et des voix visibles seulement par le joueur infecté, grâce à `Privacy` et `Overlay` de ZAMonde (111, 22) ;
  - **corps** : la peau change sur le modèle du joueur (📦, code client) ;
  - **stratégie** : au stade terminal, les zombies l'ignorent davantage, parce qu'il sent comme eux. Mais les PNJ ont peur (95) et les chiens jappent (44).
- 🔗 22, 44, 95, 111, F7.

#### 72. Soins à trois niveaux (avec la chirurgie)
- **Aujourd'hui** : blessures par partie du corps (p53), bandage, attelle, médecin, poste de soins de l'hôpital qui demande du courant (p51).
- **Extrême** :
  - **clinique** : bandage, désinfection, antibiotiques, attelle, garrot ;
  - **hôpital** (courant obligatoire) :
    - chirurgie minutée, en étapes, par menu. Le risque dépend du rôle Médecin (p19), de la stérilité et du courant ;
    - transfusion : chaque joueur a un groupe sanguin, le don de sang entre joueurs est possible si les groupes sont compatibles ;
    - banque de sang, qui se périme sans frigo (97) ;
    - plâtre (guérison plus rapide des fractures), soins des brûlures (73) ;
  - **hôpital militaire** (rare, sur la base militaire) : chirurgie avancée, qui peut retirer une infection prise tôt ;
  - les séquelles sont **temporaires** (règle 8) ;
  - contrôler un hôpital devient un objectif de faction (production de médicaments, p67) ;
  - états de l'hôpital : débordé, sans courant, contaminé, transformé en forteresse.
- 🔗 73, 97, p19, p51, p53, p67.

#### 73. Brûlures et blessures avancées
- **Extrême** :
  - **brûlures** (feu, explosions, zombies Brûlés) en degrés, avec risque d'infection (p27) ; soins : pommade, eau froide, bloc (72) ;
  - **bras blessé** : moins de précision. 🔍 Vérifier si l'on peut agir sur la précision de TaCZ ; sinon, un tremblement de visée par le code client (F7) ;
  - **commotion** (tête) : sifflement d'oreille et flou (📦) ;
  - la jambe blessée ralentit déjà (p53).
- 🔗 72, p27, p53, F7.

#### 94. Faux remèdes
- **Extrême** :
  - des charlatans (le marchand Trafiquant, des PNJ menteurs) vendent de faux vaccins et de faux antibiotiques, identiques aux vrais ;
  - on découvre la vérité par une analyse (19)… ou après coup : aucun effet, ou des effets secondaires ;
  - les arnaques font des rumeurs (IA-8) ;
  - les joueurs peuvent aussi vendre des faux : c'est un crime (112) ;
  - NORDA distribue un « vaccin » qui sert à suivre ceux qui le prennent (101).
- 🔗 19, 78, 101, 112, IA-9.

#### 97. Frigo médical
- **Extrême** :
  - un vrai bloc de frigo (Refurbished Furniture en a, déjà installé 🔍) ;
  - tant qu'il est alimenté (réseau p61 ou génératrice p14), médicaments, échantillons et nourriture ne se gâtent pas ;
  - si le courant coupe, une minuterie démarre : les médicaments se périment, les échantillons (19) et le sang (72) se perdent, la nourriture pourrit (p11) ;
  - une alarme sonne quand le courant coupe ;
  - un frigo alimenté laisse une petite signature électrique (108).
- 🔗 19, 72, 108, p14, p61.

### I. Bases et défense

#### 41. Barricades qui s'usent
- **Extrême** :
  - des barricades reconnues (planches, barbelés, tôles) avec des points de vie par bloc ;
  - les Brutes les abîment ; le bloc change d'apparence en s'abîmant (fissures) ;
  - on répare avec des matériaux et un marteau ;
  - **barbelés** : ralentissent et blessent ; **électrifiés** : ils consomment du courant ;
  - les tempêtes abîment les barricades faibles (12) ;
  - **rapport de siège** après chaque attaque : ce qui a cédé, les morts, les réparations à faire (p8).
- 🔗 5, 12, p8, IA-5.

#### 42. Projecteurs électriques
- **Extrême** :
  - le projecteur d'Immersive Engineering (déjà installé 🔍) est orientable et consomme du courant ; sinon, des lampes Macaw's ;
  - les zombies dans le faisceau sont éblouis : lents et faibles (le mécanisme existe déjà dans p74) ;
  - **mode clignotant** : repousse les zombies ordinaires, mais attire les Phototropes ;
  - la lumière se voit de loin : les hordes et NORDA la remarquent (règle 3) ;
  - les pillards peuvent tirer dessus pour les éteindre.
- 🔗 25, 108, p61, p74.

#### 43. Canons sur les murs
- **Extrême** :
  - les canons de Create Big Cannons, avec des munitions rares (butin et atelier militaire, plans 114) ;
  - **énorme bruit** (300 blocs, point 3) et attention de NORDA ;
  - dégâts au terrain à régler dans la configuration du mod 🔍 ;
  - en JcJ, seulement pendant une offensive déclarée (45).
- 🔗 3, 45, 114.

#### 44. Chiens de garde
- **Extrême** :
  - un loup apprivoisé qu'on entraîne par étapes :
    - **garde** : jappe quand un zombie approche à 24 blocs ; alerte le maître et l'alarme de la base (p23) ;
    - **pisteur** : suit les pistes d'odeur et de sang (26, 104) pour retrouver des joueurs, des PNJ ou des caches ;
    - **détecteur** : grogne contre les infectés qui se cachent (110) ;
  - il faut le nourrir ;
  - il peut être infecté (23) : le soigner au labo (19) ou le perdre ;
  - un chien célèbre a sa place au Hall des survivants.
- 🔗 19, 23, 26, 104, 110, p23.

### J. Factions et économie

#### 45. Offensives de territoire
- **Aujourd'hui** : territoires (p45), sabotage, diplomatie et trêves (p67), `/negociation`, `/treve`.
- **Extrême** :
  - **déclaration** avec un ultimatum de 24 heures ;
  - **objectifs** : des points de capture (bannières au cœur du territoire) ;
  - **fenêtres d'attaque** : seulement quand au moins un défenseur est connecté, pour éviter les raids pendant que l'autre camp dort (règle 2) ;
  - défense avec la milice (p75) et les canons (43) ;
  - **issue** : le territoire change de main (p45), avec les ressources, des prisonniers (48), puis un traité (p67) ;
  - des factions PNJ peuvent se joindre comme alliées (IA-10) ; Léa couvre la guerre (IA-12).
- 🔗 43, 48, 49, 109, p45, p67, IA-10.

#### 46. Inflation locale
- **Aujourd'hui** : cours qui bougent avec le monde (p68), pénuries (p7), ressources stratégiques (p48).
- **Extrême** :
  - **prix par région** sur le graphe : l'offre et la demande, les guerres, les blocus (92), les tempêtes (12) ;
  - écarts de prix entre régions : des routes commerciales rentables, des joueurs qui deviennent marchands ;
  - prix affichés sur des tableaux, mais l'information vieillit (7) ;
  - une crise économique régionale peut suivre une catastrophe.
- 🔗 7, 12, 47, 92, p68.

#### 47. Marchands itinérants
- **Aujourd'hui** : cinq marchands nomades (Charognard, Médecin, Trafiquant, Collectionneur, Mécano) et le jour du marché noir (p7).
- **Extrême** :
  - ils voyagent virtuellement sur le graphe (F4), avec des gardes, un horaire et une route ;
  - leur stock dépend de la région d'où ils viennent ;
  - on peut les escorter (contrat), les braquer (crime, 112), ou les voir mourir en route ;
  - un marchand peut mentir sur son stock ou sa qualité (94, IA-9).
- 🔗 46, 92, 94, 112, F4.

#### 48. Prison et procès
- **Aujourd'hui** : primes, trahison, négociation (p29).
- **Extrême** :
  - **avis de recherche** affichés sur les tableaux des camps (Supplementaries 🔍), avec la tête du joueur recherché ;
  - **chasseurs de primes** : joueurs et PNJ ;
  - **arrestation** : un joueur recherché mis hors de combat par une faction qui a une prison est capturé au lieu d'être tué ;
  - **procès** : jury de joueurs ou chef de faction ;
  - **preuves** : témoins (112), enregistrements radio (107), caméras SecurityCraft 🔍, documents ;
  - **peines** : amende, travaux, exil d'un territoire, échange de prisonniers ;
  - évasions et attaques de prison ;
  - ⚠️ à encadrer par des règles de serveur claires sur le JcJ.
- 🔗 26, 45, 107, 112, p29.

#### 49. Arsenal de faction
- **Aujourd'hui** : armes en 4 niveaux avec numéro de série, état et historique ; munitions spéciales (perforantes, explosives, incendiaires, slug) (p49).
- **Extrême** :
  - chaque faction peut fabriquer une arme ou une finition signature 🔍 (packs d'armes TaCZ) ;
  - les numéros de série sont enregistrés à la faction : une preuve… ou une fausse preuve (81) ;
  - capacité de production limitée par l'atelier militaire (p52) ;
  - certaines armes sont interdites dans certains territoires et repérées aux points de contrôle (109).
- 🔗 81, 109, p49, p52.

#### 77. Plusieurs réputations
- **Aujourd'hui** : `/reputation` (p7), relations entre factions (p67), confiance des camps (p44).
- **Extrême** :
  - **pistes séparées** : civils, militaires (Milice, Bravo), marchands, milieu criminel, NORDA (cachée), et chaque faction PNJ ;
  - **par région** : on peut être un héros ici et un traître là-bas, parce que les rumeurs voyagent avec du retard (112) ;
  - **effets** : prix, accès (équipement militaire, marché noir 78, hôpitaux 72), dialogues (IA-8), surnoms (16) ;
  - **conflits** : aider les criminels fait baisser la réputation civile ;
  - **réputation secrète** : connue seulement de NORDA ou du milieu criminel.
- 🔗 16, 72, 78, 112, IA-8.

#### 78. Marché noir permanent
- **Aujourd'hui** : le jour du marché noir, quand tous les marchands se réunissent 15 minutes (p7).
- **Extrême** :
  - un lieu caché qui **change de place** ; on l'apprend par une rumeur du milieu criminel (77) ;
  - accès par réputation criminelle ou par mot de passe (la radio pirate le donne chaque semaine) ;
  - **à vendre** : technologie NORDA, faux papiers (83), armes militaires (49), objets volés, renseignements (91), cartes de caches ;
  - **receleur** : les joueurs y vendent des objets volés, mais les objets marqués (numéro de série) restent traçables (48, 81) ;
  - **dangers** : descentes de la milice ou de NORDA, arnaques (94).
- 🔗 49, 77, 81, 83, 91, 94.

#### 91. Renseignement
- **Extrême** :
  - **moyens** : écouter la radio d'une faction près de son territoire (93), voler les documents d'un convoi (92), soudoyer un PNJ (IA-8), placer un informateur, voler le registre d'une faction, observer à la longue-vue ;
  - **on apprend** : les stocks, les contrats, la date d'une offensive (45), l'horaire des convois (92) ;
  - le renseignement devient un objet, un « rapport », qui se vend (78), se falsifie (81) et se périme ;
  - avec des voix réelles sur la radio 🔍, l'espionnage devient vrai : on écoute vraiment l'autre faction.
- 🔗 45, 78, 81, 92, 93, IA-8.

#### 92. Convois de ravitaillement
- **Extrême** :
  - des convois virtuels entre les territoires d'une faction, à pied avec des charrettes ou par train (36) ;
  - horaires et trajets connaissables par le renseignement (91) ;
  - escorte sous contrat ou embuscade (braquage) : butin, mais une guerre peut commencer ;
  - les factions PNJ ont leurs convois aussi (IA-10) ;
  - la marchandise transportée change les prix des régions (46).
- 🔗 36, 46, 91, IA-10.

#### 109. Péages et points de contrôle
- **Extrême** :
  - les factions (joueurs et PNJ) construisent des points de contrôle sur les routes de leur territoire ;
  - **péage** en jetons ; **fouille** : la contrebande (liste propre à chaque faction) et la qualité des faux papiers (83) ;
  - NORDA installe les siens à partir du palier 3 (79) ;
  - on peut contourner par des routes plus dangereuses : un vrai choix ;
  - pour un point de contrôle de joueurs, ce sont des gardes PNJ qui fouillent, jamais un piège automatique.
- 🔗 49, 79, 83, F3.

#### 114. Plans rares
- **Aujourd'hui** : le menu des ateliers (p52) sait déjà griser une recette en expliquant pourquoi.
- **Extrême** :
  - des plans qui débloquent des recettes : militaires (obus, silencieux), NORDA (brouilleur de drone, grenade EMP, combinaison de décontamination), médicaux (outils de chirurgie, sérum), de survivant (filtre à eau, barbelés électrifiés), électroniques (répéteur radio) ;
  - souvent en **morceaux** (3 à 5), trouvés dans des régions différentes : nouveaux lieux (28 à 31), crashs (2), boss (6), convois (92) ;
  - une copie par faction ; un plan peut être volé (91) ;
  - un plan légendaire unique par saison (p72).
- 🔗 2, 6, 28 à 31, 91, 92, p52.

### K. Lieux et monde physique

#### 28. Aéroport et avion écrasé 🗺️
- **Extrême** :
  - un terminal où des survivants ont tenu (journaux) ;
  - une **tour de contrôle** dont la radio longue portée se répare (106) : un contact avec l'extérieur, et une piste pour l'histoire ;
  - une traînée de débris de 300 blocs jusqu'à l'avion ;
  - un hangar avec des pièces de drones (99) ;
  - un dépôt de carburant qui peut exploser (32) ;
  - la piste sert de zone d'extraction pour l'hélicoptère de p39.
- **Autres lieux** à ajouter dans la même passe : une gare (36), une université (labo civil, 19), un port sur la rivière, un hôtel.
- 🔗 2, 19, 32, 36, 99, 106.

#### 29. Centre d'achat 🗺️
- **Extrême** :
  - un donjon sur plusieurs étages ;
  - avec le courant, les escaliers mécaniques repartent (courroies Create) ;
  - aire de restauration (nourriture), pharmacie, poste de sécurité avec caméras (SecurityCraft) ;
  - un cinéma plein de morts endormis (état Dormant, IA-3) ;
  - un camp perdu qui a tenu à l'intérieur, avec son histoire.
- 🔗 102, 106, IA-3.

#### 30. Aréna de hockey 🗺️
- **Extrême** :
  - un grand refuge possible pour un camp (p44) ;
  - la glace de la patinoire, avec des morts dessous (27) ;
  - les gradins comme marché ou lieu de rassemblement ;
  - un site de siège mémorable quand une horde arrive.
- 🔗 27, 41, p44.

#### 31. Prison 🗺️
- **Extrême** :
  - des prisonniers infectés, une armurerie (49) ;
  - des cellules utilisables par les factions (48) ;
  - une émeute passée a donné naissance à une faction de pillards (IA-10) ;
  - la salle de contrôle ouvre toutes les cellules : un événement d'évasion.
- 🔗 48, 49, IA-10.

#### 34. Habillage du monde 🗺️
- **Extrême** :
  - une passe du générateur qui ajoute des **scènes** dans les bâtiments : le dernier souper d'une famille, une salle de bain barricadée avec des notes, du ruban de quarantaine, des bagages abandonnés, des mains ensanglantées sur un mur ;
  - des lettres et notes (p6, p69), cohérentes avec la chronologie du prologue (les horloges arrêtées au même moment, les calendriers figés) ;
  - des photos (p69), des graffitis (111) ;
  - les points d'embuscade (102) se placent dans la même passe.
- 🔗 102, 111, p6, p69.

#### 35. Mods déco pas encore utilisés
- **Extrême** :
  - Macaw's Lights : lampadaires du réseau électrique (p50) ;
  - Macaw's Bridges : ponts réparables (86) ;
  - Macaw's Paintings : intérieurs ;
  - Supplementaries : tableaux d'affichage (avis de recherche 48, prix 46), drapeaux de faction, cendres (32) 🔍 ;
  - Refurbished Furniture : frigos (97), téléviseurs, ordinateurs 🔍.
- 🔗 32, 46, 48, 86, 97.

#### 36. Ligne de train 🗺️
- **Aujourd'hui** : Create et Steam 'n' Rails sont installés.
- **Extrême** :
  - une ligne qui relie les villes, posée par le générateur avec des trous : segments arrachés, ponts détruits (86), tunnels bloqués (p77) ;
  - réparation en plusieurs étapes : rails, aiguillages, signaux, stations de ravitaillement ;
  - les trains servent de convois (92) et d'évacuation de réfugiés (89) ;
  - un train fait du bruit et attire les hordes (3) ;
  - les gares deviennent des places fortes de faction, ou des refuges ;
  - **déraillement** (32) ; un **train de cargo NORDA** à attaquer (101) ;
  - projet de fin de partie : un train blindé construit par une faction.
- 🔗 3, 86, 89, 92, 101, 106.

#### 86. Ponts détruits 🗺️
- **Extrême** :
  - le générateur détruit ou abîme certains ponts : des passages obligés sur la carte ;
  - réparation avec Macaw's Bridges et des matériaux, en plusieurs étapes (106) ;
  - **faire sauter un pont** volontairement pour arrêter une horde : les hordes suivent les liens du graphe et doivent faire un détour (IA-7) ;
  - les crues du printemps peuvent l'abîmer (9) ; une faction peut y poser un péage (109).
- 🔗 9, 106, 109, IA-7.

#### 87. Barrage endommagé 🗺️
- **Aujourd'hui** : des barrages existent déjà dans les lieux générés (p73).
- **Extrême** :
  - réparer les turbines (Create ou Immersive Engineering) donne du courant à toute la région (p61) ;
  - des fissures grandissent si on le néglige ou si on l'attaque ;
  - **s'il cède** : la zone inondable en aval se remplit, les camps du bas sont détruits. C'est irréversible pour l'histoire de la saison ; la carte se rétablit après la décrue ;
  - les factions se le disputent ; NORDA s'intéresse à sa signature électrique ;
  - c'est l'arène de la Chose du barrage (6).
- 🔗 6, 32, 106, IA-10, IA-11.

### L. Survie

#### 38. Poids de l'inventaire
- **Extrême** :
  - un poids par catégorie (armes, munitions, blocs, nourriture) ;
  - paliers : plus lent, plus de faim, et des pas plus bruyants (3) ;
  - les sacs (Sophisticated Backpacks) ajoutent de la place mais aussi du poids ;
  - le vrai choix : rapporter le butin ou pouvoir fuir ;
  - calculé seulement quand l'inventaire change, jamais à chaque tick.
- 🔗 3, 104.

#### 40. Chaux vive et produits chimiques
- Fusionné avec les points 1 et 80.

### M. Histoire et immersion

#### 50. Vraies voix ✍️
- **Aujourd'hui** : 11 répliques en voix de synthèse (Piper, `za_modeles` 1.6) ; les clés `voix.*` existent déjà.
- **Extrême** :
  - un appel aux amis pour les rôles ; enregistrement au téléphone, puis filtre radio ;
  - une banque de répliques par station (IA-12) ;
  - de courtes phrases de PNJ selon la personnalité (« Ils arrivent ! », « Merci… ») ;
  - Léa a sa voix principale.
- 🔗 22, IA-12.

#### 52. Cassettes 📦
- **Extrême** :
  - des enregistrements audio à collectionner (sons dans `za_modeles`) avec leur transcription en livre ;
  - placés par le générateur (34), portés par des vétérans (ceux de leurs victimes) ;
  - les écouter avec un baladeur ou un poste ; avec haut-parleur, ça attire les morts (règle 3) ;
  - des arcs d'histoire sur plusieurs cassettes (NORDA, Arel, des familles) ;
  - certaines contiennent du morse ou une fréquence (93).
- 🔗 34, 84, 93.

#### 53. Cinématiques
- **Aujourd'hui** : `Cameras` de ZAMonde fait déjà des cinématiques fluides ; p80 en utilise une.
- **Extrême** :
  - introduction de saison, apparition des boss (6), chute d'une ville (74), crash (2), fin de saison ;
  - bandes noires et sous-titres (code client, F7) ;
  - courtes, et on peut les passer.
- 🔗 2, 6, 74.

#### 54. Sang, impacts et cadavres 📦
- **Extrême** :
  - particules de sang à l'impact (possible côté serveur) ;
  - taches de sang au sol (bloc mince de `za_modeles`) effacées par la pluie (26) ;
  - impacts de balles sur les murs 🔍 ;
  - corps qui restent quelques minutes, puis deviennent des compteurs de cadavres (1).
- 🔗 1, 26.

#### 55. Fumée et cendres
- **Extrême** :
  - colonnes de fumée (incendies, crash 2), cendres qui tombent sur les zones brûlées (Supplementaries 🔍), poussière dans les ruines, spores autour des nids (25), brume dans les zones contaminées (18) ;
  - une colonne de fumée se voit de loin : par les hordes, par NORDA, et par les autres joueurs (règle 3).
- 🔗 2, 18, 25, 32.

#### 56. Resource pack ZA 📦
- **Extrême** :
  - écran titre avec un panorama de Saint-Aurèle en ruines, écran de chargement ;
  - interface : bruit, attention, infection, blessures ;
  - polices et icônes (bestiaire 116) ;
  - le tout dans `za_modeles` (F7).
- 🔗 116, F7.

#### 57. Musique dynamique 📦
- **Extrême** :
  - une musique en couches pilotée par l'intensité du Directeur (IA-1) : calme, tension, combat, horde ;
  - des thèmes par région ; des signatures sonores (Némésis, boss, crash) ;
  - le silence comme outil ;
  - côté client dans `za_modeles` ; le serveur envoie seulement l'état.
- 🔗 80, IA-1, F7.

#### 58. Shaders et sons
- **Extrême** :
  - un preset de shaders officiel « apocalypse » (Oculus, à tester avec EMF 🔍) ;
  - Sound Physics Remastered (écho dans les tunnels, parfait avec 113) et AmbientSounds ;
  - un pack facultatif pour les bons PC.
- 🔗 64, 113.

### N. Technique et communauté

#### 59. Discord 🔍
- **Extrême** :
  - pont entre le chat Discord et le jeu (DiscordSRV à tester avec Arclight, ou un webhook envoyé par ZAMonde) ;
  - les bulletins de Léa publiés chaque jour dans un salon « radio » (IA-12) : le monde parle aussi sur Discord ;
  - avis de recherche des Némésis (84), guerres de factions, inscriptions à la whitelist (61), classements (62), alertes admin (F5).
- 🔗 61, 62, 84, F5, IA-12.

#### 60. Carte 3D sur le web (BlueMap) 🔍
- **Extrême** :
  - des calques venus de ZAMonde : couleurs des zones (80), territoires (p45), lieux **déjà découverts par la communauté** (pour garder le brouillard d'information, 7) ;
  - **jamais** la position des hordes en direct, ça tuerait la tension ; seulement les observations rapportées par la radio ;
  - rendu la nuit, mis à jour par morceaux.
- 🔗 7, 80.

#### 61. Whitelist
- **Extrême** : inscription par formulaire sur Discord, validation manuelle, une ou deux questions pour comprendre le style de jeu.
- 🔗 59.

#### 62. Classement
- **Extrême** :
  - jours survécus, Némésis vaincues, villes reprises, recherche apportée (19), réputations ;
  - par saison, gardé au Hall (p72) ;
  - en jeu et sur Discord ;
  - pas de classement des joueurs tués, pour ne pas encourager le harcèlement.
- 🔗 19, 59, p72.

#### 63. Menu admin `/zaadmin`
- **Extrême** :
  - voir l'état du Directeur pour chaque joueur ;
  - forcer, inspecter et annuler chaque système (régions, hordes, dossiers NORDA, cerveaux de PNJ) ;
  - simulateur accéléré (F6) ;
  - activer ou couper chaque système ;
  - retours en arrière des catastrophes (32) ;
  - rapport de télémétrie (F5).
- 🔗 F5, F6.

#### 64. Mods d'optimisation dans le modpack 🔍
- **Extrême** : Embeddium, EntityCulling, ImmediatelyFast, FerriteCore, ModernFix côté client ; test de compatibilité avec EMF, ETF et `za_modeles` ; un profil « petit PC ».
- 🔗 58.

#### 65. Sauvegardes et redémarrages
- **Extrême** :
  - redémarrage quotidien planifié sur Apex, annoncé dans le jeu : « Coupure de courant générale dans 5 minutes » (Léa) ;
  - sauvegardes quotidiennes et avant chaque mise à jour, copie de la base ZAMonde ;
  - une copie hors d'Apex chaque semaine.
- 🔗 F1.

## Partie 4 — Les systèmes déjà en place, poussés plus loin

Les 88 scripts existants ne sont pas jetés : ils deviennent le contenu que le moteur et l'IA font vivre. Pour chacun, voici où il peut aller. Les numéros entre parenthèses renvoient aux 117 points.

### Histoire

- **Prologue, jour 0 à 8 (p38)** :
  - les choix du prologue alimentent dès le départ les cerveaux des PNJ (IA-8) et le dossier NORDA (IA-11) ;
  - un mode « souvenir » pour revivre le prologue sans rien changer ;
  - vraies voix (50) et cinématiques retravaillées (53).
- **Grande histoire et parcours (p40, p60)** :
  - les chapitres du parcours se ramifient selon les réputations (77) et le palier NORDA (79) ;
  - le Directeur narratif (IA-1) règle le rythme de chaque joueur.
- **Dossier Arel, énigmes, enquêtes (p69, p54)** :
  - les indices sont répartis entre les régions et dans la **tête des PNJ** (IA-8) : certains savent, d'autres mentent (IA-9) ;
  - placement dynamique : un indice déjà trouvé ne réapparaît pas, un indice manqué peut revenir par un autre chemin.
- **Échos de Saint-Aurèle (p63)** : les survivants du prologue deviennent des PNJ complets (IA-8) ; ceux qui sont devenus zombies gardent leurs souvenirs de vie (IA-4).
- **Fin de saison (p41, p80)** :
  - le choix final pèse tout : réputations, croyances de NORDA, recherche collective (19), villes tenues (8) ;
  - plus de fins possibles ;
  - la saison suivante démarre à partir des archives : ruines des bases (70), légendes, mémoire de NORDA, descendants des PNJ.

### Mémoire du monde

- **Journal, chronique, mémoire des lieux (p21, p62, p71)** : ils deviennent des vues de la Chronique (F2). Une **chronologie publique** pour tous, et une **chronologie secrète** (la version de NORDA) qu'on peut trouver.
- **Stèles et Rue des disparus (p58)** : la Némésis (IA-4) est nommée sur la stèle de sa victime ; on peut y déposer des objets en hommage.
- **Archives de saison et Hall (p72, p41)** : un vrai **musée physique** construit automatiquement à chaque fin de saison (cadres, panneaux, objets, reliques), avec une aile pour les chiens célèbres (44) et une pour les Némésis vaincues.
- **Légendes et reliques (p30, p64)** : chaque relique garde l'historique de ceux qui l'ont portée ; les têtes de Némésis deviennent des reliques.
- **Titres et succès (p20, p57)** : reliés aux surnoms (16) et au bestiaire (116).

### Survie et corps

- **Soif, nourriture, sommeil (p11)** : rareté régionale de l'eau et de la nourriture (46, 85) ; les frigos changent la conservation (97).
- **Température et hiver (p15, p78)** : vêtements adaptés, tempêtes et blizzards (12), carburant de chauffage.
- **Maladies, hygiène, épuisement (p27)** : maladies selon la saison (9 à 12) et selon l'eau (85).
- **Virus et souches (p12, p26, `za_infection`)** : la souche d'une région suit son génome (IA-6) ; les stades d'infection deviennent visibles (39) ; l'infection peut se cacher (110).
- **Blessures (p53)** : prolongées par les points 72 et 73.
- **Cadavres (p13)** : prolongés par le point 1.

### Combat et équipement

- **Armes v2 (p49)** :
  - le numéro de série devient une preuve (81) ;
  - une arme rouillée s'enraye plus et fait plus de bruit (3) ;
  - arsenal de faction (49).
- **Ateliers (p52)** : plans rares (114) ; les ateliers bruyants attirent (3) ; un atelier électronique alimenté laisse une signature (108).
- **Rôles (p19 : soldat, médecin, ingénieur, éclaireur)** :
  - le médecin opère (72) ;
  - l'ingénieur répare les infrastructures plus vite (106) ;
  - l'éclaireur lit les signes avant-coureurs (105) et les traces (104) ;
  - ajouter un rôle de **radioamateur** qui décode les fréquences (93).
- **Squads et moral (p28)** : le moral du groupe nourrit l'intensité du Directeur (IA-1) ; un groupe soudé résiste mieux à l'horreur psychologique.
- **Progression (p7)** : de nouveaux paliers liés aux réputations (77) et à la recherche collective (19).

### Monde et lieux

- **Électricité (p50, p61)** :
  - équilibrage réel de la charge par région, sur le graphe (F3) ;
  - les pannes se propagent ; les tempêtes abîment les lignes (12) ;
  - vol de courant entre factions (repérable) ;
  - le barrage (87) alimente toute une région ;
  - chaque installation électrique a sa signature pour NORDA (108).
- **Monde vivant (p39)** : `/zone`, nids, convois, extraction et évolution des lieux deviennent des morceaux du graphe (F3) et du point 80.
- **Bâtiments et lieux (p35, p51, p73)** : chaque bâtiment a un état complet (7), peut tomber, être repris (8) et se reconstruire.
- **Saint-Aurèle en ruines (p66)** : la ruine évolue (végétation 115, effondrements 32) et peut être reconstruite (8).
- **Souterrains et labos (p77, p25)** :
  - nids endormis sous la ville (IA-3) ;
  - inondations au printemps (9) ;
  - archives NORDA avec les dossiers des joueurs (79) ;
  - accès par cartes magnétiques SecurityCraft 🔍 de différents niveaux (le badge NORDA).
- **Catastrophes et événements (p55, p3)** : régionales au lieu de globales, avec des effets physiques (32) et des prévisions exactes si la station météo est réparée (106).
- **Air toxique et EMP (p34)** : les zones toxiques suivent la contamination (18) ; l'EMP abat les drones (99) et coupe les réseaux.
- **Ambiance et horreur (p31, p4)** : pilotées par le Directeur (IA-1), le stade d'infection (39) et l'isolement ; les hallucinations peuvent être privées (`Privacy`, `Overlay`).

### Zombies

- **Apparitions, soleil, aube, routes, migration (p36, p32, p74, p76, p33)** : ils deviennent le « corps » du cerveau des zombies (IA-3) et des hordes-agents (IA-7). Le leurre invisible de p33 sert de moyen de déplacement à toute l'IA.
- **Meute (p79)** : prolongée par la tactique de groupe (IA-5).
- **Zombies intelligents (p56)** : prolongés par les sens (IA-2), l'évolution régionale (IA-6) et la Némésis (IA-4).
- **Comportements rares et butin par métier (p65)** : prolongés par l'individualité (IA-4).
- **Boss (za_boss, p37)** : prolongés par les boss régionaux (6).
- **Horde (za_horde)** : devient un objectif possible des hordes-agents (IA-7) et un outil du Directeur (IA-1).

### Société

- **Survivants et camps (p43, p44)** : cerveaux de PNJ (IA-8), politique interne (90), quarantaine (95), réfugiés (89), reconstruction (8).
- **Relations et social (p46, p9, p29)** : réseau social des PNJ (IA-8), témoins (112), rumeurs.
- **PNJ et quêtes (p18)** : les quêtes naissent des objectifs personnels des PNJ (IA-8) au lieu d'être fixes.
- **Factions, territoires, diplomatie (p45, p67)** : factions PNJ stratèges (IA-10), offensives (45), péages (109), convois (92).
- **Marché, cours, économie, ressources (p47, p68, p7, p48)** : prix régionaux (46), information à vendre (91), marché noir permanent (78).
- **Ondes et téléphone (p70)** : stations et fréquences (93), Léa journaliste (IA-12), réseau par tours (106), traçage (82), faux appels des imitateurs (22).

### Défense

- **Bases et sièges (p8)** : barricades (41), rapport de siège, règle des sièges conservée (seulement quand un joueur est présent).
- **Tourelles (p16)** : elles ont besoin de munitions ou de courant, et elles font du bruit (3).
- **Défense et alarmes (p23)** : l'alarme se branche sur les chiens de garde (44).
- **Milice (p75)** : soldats avec moral, loyauté et expérience (IA-14).
- **Génératrices, usines, bruit (p14, p17, p24)** : intégrées au tableau de bruit (3) et aux deux attentions (108).

### Accueil

- **Guide des dix premières minutes (p81)** : le Directeur protège les nouveaux (IA-1), et le guide apprend à **lire les signaux** (bruit, animaux, corbeaux, radio), parce que tout le reste du serveur repose dessus.
- **Finition et performance (p10, p5)** : budget par tick, virtualisation (F4), télémétrie (F5).

## Partie 5 — Chaînes de conséquences (scénarios de test)

Aucune de ces chaînes n'est écrite d'avance dans le code : chacune doit **naître** des règles de réaction (F2). Pour tester, on force la première étape avec `/zaadmin` et on vérifie que la chaîne se rend au bout, avec les bons signaux pour le joueur. Si une étape ne se déclenche jamais, c'est un branchement manquant.

### Chaîne 1 — Le coup de feu de trop
1. Un joueur vide un chargeur de fusil en pleine ville (3).
2. La trace sonore dure 10 minutes ; une horde virtuelle à 250 blocs l'entend et change d'objectif (IA-7).
3. La horde passe par un camp de survivants sur sa route et attaque ses barricades (41, IA-5).
4. Une barricade cède ; un PNJ connu meurt (IA-8).
5. Panique dans le camp ; le moral chute ; une famille décide de partir (7, 90).
6. La colonne de réfugiés prend la route (89) ; des pillards l'attaquent.
7. Léa en parle le soir même (IA-12).
8. Une faction rivale voit une occasion et envoie un convoi pour s'installer (IA-10, 92).
- **Signaux à vérifier** : le son de la horde qui approche, les oiseaux qui s'envolent (105), le panneau du camp qui change (7), le bulletin de Léa, la fiche de faction rivale.
- **Réussi si** : le joueur peut remonter toute la chaîne jusqu'à son coup de feu en lisant la Chronique (`/lieu`, `/souvenirs`, radio).

### Chaîne 2 — Le labo
1. Des joueurs font sauter un labo scellé (p25).
2. La contamination de la région bondit (18) ; une pluie toxique locale suit quelques heures plus tard (p55).
3. La rivière transporte la contamination vers l'aval (F3, 85) ; les poissons disparaissent (IA-13).
4. Le village en aval tombe malade (p27) ; des PNJ meurent ou partent.
5. L'armée pose une quarantaine (33).
6. NORDA lance une opération de nettoyage (101) et cherche les responsables (IA-11).
- **Signaux** : ciel de la souche (p31), eau qui rend malade, panneaux de quarantaine, SMS inconnu, bulletin sanitaire.
- **Réussi si** : le soupçon NORDA des joueurs monte seulement s'il existe une preuve réelle (témoin, caméra, drone, objet laissé).

### Chaîne 3 — La Némésis
1. Un zombie tue un joueur (IA-4).
2. Il devient vétéran nommé et prend le casque et l'arme de sa victime.
3. Léa signale un mort « armé » dans le secteur (IA-12) ; un avis de recherche s'ajoute au bestiaire (116).
4. Quelques jours plus tard, le Directeur organise la revanche, ailleurs (IA-1).
5. Le joueur gagne : surnom « Le Revenant » (16), haut fait (p30), il récupère son équipement, la tête devient une relique.
- **Signaux** : nom au-dessus du zombie, équipement visible, musique signature (57).
- **Réussi si** : la Némésis ne réapparaît jamais en vue directe ; elle arrive comme une vraie rencontre.

### Chaîne 4 — Le traître du camp
1. Un agent NORDA vit dans un camp (98) et rapporte les visites d'un joueur.
2. NORDA monte le joueur au palier 2 ; un drone vient l'observer (99).
3. Le joueur abat le drone et récupère ses données : on y voit qu'un informateur parle (IA-11).
4. Le joueur file les PNJ du camp la nuit et surprend l'agent à une boîte aux lettres morte (98).
5. Il retourne l'agent et lui fait livrer une fausse piste (81).
6. NORDA envoie son barrage au mauvais endroit (IA-11).
- **Signaux** : questions bizarres du PNJ, bourdonnement du drone, nouvelle entrée du dossier, barrage visible ailleurs.
- **Réussi si** : NORDA agit sur une croyance fausse, et le joueur peut le constater.

### Chaîne 5 — La ville reprise
1. Une faction nettoie une ville : zombies, cadavres, nids (1, 25, 69).
2. Elle rétablit le courant (106, p61) ; les lampadaires se rallument.
3. La lumière se voit de loin : une horde est attirée (règle 3, IA-7) et NORDA remarque la signature (108).
4. La faction tient la défense (41 à 44).
5. Fête ; la ville passe au vert (8, 80) ; la végétation recule (115), les animaux reviennent (IA-13).
6. Trente jours serveur plus tard, Léa rappelle l'anniversaire de la reprise.
- **Signaux** : couleur de la zone, retour des sons d'ambiance (113), panneau de la ville, plaque conservée « Chute de… ».
- **Réussi si** : la plaque de la chute reste, même quand la ville est verte (règle 1).

### Chaîne 6 — Le barrage
1. Une faction répare les turbines du barrage (87) : du courant pour toute la région.
2. NORDA repère la signature électrique (108) et s'y intéresse (IA-11).
3. Une tempête (12) ou un sabotage d'une faction rivale (p45) fissure le barrage.
4. Personne ne répare à temps : le barrage cède, la zone en aval est inondée (32).
5. Un camp en aval est détruit ; ses survivants deviennent des réfugiés (89).
6. Léa couvre la catastrophe en direct (74).
- **Signaux** : bruit de fissure, alertes de l'ingénieur, montée de l'eau, radio.
- **Réussi si** : la catastrophe ne touche jamais une base enregistrée (règle 2), et la carte se rétablit après la décrue.

### Chaîne 7 — Le cellulaire
1. Un joueur au palier 3 utilise son cellulaire dans une zone avec trois tours réparées (82, 106).
2. NORDA obtient sa position avec un petit rayon d'incertitude (IA-11).
3. NORDA pose un barrage sur la route que le joueur prend toujours (habitudes, 4).
4. Le joueur change de route (104) ou présente de faux papiers au point de contrôle (83, 109).
- **Signaux** : SMS qui dit « Nous savons où tu es », barrage visible au loin.
- **Réussi si** : avec une seule tour, le rayon est trop grand pour que NORDA trouve le joueur.

### Chaîne 8 — L'infecté caché
1. Un réfugié infecté cache son état (110) et entre dans un camp ; le test du camp se trompe (95).
2. Un chien de garde grogne contre lui (44) ; personne n'écoute.
3. La nuit, il se transforme à l'intérieur du camp : épidémie (110).
4. Le camp se divise sur quoi faire : brûler, isoler, fuir (90).
5. Les survivants fuient en colonne (89) ; le camp devient un nid (25).
6. Une quarantaine est posée (33) ; un scientifique demande des échantillons du nouveau nid (19).
- **Signaux** : toux du PNJ, chien qui grogne, cris la nuit, cloche du camp.
- **Réussi si** : les joueurs présents avaient au moins deux indices avant la transformation (IA-9).

## Partie 6 — Ce qui reste impossible, et comment le contourner

| Impossible | Pourquoi | Contournement |
|---|---|---|
| Véhicules | Aucun mod fiable avec Arclight ; la map est pensée autour des routes bloquées | Trains Create (36), convois à pied (92), hélicoptère d'extraction (p39) |
| Une IA qui pense vraiment | Le jeu tourne avec des règles | Règles nombreuses et branchées (Partie 2) ; niveau Ω pour la parole (IA-15) |
| Dialogues libres sans payer | Il faut un modèle de langage | Gabarits riches (IA-8) ; niveau Ω payant |
| Modèles 3D côté serveur (ModelEngine) | Incompatible avec MythicMobs 5.7.2 sur Arclight | `za_modeles` côté client choisit le modèle par le nom |
| Vraie physique de l'eau et du vent | Trop lourd, et invisible | Règles sur le graphe (rivières vers l'aval), zones inondables prédéfinies |
| Des milliers de zombies réels | Le serveur tient quelques centaines d'entités | Hordes virtuelles et renforts en continu (F4) |
| Voix générées en direct | Apex n'héberge que Java | Banque de répliques enregistrées, texte toujours unique |
| Calcul lourd sur Apex | CPU partagé | Simulation hors du fil principal, budgets, profils spark |

### À vérifier avant de construire 🔍

Ces points dépendent d'un mod, d'une compatibilité ou d'un détail technique qu'on n'a pas encore testé :

- **Simple Voice Chat** : son API est-elle accessible à un plugin sur Arclight (voix des joueurs comme bruit, point 3) ?
- **Radio vocale** : un module radio pour Simple Voice Chat existe-t-il pour Forge 1.20.1, et marche-t-il avec Arclight (93) ?
- **Immersive Engineering** : le projecteur orientable (42).
- **Refurbished Furniture** : frigos, téléviseurs et ordinateurs (97, 35).
- **Supplementaries** : tableaux d'affichage, cendres, fronde, haut-parleur (7, 32, 48, 117).
- **SecurityCraft** : cartes magnétiques par niveau, caméras comme preuves (112, p77).
- **Create Big Cannons** : réglage des dégâts au terrain (43).
- **TaCZ** : peut-on modifier la précision d'une arme selon une blessure (73) ? Peut-on ajouter des finitions de faction (49) ?
- **Oculus avec EMF et ETF** : compatibilité des shaders (58).
- **DiscordSRV et BlueMap** sur Arclight (59, 60).
- **Zombie Awareness** : ce qu'il fait déjà avec le sang et les odeurs (26).
- **Tough As Nails** : récupérateur d'eau de pluie (85).
- **Skript 2.9.5** : SQLite sans le plugin SQLibrary (F8).
- **Drones** : quelle entité de base vole bien sans traverser les murs (99).

## Annexe — Index des 117 points

| N° | Point | Domaine | Marques |
|---|---|---|---|
| 1 | Cadavres → nid | Zombies | ⚙️ |
| 2 | Crash sans annonce | Événements et saisons | 🗺️📦 |
| 3 | Bruit qui voyage | Hordes et bruit | ⚙️ |
| 4 | Nouvelles adaptations | Zombies | 🧠 |
| 5 | Rôles dans la horde | Zombies | 🧠 |
| 6 | Un boss par région | Zombies | ⚙️📦🗺️ |
| 7 | Fiche d'état de chaque lieu | Monde vivant et contamination | ⚙️ |
| 8 | Reprendre une ville | Monde vivant et contamination | ⚙️🗺️ |
| 9 | Printemps | Événements et saisons | 🗺️ |
| 10 | Été | Événements et saisons |  |
| 11 | Automne | Événements et saisons |  |
| 12 | Hiver | Événements et saisons |  |
| 13 | Zombies de saison | Zombies | 📦 |
| 14 | Événements sans annonce variés | Événements et saisons |  |
| 15 | PNJ avec personnalité | PNJ et société | 🧠 |
| 16 | Surnoms automatiques | PNJ et société | ✍️ |
| 17 | La radio le soir même (fusionné → 74) | Radio et communications |  |
| 18 | La contamination se propage | Monde vivant et contamination | ⚙️ |
| 19 | Science | Médecine et infection | ⚙️ |
| 20 | Chaînes d'événements | Monde vivant et contamination | ⚙️ |
| 21 | Freins anti-cercle vicieux (fusionné → 80) | Monde vivant et contamination |  |
| 22 | Imitateurs | Zombies | 📦🧠 |
| 23 | Chiens infectés et corbeaux | Zombies | 📦 |
| 24 | Démembrement | Zombies | 📦 |
| 25 | Nids qui grandissent | Zombies | 🗺️📦 |
| 26 | Trace de sang | Zombies |  |
| 27 | Noyés et zombies sous la glace | Zombies | 📦 |
| 28 | Aéroport et avion écrasé | Lieux et monde physique | 🗺️ |
| 29 | Centre d'achat | Lieux et monde physique | 🗺️ |
| 30 | Aréna de hockey | Lieux et monde physique | 🗺️ |
| 31 | Prison | Lieux et monde physique | 🗺️ |
| 32 | Catastrophes physiques | Événements et saisons | ⚙️🗺️ |
| 33 | Zones de quarantaine militaire | Événements et saisons | 🗺️ |
| 34 | Habillage du monde | Lieux et monde physique | 🗺️ |
| 35 | Mods déco pas encore utilisés | Lieux et monde physique |  |
| 36 | Ligne de train | Lieux et monde physique | 🗺️ |
| 37 | Chirurgie et bloc opératoire (fusionné → 72) | Médecine et infection |  |
| 38 | Poids de l'inventaire | Survie |  |
| 39 | Mutation visible du joueur infecté | Médecine et infection | 📦 |
| 40 | Chaux vive et produits chimiques (fusionné → 1, 80) | Survie |  |
| 41 | Barricades qui s'usent | Bases et défense |  |
| 42 | Projecteurs électriques | Bases et défense |  |
| 43 | Canons sur les murs | Bases et défense |  |
| 44 | Chiens de garde | Bases et défense |  |
| 45 | Offensives de territoire | Factions et économie |  |
| 46 | Inflation locale | Factions et économie |  |
| 47 | Marchands itinérants | Factions et économie |  |
| 48 | Prison et procès | Factions et économie |  |
| 49 | Arsenal de faction | Factions et économie |  |
| 50 | Vraies voix | Histoire et immersion | ✍️ |
| 51 | Propagande contradictoire (fusionné → 75) | Radio et communications |  |
| 52 | Cassettes | Histoire et immersion | 📦 |
| 53 | Cinématiques | Histoire et immersion |  |
| 54 | Sang, impacts et cadavres | Histoire et immersion | 📦 |
| 55 | Fumée et cendres | Histoire et immersion |  |
| 56 | Resource pack ZA | Histoire et immersion | 📦 |
| 57 | Musique dynamique | Histoire et immersion | 📦 |
| 58 | Shaders et sons | Histoire et immersion |  |
| 59 | Discord | Technique et communauté | 🔍 |
| 60 | Carte 3D sur le web (BlueMap) | Technique et communauté | 🔍 |
| 61 | Whitelist | Technique et communauté |  |
| 62 | Classement | Technique et communauté |  |
| 63 | Menu admin `/zaadmin` | Technique et communauté |  |
| 64 | Mods d'optimisation dans le modpack | Technique et communauté | 🔍 |
| 65 | Sauvegardes et redémarrages | Technique et communauté |  |
| 66 | Adaptation par région | Zombies | 🧠 |
| 67 | Refuges trop utilisés | Monde vivant et contamination |  |
| 68 | Panique | Hordes et bruit |  |
| 69 | Ville nettoyée = période calme | Monde vivant et contamination |  |
| 70 | Constructions abandonnées | Monde vivant et contamination | ⚙️ |
| 71 | Une faction qui tue beaucoup attire les hordes | Monde vivant et contamination | ⚙️ |
| 72 | Soins à trois niveaux (avec la chirurgie) | Médecine et infection |  |
| 73 | Brûlures et blessures avancées | Médecine et infection |  |
| 74 | La radio en direct | Radio et communications | 🧠 |
| 75 | La radio qui ment | Radio et communications | 🧠 |
| 76 | Survivants qui mentent | PNJ et société | 🧠 |
| 77 | Plusieurs réputations | Factions et économie |  |
| 78 | Marché noir permanent | Factions et économie |  |
| 79 | NORDA en paliers | NORDA | 🧠 |
| 80 | Rouge → vert (et freins anti-cercle vicieux) | Monde vivant et contamination | ⚙️ |
| 81 | Fausses traces | NORDA | 🧠 |
| 82 | Cellulaire traçable | NORDA | 🧠 |
| 83 | Faux papiers | NORDA |  |
| 84 | Zombies vétérans | Zombies | 🧠 |
| 85 | Eau contaminée et puits | Monde vivant et contamination |  |
| 86 | Ponts détruits | Lieux et monde physique | 🗺️ |
| 87 | Barrage endommagé | Lieux et monde physique | 🗺️ |
| 88 | Les Déserteurs de Bravo | PNJ et société | 🧠✍️ |
| 89 | Colonnes de réfugiés | PNJ et société | 🧠 |
| 90 | Conflits dans les camps | PNJ et société | 🧠 |
| 91 | Renseignement | Factions et économie |  |
| 92 | Convois de ravitaillement | Factions et économie |  |
| 93 | Radio à fréquences | Radio et communications |  |
| 94 | Faux remèdes | Médecine et infection |  |
| 95 | Quarantaine dans les camps | PNJ et société |  |
| 96 | Antenne de base | NORDA |  |
| 97 | Frigo médical | Médecine et infection |  |
| 98 | Agents NORDA infiltrés | NORDA | 🧠 |
| 99 | Drones NORDA | NORDA | 📦 |
| 100 | Capture par NORDA | NORDA |  |
| 101 | Opérations NORDA | NORDA | 🧠 |
| 102 | Embuscades dans le décor | Zombies | 🗺️ |
| 103 | Hordes virtuelles | Hordes et bruit | 🧠⚙️ |
| 104 | Semer ses poursuivants | Zombies | 🧠 |
| 105 | Signes avant-coureurs | Hordes et bruit |  |
| 106 | Infrastructures à réparer | Radio et communications |  |
| 107 | Radio des joueurs | Radio et communications |  |
| 108 | Deux jauges d'attention | NORDA | ⚙️ |
| 109 | Péages et points de contrôle | Factions et économie |  |
| 110 | Infection cachée | PNJ et société | 🧠 |
| 111 | Graffitis dynamiques | Monde vivant et contamination | 🗺️✍️ |
| 112 | Réputation avec témoins | PNJ et société | 🧠 |
| 113 | Ambiance sonore au loin | Radio et communications | 📦 |
| 114 | Plans rares | Factions et économie |  |
| 115 | La végétation reprend | Monde vivant et contamination | 🗺️ |
| 116 | Bestiaire | Zombies | ✍️📦 |
| 117 | Leurres sonores | Zombies |  |
