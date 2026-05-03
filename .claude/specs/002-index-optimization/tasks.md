# Taches — 002 Indexation Parallele (Workers Configurables)

> Ce fichier guide l'implementation entre les sessions.
> Cocher les taches completees. Reprendre a la premiere tache non-cochee.
> Ne pas modifier l'ordre des taches sans raison.

## Phase 1 — Setup & Preparation
- [x] [T001] Bumper la version a 0.2.0 dans `__init__.py` — `src/plakar_search/__init__.py`
- [x] [T002] Bumper la version a 0.2.0 dans `pyproject.toml` — `pyproject.toml`

## Phase 2 — Core Implementation
- [x] [T010] [REQ-003] Passer `DEFAULT_MAX_WORKERS` de 4 a 16 — `src/plakar_search/config.py`
- [ ] [T011] [REQ-002] Modifier `Indexer.__init__` pour accepter `max_workers` — `src/plakar_search/indexer.py`
- [ ] [T012] [REQ-002] Remplacer `DEFAULT_MAX_WORKERS` par `self.max_workers` dans les 2 `ThreadPoolExecutor` — `src/plakar_search/indexer.py`
- [ ] [T013] [REQ-001] Ajouter le flag `--workers` a la commande `index` et le passer a `Indexer` — `src/plakar_search/cli.py`

## Phase 3 — Validation
- [ ] [T020] Verifier que `plakar-search version` affiche bien `v0.2.0`
- [ ] [T021] Verifier que `plakar-search index --help` affiche l'option `--workers`
- [ ] [T022] [REQ-005] Verifier que `--workers 0` et `--workers -1` sont rejetes
- [ ] [T023] [REQ-009] Verifier que l'indexation reprend sans erreur sur un store deja indexe (compatibilite arriere)
- [ ] [T024] [SC-001] Benchmark : mesurer le temps d'indexation avec `--workers 16` sur un store reel

## Notes de Session
<!-- Les notes sont ajoutees automatiquement par /implement -->
<!-- Format : ### Session YYYY-MM-DD HH:MM -->
