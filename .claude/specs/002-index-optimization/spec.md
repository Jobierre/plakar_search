# 002 - Indexation Parallele (Workers Configurables)

## Metadata
- Cree : 2026-05-03
- Status : Draft
- Branche : feature/002-index-optimization

## Resume
Ajouter un flag `--workers` a la commande `index` pour controler le parallelisme, et passer le nombre de workers par defaut de 4 a 16. L'objectif est de reduire drastiquement le temps d'indexation en exploitant mieux le CPU, le goulot principal etant le subprocess `plakar cat` par fichier.

## Scenarios Utilisateur

### [P1] Scenario principal : Indexation plus rapide avec 16 workers par defaut
**Description** : Jobierre relance `plakar-search index @macbook` et constate que l'indexation est environ 3-4x plus rapide grace aux 16 workers paralleles.

**Criteres d'acceptation** :
- GIVEN un store Plakar avec ~10 000 fichiers (texte + images)
- WHEN Jobierre lance `plakar-search index @macbook`
- THEN l'indexation utilise 16 workers par defaut
- AND l'indexation complete en < 5 minutes (vs > 12 min precedemment)
- AND les snapshots deja indexes sont toujours sautes (reprise via state.json)
- AND la progression rich affiche correctement l'avancement

### [P2] Scenario secondaire : Ajustement manuel via --workers
**Description** : Jobierre peut forcer un nombre specifique de workers selon sa machine.

**Criteres d'acceptation** :
- GIVEN un store Plakar
- WHEN Jobierre lance `plakar-search index @macbook --workers 32` sur une machine puissante
- THEN 32 workers sont utilises pour l'indexation
- GIVEN un petit serveur avec 2 coeurs
- WHEN Jobierre lance `plakar-search index @backups --workers 2`
- THEN seuls 2 workers sont utilises, evitant la saturation CPU
- AND en l'absence du flag, le defaut (16) est utilise

### [P3] Scenario : Validation de la valeur --workers
**Description** : Les valeurs invalides sont rejetees avec un message clair.

**Criteres d'acceptation** :
- GIVEN la commande `plakar-search index @macbook --workers 0`
- THEN un message d'erreur indique que la valeur doit etre >= 1
- GIVEN la commande `plakar-search index @macbook --workers -1`
- THEN un message d'erreur indique que la valeur doit etre positive
- GIVEN la commande `plakar-search index @macbook --workers abc`
- THEN un message d'erreur indique que la valeur doit etre un entier

### [P4] Scenario : Bump version 0.2.0
**Description** : La version du package passe a 0.2.0 pour refleter la nouvelle fonctionnalite.

**Criteres d'acceptation** :
- GIVEN l'installation de plakar-search v0.2.0
- WHEN Jobierre lance `plakar-search version`
- THEN l'outil affiche "plakar-search v0.2.0"
- AND l'option --workers apparait dans `plakar-search index --help`

## Requirements

### P1 - Workers configurables

- REQ-001 : La commande `index` accepte un flag `--workers <n>` (int, min=1, default=16)
- REQ-002 : Le `ThreadPoolExecutor` est initialise avec `max_workers` egal a la valeur du flag
- REQ-003 : La constante `DEFAULT_MAX_WORKERS` passe de 4 a 16 dans `config.py`
- REQ-004 : Le `--help` de `index` affiche l'option --workers avec sa valeur par defaut et une description

### P2 - Validation

- REQ-005 : Si `--workers < 1`, afficher une erreur explicite et exit avec code 1
- REQ-006 : Si `--workers` n'est pas un entier valide, typer gere l'erreur automatiquement

### P3 - Version

- REQ-007 : La version dans `__init__.py` (ou `pyproject.toml`) passe de 0.1.0 a 0.2.0
- REQ-008 : Le `pyproject.toml` reflete la version 0.2.0

### P4 - Compatibilite

- REQ-009 : Les snapshots deja indexes avec la v0.1.0 restent valides (ChromaDB et state.json inchanges)
- REQ-010 : Les commandes `query`, `status` et `version` ne sont pas impactees

## Hors Scope

- Auto-detection du nombre de CPU (os.cpu_count) — l'utilisateur gere avec --workers
- Parallelisation inter-snapshots (les snapshots restent traites sequentiellement)
- Multi-cat / batching des appels plakar cat
- Deduplication cross-snapshot
- Optimisation de l'extraction de texte ou de l'embedding

## Criteres de Succes

- SC-001 : Benchmark : `plakar-search index @macbook` (avec 10k fichiers) passe de > 8 minutes a < 5 minutes
- SC-002 : Aucune regression fonctionnelle : query, status, reprise, Ctrl+C fonctionnent comme avant
- SC-003 : L'aide (`plakar-search index --help`) documente clairement l'option --workers
- SC-004 : La version 0.2.0 est affichee par `plakar-search version`
