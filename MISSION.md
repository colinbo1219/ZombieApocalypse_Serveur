# MISSION CLAUDE CODE — ZOMBIEAPOCALYPSE

Tu travailles sur un serveur Minecraft 1.20.1 nommé ZombieApocalypse.
Le projet utilise notamment : Arclight / Forge, Skript, MythicMobs, ModelEngine / modèles zombies custom, Create,
Create Crafts & Additions, Immersive Engineering, TaCZ, Zombie Awareness, SecurityCraft, Lost Cities, Tough As Nails,
Serene Seasons, Voice Chat, Gravestone, autres mods/plugins déjà présents dans le projet.

Le serveur possède déjà beaucoup de systèmes. Ta mission n'est PAS de repartir de zéro.
Tu dois améliorer et compléter le serveur en conservant les systèmes existants.

## 1. RÈGLE ABSOLUE
Avant de modifier quoi que ce soit :
1. Inspecte entièrement le projet.
2. Identifie les scripts existants.
3. Identifie les dépendances.
4. Identifie les variables globales déjà utilisées.
5. Identifie les commandes déjà existantes.
6. Identifie les systèmes déjà implémentés.
7. Identifie les doublons.
8. Identifie les fichiers responsables de chaque système.
9. Vérifie les interactions entre scripts.

NE SUPPRIME PAS un système existant simplement parce qu'il pourrait être amélioré.
Avant toute modification importante :
- recherche les variables utilisées ailleurs ;
- recherche les commandes appelées ailleurs ;
- recherche les fonctions utilisées ailleurs ;
- recherche les événements qui pourraient être déclenchés deux fois.

## 2. OBJECTIF GLOBAL
Le serveur doit donner cette expérience :
LE JOUEUR N'ARRIVE PAS DANS L'APOCALYPSE. Il arrive dans une ville moderne normale. Il vit une journée normale. Puis :
maladie → inquiétude → quarantaine → panique → premiers morts → premiers zombies → intervention militaire →
effondrement → blackout → apocalypse.

Après cette introduction, le joueur entre dans le vrai gameplay :
survie → exploration → bases → infection → zombies → factions → survivants → économie → laboratoires →
Patient Zéro → mutations → Overlord → fin de saison.

## 3. PRIORITÉ NUMÉRO 1 : NE PAS CASSER L'EXISTANT
Les systèmes déjà présents doivent être considérés comme la base officielle. Ils comprennent notamment :
infection ; souches ; résistance ; santé mentale ; bruit ; hordes ; migrations ; sièges ; bases ; générateurs ;
tourelles ; économie ; marchands ; dettes ; contrats ; squads ; réputation ; PNJ ; journal ; laboratoires ;
maladies ; saisons ; événements ; bâtiments ; survivants ; camps ; factions ; territoires ; monde vivant ;
mémoire ; finale Overlord.

Ne recrée pas ces systèmes sous un autre nom. Cherche d'abord comment les étendre.

## 4. PROLOGUE — LE MONDE MODERNE
Créer ou améliorer un système de prologue entièrement scénarisé.
Le prologue doit être une expérience séparée du gameplay normal.

Nom de la ville : **SAINT-AURÈLE**

Le joueur commence dans une ville moderne. Au début : aucune horde ; aucune zone morte ; aucune apocalypse ;
très peu ou aucun zombie ; ville fonctionnelle ; PNJ normaux ; commerces ; hôpital ; poste de police ; transport ;
radio ; circulation ; vie civile.

Le joueur doit avoir l'impression d'être dans une ville normale.

## 5. JOUR 0
Début du prologue. Heure : 08:00 environ. Message : UNE JOURNÉE ORDINAIRE.
Le joueur reçoit de petites tâches civiles. Exemples : acheter quelque chose ; parler à un PNJ ; aller à l'hôpital ;
passer chez un commerçant ; retrouver un personnage ; retourner chez lui.
Le but est d'apprendre le serveur sans afficher un gros tutoriel technique.

## 6. PNJ DU PROLOGUE
Créer plusieurs PNJ importants. Minimum :
- Dr Lefort — Médecin.
- Sergent Vega — Responsable militaire.
- Léa — Radio / communications.

Les personnages doivent pouvoir réapparaître après l'apocalypse.
Chaque personnage doit avoir : nom ; rôle ; dialogues ; relations ; état ; variables persistantes ;
possibilités de survie / mort / disparition.

## 7. PREMIERS SIGNES DE L'ÉPIDÉMIE
Progressivement :
- Étape 1 : Quelques personnes malades.
- Étape 2 : Plus d'ambulances.
- Étape 3 : Hôpital sous pression.
- Étape 4 : Messages radio inquiétants.
- Étape 5 : Certains commerces ferment.
- Étape 6 : Premières quarantaines.
- Étape 7 : Police présente dans certaines zones.

Toujours PAS de grosse horde. L'apocalypse doit monter lentement.

## 8. JOUR 2–3
Introduire : quarantaines ; barrages ; ambulances ; premiers incidents ; foules paniquées ; premiers PNJ disparus ;
premiers rapports médicaux ; premiers messages d'urgence.
Les joueurs doivent comprendre : Quelque chose va très mal. Mais ne pas encore tout révéler.

## 9. PREMIER ZOMBIE
Le premier zombie doit être un événement narratif. Ne pas simplement faire apparaître un zombie au hasard.
Le joueur doit voir : malade → crise → mort → silence → réanimation → attaque.
Afficher une alerte forte mais courte. Exemple : QUELQUE CHOSE VIENT DE SE RELEVER.
Puis le joueur doit réellement rencontrer son premier zombie.

## 10. EFFONDREMENT DE LA VILLE
Faire progresser l'état de Saint-Aurèle :
1. VILLE NORMALE
2. ALERTE SANITAIRE
3. QUARANTAINE
4. PANIQUE
5. ÉPIDÉMIE
6. EFFONDREMENT
7. BLACKOUT
8. APOCALYPSE

Chaque état doit modifier au minimum certains éléments : messages ; PNJ ; radio ; événements ; lumière ;
bâtiments ; ambiance ; danger ; circulation ; apparitions.

## 11. JOUR 8 — LE BLACKOUT
Le point de rupture. Les lumières de certains quartiers s'éteignent. Puis davantage. Puis blackout.
Dernière transmission de Léa : « Si quelqu'un reçoit ce message... » Puis : « Ne venez pas au centre-ville. »
Puis perte du signal. Écran noir. Puis :

JOUR 8
Il n'y a plus de réseau.
Il n'y a plus d'électricité.
Il n'y a plus personne pour vous protéger.

Le gameplay de survie commence.

## 12. CHOIX DU PROLOGUE
Le prologue doit contenir plusieurs choix. Exemples :
- Choix A : Aider l'hôpital.
- Choix B : Suivre les militaires.
- Choix C : Aider des civils à fuir.
- Choix D : Fuir seul avec des ressources.

Ces choix doivent être conservés. Créer des variables persistantes. Exemple conceptuel :
```text
{za::prologue::choix::joueur}
{za::relation::lefort::joueur}
{za::relation::vega::joueur}
{za::relation::lea::joueur}
```
Les choix doivent avoir des conséquences plus tard.

## 13. CONSÉQUENCES DU PROLOGUE
Exemple :
- Si le joueur aide Lefort : Lefort peut réapparaître plus tard.
- S'il l'abandonne : Lefort peut lui reprocher.
- S'il suit Vega : Vega peut avoir confiance.
- S'il aide les civils : certains survivants peuvent rejoindre un camp.

Le but est que le joueur se dise : « Ce que j'ai fait avant l'apocalypse compte encore. »

## 14. SYSTÈME ÉLECTRIQUE AVEC CREATE
Créer le système électrique autour de :
- Create : production mécanique.
- Create Crafts & Additions : conversion mécanique ↔ FE.
- Immersive Engineering : infrastructure et consommation électrique.

NE PAS créer un faux système parallèle uniquement en Skript si Create peut fournir la vraie énergie.
Skript doit gérer : logique des quartiers ; état des bâtiments ; événements ; pannes ; conditions ; objectifs ;
conséquences.

## 15. STRUCTURE DU RÉSEAU ÉLECTRIQUE
Créer conceptuellement :
```text
CENTRALE
   ↓
SOUS-STATION
   ↓
QUARTIER
   ↓
BÂTIMENTS
```
Créer plusieurs quartiers. Exemple : centre-ville ; hôpital ; police ; zone industrielle ; gare ; banlieue.
Chaque quartier doit pouvoir avoir son propre état :
```text
ALIMENTÉ
PARTIEL
PANNE
BLACKOUT
```

## 16. PRODUCTION ÉLECTRIQUE
Prévoir :
- Petite production : petits générateurs.
- Production moyenne : générateurs Create.
- Grande production : centrale industrielle.
- Secours : batteries / stockage.

Les sources de production doivent avoir une valeur réelle.

## 17. CONSOMMATION
Les bâtiments consomment de l'électricité. Exemples :
- Hôpital : forte consommation.
- Police : moyenne.
- Commerce : faible.
- Industrie : très forte.
- Base : selon ses installations.

## 18. PRIORITÉS D'ÉLECTRICITÉ
Créer un système permettant de définir :
1. hôpital ;
2. sécurité ;
3. survivants ;
4. industrie ;
5. commerces ;
6. autres.

En cas de manque d'énergie : le réseau coupe les secteurs les moins prioritaires.

## 19. RÉSEAU ET APOCALYPSE
Pendant le prologue : 100 % du réseau fonctionne.
Puis : pannes ; surcharge ; sous-stations détruites ; quartiers privés de courant ; blackout.
Après le Jour 8 : les joueurs peuvent réparer le réseau.

## 20. RÉPARATION DES SOUS-STATIONS
Créer des objectifs comme : Réparer la sous-station nord.
Le joueur doit : trouver les composants ; atteindre la sous-station ; réparer ; réactiver ;
éventuellement défendre la zone.
La réparation doit modifier réellement le quartier.

## 21. ÉLECTRICITÉ ET LUMIÈRE
Connecter le système électrique aux lumières et infrastructures.
- Quartier alimenté : lampadaires ; commerces ; hôpital ; systèmes.
- Blackout : quartier sombre ; moins de visibilité ; ambiance différente ; zombies plus difficiles à détecter.

## 22. ÉLECTRICITÉ ET ZOMBIES
Connecter l'électricité au système existant. Exemples :
- centrale active → bruit.
- forte activité industrielle → bruit.
- éclairage massif → visibilité accrue.
- blackout → moins de visibilité.

L'idée : ÉLECTRICITÉ = AVANTAGE + RISQUE.

## 23. ZOMBIES CUSTOM 2.0
Améliorer les zombies visuellement. Chaque type doit avoir une silhouette reconnaissable.
Créer des différences visuelles pour : Shambler ; Runner ; Spitter ; Bloater ; Leaper ; Crawler ; Stalker ;
Screamer ; Armored ; Shielded ; Alpha ; autres variantes déjà présentes.

## 24. APPARENCE PAR PROFESSION
Ajouter des variantes visuelles :
- Civil : vêtements quotidiens.
- Policier : uniforme.
- Militaire : camouflage.
- Médecin : blouse / matériel médical.
- Ouvrier : équipement industriel.
- Pompier : équipement incendie.

Ces variantes doivent être utilisées selon les lieux.

## 25. ZOMBIES PAR ENVIRONNEMENT
- Hôpital : patients / médecins / infectés.
- Police : policiers / prisonniers / armored.
- Centrale : ouvriers / variantes brûlées.
- Militaire : soldats.
- Forêt : variants sales / stalkers / crawlers.
- Zone contaminée : mutations avancées.

## 26. ANIMATIONS
Améliorer les animations des zombies : idle ; marche ; course ; attaque ; mort ; chute ; relève ; boiterie ;
regarder autour ; comportement agressif.
Certains types doivent avoir des animations spécifiques.

## 27. ANIMATIONS RARES
Ajouter des animations très rares : regard vers le joueur ; tête qui tourne ; zombie qui reste immobile ;
zombie qui mange ; zombie qui frappe une porte ; zombie qui se relève.
Ces événements doivent rester rares.

## 28. ZOMBIES ET SON
Chaque type important doit avoir une identité sonore. Exemples :
- Runner : cri court / respiration rapide.
- Bloater : respiration lourde.
- Screamer : cri reconnaissable.
- Stalker : quasi silencieux.
- Alpha : son grave.
- Overlord : signature sonore unique.

## 29. SYSTÈME DE NIDS
Créer des nids de zombies. Un nid possède : niveau ; zone ; contamination ; apparitions ; cœur du nid ; récompense.
Objectif : détruire le cœur.
Après destruction : baisse temporaire de danger ; récompense ; traces ; changement de zone.

## 30. ZOMBIES ADAPTATIFS
Le monde doit apprendre des joueurs. Exemples :
- beaucoup d'armes à feu → plus d'Armored.
- beaucoup de lumière → zombies attirés vers la lumière.
- beaucoup de bruit → plus de migrations.
- forte présence dans une base → plus de sièges.

Utiliser les systèmes existants plutôt que créer un second système de danger.

## 31. MONDE VISUELLEMENT ÉVOLUTIF
Chaque zone possède un état. Exemple :
```text
NORMAL
↓
TENDUE
↓
CONTAMINÉE
↓
ABANDONNÉE
↓
INFESTÉE
↓
ZONE MORTE
```
Chaque état peut modifier visuellement : lumières ; fumée ; barricades ; cadavres ; végétation ; sons ; PNJ ; zombies.

## 32. VILLE AVANT / APRÈS
La même ville doit évoluer :
- JOUR 0 : propre.
- JOUR 2 : quelques barricades.
- JOUR 4 : véhicules abandonnés.
- JOUR 6 : militaires.
- JOUR 8 : effondrement.
- APRÈS : ruines.

Le joueur doit reconnaître les mêmes endroits.

## 33. SURVIVANTS
Chaque survivant important doit avoir : histoire ; métier ; relation ; faction ; moral ; état ; localisation ;
possibilité de mourir ; possibilité de rejoindre un camp.
Les survivants secondaires peuvent être générés avec des profils plus simples.

## 34. CAMPS
Chaque camp doit avoir des statistiques :
```text
Population
Nourriture
Sécurité
Moral
Électricité
Contamination
```
Le joueur peut améliorer ou perdre un camp.

## 35. FACTIONS
Les factions doivent disposer de : réputation ; territoire ; ressources ; relations ; contrats ; ennemis ; alliés.
Les territoires peuvent changer de propriétaire.

## 36. MARCHÉ JOUEUR
Créer un véritable marché joueur-à-joueur.
Fonctions : vendre ; acheter ; rechercher ; prix ; quantité ; expiration ; historique.
Ne pas créer une nouvelle monnaie. Utiliser l'économie existante.

## 37. MARCHÉ DYNAMIQUE
Créer : pénuries ; hausse des prix ; baisse des prix ; pénuries régionales ; ressources rares.
Les événements peuvent influencer les prix.

## 38. ARMES
Créer une progression visuelle et fonctionnelle :
- CIVIL : armes courantes.
- MILITAIRE : armes avancées.
- RARE : armes difficiles à trouver.
- EXPÉRIMENTAL : objets extrêmement rares.

Ajouter : usure ; réparation ; personnalisation ; munitions spéciales ; armes uniques.

## 39. BLESSURES
Créer un système médical cohérent :
- Bras : précision réduite.
- Jambe : mobilité réduite.
- Torse : saignement.
- Tête : effets critiques.

Relier ce système au rôle Médecin.

## 40. EXPLORATION
Créer des lieux avec plusieurs couches. Exemple :
```text
extérieur
↓
bâtiment
↓
zone sécurisée
↓
pièce secrète
↓
énigme
↓
récompense
```

## 41. ÉNIGMES
Favoriser : indices visuels ; documents ; calendriers ; codes ; objets ; relations entre lieux.
Éviter de faire uniquement : tape le code X.

## 42. CHASSE AU TRÉSOR
Créer des fragments de cartes. Exemple :
```text
Fragment A
Fragment B
Fragment C
↓
Carte complète
↓
Bunker secret
```
Récompense rare.

## 43. RADIO DYNAMIQUE
La radio doit pouvoir parler des événements réels du serveur. Exemples : horde ; camp attaqué ; centrale réparée ;
territoire perdu ; convoi ; personnage mort ; extraction ; événement mondial.
La radio doit donner l'impression qu'elle observe ce qui se passe.

## 44. TÉLÉPHONE
Le téléphone doit servir à : SMS ; appels ; alertes ; missions ; informations ; messages des survivants ;
messages de factions.
Les messages doivent dépendre du contexte.

## 45. DOCUMENTS
Les documents importants doivent avoir : date ; lieu ; auteur ; numéro ; contexte.
Cela permet aux joueurs de reconstruire l'histoire.

## 46. MÉMOIRE DU MONDE
Quand quelque chose d'important se produit : enregistrer l'événement.
Exemples : horde majeure ; camp détruit ; personnage mort ; centrale réparée ; territoire conquis ; boss tué ;
laboratoire découvert.
Le monde doit s'en souvenir.

## 47. MÉMOIRE DES PERSONNAGES
Les PNJ importants doivent se souvenir : choix du joueur ; missions terminées ; personnes sauvées ;
personnes abandonnées ; faction ; réputation.

## 48. FIN DE SAISON
La fin doit suivre :
objectifs ↓ révélation ↓ localisation ↓ préparation ↓ Overlord ↓ combat ↓ cérémonie ↓ chronique.

## 49. APRÈS-SAISON
Conserver : héros ; événements ; camps ; territoires ; reliques ; personnages ; statistiques ; morts importantes.
La saison suivante peut lire ces données.

## 50. OBJECTIF D'IMMERSION
Le joueur doit pouvoir penser : « Cette ville existait avant moi. »
Puis : « J'ai vécu sa chute. »
Puis : « Les décisions que j'ai prises ont changé ce monde. »
Puis : « Le monde se souvient de ce que j'ai fait. »

## 51. RÈGLES TECHNIQUES IMPORTANTES
Ne jamais créer un doublon. Avant de créer : système ; commande ; variable ; événement ; chercher s'il existe déjà.

Éviter les systèmes parallèles. Un seul système doit contrôler :
- Zombies : un système principal d'apparition.
- Overlord : un système principal.
- Électricité : Create + CCA pour l'énergie réelle, Skript pour la logique du monde.
- Infection : système existant.
- Bruit : système existant.
- Saison : système principal.

## 52. STRUCTURE DU CODE
Conserver une organisation claire. Créer de nouveaux fichiers uniquement quand nécessaire.
Exemples possibles :
```text
za_p60_electricite.sk
za_p61_immersion.sk
za_p62_radio.sk
za_p63_pnj_avances.sk
```
Mais avant de créer ces fichiers : chercher une meilleure place dans les scripts existants.
Éviter les fichiers gigantesques.

## 53. COMPATIBILITÉ
Ne pas remplacer un mod existant sans raison.
Ne pas introduire une dépendance externe uniquement pour quelque chose déjà faisable avec : Skript ; MythicMobs ;
Create ; Create Crafts & Additions ; Immersive Engineering ; ressources existantes.

## 54. VALIDATION APRÈS CHAQUE GROS SYSTÈME
Après chaque modification :
1. vérifier la syntaxe ;
2. rechercher références cassées ;
3. rechercher commandes inconnues ;
4. rechercher variables incohérentes ;
5. vérifier les doublons ;
6. vérifier les dépendances ;
7. vérifier les noms de fichiers ;
8. vérifier les appels console ;
9. faire un rapport des modifications.

## 55. NE PAS FAIRE
NE PAS :
- réécrire tout le serveur ;
- migrer tout vers Java ;
- remplacer Skript simplement parce qu'il est gros ;
- ajouter 20 nouveaux mods ;
- créer plusieurs systèmes qui font la même chose ;
- supprimer du contenu existant sans justification ;
- changer les mécaniques importantes sans documenter le changement ;
- créer des commandes dont le nom entre en conflit avec une commande existante ;
- créer une nouvelle monnaie ;
- créer un deuxième système d'infection ;
- créer un deuxième système de hordes.

## 56. ORDRE OBLIGATOIRE DE DÉVELOPPEMENT
- PHASE 1 : Analyser le projet.
- PHASE 2 : Finaliser le prologue.
- PHASE 3 : Finaliser les choix + conséquences.
- PHASE 4 : Créer le système électrique Create.
- PHASE 5 : Connecter l'électricité à la ville et aux bases.
- PHASE 6 : Améliorer les zombies custom visuellement.
- PHASE 7 : Améliorer animations + sons zombies.
- PHASE 8 : Améliorer la ville avant/après.
- PHASE 9 : Finaliser survivants + camps.
- PHASE 10 : Finaliser factions + territoires.
- PHASE 11 : Finaliser marché joueur.
- PHASE 12 : Finaliser exploration + énigmes.
- PHASE 13 : Finaliser radio + téléphone.
- PHASE 14 : Finaliser mémoire du monde.
- PHASE 15 : Finaliser saison + après-saison.

## 57. FORMAT DU RAPPORT CLAUDE CODE
À la fin de chaque phase, répondre :
- MODIFICATIONS : Liste des fichiers modifiés.
- NOUVEAUX FICHIERS : Liste des fichiers ajoutés.
- SYSTÈMES AJOUTÉS : Liste des systèmes fonctionnels.
- SYSTÈMES MODIFIÉS : Liste des systèmes existants touchés.
- DÉPENDANCES : Nouvelles dépendances éventuelles.
- RISQUES : Problèmes potentiels détectés.
- TESTS : Tests effectués.
- RESTE À FAIRE : Travail restant.

Ne jamais dire simplement : « terminé ». Décrire précisément le travail.

## 58. PRIORITÉ ABSOLUE DU PROJET
Le serveur doit devenir : UNE VILLE MODERNE QUI TOMBE SOUS LES YEUX DU JOUEUR
puis : UN MONDE ZOMBIE QUI SE SOUVIENT DE LUI.
Toutes les nouvelles mécaniques doivent servir cette idée.

## 59. PHRASE DIRECTRICE
« Le monde n'était pas détruit quand vous êtes arrivés. Vous étiez là quand il est tombé. »
Cette phrase doit guider toute la conception du serveur.

## FIN DES INSTRUCTIONS
Commence par analyser le projet réel. Ne modifie rien pendant la phase d'analyse.
Présente ensuite :
1. architecture actuelle ;
2. systèmes déjà présents ;
3. systèmes manquants ;
4. dépendances ;
5. plan de modifications ;
6. fichiers concernés.

Ensuite seulement, commence l'implémentation dans l'ordre défini ci-dessus.
