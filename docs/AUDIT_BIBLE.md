# Audit : la bible v2 face au code (7 octobre, mis à jour après p121-p128)

Méthode : pour chacun des 117 points et chaque section F, IA et S, j'ai cherché une trace dans le code (scripts Skript,
moteur Java, générateur, MythicMobs). Ensuite, j'ai relu le texte de la bible pour les cas douteux. Une trace ne prouve
pas que le point marche en jeu : **rien n'a été testé sur un serveur**.

Légende : ✅ fait · 🟡 en partie · ❌ manquant · 📦 côté client (mod `za_modeles`) · 🔍 hors du dépôt (hébergeur, Discord, modpack)

## Fondations, IA et systèmes

| Section | État | Où / ce qui manque |
|---|---|---|
| F1-F6, F9, F10 | ✅ | ZAMoteur (Chronique, graphe, matérialisation, télémétrie, simulateur, information, mémoire) |
| F7 Pack joueurs groupé | 📦 | à faire dans le modpack |
| F8 Variables en SQLite | 🔍 | configuration de Skript, non faite |
| IA-1 à IA-16 | ✅ | Directeur, Cerveaux, Némésis, génome, hordes, PNJ, mensonges, factions, NORDA, Léa, écosystème, compagnons, bases, Ω |
| S-1 Corps | ✅ | p105, p53, p110 |
| S-2 Combat et armes | 🟡 | numéros de série, usure, saisies (p49, p113). suppression (p124). **Manque** : munitions subsoniques et artisanales (il faut savoir ce que TaCZ permet de lire 🔍), fiabilité selon l'état du tireur |
| S-3 Économie | ✅ | prix régionaux, convois, blocus |
| S-4 Social, S-5 Radio | ✅ | p107, p85, p109 |
| S-6 Mémoire du monde | ✅ | p62, p64, moteur |
| S-7 Campagne | ✅ | p116 |
| S-8 Horreur et visuel | 🟡 | sons, silence, ambiances ✅ ; écran, interface, sept états visuels des bâtiments 📦 |
| S-9 Exploration | 🟡 | lieux, plans, carte personnelle ✅ ; cartes magnétiques SecurityCraft 🔍 |
| S-10 Accueil | ✅ | /fil, /aide, p114 ; accessibilité 📦 |

## Les 117 points

**Faits (✅)** : 1 (simplifié : charge de cadavres par région, pas par case de 16 × 16), 2, 3, 4, 5, 6, 8, 9-13, 15, 16,
18, 19, 20, 22, 23, 25, 27-31, 33, 36, 38, 41-50, 52, 53, 55, 62, 63, 65-117.
Ajoutés après l'audit : 45 offensives (p121), 62 classement et 65 annonce de redémarrage (p122), 96 antenne camouflée,
98 informateur et filature, 101 opérations NORDA, 112 témoins (p123).
Fusionnés : 17, 21, 37, 40, 51.

**Terminés côté serveur après la seconde passe (p129 et générateur)** : 7 panneau d'entrée (fiche datée, brouillard
d'information) ; 26 viande saignante comme appât ; 32 grue qui tombe (+ remise debout par l'admin, qui sert de
« retour en arrière » pour cette catastrophe) ; 34 scènes posées dans les maisons des villes (dernier souper, porte
barricadée, valises, horloges arrêtées à 4 h 12 le Jour 8, traînée de sang, ruban de quarantaine) ; 35 tableaux
d'affichage Supplementaries (avis de recherche, prix du Jour 7, évacuation), drapeaux de faction, cendres des
quartiers brûlés ; S-2 fiabilité : balles déviées et enrayage selon l'état du tireur (ZAMoteur).

**Ce qui reste en partie (🟡)**

| N° | Ce qui existe | Ce qui manque |
|---|---|---|
| 14 Événements sans annonce | largage, survivant poursuivi, alarme, chien, patrouille (Directeur) | à vérifier en jeu |
| 26 Trace de sang | piste d'odeur du moteur, appât de viande | taches visibles au sol 📦 |
| 32 Catastrophes | incendie, barrage, tempête, effondrement, dépôt de carburant, grue | « photo » générale avant dégâts (seule la grue se remet debout) |
| 34 Habillage | scènes dans les maisons des villes générées | les mêmes scènes dans les villages (demanderait de régénérer toute la carte) |
| 24, 39, 54, 56, 57 | partie serveur faite | modèles, peaux, décalques, interface, musique 📦 |
| S-2 munitions | | munitions subsoniques et artisanales (ce que TaCZ permet de lire 🔍) |

**Manquants (❌)**

| N° | Remarque |
|---|---|
| 58 Shaders et sons | 🔍 modpack |
| 59 Discord, 60 BlueMap, 61 Whitelist | 🔍 hors du serveur Skript |
| 64 Mods d'optimisation | 🔍 modpack |
| 65 Sauvegardes | 🔍 hébergeur (l'annonce de redémarrage est faite : /zaredemarrer, p122) |

## Reste faisable ici, côté serveur

Rien d'important : vérifier 14 en jeu. Tout le reste dépend du mod client 📦 ou de l'hébergeur 🔍.
