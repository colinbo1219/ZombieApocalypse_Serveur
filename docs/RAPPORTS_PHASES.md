# Rapports de fin de phase (MISSION §57)

Rien de ce qui suit n'a été testé en jeu : il n'y a pas de serveur dans la session cloud.
Validation faite : relecture, `python3 docs/outils/verif_skript.py plugins/Skript/scripts/*.sk` (indentation,
guillemets, `%` appariés, blocs vides, fonctions appelées mais jamais définies) → aucune anomalie sur les 67+ scripts.

---

## PHASE 2 — Finaliser le prologue

**MODIFICATIONS**
- `plugins/Skript/scripts/za_p38_prologue.sk`
- `plugins/Skript/scripts/za_p4_horreur.sk` (garde prologue sur `on chat`)
- `plugins/Skript/scripts/za_p9_social.sk` (garde prologue sur `on chat`)

**NOUVEAUX FICHIERS** : `docs/outils/verif_skript.py` (vérificateur statique).

**SYSTÈMES AJOUTÉS**
- **États de Saint-Aurèle** (MISSION §10) : `za_pro_ville(p, n)` affiche en barre d'action et dans le chat l'état de la
  ville : 1 VILLE NORMALE (J0) → 2 ALERTE SANITAIRE (J1) → 3 QUARANTAINE (J3) → 4 PANIQUE (incident de l'urgence) →
  5 ÉPIDÉMIE (J5) → 6 EFFONDREMENT (J7) → 7 BLACKOUT → 8 APOCALYPSE (réveil au Jour 8). Publié dans
  `{za::pro::ville::<uuid>}` pour les autres modules.
- **Entractes Jours 2, 4 et 6** (MISSION §8 et §32) : carte noire + texte + SMS + radio (texte seul, sans voix) entre
  les chapitres : les barrages (J2), les voitures abandonnées (J4), l'armée (J6). ~16 s chacun, la montée est plus lente.
- **Premier zombie** (MISSION §9) : alerte courte « QUELQUE CHOSE vient de se relever. » au moment où Mme Gagnon se
  relève, avant « TU N'ES PLUS EN SÉCURITÉ ».

**SYSTÈMES MODIFIÉS**
- Enchaînement des chapitres : `maison1` → entracte J2 → J3 ; `maison3` → entracte J4 → J5 ; `sortie5` → entracte J6 → J7.
  `/prologue chapitre` saute toujours directement au chapitre demandé (pas d'entracte).
- `za_p4_horreur` (l'Écho) et `za_p9_social` (les noms) ne récupèrent plus les messages tapés dans le prologue.

**DÉPENDANCES** : aucune nouvelle.

**RISQUES** : les entractes n'ont pas de voix (fichiers .ogg absents) : texte seul, volontairement.

**TESTS** : statiques seulement. À tester en jeu : `/prologue lancer <joueur>` puis suivre J0 → blackout ; vérifier la
barre d'action à chaque chapitre et les trois entractes.

**RESTE À FAIRE** : enregistrer des voix pour les entractes si tu le souhaites (clés libres : `voix.radio_j2`, `j4`, `j6`).

---

## PHASE 3 — Choix + conséquences

Constat : les 4 choix (hôpital, Leblanc, Théo, Vega) ont déjà beaucoup de conséquences (`za_p46_relations`,
`za_p44_camps` pour Leblanc/Théo, `za_p60_parcours`, `za_p57_succes`). Rien n'a été recréé.
Ce qui manquait : le devenir des **personnages secondaires** du prologue.

**NOUVEAUX FICHIERS** : `plugins/Skript/scripts/za_p63_echos.sk` — « Échos de Saint-Aurèle ».

**SYSTÈMES AJOUTÉS**
- 6 personnages du prologue reviennent, une seule fois pour tout le serveur, chez un joueur dont les choix le permettent :
  Ginette (tous), Rita (tous), Infirmière Côté (hôpital aidé), Policier Roy (Leblanc sauvée), Soldat Nguyen (Vega obéi),
  Soldat Ortiz **infecté** (ruelle clandestine). Les survivants passent par le module survivants (`za_p43`) : ils se
  recrutent, se nourrissent, peuvent mourir ou disparaître (puis être recroisés 3 jours plus tard).
- Retrouvailles : réplique personnelle qui cite ce que le joueur a fait, souvenir personnel, mémoire du monde, et
  bonus de relation (Côté → Lefort +5 ; Nguyen → Vega +5 et Milice +5).
- Roy remet le **carnet de l'agente Pelletier** : premier document au format MISSION §45 (n°, date, lieu, auteur).
- Mort d'un écho : Léa l'annonce à la radio, journal du serveur. Ortiz abattu : plaque d'identité (compte pour Vega).
- Outil partagé `za_doc_donner(p, numéro, date, lieu, auteur, titre, texte)` : livre avec fiche en première page,
  pages séparées par `||`.
- Admin : `/zaecho` (état) · `/zaecho lancer <id> <joueur>` · `/zaecho reinit <id>`.

**SYSTÈMES MODIFIÉS** : aucun (le module lit `za_p43`, `za_p46`, `za_p62` via leurs fonctions publiques).

**VARIABLES** : `{za::echo::<id>::etat|id|pour|jour|loc}`, `{za::echo::der::<uuid>}`, `{za::echo::salue::<id>::<uuid>}`.

**RISQUES**
- Chaque écho occupe une place de survivant « libre » (max 3, règle de `za_p43`).
- Le nom du villageois choisit la peau via le pack : « Infirmière… », « Policier… », « Soldat… ».

**TESTS** : statiques. En jeu : `/zaecho lancer ginette <toi>`, suivre l'indice radio, s'approcher à moins de 6 blocs.

**RESTE À FAIRE** : rien de bloquant.

---

## PHASES 4 et 5 — Système électrique Create, relié à la ville et aux bases

**NOUVEAUX FICHIERS** : `plugins/Skript/scripts/za_p61_electricite.sk`

**MODIFICATIONS**
- `za_p50_reseau.sk` : 3 lignes dans `za_reseau_appliquer` : un quartier est aussi allumé quand les sous-stations
  l'alimentent (`{za::elec2::alim::<quartier>}`). Tous les effets existants (postes de soins, armoires de police,
  prix, sanité…) marchent donc avec la vraie énergie, sans rien dupliquer.
- `za_p10_finition.sk` (/aide) et `za_p60_parcours.sk` (commandes du niveau 6) : mention de `/electricite`.

**SYSTÈMES AJOUTÉS**
- **Sous-stations réelles** : le joueur construit un tableau (n'importe quel bloc) et y amène le signal d'une vraie
  machine : accumulateur Create Crafts & Additions, compteur de vitesse ou stressomètre Create, condensateur Immersive
  Engineering → comparateur → fil de redstone collé au tableau. La puissance du fil (0-15) donne 0 à 5 unités. Pas de
  machine Create/CCA/IE à 4 blocs = 0 unité (anti-torche). Chunk déchargé = dernière mesure gardée.
- **Chaîne CENTRALE → SOUS-STATION → QUARTIER → BÂTIMENTS** : les sous-stations « ville » (posées par l'admin dans les
  ruines, voir phase 8) relaient la centrale historique (4 unités quand elle tourne) mais démarrent **endommagées** :
  objectif « Réparer la sous-station nord ».
- **Réserve partagée + priorités** (MISSION §18) : hôpital > police > résidentiel > commerce par défaut, modifiable par
  ceux qui font tourner une sous-station (`/electricite priorite …`). En cas de manque, les derniers sont coupés.
- **États par quartier** : ALIMENTÉ / PARTIEL / PANNE / BLACKOUT, annoncés par CKZA et inscrits dans la mémoire du monde.
- **Production / consommation** (MISSION §16-17) : petits générateurs = `za_p14` (base), moyenne = machines Create
  (sous-station joueur, jusqu'à 5 u.), grande = centrale (via sous-stations de ville) ; conso hôpital 4, police 3,
  résidentiel 3, commerce 2.
- **Pannes et réparations** (MISSION §19-20) : surcharge quotidienne (8 %, 15 % au-delà de 4 u.), foudre pendant les
  tempêtes (`za_p55`). Réparer = 2 Composants électroniques (1 pour l'ingénieur) + 4 lingots de cuivre, 20 s immobile,
  des zombies arrivent : il faut défendre. Stat `reparations_reseau`.
- **Bases** (phase 5) : base sous tension si une sous-station produit à 48 blocs ou si un générateur `za_p14` tourne.
- **Lumière et zombies** (MISSION §21-22) : la nuit, zone alimentée (base, bâtiment d'un quartier alimenté, sous-station)
  = les zombies à 28 blocs deviennent visibles (brillance) et la sanité remonte ; quartier en blackout = message
  d'obscurité. Chaque sous-station qui produit ajoute de l'activité (`za_activite_ajouter`) : hordes attirées.

**COMMANDES** : `/electricite` (alias `/elec`, `/courant`) `[installer [quartier] | retirer | reparer | priorite … | aide]`,
admin `/zaelec etat | panne <id> | reparer <id> | supprimer <id> | ville <x> <y> <z> <monde> <quartier> <nom_souligné> | tick`.

**VARIABLES** : `{za::elec2::ss::<id>::loc|nom|quartier|type|etat|prod|fil|proprio|triche}`, `{za::elec2::ss::liste::*}`,
`{za::elec2::alim|etat::<quartier>}`, `{za::elec2::base::<uuid>}`, `{za::elec2::reserve|surplus|prio::*|jour}`.

**DÉPENDANCES** : aucune nouvelle (Create, CCA, IE déjà installés).

**RISQUES**
- Détection des blocs moddés par leur nom de type (« create », « immersive » + mot-clé), comme `za_p17_usines` :
  si `/electricite` affiche « aucune machine à 4 blocs » alors qu'il y en a une, envoyer le nom affiché par `/zaelec`.
- Lecture de la puissance par `block data` du fil de redstone (texte `power=N`) : à vérifier sur Arclight.
- Condition `is redstone powered` : syntaxe Skript 2.9 standard, non testée ici.

**TESTS** : statiques. En jeu : poser un accumulateur CCA chargé, un comparateur, un fil, un bloc de laine au bout,
`/electricite installer`, attendre 15 s, `/electricite`. Puis `/zaelec panne <id>` et `/electricite reparer`.

**RESTE À FAIRE** : placer les sous-stations de ville quand les ruines seront posées (phase 8, commandes fournies).

---

## PHASES 6 et 7 — Zombies custom 2.0 : apparences, animations, sons

**NOUVEAUX FICHIERS**
- `pack_joueurs/za_modeles-1.3.0.jar` : **nouvelle version du mod client** (remplace 1.2.0 dans le pack des joueurs).
- `ZA_sources/modeles_generateur/extension_1_3.py` (dans le zip des sources) : fabrique 1.3.0 à partir du jar 1.2.0 déployé.
- `plugins/Skript/scripts/za_p65_zombies_vivants.sk` : scènes rares et butin par métier.

**MODIFICATIONS**
- `plugins/MythicMobs/Mobs/ZombieApocalypse.yml` : 6 nouveaux zombies + 1 son d'identité ajouté à 14 types existants
  (lignes ajoutées seulement, les sons vanilla existants restent ; Stalker rendu presque silencieux : volume 0,25).
- `plugins/Skript/scripts/za_p36_apparitions.sk` : zombies du lieu + forêt la nuit + zones contaminées.

**SYSTÈMES AJOUTÉS**
- **Apparence par métier** (MISSION §24) : `ZA_Policier_Infecte` (uniforme marine, insigne, casquette),
  `ZA_Medecin_Infecte` (blouse blanche, stéthoscope, pantalon de bloc), `ZA_Ouvrier_Infecte` (dossard orange à bandes,
  casque jaune), `ZA_Ouvrier_Brule` (carbonisé, braises, fumée, met le feu), `ZA_Pompier_Infecte` (tenue sombre à bandes
  jaunes, casque noir), `ZA_Prisonnier_Infecte` (combinaison orange, rapide). Textures générées depuis les citoyens
  infectés du pack (même visage, mêmes blessures).
- **Zombies par environnement** (MISSION §25) près des bâtiments `za_p35` : hôpital → patients / médecins ;
  labo → médecins, patients, spitters ; police → policiers, prisonniers, blindés ; caserne → soldats, blindés ;
  centrale → ouvriers, ouvriers brûlés ; station-service → pompiers ; école → enfants ; forêt la nuit → stalkers /
  crawlers ; chunk très contaminé (≥ 150) → brutes, screamers, spitters, bloaters. Le plafond par joueur est inchangé.
- **Animations** (MISSION §26-27, mod client) : humains infectés (citoyens, patients, soldats, nouveaux métiers) :
  regard qui balaie à l'arrêt, tic rare de la tête, boiterie (jambe droite raide), bras qui pendent.
  Côté serveur (`za_p65`), scènes rares ≈ 5 % toutes les 20 s par joueur, max une toutes les 4 min : le mort qui te
  **fixe**, le mort qui **mange** (particules, bruits de mastication), le mort qui **frappe une porte**, le mort **figé**.
- **Identité sonore** (MISSION §28) : 15 sons `za_modeles:zombie.*` (respiration rapide du Runner, respiration lourde du
  Bloater, hurlement du Screamer, Stalker quasi silencieux, grondement grave de l'Alpha, pas métalliques du blindé…),
  construits sur des sons vanilla (aucun fichier audio ajouté), avec sous-titres. L'Overlord garde sa signature.
- **Butin par métier** : munitions 9 mm TaCZ (policier), bandages / antibiotique (médecin), masque à gaz rare (pompier),
  note de survivant (prisonnier).
- Admin : `/zazv scene <regard|repas|porte|immobile> [joueur]`.

**DÉPENDANCES** : aucune nouvelle côté serveur. Côté joueurs : mettre `za_modeles-1.3.0.jar` à la place de 1.2.0.

**RISQUES**
- Un joueur qui garde le mod 1.2.0 voit les nouveaux zombies avec la peau « Zombie » générique et n'entend pas les
  nouveaux sons (pas de plantage).
- Les animations sont écrites dans le même format que celles de 1.2.0 mais n'ont pas été vues en jeu (EMF).
- Les scènes rares utilisent `tp … facing` vanilla sur l'entité : si un zombie « glisse », baisser `scene_chance`.

**TESTS** : statiques + YAML MythicMobs relu par un parseur (38 mobs), properties vérifiées au même format que 1.2.0,
planche des 6 textures contrôlée visuellement. En jeu : `/mm mobs spawn ZA_Policier_Infecte`, `/zazv scene regard`.

**RESTE À FAIRE** : mettre le jar dans le pack CurseForge des joueurs (voir `docs/A_INSTALLER.md`).

---

## PHASE 8 — La ville avant / après

**NOUVEAUX FICHIERS**
- `plugins/ZAMonde/ruines.json.gz` + `ruines_pois.json` : **Saint-Aurèle en ruines**, structure ZAMonde (288×48×288,
  791 182 blocs, 570 états de bloc tous validés contre le rapport officiel 1.20.1).
- `plugins/Skript/scripts/za_p66_ruines.sk` : la ville dans le monde de survie.
- `plugins/Skript/scripts/za_p66_ruines_donnees.sk` : lampes par quartier (généré, ne pas éditer).
- `ZA_sources/ville/gen_ruines.py` (dans le zip des sources) : générateur déterministe.

**MODIFICATIONS** : `za_p36_apparitions.sk` (zombies des ruines selon le quartier).

**SYSTÈMES AJOUTÉS**
- **Même ville, après** (MISSION §32) : la ville du prologue figée au soir du Jour 8 — les calques du prologue
  (dépanneur fermé, quarantaine, incident, chaos, checkpoint) deviennent de vrais blocs ; toutes les lampes éteintes ;
  ~50 % des vitres brisées (toiles d'araignée) ; vignes sur les façades ; herbes et fissures dans les rues ; débris ;
  station-service incendiée avec cratère ; panneaux réécrits (« ZONE MILITAIRE — Ordre de tirer à vue »,
  « NE PAS ENTRER — MORTS À L'INTÉRIEUR », « ILS SONT DEDANS », « Z-01 : OUVERT »…).
- **Reconnaissance** (MISSION §50) : 11 lieux du prologue déclenchent un souvenir la première fois qu'on s'en approche
  (ton appartement, le lit de Mme Gagnon, la barrière où Leblanc est tombée, la ruelle du checkpoint…), le texte
  dépend de **tes** choix. Titre « SAINT-AURÈLE — Population : 0 » à l'entrée. **Mot de Maman** dans le coffre du 2A.
- **Mémoire du monde** : 8 lieux inscrits (`sa:hopital`, `sa:police`, `sa:depanneur`, `sa:station`, `sa:immeuble`,
  `sa:cafe`, `sa:ecole`, `sa:parc`) : ils vivent ensuite comme tous les lieux de `za_p62` (contamination, chute…).
- **Électricité dans la ville** (fin de la phase 5) : 4 sous-stations de ville (hôpital, police, rue Principale,
  Érables) créées **endommagées** ; une fois réparées et la centrale relancée, le quartier est alimenté et **ses
  lampadaires se rallument pour de vrai** (321 lampes réparties par quartier).
- **Zombies des ruines** : patients / médecins / crawlers à l'hôpital, policiers / soldats / prisonniers au poste,
  citoyens / pompiers / runners rue Principale, citoyens / enfants dans le quartier résidentiel.

**INSTALLATION (à faire une fois, en jeu)** : pré-générer la zone avec Chunky, se placer au centre voulu (terrain
plat, idéalement à 150-300 blocs de l'autobus d'arrivée), puis `/zaville installer`. Suivi : `/zamonde etat`.

**DÉPENDANCES** : aucune.

**RISQUES**
- La pose remplace 288×48×288 blocs (`degager`) : choisir un endroit sans construction de joueur. Sauvegarder avant.
- Les lampes ne changent que dans les tronçons chargés (rattrapage toutes les 5 min quand un joueur est dans la ville).
- Chaque changement de lampes écrit une ligne `setblock` par lampe dans la console (bruit de log, sans danger).

**TESTS** : génération exécutée (5,9 s), palette validée (0 état invalide), aperçu du dessus avant/après contrôlé,
vérificateur Skript OK. Non testé en jeu : la pose, les souvenirs, les lampes.

**RESTE À FAIRE** : `/zaville installer` sur le serveur.

---

## PHASE 9 — Survivants + camps

Constat : survivants (`za_p43`, histoire, métier, faction, moral, état, lieu, mort, camp) et camps (`za_p44`,
population, vivres, sécurité, moral, contamination, attaques, chute) sont complets. Les personnages du prologue
peuvent désormais rejoindre un camp (phase 3). Il manquait la statistique **Électricité** (MISSION §34).

**MODIFICATIONS** : `za_p44_camps.sk` (13 lignes).

**SYSTÈMES MODIFIÉS**
- Camp sous tension si une sous-station qui produit (`za_p61`) est à 64 blocs : chaque jour moral +2, sécurité +3,
  mais +5 % de risque d'attaque (le bruit). Affiché dans « État du camp » avec un conseil (`/electricite`).
  Publié : `{za::camp::<id>::elec}`.

**RISQUES** : aucun nouveau. **TESTS** : statiques. **RESTE À FAIRE** : rien.

---

## PHASE 10 — Factions + territoires

Constat : réputation (`za_p40`), territoires qui changent de propriétaire avec défense / raid / reconquête (`za_p45`)
existent. Il manquait : **ressources**, **alliés / ennemis**, **contrats** de faction (MISSION §35).

**NOUVEAUX FICHIERS** : `plugins/Skript/scripts/za_p67_diplomatie.sk`

**MODIFICATIONS**
- `za_p45_territoires.sk` : 2 lignes dans `za_terr_change` (seul point de changement de propriétaire) →
  `za_diplo_changement`.
- `za_p40_histoire.sk` : `/faction` accepte `diplomatie`, `ressources`, `contrats`, `livrer <faction>`.

**SYSTÈMES AJOUTÉS**
- Relations entre les 6 factions (-100..100), valeurs de départ cohérentes avec l'histoire (Milice/Pilleurs et
  Scientifiques/Culte ennemis, Marchands neutres avec tous). Prendre un territoire à une faction : -20. Passage en
  guerre ouverte annoncé par Léa. Dérive lente vers la neutralité (sauf rivaux historiques).
- Ressources par faction (vivres, médicaments, munitions, carburant, énergie) produites par leurs territoires,
  consommées chaque jour ; pénurie = emprise -3/jour ; abondance = +2/jour ; quartier sous tension = +1 énergie.
- Contrats : une faction en pénurie publie un contrat à la radio ; le livrer rapporte réputation + jetons, plaît à ses
  alliés et déplaît à ses ennemis. Stat `contrats_faction`.
- Admin : `/zadiplo etat | jour | set | stock`.

**RISQUES** : la production modifie `{za::terr::<clé>::ctrl}` (±3 max par jour) : équilibre à surveiller.

**TESTS** : statiques. En jeu : `/zadiplo stock milice munitions 0`, `/zadiplo jour`, `/faction contrats`.

**RESTE À FAIRE** : rien de bloquant.

---

## PHASE 11 — Marché joueur + marché dynamique

Constat : le marché entre joueurs (`za_p47`) couvre déjà tout le §36 : vendre, acheter, rechercher, prix (moyenne des
10 dernières ventes), quantité, expiration (7 jours de jeu), historique, pénurie par objet, sans nouvelle monnaie.
Manquait le §37 : des prix qui bougent avec le monde.

**NOUVEAUX FICHIERS** : `plugins/Skript/scripts/za_p68_cours.sk`

**MODIFICATIONS** : `za_p7_economie.sk` : `za_prix_marchand` applique le cours de la catégorie ; l'achat utilise
désormais `za_prix_marchand` (avant, il utilisait `za_prix` : la remise ingénieur sur les pièges était affichée mais
**pas appliquée** — corrigé au passage).

**SYSTÈMES AJOUTÉS** : cours par catégorie (vivres, médicaments, munitions, armes, carburant, matériaux), de ×0,70
à ×1,80, influencés par les stocks des factions (`za_p67`), les hordes, la lune de sang, les catastrophes, l'absence
totale de courant, la faim des camps (pénurie régionale). Annonces radio aux seuils ×1,30 et ×0,85. `/cours`,
admin `/zacours`.

**RISQUES** : les prix des marchands peuvent monter jusqu'à ×1,8 : surveiller l'économie la première semaine.

**TESTS** : statiques. En jeu : `/zacours set munitions 1.5` puis ouvrir le Trafiquant.

---

## PHASE 12 — Exploration + énigmes

Constat : énigmes (coffres scellés, codes, dossiers), chasse au trésor (fragments A/B/C → carte → bunker Z-01) et
enquêtes existent (`za_p54`). Ajout : une **exploration en couches dans Saint-Aurèle en ruines** (MISSION §40).

**NOUVEAUX FICHIERS** : `plugins/Skript/scripts/za_p69_exploration.sk` ; `za_p66_ruines_donnees.sk` exporte aussi la
position de 6 panneaux de la ville (régénéré, sortie désormais identique d'une exécution à l'autre).

**SYSTÈMES AJOUTÉS** — « Le dossier Arel » : extérieur (menu du Café du Coin : reçu payé avec la carte d'employé
NORDA n° 0731) → bâtiment (porte de la chambre 104 : fiche du patient transféré au labo) → zone sécurisée (bureau du
Dr Lefort à l'étage : agenda des jours 0 à 3, « chez NORDA tout est rangé sous le numéro d'employé ») → pièce secrète
(labo : serrure magnétique = courant dans le quartier hospitalier **ou** Carte d'accès) → énigme (choisir le bon
casier en reliant les documents ; erreur = alarme, infectés, 10 min de verrou) → récompense (Disque de données Z-01
utilisable dans la quête de Lefort, rapport NORDA confidentiel, 25 jetons, stat `enigmes`, souvenir, mémoire du monde,
légende pour le premier). 4 documents au format §45. Admin `/zaexpl <joueur> [reset]`.

**RISQUES** : repose sur les panneaux d'origine des ruines ; si un joueur les casse, l'étape n'est plus cliquable.

**TESTS** : statiques + positions des panneaux extraites automatiquement de la structure.

---

## PHASE 13 — Radio + téléphone

**NOUVEAUX FICHIERS** : `plugins/Skript/scripts/za_p70_ondes.sk` · **MODIFICATIONS** : `/aide` (`za_p10`).

**SYSTÈMES AJOUTÉS**
- **Bulletin quotidien de Léa** (MISSION §43) : à chaque nouveau jour de serveur, Léa lit à l'antenne jusqu'à 3
  événements réels de la veille pris dans le journal du serveur (morts, camps, territoires, réseau, légendes,
  retrouvailles…). Les annonces existantes des modules restent inchangées.
- **Téléphone** (MISSION §44) : le « Cellulaire mort » du réveil au Jour 8 se répare (clic droit + 1 Composant
  électronique). Réseau seulement là où le courant revient (centrale en marche ou sous-station qui produit à 300
  blocs) ; batterie -1 %/min, recharge dans une zone sous tension. `/telephone` (`/tel`) : messages, appels (Léa,
  Lefort, Vega : réponses selon la confiance, le danger local, le dossier Arel), alertes (horde, Overlord, lune de
  sang, catastrophe, camps attaqués, pannes, danger local), missions (contrats, sous-stations, dossier Arel, /guide).
- **SMS de contexte** : camp attaqué (si ce camp te fait confiance), contrat d'une faction où tu es connu, horde,
  lune de sang, panne de TA sous-station, nouvelles des survivants retrouvés (échos), et un « numéro inconnu »…
  Les messages attendent le réseau. API : `za_tel_sms(uuid, expéditeur, texte)`.
- Admin : `/zatel <joueur> donner|sms <texte>|batterie <n>|reset`.

**RISQUES** : le bulletin lit `{za::journal::*}` (200 lignes max) : si la veille a été très chargée, seuls les
événements encore présents sont lus.

**TESTS** : statiques. En jeu : `/zatel <toi> donner`, `/telephone`, `/zacamp attaque <id> zombies`.

---

## PHASE 14 — Mémoire du monde

Constat : mémoire des lieux (`za_p62`), des morts (`za_p58`), légendes (`za_p64`), nids, labos, camps, territoires
existent déjà. Manquaient : les hordes, l'Overlord hors finale, la relance de la centrale, les survivants du
prologue, et une mémoire plus large des personnages (MISSION §47).

**NOUVEAUX FICHIERS** : `plugins/Skript/scripts/za_p71_chronique.sk`

**MODIFICATIONS** (une ligne d'appel chacune) : `za_horde.sk` (`za_horde_fin`), `za_boss.sk` (`/zaboss mort`),
`za_p62_memoire_monde.sk` (`za_souvenir_ligne` complète avec `za_pnj_memoire` quand elle n'a rien à dire).

**SYSTÈMES AJOUTÉS**
- Monde : horde repoussée / subie (légende au-delà de 150 morts), Overlord abattu hors finale, centrale relancée —
  avec témoins et souvenirs (`za_monde_evt`).
- Registre des **survivants de Saint-Aurèle** : `{za::memoire::sa::<uuid>}` = nom, jour, choix (lu par les archives).
- Lefort, Vega et Léa se souviennent, une fois chacun : du dossier Arel, des personnes sauvées (par tranche de 3),
  du courant rendu, des gens de Saint-Aurèle retrouvés, de tes fréquentations (Pilleurs, Scientifiques, Milice).
- Admin `/zachronique`.

**TESTS** : statiques.

---

## PHASE 15 — Saison + après-saison

Constat : fin de saison (révélation, finale Overlord en 4 phases, cérémonie, Hall), après-saison (chronologie J+0 à
J+8, thèmes, chroniques, livre) existent (`za_p22`, `za_p41`, `za_p59`). Ajout : ce qui manquait aux archives.

**NOUVEAUX FICHIERS** : `plugins/Skript/scripts/za_p72_archives.sk`

**MODIFICATIONS** : `za_p59_saisons.sk` : 4 appels (archivage, page 2 de `/chroniques`, monologue de Léa, début de
saison).

**SYSTÈMES AJOUTÉS**
- Archivés par saison : état de Lefort / Vega / Léa et des 6 gens de Saint-Aurèle, sous-stations en service / hors
  service, quartiers éclairés, nombre de survivants de Saint-Aurèle, premier à percer le dossier Arel, guerres et
  alliances entre factions, porteur de la relique.
- Relus : page 2 des chroniques ; une phrase de plus dans le monologue de Léa à l'ouverture de la saison suivante.
- Séquelles : l'hiver entre deux saisons endommage la moitié des sous-stations (nouveaux objectifs de réparation) ;
  les gens de Saint-Aurèle disparus peuvent être recroisés tout de suite.

**RISQUES** : la moitié des sous-stations tombe en panne à chaque nouvelle saison : voulu, à ajuster si trop dur.

**TESTS** : statiques. En jeu : `/zasaison enregistrer`, puis `/chroniques <n> 2`.

---

## COMPLÉMENT PHASE 8 — Saint-Aurèle habillée avec les mods décoratifs (30 sept.)

**MODIFICATIONS** : `plugins/ZAMonde/town.json.gz`, `layers.json`, `hall.json.gz`, `ruines.json.gz` (régénérés),
`JARS.txt` (16 mods + SHA-1), `CLAUDE.md`, `docs/A_INSTALLER.md`, `ZA_sources_build.zip`.

**NOUVEAUX FICHIERS (zip des sources)** : `ville/extraire_blocs_mods.py`, `ville/blocs_mods.json.gz` (3 909 blocs
moddés et leurs propriétés, lus dans les jars), `ville/za_moderne.py`.

**SYSTÈMES MODIFIÉS** : générateur de la ville (`za_blocs.py` accepte les blocs moddés ; `za_meubles.py` pose des
meubles Handcrafted / Macaw's ; `za_rue.py` trottoirs en pavés ; `za_pois.py` aligné sur la caméra du blackout
déployée, qui avait été ralentie à la main).

**CHANGEMENTS VISIBLES** : 188 portes Macaw's, 82 lits, 58 chaises, 31 tables, 27 canapés, 12 commodes, 11 bureaux,
6 tabourets, fours, éviers et armoires de cuisine ; 180 blocs de toit, 360 clôtures à piquets, 583 grilles
industrielles, 395 dalles d'allée, tous les trottoirs en pavés carrés. Le frigo reste une porte en fer vanilla.

**TESTS** : 0 erreur de validation (portes et lits appariés, états valides), 78 POIs accessibles à pied, palettes
de la ville (531), des ruines (630) et du Hall (46) validées contre le rapport 1.20.1 + les blockstates des mods ;
`ZA_VANILLE=1` redonne les anciens fichiers octet pour octet. Non testé : rendu en jeu, orientation des meubles de
Macaw's (Handcrafted vérifié sur le modèle 3D de la chaise), acceptation des blocs moddés par Arclight.

**RISQUES** : si Arclight refuse un bloc moddé, ZAMonde l'ignore (trou) et l'écrit dans la console. Les mods
deviennent obligatoires côté serveur et côté joueurs.

---

## COMPLÉMENT — Add-ons Create (30 sept.)

**MODIFICATIONS** : `za_p17_usines.sk` (mots-clés de machines : diesel, pumpjack, distillation, energiser, stirling,
reactor, cannon), `za_p61_electricite.sk` (sources d'énergie reconnues : diesel, énergiseur, stirling, réacteur,
balais, aimants, solaire), `za_p56_zombies_ia.sk` (une explosion ajoute de l'activité et du bruit à 60 blocs),
`JARS.txt`, `docs/A_INSTALLER.md` (§6 bis), `CLAUDE.md`.

**VÉRIFICATIONS** : doublons par SHA-1 ; dépendances obligatoires de chaque mod ; références de chaque add-on aux
classes de Create 6.0.8 (+ Flywheel, Ponder inclus). Résultat : Design Decor 0.4.0b et Create D&D 0.1b
incompatibles ; Kotlin for Forge et Energy Storage Lib 1.1.3 manquants.

**TESTS** : vérificateur Skript OK. Non testé : démarrage réel avec ces mods sur Arclight.

---

## COMPLÉMENT — Le monde de la région de Saint-Aurèle, 10 000 × 10 000, sans Lost Cities (30 sept.)

**OBJECTIF** : demande de Colin : « fais un nouveau monde 10000 par 10000 », « tout généré par moi », Lost Cities
retiré de l'overworld. Aucune génération par Minecraft : le programme écrit directement les 400 fichiers de région.

**NOUVEAU** :
- `generateur_monde/` (Python + numpy) :
  - `anvil.py` : format NBT et régions 1.20.1, écriture atomique ;
  - `bruit.py` : bruit déterministe ;
  - `plan.py` : lieux, routes, lacs ;
  - `terrain.py` : relief, rivière Blanche, réservoir, 11 biomes ;
  - `flore.py` : arbres et végétation ;
  - `monde.py` : roche, minerais vanilla, Create et IE, grottes, routes et ponts, végétation ;
  - `sites.py` : pose des structures, panneaux, coffres à butin ;
  - `batisse.py` : 13 types de lieux construits avec le générateur de la ville, puis passe « apocalypse » (vitres
    brisées, toiles, lierre, herbes folles, lampes éteintes) ;
  - `generer.py` : lanceur multiprocessus avec reprise après interruption ; `--vanille` pour les tests ;
  - `apercu.py` : carte, publiée dans `docs/carte_region.png`.
- Lieux :
  - ruines de Saint-Aurèle au centre ;
  - l'autobus du Jour 8, qui sert de point d'apparition ;
  - la base Bravo, NORDA Biotech, le barrage, le parc industriel, l'émetteur CKZA, la carrière, le motel ;
  - 3 villages, 4 stations-service, 2 barrages routiers ;
  - 18 fermes, 16 chalets, 22 camps de chasse.
- `za_p73_sites.sk` :
  - nom du lieu à l'entrée : titre, ambiance et souvenir la première fois ;
  - zombies propres à chaque lieu, via `za_type_lieu` de p36 ;
  - `/zasites installer` : branche les ruines (sans `/zaville installer`), inscrit les 73 lieux dans la mémoire du monde,
    règle la bordure à 10 000 et le point d'apparition à l'autobus.
- `za_p73_sites_donnees.sk` : généré par `generer.py`.

**MODIFIÉ** :
- `za_p36_apparitions.sk` : les lieux générés passent après les bâtiments de p35 et avant la contamination.
- `world/serverconfig/lostcities-server.toml` : `selectedProfile = ""`.

**TESTS** :
- Les 13 types de lieux se construisent sans erreur. Ils sont identiques d'un processus à l'autre : un `hash()` Python
  variait selon le processus, il est remplacé par crc32. Les régions sont identiques octet pour octet entre deux
  exécutions.
- Environ 7 s par région et par cœur, soit environ 13 min pour le monde entier sur 4 cœurs.
- Serveur Minecraft 1.20.1 vanilla, en mode `--vanille` : 6 régions chargées, forcées et réenregistrées sans aucune
  erreur. Les chunks restent `full`. Panneaux, coffres et barils sont conservés avec leur table de butin (30 à la base
  Bravo, 50 à Val-des-Pins).
- Vérificateur Skript : aucune anomalie (80 scripts).

**NON TESTÉ** :
- Chargement avec Arclight et les mods : identifiants des blocs moddés, en particulier les minerais d'IE (jar non
  vu).
- `/zasites installer` en jeu.
- Effet de `selectedProfile = ""` sur Lost Cities. Tout le monde est pré-généré, donc Lost Cities ne génère de toute
  façon rien dans la bordure.

**RISQUES** :
- Les anciennes données de joueurs pointent vers l'ancien monde : bases, camps, `{za::pro::retour}`.
- Les 311 barils des ruines restent vides : leur contenu vient des systèmes de jeu, comme avant.
- Les 1,8 Go de régions ne sont pas versionnés : Colin les génère chez lui.

**AJOUT (même jour) : signalisation routière** (`generateur_monde/signalisation.py`, 47 panneaux sur poteau).
L'autobus du Jour 8 est à ~700 blocs des ruines : un panneau à côté de lui indique Saint-Aurèle (sortie 117, tout
droit vers l'ouest) ; la sortie 117 est annoncée dans les deux sens ; aux deux entrées de la ville, « Bienvenue à
Saint-Aurèle » puis « QUARANTAINE — Accès interdit » ; chaque chemin de lieu a son panneau (nom + distance).
Testé sur le serveur vanilla : panneaux conservés après chargement et sauvegarde (texte, couleur, texte lumineux).
