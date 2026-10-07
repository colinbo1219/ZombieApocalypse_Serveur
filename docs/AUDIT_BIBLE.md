# Audit : la bible v2 face au code (7 octobre)

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
18, 19, 20, 22, 23, 25, 27-31, 33, 36, 38, 41-44, 46-50, 52, 53, 55, 63, 66-95, 97, 99, 100, 102-111, 113-117.
Fusionnés : 17, 21, 37, 40, 51.

**En partie (🟡)**

| N° | Ce qui existe | Ce qui manque |
|---|---|---|
| 7 Fiche d'état de chaque lieu | `/ville` avec le brouillard d'information (p122) | panneau dynamique à l'entrée |
| 14 Événements sans annonce | largage, survivant poursuivi, alarme, chien, patrouille (Directeur) | à vérifier en jeu |
| 26 Trace de sang | piste d'odeur du moteur, sang = piste forte | taches visibles au sol 📦, viande crue comme appât |
| 32 Catastrophes | incendies (p98), barrage (p119), tempêtes (p55), effondrements et dépôt de carburant (p125) | grue (aucune n'est générée), « photo » avant dégâts pour les retours en arrière |
| 34 Habillage du monde | notes, graffitis, embuscades | scènes posées par le générateur (dernier souper, horloges arrêtées) |
| 35 Mods déco | lampadaires Macaw's | tableaux d'affichage Supplementaries (avis de recherche, prix), drapeaux de faction 🔍 |
| 54 Sang, impacts, cadavres | corps de joueurs (p13), particules | décalques de sang 📦 |
| 56, 57 Pack de ressources, musique | voix, sons | interface, écran titre, musique en couches 📦 |

**Manquants (❌)**

| N° | Remarque |
|---|---|
| 24 Démembrement | 🟡 côté serveur fait (p124) ; modèles 📦 |
| 39 Mutation visible | 🟡 côté serveur fait (p124) ; effets d'écran et peau 📦 |
| 58 Shaders et sons | 🔍 modpack |
| 59 Discord, 60 BlueMap, 61 Whitelist | 🔍 hors du serveur Skript |
| 64 Mods d'optimisation | 🔍 modpack |
| 65 Sauvegardes et redémarrages | 🔍 hébergeur ; **faisable** : l'annonce de Léa avant le redémarrage |

## Faisable ici, côté serveur

7, 24 (partie serveur), 39 (partie serveur), 45, 62, 65 (annonce), 96, 98, 101, 112, une partie de S-2 (munitions,
suppression), 32 (effondrement, dépôt de carburant).
