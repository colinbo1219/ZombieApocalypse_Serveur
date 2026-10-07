# Réponse à l'audit de `main-eoee6l` (commit audité : 4c7401f)

Rien n'a été testé en jeu : il n'y a pas de serveur de test ici. Chaque correctif a été validé par relecture et par
`verif_skript.py` (« aucune anomalie »). Pour le Java : compilation, plus `Simulateur` quand c'était pertinent.

## Critiques

| Point | État | Correctif |
|---|---|---|
| C1 Monnaie | Corrigé (1ee1ef0) | Le dépôt de jetons ne compte que les pépites d'or. Le retrait accepte un entier de 1 à 640. Noms protégés à l'enclume. Crédit hors ligne : `za_jetons_crediter`. |
| C2 Inventaire du prologue | Corrigé (1ee1ef0) | Les prérequis sont vérifiés avant la sauvegarde. Le sac n'est jamais écrasé. `za_pro_rendre_sac`. |
| C3 Blocs | Corrigé (1ee1ef0) | Les positions des os sont mémorisées, puis restaurées. |
| C4 Pièges | Corrigé (1ee1ef0) | `za_piege_tick` unique ; un piège cassé est retiré. |
| C5 /base, /avantposte | Corrigé (1ee1ef0) | Gardes : monde, prologue, distance, propriétaire. |
| C6 Emprise des bâtiments | Corrigé (8c732e2) | `za_point_construire` / `za_emprise_ok`. Le bâtiment n'est pas posé s'il n'y a pas de place. |
| C7 Overlord final | Corrigé (8c732e2) | Tags et UUID, `final_vivant` séparé, réconciliation au chargement. |
| C8 Plafond de zombies | Corrigé (8c732e2) | `za_zombie_protege`. Le nettoyage ne touche que les zombies à plus de 24 blocs. |

## Nouveaux points (N)

| Point | État | Correctif |
|---|---|---|
| N1 Gardes traités en zombies | Corrigé (788afc1) | `Cerveaux.infecte` / `geres` excluent les gardes et les acteurs. |
| N2 Capture NORDA | Corrigé (788afc1) | Séquestre `{za::mot::capt::<u>::sac::*}` et casier personnel. |
| N3 Taille des hordes | Corrigé (c614f20) | Matérialisation bornée, persistance cohérente. |
| N4 Rattachement des apparitions | Corrigé (c614f20) | Rattachement seulement pendant la commande MythicMobs en cours. |
| N5 Bases | Corrigé (c614f20) | `basesdebut` / `basesfin`, appelés par `za_mot_base_sync`. |
| N6 Frontière asynchrone | Corrigé (d4e1a9c) | Télémétrie synchronisée ; instantané `nuitObservee`. |
| N7 Budget de l'IA | Corrigé (788afc1) | |
| N8 Événements privés | Corrigé (d4e1a9c) | Un événement `prive` ne se répand plus dans la région (vérifié au simulateur). |
| N9 Réputation | Corrigé (8c0e358) | Plafonds par paire de joueurs et par jour. |
| N10 Échéances des accords | Corrigé (8c0e358) | Échéances vérifiées, crédit hors ligne. |
| N11 Procès | Corrigé (8c0e358) | Identifiant par procès : `za_jus_verdict(u, id)`. |
| N12 Budget de population | Corrigé (af73d62) | `za_population_pleine` dans `za_spawn_near` / `za_spawn_at`, et dans le moteur. |

## Moyens et mineurs

| Point | État | Correctif |
|---|---|---|
| M1 Ordre du prologue | Corrigé (1ee1ef0) | Rejeu seulement si l'état est « fini ». |
| M2 Bandages | Corrigé (3296b0b) | Un seul gestionnaire. |
| M3 Soleil | Corrigé (3296b0b) | Condition OU. |
| M4 Météo | Corrigé (ae59e53) | `za_meteo_prendre` / `za_meteo_rendre` (`{za::meteo::proprio}`). Une catastrophe prime : pas de Blood Moon, de pluie acide ni d'événement aléatoire pendant qu'elle dure. Le drapeau Blood Moon est remis à zéro au chargement. |
| M5 Escouades | Corrigé (3296b0b) | |
| M6 Caches | Corrigé (eb63ac7) | Les `{-…}` sont des variables mémoire : Skript ne les sauvegarde pas, le filtre CSV n'a donc pas besoin de changer. Elles grossissaient quand même pendant que le serveur tourne. Purge à la mort du zombie, plus une purge des délais expirés toutes les 10 min. |
| M7 Menus | Corrigé (fbff9c5) | `za_menu` : table case → action (`{za::menu::slot::*}`). Clics hors du coffre (inventaire du joueur, maj-clic) ignorés. Glisser annulé dans tous les menus (», Aide, Dialogue, Marchand). |
| M8 Types de bâtiments | Corrigé (3296b0b) | `za_bat_types()`. |
| M9 Migration légendaire | Corrigé (3296b0b) | Filtres d'identité et de prologue. |
| M10 Caméras (ZAMonde) | Non corrigé | Java de ZAMonde : impossible à recompiler ici. À corriger dans `ZA_sources/` : garder l'état du premier plan dans `Cameras.start`. |
| M11 Budget de pose (ZAMonde) | Non corrigé | Même raison. À profiler sur le vrai serveur avant de changer les 80 ms. |
| M12 Tâches périodiques | À profiler | Le nombre seul n'est pas un défaut. N7/N12 ont réduit les balayages ; il faut un profil réel (Spark) pour aller plus loin. |
| M13 | Déjà corrigé | |
| M14 Générateur de Saint-Aurèle | Non corrigé | Le code est dans l'archive `ZA_sources_build.zip`. À faire : refuser d'écrire les sorties quand la validation échoue. |
| m1 Annonces | Corrigé (3296b0b) | `za_diffuser`. |
| m2 /heritier | Corrigé (3296b0b) | `/heritier <text>`. |
| m3 Son de porte | Corrigé (3296b0b) | Son vanilla à la place de `sfx.porte_grince`. |

Autre correctif : `reactions.yml` est maintenant du YAML standard valide (3 valeurs entre guillemets, d0e04e8). Ses copies
`plugins/ZAMoteur/` et `moteur/resources/` sont identiques.

## Pour Colin : mise en place

1. Remplacer `plugins/ZAMoteur.jar` et `plugins/ZAMoteur/reactions.yml`, puis redémarrer.
2. Les scripts ont beaucoup changé : un redémarrage complet est plus sûr que des `sk reload <fichier>` un par un.
3. À tester en priorité, dans cet ordre :
   - dépôt et retrait de jetons ;
   - prologue lancé puis quitté (l'inventaire doit revenir) ;
   - capture NORDA puis casier ;
   - pluie toxique pendant une Blood Moon ;
   - menus : maj-clic et glisser ;
   - procès ;
   - accords.
