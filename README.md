# Workshop : Alimenter la base de connaissance de ses applications Gen AI (chatbot RAG) de manière industrielle et automatisée

## Info réseau

TODO, quel réseau au Toten ?

## Sommaire


### Part 1 - Découverte de notre environment

* Architecture et setup de l'environnement
  * Configurer sa clé Open AI
  * Lancer la petite stack avec un mini chatbot
  * Jetons un coup d'œil rapide aux sources
  * [Optionnel] Activer l'outil d'observabilité Langfuse [voir init headless](https://langfuse.com/self-hosting/administration/headless-initialization)

* Problématique : TODO slide nécessité de RAG, chunking et vectorisation
    * Opération longues on va par faire un simple API, nécessité de "batch" / workflow

* Introduction rapide à Temporal IO
  * Mon premier workflow et activité hello world en python
  * Indexing des pages web dans notre bot (en brute HTML)

### Part 2 - Collect de données, scriptons un peu [Python OU TypeScript]

* Découverte de la source de données
  * [Actu Brest Métropole > Déplacements](https://brest.fr/nos-actualites?category%5B927%5D=927&commune=&quartier=&query=)
* Crawling Web simple en TypeScript ou Python, au choix
* Scraping Web basique (non authentifié, sans JS)

### Partie 3 - Convertion [Typescript]

* Découverte de Readability / Deffuble
* HTML vers MD, TurnItDown

### Chunking [Python]

### Indexing [Python]
