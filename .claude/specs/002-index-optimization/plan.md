# Plan Technique — 002 Indexation Parallele (Workers Configurables)

## Contexte Technique
- **Stack** : Python 3.11+, typer + rich (CLI), subprocess (plakar)
- **Fichiers impactes** : `cli.py`, `indexer.py`, `config.py`, `__init__.py`, `pyproject.toml`
- **Dependencies existantes** : typer, rich, concurrent.futures (stdlib)
- **Dependencies nouvelles** : aucune

## Approche

Ajouter un flag `--workers` a la commande `index` (via typer), le propager jusqu'au `Indexer` puis aux `ThreadPoolExecutor`. Modifier `DEFAULT_MAX_WORKERS` de 4 a 16 dans `config.py`. Bumper la version du package a 0.2.0 dans `__init__.py` et `pyproject.toml`.

C'est une feature de surface : la logique d'indexation ne change pas, seul le nombre de threads d'extraction parallele est modifie. Aucun changement d'architecture, aucun risque de regression fonctionnelle.

## Decisions Techniques

| Decision | Choix | Raison | Alternatives rejetees |
|----------|-------|--------|-----------------------|
| Type du flag --workers | `int` avec `min=1` via typer | typer gere la validation native, message d'erreur automatique | Validation manuelle dans la fonction |
| Propagation des workers | Parametre `max_workers` dans `Indexer.__init__` | Injection explicite, facile a tester | Variable globale / env var — moins propre |
| Commit atomique du bump | Meme commit que le flag --workers | Toute la feature v0.2.0 ensemble | Separer version et workers — inutile |
| Defaut workers | 16 (inchangé si déjà 16 avant... attends, c'est 4 actuellement → on passe a 16) | Demande explicite de Jobierre — agressif mais efficace | 8, 32 |

## Structure des Changements

### Fichiers a modifier

- `src/plakar_search/config.py` — `DEFAULT_MAX_WORKERS = 4` → `16`
- `src/plakar_search/cli.py` — ajouter `--workers` a `def index()`, le valider et le passer a `Indexer()`
- `src/plakar_search/indexer.py` — `Indexer.__init__` accepte `max_workers`, le stocke dans `self.max_workers`, et l'utilise dans `ThreadPoolExecutor(max_workers=self.max_workers)` aux lignes 148 et 211
- `src/plakar_search/__init__.py` — `__version__` de `"0.1.0"` → `"0.2.0"`
- `pyproject.toml` — `version = "0.1.0"` → `version = "0.2.0"`

### Fichiers a creer
Aucun.

### Fichiers a supprimer
Aucun.

## Mapping Requirements → Implementation

| Requirement | Fichier(s) | Approche |
|-------------|-----------|----------|
| REQ-001 (flag --workers) | `cli.py:26-49` | Ajouter `workers: int = typer.Option(DEFAULT_MAX_WORKERS, "--workers", "-w", min=1, help="...")`, passer `workers` a `Indexer(repo, passphrase, verbose, max_workers=workers)` |
| REQ-002 (ThreadPoolExecutor) | `indexer.py:148,211` | Utiliser `self.max_workers` au lieu de `DEFAULT_MAX_WORKERS` dans les 2 `ThreadPoolExecutor` |
| REQ-003 (DEFAULT_MAX_WORKERS 16) | `config.py:11` | Changer `4` en `16` |
| REQ-004 (--help affiche --workers) | `cli.py` | Automatique via typer.Option |
| REQ-005 (workers < 1 → erreur) | `cli.py` | `min=1` dans typer.Option gere ca automatiquement |
| REQ-006 (workers non entier) | `cli.py` | typer gere le parsing int automatiquement |
| REQ-007 (version 0.2.0) | `__init__.py` | Changer `"0.1.0"` en `"0.2.0"` |
| REQ-008 (pyproject.toml 0.2.0) | `pyproject.toml` | Changer `version = "0.1.0"` en `version = "0.2.0"` |
| REQ-009 (compatibilite arriere) | Tous | Aucun changement de schema ChromaDB ou state.json — full retrocompatible |
| REQ-010 (autres commandes inchangees) | `cli.py` | `query`, `status`, `version` ne sont pas touches |

## Risques et Mitigations

| Risque | Impact | Probabilite | Mitigation |
|--------|--------|-------------|------------|
| 16 workers saturent le CPU sur petite machine | Moyen | Moyen | Le flag `--workers` permet de reduire. L'utilisateur est informe dans le --help. Pas d'auto-detection CPU (hors scope). |
| 16 subprocess plakar simultanes saturent plakar lui-meme (locks, connexions store) | Moyen | Bas | Plakar est conçu pour etre utilise en production. 16 appels simultanes restent raisonnables. Si probleme, reduire avec --workers. |
| Regression sur la reprise (Ctrl+C) | Bas | Tres bas | Les workers sont dans un `with ThreadPoolExecutor`, le finally/atexit n'est pas impacte. Le signal handler reste en place. |

## Questions Ouvertes

Aucune — la spec est complete et les decisions sont claires.
