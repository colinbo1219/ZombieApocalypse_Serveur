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
