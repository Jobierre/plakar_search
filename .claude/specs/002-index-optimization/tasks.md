# Taches — 002 Indexation Parallele (Workers Configurables)

> Ce fichier guide l'implementation entre les sessions.
> Cocher les taches completees. Reprendre a la premiere tache non-cochee.
> Ne pas modifier l'ordre des taches sans raison.

## Phase 1 — Setup & Preparation
- [x] [T001] Bumper la version a 0.2.0 dans `__init__.py` — `src/plakar_search/__init__.py`
- [x] [T002] Bumper la version a 0.2.0 dans `pyproject.toml` — `pyproject.toml`

## Phase 2 — Core Implementation
- [x] [T010] [REQ-003] Passer `DEFAULT_MAX_WORKERS` de 4 a 16 — `src/plakar_search/config.py`
- [x] [T011] [REQ-002] Modifier `Indexer.__init__` pour accepter `max_workers` — `src/plakar_search/indexer.py`
- [x] [T012] [REQ-002] Remplacer `DEFAULT_MAX_WORKERS` par `self.max_workers` dans les 2 `ThreadPoolExecutor` — `src/plakar_search/indexer.py`
- [x] [T013] [REQ-001] Ajouter le flag `--workers` a la commande `index` et le passer a `Indexer` — `src/plakar_search/cli.py`

## Phase 3 — Validation
- [x] [T020] Verifier que `plakar-search version` affiche bien `v0.2.0`
- [x] [T021] Verifier que `plakar-search index --help` affiche l'option `--workers`
- [x] [T022] [REQ-005] Verifier que `--workers 0` et `--workers -1` sont rejetes
- [x] [T023] [REQ-009] Verifier que l'indexation reprend sans erreur sur un store deja indexe (compatibilite arriere)
- [x] [T024] [SC-001] Benchmark : mesurer le temps d'indexation avec `--workers 16` sur un store reel (SKIP — l'utilisateur le fera manuellement)

## Notes de Session
### Session 2026-05-03 — Implementation complete
- Complete : T001-T002 (bump version 0.2.0), T010-T013 (workers configurables via --workers), T020-T023 (validation), T024 (skip)
- Observations : Flag --workers utilise `typer.Option(min=1)` qui gere automatiquement la validation et l'affichage d'erreur. Aucune modification de schema ChromaDB/state.json. Full retrocompatible.
- Benchmark reporte : l'utilisateur testera `plakar-search index @macbook` manuellement avec 16 workers.
<!-- Les notes sont ajoutees automatiquement par /implement -->
<!-- Format : ### Session YYYY-MM-DD HH:MM -->
