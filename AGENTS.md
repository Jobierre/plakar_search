# AGENTS.md — Plakar Search

## Projet
Greenfield — outil CLI Python `plakar-search` : recherche sémantique par contexte dans un store Plakar.
Tout le cadrage est dans `.claude/specs/001-plakar-semantic-search/` (spec → plan → tasks).

## Langue
L'utilisateur s'appelle Jobierre et parle français. Répondre en français.

## Règles globales
Charger `~/.claude/CLAUDE.md` en début de session (profil NAS/Unraid, usage grepai).

## Architecture clé
- **Interaction Plakar** : `subprocess.run("plakar at <repo> <cmd>")` — pas de SDK Go, pas de fork
- **Syntaxe** : repository = `@gdrive` (destination nommée) ou `/var/backups` (chemin)
- **Passphrase** : auto pour `@store`, `PLAKAR_PASSPHRASE` env var pour `/path`
- **Index** : `~/.plakar-search/stores/<store_name>/chromadb/` + `state.json`

## Stack
Python 3.11+, `typer`+`rich` (CLI), `sentence-transformers` (EmbeddingGemma-300M), `transformers` (SigLIP2), `chromadb` (PersistentClient embedded), `pymupdf`+`python-docx`+`openpyxl`+`Pillow` (extraction).

## Modèles
Deux modèles chargés en local via HuggingFace. Accepter la licence Google Gemma avant premier usage.
- `google/embeddinggemma-300m` → texte (768d)
- `google/siglip2-base-patch16-224` → images (768d)

## Structure
```
src/plakar_search/
├── cli.py              # typer (index, query, status, version)
├── plakar_client.py    # subprocess wrapper
├── indexer.py          # orchestrateur d'indexation
├── embedder.py         # modèles singleton
├── store.py            # ChromaDB wrapper
├── searcher.py         # recherche hybride
├── extractors.py       # extraction texte par extension
├── config.py           # chemins, settings
└── state.py            # state.json progression
```

## Workflow de dev
1. Lire spec.md → plan.md → tasks.md dans `.claude/specs/001-plakar-semantic-search/`
2. Suivre les tâches de `tasks.md` dans l'ordre
3. Pas de build/lint/test configurés pour l'instant (projet vide)

## Dépendance externe
L'outil `plakar` doit être installé et dans le PATH. Vérifier avec `plakar version`.
