# PHASE 1 — Analyse du projet (aucune modification du serveur)

Analyse statique du dépôt (grep + lecture ciblée). Aucun serveur de test dans cette session.

## 1. Architecture actuelle
- **Arclight 1.20.1** (Forge 47 + API Bukkit). 37 mods Forge (Create 6.0.8, Create Crafts & Additions 1.3.3,
  Immersive Engineering 10.2, Steam 'n' Rails, TaCZ + addons, Zombie Awareness, Enhanced AI, SecurityCraft,
  Lost Cities, Tough As Nails, Serene Seasons, Voice Chat, Gravestone, Waystones, Lootr, Sophisticated Backpacks,
  Refurbished Furniture, zombie_extreme modifié…).
- **Skript 2.9.5** : 67 scripts `za_*.sk`, 32 229 lignes, 1,7 Mo. 132 commandes, 1 039 fonctions.
- **MythicMobs 5.7.2** (+ `ZAPaperCompat.jar`) : 36 mobs custom (`Mobs/ZombieApocalypse.yml`, `ZA_Humains.yml`, `ZA_IA.yml`),
  apparitions aléatoires désactivées (`Generator: NONE`) et gérées par `za_p36_apparitions.sk`.
- **Plugin ZAMonde** (Java, sources dans le zip) : monde privé `za_prologue`, pose de structures (`/zamonde placer`),
  calques de blocs par joueur, lampes / blackout, PNJ privés, props (véhicules en BlockDisplay), caméras, HUD, sons.
- **Mod client `za_modeles` 1.2.0** : modèles EMF/ETF (format OptiFine CEM) pour 21 règles de noms de zombies,
  skins de villageois (humains), 40 voix, 34 effets, 6 musiques.
- **Générateurs Python** (zip) : ville de Saint-Aurèle (`ville/gen_ville.py`, 288×48×288, calques, lampes, POIs, props),
  modèles zombies (`modeles_generateur/`).

## 2. Systèmes déjà présents (base officielle)
| Système | Fichiers |
|---|---|
| Noyau / fonctions partagées | `za_00_core`, `za_p42_noyau` |
| Prologue Saint-Aurèle J0→J8 (instance privée, ~25 min, 4 choix, blackout, arrivée) | `za_p38_prologue`, `za_p38_lieux` |
| PNJ Lefort / Vega / Léa + dialogues | `za_p18_pnj`, `za_p40_histoire`, `za_p46_relations` |
| Fil rouge 7 niveaux (/guide) | `za_p60_parcours` |
| Infection, souches, résistance, patient zéro | `za_infection`, `za_p12_virus`, `za_p26_virus2` |
| Survie (soif, faim, sommeil, température, maladies, blessures) | `za_p11`, `za_p15`, `za_p27`, `za_p53` |
| Santé mentale / horreur / ambiance | `za_p4_horreur`, `za_p31_ambiance` |
| Bruit, hordes, migrations, IA adaptative | `za_p24_bruit`, `za_horde`, `za_p33_migration`, `za_p56_zombies_ia` |
| Apparitions, nids, carte de danger, lieux évolutifs, centrale | `za_p36`, `za_p39_monde_vivant` |
| Bases, sièges, défense, générateurs, tourelles, usines | `za_p8`, `za_p23`, `za_p14`, `za_p16`, `za_p17` |
| Réseau électrique (quartiers, vote) — 100 % Skript | `za_p50_reseau` |
| Bâtiments spéciaux générés, mécaniques par lieu | `za_p35_batiments`, `za_p51_lieux` |
| Économie (jetons, troc, contrats, dettes, marchands), marché joueurs | `za_p7_economie`, `za_p47_marche` |
| Survivants, camps, territoires, factions | `za_p43`, `za_p44`, `za_p45`, `za_p40` |
| Armes v2, ateliers, ressources de saison | `za_p49`, `za_p52`, `za_p48` |
| Énigmes, chasse au trésor (fragments), enquêtes | `za_p54_enigmes` |
| Catastrophes, événements (blood moon…) | `za_p55`, `za_p3_evenements` |
| Mémoire des morts, mémoire des lieux, légendes, succès | `za_p58`, `za_p62`, `za_p64`, `za_p57` |
| Saison, finale Overlord, après-saison / chroniques | `za_p22`, `za_boss`, `za_p41`, `za_p59` |

## 3. Systèmes manquants ou incomplets
1. **États nommés de la ville** pendant le prologue (VILLE NORMALE → APOCALYPSE) : les calques existent, pas l'indicateur.
2. **Électricité réelle** : `za_p50` est un réseau 100 % Skript ; aucun lien avec l'énergie Create / CCA / IE.
   Pas de sous-stations, pas de priorités, pas d'états ALIMENTÉ / PARTIEL / PANNE / BLACKOUT, pas de réparation.
3. **Zombies par métier** : policier, médecin, ouvrier, pompier absents (seuls citoyen / patient / soldat existent).
   Pas d'identité sonore par type. Pas d'animations rares côté serveur.
4. **Ville avant / après** : dans le monde principal, seule l'épave de l'autobus (`arrivee`) existe : on ne retrouve pas
   Saint-Aurèle en ruines.
5. **Téléphone** après l'apocalypse : inexistant (seulement des SMS scénarisés dans le prologue).
6. **Radio dynamique** : `za_radio` existe, mais peu de systèmes l'appellent sur des événements réels.
7. **Stat « Électricité » des camps** : absente.

## 4. Dépendances et points de vigilance
- Pas de doublon de commande ni de fonction ; aucune fonction appelée sans définition ; 11 fonctions jamais appelées.
- Gardes `za_pro` : `za_p4_horreur` (`on chat`) peut rediffuser au monde de survie un message tapé pendant le prologue.
- 15 tâches `every` < 5 s (prologue, tourelles, bruit, blessures…) : à ne pas multiplier.
- Le générateur de modèles du zip (16 modèles) est **plus ancien** que le mod déployé 1.2.0 (26 modèles) : toute
  nouvelle version du mod doit partir du jar déployé, pas du générateur.
- ZAMonde ne peut pas être recompilé ici (jar Arclight absent, GitHub bloqué par le réseau) : aucune modification Java.
- Skript ne peut pas lire les FE d'une machine : le pont énergie → Skript passe par un signal redstone de comparateur
  (Create : compteur de vitesse / stressomètre ; CCA : accumulateur ; IE : condensateurs).

## 5. Plan de modifications
Phase 2 : états de la ville + alerte « QUELQUE CHOSE VIENT DE SE RELEVER » + correctif garde prologue.
Phase 3 : échos des choix (Lefort, Vega, Léa, civils) dans le monde de survie.
Phases 4-5 : `za_p61_electricite.sk` qui étend `za_p50` (sous-stations Create réelles, quartiers, priorités, bases, lumière, bruit).
Phases 6-7 : variantes de métier MythicMobs + équipements + sons, mod client 1.3.0, comportements rares.
Phase 8 : structure `ruines` générée depuis la ville du prologue (même plan, calques de crise, dégâts).
Phases 9-15 : électricité des camps, radio qui observe le monde, téléphone, mémoire, archives de saison.

## 6. Fichiers concernés
Existants modifiés au minimum : `za_p38_prologue.sk`, `za_p4_horreur.sk`, `za_p50_reseau.sk`,
`MythicMobs/Mobs/ZombieApocalypse.yml`, `za_p36_apparitions.sk`. Nouveaux : `za_p61_*`, `za_p63_*`, `za_p65_*`…,
`ZA_sources` régénéré (zip), `docs/`.
