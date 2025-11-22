# Partie 1 - Découverte et installation de l'environment

<u>Objectifs de cette étape :</u>

* Lancer l'application streamlit avec le bot RAG de démonstration
* Ajouter un article du réseau de transport
* Consulter les documents en base vectorielle et interroger le bot


## Sommaire

<!-- TOC -->
* [Partie 1 - Découverte et installation de l'environment](#partie-1---découverte-et-installation-de-lenvironment)
  * [Sommaire](#sommaire)
  * [Architecture](#architecture)
  * [Lancer l'application AvelBot](#lancer-lapplication-avelbot)
  * [](#)
<!-- TOC -->

## Architecture

Lancement de la stack docker :
```bash
cd $(git rev-parse --show-toplevel)/docker
cp template.env .env
chmod a+r scripts/postgres/init.sql
docker compose --env-file ../.env -f docker-compose.langfuse.yml -f docker-compose.pg.yml up -d
```

## Découvrir AvelBot

```bash
cd $(git rev-parse --show-toplevel)/
streamlit run brest-transport-bot/app.py
```

TODO détailler les différentes fonctions de l'application.

## Langfuse outil d'observabilité

TODO, URL + donner les credentials par défaut.
