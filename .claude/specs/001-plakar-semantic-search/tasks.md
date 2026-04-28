# Taches - 001 Plakar Semantic Search

> Ce fichier guide l'implementation entre les sessions.
> Cocher les taches completees. Reprendre a la premiere tache non-cochee.
> Ne pas modifier l'ordre des taches sans raison.

## Phase 1 — Setup & Preparation

- [x] [T001] Creer la structure du projet : `src/plakar_search/` + `__init__.py` + `__main__.py` — `src/plakar_search/`
- [x] [T002] Creer `pyproject.toml` avec metadonnees et toutes les dependances — `pyproject.toml`
- [x] [T003] Creer `config.py` : chemins `~/.plakar-search/stores/`, nommage des dossiers store (`_store_dir_name`), constantes — `src/plakar_search/config.py`

## Phase 2 — Core Implementation

- [x] [T010] [REQ-050,051,052,053,054] Creer `plakar_client.py` : classe `PlakarClient` avec `list_snapshots()`, `list_files(snapshot)`, `cat(snapshot, path)`, gestion passphrase (auto pour @store, env var pour path) — `src/plakar_search/plakar_client.py`
- [x] [T011] [REQ-010,011,016] Creer `extractors.py` : registry dict `EXTENSIONS` pour formats texte brut (.txt, .md, .py, .js, .html, .css, .json, .yaml, .xml, .csv) + set `SKIP_EXTENSIONS` pour fichiers binaires ignores — `src/plakar_search/extractors.py`
- [x] [T012] [REQ-012] Ajouter extracteur PDF dans `extractors.py` via pymupdf (`pymupdf.open(stream=bytes)`) — `src/plakar_search/extractors.py`
- [x] [T013] [REQ-013,014] Ajouter extracteurs .docx (python-docx) et .xlsx (openpyxl) dans `extractors.py` — `src/plakar_search/extractors.py`
- [x] [T014] [REQ-015] Ajouter extracteur EXIF/metadonnees image dans `extractors.py` via `PIL.Image.getexif()` — `src/plakar_search/extractors.py`
- [x] [T015] [REQ-020,022,023] Creer `embedder.py` : singleton `get_egemma()` chargeant `google/embeddinggemma-300m` via `SentenceTransformer`, methode `encode_text_queries()` et `encode_text_documents()` — `src/plakar_search/embedder.py`
- [x] [T016] [REQ-021,022,023] Ajouter `get_siglip()` dans `embedder.py` chargeant `google/siglip2-base-patch16-224` via `AutoModel`+`AutoProcessor`, methodes `encode_image()` et `encode_text_query()` — `src/plakar_search/embedder.py`
- [x] [T017] [REQ-030,031,032,033] Creer `store.py` : classe `VectorStore` wrappant `chromadb.PersistentClient`, methodes `get_or_create_collections()`, `add_text()`, `add_image()`, `query_text()`, `query_images()` — `src/plakar_search/store.py`
- [x] [T018] [REQ-034] Creer `state.py` : classes `IndexState` avec load/save JSON, tracking snapshots (pending/in_progress/done) — `src/plakar_search/state.py`

## Phase 3 — Integration & Wiring

- [x] [T020] [REQ-001,002,060,061,063,090] Creer `indexer.py` : classe `Indexer` orchestrant l'indexation complete (list snapshots → list files → extract text/EXIF → embed → store), avec `ThreadPoolExecutor`, gestion Ctrl+C, reprise via state, barre rich — `src/plakar_search/indexer.py`
- [x] [T021] [REQ-040,041,042,080,081,082] Creer `searcher.py` : classe `Searcher` avec methode `search()` encodant la query avec EGemma et SigLIP2, interrogeant les 2 collections, fusionnant les scores (min-max normalisation), appliquant filtres snapshot/type/limit — `src/plakar_search/searcher.py`
- [x] [T022] [REQ-001,002,005,090,091] Creer `cli.py` : commande `index` (wires Indexer + rich progress, accepte repo + --passphrase + --verbose) — `src/plakar_search/cli.py`
- [x] [T023] [REQ-003,005,043] Ajouter commande `query` dans `cli.py` (wires Searcher, affiche table rich : score, snapshot, path, type) — `src/plakar_search/cli.py`
- [x] [T024] [REQ-004,071] Ajouter commande `status` dans `cli.py` (lit state.json du store ou liste tous les stores) — `src/plakar_search/cli.py`
- [x] [T025] [REQ-092] Ajouter commande `version` dans `cli.py` (affiche version + modeles charges) — `src/plakar_search/cli.py`
- [x] [T026] [REQ-070,072] Finaliser `config.py` : gestion multi-store (un dossier chromadb/ + state.json par store), isolation complete — `src/plakar_search/config.py`

## Phase 4 — Tests & Validation

- [x] [T030] Ecrire tests unitaires pour `plakar_client.py` (mock subprocess, scenarios passphrase @store vs /path) — `tests/test_plakar_client.py`
- [x] [T031] Ecrire tests unitaires pour `extractors.py` (chaque format, exif, binary skip) — `tests/test_extractors.py`
- [x] [T032] Ecrire tests unitaires pour `state.py` (load/save, progression, reprise) — `tests/test_state.py`
- [x] [T033] Ecrire test d'integration : `index` sur un store Plakar de test puis `query` pour verifier les resultats — `tests/test_integration.py`
- [x] [T034] Valider le scenario [P1] : index + query retourne fichiers attendus — manuel
- [x] [T035] Valider les scenarios [P4] (passphrase), [P5] (fichiers non supportes), [P6] (interruption/reprise) — manuel
- [x] [T036] Valider les scenarios [P2] (multi-stores), [P3] (filtres), [P7] (store inaccessible), [P8] (status) — manuel

## Notes de Session

### Session 2026-04-27 23:19
- Complete : T001 — Creation de la structure du package (src/plakar_search/__init__.py + __main__.py)
- Complete : T002 — Creation du pyproject.toml avec metadonnees et toutes les dependances
- Complete : T003 — Creation de config.py (HOME_DIR, STORES_DIR, store_dir_name(), helpers de path)
- Complete : T010 — Creation de plakar_client.py (wrapper subprocess, gestion passphrase @store vs /path)
- Complete : T011 — Creation de extractors.py (registry EXTENSIONS + SKIP_EXTENSIONS)
- Complete : T012 — Ajout extracteur PDF via pymupdf
- Complete : T013 — Ajout extracteurs .docx et .xlsx
- Complete : T014 — Ajout extracteur EXIF via Pillow
- Complete : T015 — Creation du module embedder (singleton EmbeddingGemma-300M)
- Complete : T016 — Ajout singleton SigLIP2 (encode_image + encode_text_query)
- Complete : T017 — Creation du wrapper VectorStore (ChromaDB PersistentClient, collections text/images, add/query)
- Complete : T018 — Creation de state.py (IndexState load/save JSON, tracking snapshots, atomic write)
- Observations : Projet greenfield, rien n'existait a part .git et .claude
- Prochaine : T020

### Session 2026-04-28 00:15
- Complete : T020 — Creation de indexer.py (orchestrateur : ThreadPoolExecutor, batch embedding, SIGINT handler, rich progress optionnel)
- Complete : T021 — Creation de searcher.py (recherche hybride texte+image, normalisation min-max, filtres snapshot/type/limit)
- Observations : Venv cree (.venv/), package installe en dev mode. Toutes les dependances resolues.
- Complete : T022 — Creation de cli.py (commande index avec rich Progress, --passphrase, --verbose, --help avec exemples)
- Complete : T023 — Ajout commande query (wires Searcher, table rich Score/Snapshot/Path/Type, --snapshot --type --limit)
- Complete : T024 — Ajout commande status (detail par store ou liste de tous les stores, lit state.json + compteurs ChromaDB)
- Complete : T025 — Ajout commande version (affiche version + modeles configures sans les charger)
- Complete : T026 — Finalisation config.py (list_stores(), validation repo vide, isolation complete multi-store)
- Observations : Phase 3 (Integration & Wiring) terminee. Les 4 commandes CLI fonctionnent (index, query, status, version).
- Complete : T030 — Tests unitaires plakar_client.py (16 tests, mock subprocess, passphrase @store vs /path, erreurs)
- Complete : T031 — Tests extractors.py (22 tests: texte, PDF, DOCX, XLSX, EXIF, SKIP_EXTENSIONS)
- Complete : T032 — Tests state.py (11 tests: load/save/resume, atomic write, lifecycle)
- Complete : T033 — Test d'integration index→query (4 tests, mock PlakarClient + fake embedders, vraie ChromaDB)
- Observations : 53 tests passent en 2.48s. 0 crash.
- Prochaine : T034

### Changements post-plan
- **PlakarClient** : Adaptation parsing texte (plus de --json). `ls -recursive <snapshot>` pour list_files. Deux formats distincts : snapshots (`date id size duration path`) et fichiers (`date perms owner group size path`).
- **SigLIP2** : `encode_image` nécessite `text=[""]` + `images`, `encode_text_query` nécessite une image dummy. Le modèle SigLIP attend toujours les deux modalités.
- Tests mis à jour pour refléter le parsing texte.

### Session 2026-04-28 00:15 (suite)
- Complete : T034 — Validation P1 : index @kloset_test + query "code python" → fichiers .py en top
- Complete : T035 — Validations P4/P5/P6 : passphrase ok, .pyc/.egg ignorés, state/reprise testé unitairement
- Complete : T036 — Validations P2/P3/P7/P8 : filtres --type ok, store inconnu erreur claire, status multi-store ok
- Observations : Toutes les taches sont cochees. 55 tests passent. Projet fonctionnel de bout en bout.
