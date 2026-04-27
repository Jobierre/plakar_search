# 001 - Plakar Semantic Search

## Metadata
- Cree : 2026-04-27
- Status : Draft
- Branche : feature/001-plakar-semantic-search

## Resume
Outil CLI Python (plakar-search) qui ajoute une recherche semantique par contexte aux backups Plakar. Indexe les metadonnees et le contenu des fichiers dans une base vectorielle locale (ChromaDB) via EmbeddingGemma-300M (texte) et SigLIP2 (images), puis permet des requetes en langage naturel pour retrouver des fichiers sans connaitre leur nom exact.

## Scenarios Utilisateur

### [P1] Scenario principal : Indexer un store et rechercher

**Description** : Jobierre indexe un store Plakar (@gdrive) puis cherche un fichier par contexte.

**Criteres d'acceptation** :
- GIVEN un store Plakar @gdrive contenant 5000 fichiers (photos, documents, code)
- WHEN Jobierre lance `plakar-search index @gdrive`
- THEN l'indexation reussit en < 5 minutes
- AND les fichiers texte (.txt, .md, .py, .pdf, .docx, etc.) sont indexes par EmbeddingGemma
- AND les images (.jpg, .png, .heic) sont indexes par SigLIP2 (contenu visuel)
- AND les metadonnees EXIF et noms de fichiers des images sont indexes par EmbeddingGemma
- AND un fichier state.json enregistre l'etat d'indexation
- GIVEN l'index cree
- WHEN Jobierre lance `plakar-search query @gdrive "photos vacances plage 2024"`
- THEN les resultats incluent les images de plage ET les documents mentionnant des vacances
- AND chaque resultat affiche : score, snapshot_id:tronque, chemin complet

### [P2] Scenario : Plusieurs stores

**Description** : Jobierre indexe et recherche dans plusieurs stores independamment.

**Criteres d'acceptation** :
- GIVEN deux stores @gdrive et @s3
- WHEN Jobierre lance `plakar-search index @gdrive` puis `plakar-search index @s3`
- THEN deux indexes distincts sont crees dans `~/.plakar-search/stores/gdrive/` et `~/.plakar-search/stores/s3/`
- WHEN Jobierre lance `plakar-search query @s3 "backup config"`
- THEN seuls les resultats du store @s3 sont retournes

### [P3] Scenario : Recherche ciblee

**Description** : Jobierre filtre sa recherche par snapshot ou par type de fichier.

**Criteres d'acceptation** :
- GIVEN un store indexe avec plusieurs snapshots
- WHEN Jobierre lance `plakar-search query @gdrive --snapshot abc1234 "rapport"`
- THEN seuls les resultats du snapshot abc1234 sont retournes
- GIVEN un store indexe
- WHEN Jobierre lance `plakar-search query @gdrive --type images "chien"`
- THEN seuls les fichiers image sont retournes (collection ChromaDB "images")

### [P4] Scenario : Gestion de la passphrase

**Description** : L'outil gere les differents modes d'authentification Plakar.

**Criteres d'acceptation** :
- GIVEN un store nomme @gdrive configurer dans Plakar
- WHEN Jobierre lance `plakar-search index @gdrive`
- THEN Plakar utilise la passphrase de sa config interne (aucune fournie)
- GIVEN un store par chemin /var/backups non configure
- WHEN Jobierre lance `plakar-search index /var/backups --passphrase "xxx"`
- THEN la passphrase est transmise a Plakar via `PLAKAR_PASSPHRASE`
- WHEN Jobierre oublie la passphrase pour un store par chemin
- THEN l'outil affiche une erreur claire "Passphrase requise pour ce store"

### [P5] Scenario : Edge cases - Fichiers non supportes

**Description** : L'indexation continue malgre les fichiers non supportes.

**Criteres d'acceptation** :
- GIVEN un store contenant des .exe, .dll, .bin
- WHEN l'indexation est lancee
- THEN ces fichiers sont ignores silencieusement (ou logges avec --verbose)
- AND l'indexation continue normalement pour les autres fichiers

### [P6] Scenario : Edge cases - Interruption et reprise

**Description** : L'indexation peut etre interrompue et reprise.

**Criteres d'acceptation** :
- GIVEN une indexation en cours interrompue (Ctrl+C)
- WHEN Jobierre relance `plakar-search index @gdrive`
- THEN l'indexation reprend la ou elle etait (grace a state.json)
- AND les fichiers deja indexes ne sont pas re-traites

### [P7] Scenario : Edge cases - Store inaccessible

**Description** : Erreur claire si le store Plakar n'est pas accessible.

**Criteres d'acceptation** :
- GIVEN un store @gdrive dont l'authentification a expire
- WHEN Jobierre lance `plakar-search index @gdrive`
- THEN un message d'erreur explicite est affiche
- AND le code de sortie est non-zero

### [P8] Scenario : Consultation du statut

**Description** : Jobierre verifie l'etat d'indexation de ses stores.

**Criteres d'acceptation** :
- GIVEN un store @gdrive partiellement indexe
- WHEN Jobierre lance `plakar-search status @gdrive`
- THEN l'outil affiche : nom du store, nombre de fichiers indexes, nombre total de snapshots, dernier snapshot indexe, progression

## Requirements

### P1 - Fondations

- REQ-001 : La CLI accepte un repository Plakar comme premier argument (`@store` ou `/chemin`)
- REQ-002 : La commande `index` declenche l'indexation de TOUS les snapshots d'un store
- REQ-003 : La commande `query` accepte une requete en langage naturel et retourne les fichiers les plus pertinents
- REQ-004 : La commande `status` affiche l'etat d'indexation d'un store
- REQ-005 : L'aide (`--help`) est disponible pour chaque commande avec exemples

### P1 - Extraction de contenu

- REQ-010 : Extraction de texte depuis les fichiers .txt, .md, .csv (lecture directe)
- REQ-011 : Extraction de texte depuis les fichiers .py, .js, .html, .css, .json, .yaml, .xml (lecture directe)
- REQ-012 : Extraction de texte depuis les fichiers .pdf via pymupdf
- REQ-013 : Extraction de texte depuis les fichiers .docx via python-docx
- REQ-014 : Extraction de texte depuis les fichiers .xlsx via openpyxl
- REQ-015 : Extraction des metadonnees EXIF des images (.jpg, .jpeg, .png, .heic) via Pillow
- REQ-016 : Les fichiers binaires/executables (.exe, .dll, .so, .bin, .zip, .tar, .gz) sont ignores

### P1 - Embedding

- REQ-020 : Embedding du texte extrait via EmbeddingGemma-300M (768 dimensions)
- REQ-021 : Embedding des images via SigLIP2-base-patch16-224 (768 dimensions)
- REQ-022 : Les deux modeles sont telecharges automatiquement au premier lancement
- REQ-023 : Les modeles tournent exclusivement en local (pas d'API externe)

### P1 - Stockage vectoriel

- REQ-030 : Les vecteurs texte sont stockes dans une collection ChromaDB "text" (768d, cosine)
- REQ-031 : Les vecteurs image sont stockes dans une collection ChromaDB "images" (768d, cosine)
- REQ-032 : Chaque vecteur reference son snapshot_id, chemin, et type MIME dans ses metadonnees
- REQ-033 : Les indexes sont stockes dans `~/.plakar-search/stores/<store_name>/chromadb/`
- REQ-034 : Un fichier `state.json` par store enregistre la progression d'indexation

### P1 - Recherche

- REQ-040 : La recherche texte encode la requete avec EmbeddingGemma et interroge la collection "text"
- REQ-041 : La recherche image encode la requete avec SigLIP2 et interroge la collection "images"
- REQ-042 : Les resultats des deux collections sont fusionnes et tries par score normalise
- REQ-043 : Chaque resultat affiche : score (0.00-1.00), snapshot_id:tronque, chemin, type

### P1 - Interface Plakar

- REQ-050 : Communication avec Plakar via subprocess (`plakar at <repo> <cmd>`)
- REQ-051 : Les snapshots sont listes via `plakar at <repo> ls --json`
- REQ-052 : Les fichiers d'un snapshot sont listes via `plakar at <repo> ls <snapshot> --json`
- REQ-053 : Le contenu d'un fichier est lu via `plakar at <repo> cat <snapshot>:<path>`
- REQ-054 : Pour les destinations nommees (@store), aucune passphrase n'est fournie (Plakar gere)

### P1 - Robustesse

- REQ-060 : L'indexation est interruptible (Ctrl+C) avec reprise via state.json
- REQ-061 : Les fichiers illisibles/corrompus sont logges et sautes, sans arreter l'indexation
- REQ-062 : Si un store est inaccessible, un message d'erreur explicite est affiche
- REQ-063 : L'outil est parallele (threading/async) pour l'indexation de plusieurs fichiers

### P2 - Multi-stores

- REQ-070 : Les indexes de chaque store sont isoles dans des sous-dossiers distincts
- REQ-071 : `plakar-search status` (sans argument) liste tous les stores indexes
- REQ-072 : On peut indexer plusieurs stores sans conflit

### P2 - Filtres de recherche

- REQ-080 : Option `--snapshot <id>` pour filtrer les resultats par snapshot
- REQ-081 : Option `--type <text|images>` pour limiter la recherche a une collection
- REQ-082 : Option `--limit <n>` pour limiter le nombre de resultats (defaut 20)

### P2 - Experience

- REQ-090 : Barre de progression (rich) pendant l'indexation
- REQ-091 : Option `--verbose` pour afficher les logs detailles (fichiers sautes, erreurs)
- REQ-092 : Commande `plakar-search version` affiche la version et les modeles charges

## Hors Scope

- Interface web / UI graphique (CLI uniquement pour la v1)
- Restauration de fichiers depuis les resultats de recherche
- Support multi-utilisateurs
- API REST
- Indexation incrementale automatique (re-indexation manuelle uniquement)
- Mode deep avec PaliGemma 2 (OCR, captioning) → v2
- Filtrage par date/plage temporelle → v2
- Filtrage par tags Plakar → v2
- Support des fichiers video/audio (extraction de contenu)
- Packaging pypi/brew (installation via git clone + pip)

## Criteres de Succes

- SC-001 : Indexation de 10 000 fichiers en < 5 minutes sur un CPU standard (Apple M1/M2 ou equivalent)
- SC-002 : Recherche semantique en < 1 seconde (hors chargement modele, apres indexation)
- SC-003 : RAM maximale < 2 Go en mode normal (hors modele PaliGemma)
- SC-004 : 0 crash sur fichiers illisibles/corrompus (graceful degradation)
- SC-005 : L'utilisateur retrouve un fichier sans connaitre son nom exact en < 3 tentatives de requete
- SC-006 : Installation en < 3 commandes (git clone, pip install, plakar-search --help)
