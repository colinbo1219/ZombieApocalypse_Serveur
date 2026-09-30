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
