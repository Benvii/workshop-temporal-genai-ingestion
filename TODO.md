Plan du codelab


Part 1 - Découvert de l’environnement [⏰ 20 min - 0h -> 0h20]
- [ ]  Composants d’architecture
- [ ]  Lancement d’Avel Bot
    - [ ] Interroger le bot voir qu’il est vide.
    - [ ] Ajouter un page web via l’interface, en chope tout les neuds texte de la page. Pas très propre.
    - [ ] Voir que le document est bien indexé, en recherchant n’importe quoi dans la base.
    - [ ] Clean la base.
- [ ]  Découverte explication rapide de la chaine RAG via une trace langfuse + schéma

> Objectifs savoir utiliser AvelBot, clean la base vectoriel et voir les documents dedans.


Part 2 - Vectorisons quelques pages avec Temporal IO [⏰ 30 min - 0h20 -> 0h50 ]
- [x] Concept de base de Temporal IO (Workflow et Activités), schéma ? 
- [x] Transformons ce workflow en workflow d’ingestion avec la vectorisation des 2 sources déjà présentes en local, activités d’indexing.

Partie 3 - Clean les pages et les convertir en markdown (première activité TypeScript) [⏰ 25 min - 1h15 -> 1h40 ]
- [x]  TurnItDown, passe ton HTML en Markdown
- [x]  Découverte Deffuble, isoler le contenu « utile » de la page web

Partie 4 - Collectons les pages automatiquement [⏰ 25 min - 0h50 -> 1h15 ]
- [ ] Création de l’activité de Scraping qui depuis une source avec URI va télécharger la page. 
- [ ] Introduction du stage de crawling, avec l’activité pré-développée
- [ ] [Optionnel] Concept de Continue As New, introduction d’un bulk size


Partie 5 - (optimisation) - Éviter les prompts qui explosent, découpons nos documents - Chunking [⏰ 20 min - 1h40 -> 2h00 ]
- [ ]  Ajout d’un stage de Chunking avec du recurvive Text Splitter.
- [ ]  Adaptation de l’activité d’indexing pour quelle ingère le chunks générés.
- [ ]  Ouverture sur d’autres approches de chunking.

Partie 6 - Allez plus loin [⏰ 15 min - 2h00 -> 2h15 ]
- [ ]  Quid de l’authentification et Temporal, docker compose avec Keycloack, auth des workers
- [ ]  Démonstration de QaLLaM et présentation des fonctionnalités.

Bonus : JSON Schéma pour partager le même modèle en Python et TS.

Run Config Docker sur PyCharm & VSCode Task.
Hot Reload  du worker python ? : https://github.com/reloadware/reloadium
Expliquer le Terminate du workflow.


Manque quelques run config VS Code sur la partie scraping.