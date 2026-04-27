# Taches - 001 Plakar Semantic Search

> Ce fichier guide l'implementation entre les sessions.
> Cocher les taches completees. Reprendre a la premiere tache non-cochee.
> Ne pas modifier l'ordre des taches sans raison.

## Phase 1 — Setup & Preparation

- [ ] [T001] Creer la structure du projet : `src/plakar_search/` + `__init__.py` + `__main__.py` — `src/plakar_search/`
- [ ] [T002] Creer `pyproject.toml` avec metadonnees et toutes les dependances — `pyproject.toml`
- [ ] [T003] Creer `config.py` : chemins `~/.plakar-search/stores/`, nommage des dossiers store (`_store_dir_name`), constantes — `src/plakar_search/config.py`

## Phase 2 — Core Implementation

- [ ] [T010] [REQ-050,051,052,053,054] Creer `plakar_client.py` : classe `PlakarClient` avec `list_snapshots()`, `list_files(snapshot)`, `cat(snapshot, path)`, gestion passphrase (auto pour @store, env var pour path) — `src/plakar_search/plakar_client.py`
- [ ] [T011] [REQ-010,011,016] Creer `extractors.py` : registry dict `EXTENSIONS` pour formats texte brut (.txt, .md, .py, .js, .html, .css, .json, .yaml, .xml, .csv) + set `SKIP_EXTENSIONS` pour fichiers binaires ignores — `src/plakar_search/extractors.py`
- [ ] [T012] [REQ-012] Ajouter extracteur PDF dans `extractors.py` via pymupdf (`pymupdf.open(stream=bytes)`) — `src/plakar_search/extractors.py`
- [ ] [T013] [REQ-013,014] Ajouter extracteurs .docx (python-docx) et .xlsx (openpyxl) dans `extractors.py` — `src/plakar_search/extractors.py`
- [ ] [T014] [REQ-015] Ajouter extracteur EXIF/metadonnees image dans `extractors.py` via `PIL.Image._getexif()` — `src/plakar_search/extractors.py`
- [ ] [T015] [REQ-020,022,023] Creer `embedder.py` : singleton `get_egemma()` chargeant `google/embeddinggemma-300m` via `SentenceTransformer`, methode `encode_text_queries()` et `encode_text_documents()` — `src/plakar_search/embedder.py`
- [ ] [T016] [REQ-021,022,023] Ajouter `get_siglip()` dans `embedder.py` chargeant `google/siglip2-base-patch16-224` via `AutoModel`+`AutoProcessor`, methodes `encode_image()` et `encode_text_query()` — `src/plakar_search/embedder.py`
- [ ] [T017] [REQ-030,031,032,033] Creer `store.py` : classe `VectorStore` wrappant `chromadb.PersistentClient`, methodes `get_or_create_collections()`, `add_text()`, `add_image()`, `query_text()`, `query_images()` — `src/plakar_search/store.py`
- [ ] [T018] [REQ-034] Creer `state.py` : classes `IndexState` avec load/save JSON, tracking snapshots (pending/in_progress/done) — `src/plakar_search/state.py`

## Phase 3 — Integration & Wiring

- [ ] [T020] [REQ-001,002,060,061,063,090] Creer `indexer.py` : classe `Indexer` orchestrant l'indexation complete (list snapshots → list files → extract text/EXIF → embed → store), avec `ThreadPoolExecutor`, gestion Ctrl+C, reprise via state, barre rich — `src/plakar_search/indexer.py`
- [ ] [T021] [REQ-040,041,042,080,081,082] Creer `searcher.py` : classe `Searcher` avec methode `search()` encodant la query avec EGemma et SigLIP2, interrogeant les 2 collections, fusionnant les scores (min-max normalisation), appliquant filtres snapshot/type/limit — `src/plakar_search/searcher.py`
- [ ] [T022] [REQ-001,002,005,090,091] Creer `cli.py` : commande `index` (wires Indexer + rich progress, accepte repo + --passphrase + --verbose) — `src/plakar_search/cli.py`
- [ ] [T023] [REQ-003,005,043] Ajouter commande `query` dans `cli.py` (wires Searcher, affiche table rich : score, snapshot, path, type) — `src/plakar_search/cli.py`
- [ ] [T024] [REQ-004,071] Ajouter commande `status` dans `cli.py` (lit state.json du store ou liste tous les stores) — `src/plakar_search/cli.py`
- [ ] [T025] [REQ-092] Ajouter commande `version` dans `cli.py` (affiche version + modeles charges) — `src/plakar_search/cli.py`
- [ ] [T026] [REQ-070,072] Finaliser `config.py` : gestion multi-store (un dossier chromadb/ + state.json par store), isolation complete — `src/plakar_search/config.py`

## Phase 4 — Tests & Validation

- [ ] [T030] Ecrire tests unitaires pour `plakar_client.py` (mock subprocess, scenarios passphrase @store vs /path) — `tests/test_plakar_client.py`
- [ ] [T031] Ecrire tests unitaires pour `extractors.py` (chaque format, exif, binary skip) — `tests/test_extractors.py`
- [ ] [T032] Ecrire tests unitaires pour `state.py` (load/save, progression, reprise) — `tests/test_state.py`
- [ ] [T033] Ecrire test d'integration : `index` sur un store Plakar de test puis `query` pour verifier les resultats — `tests/test_integration.py`
- [ ] [T034] Valider le scenario [P1] : index + query retourne fichiers attendus — manuel
- [ ] [T035] Valider les scenarios [P4] (passphrase), [P5] (fichiers non supportes), [P6] (interruption/reprise) — manuel
- [ ] [T036] Valider les scenarios [P2] (multi-stores), [P3] (filtres), [P7] (store inaccessible), [P8] (status) — manuel

## Notes de Session
<!-- Les notes sont ajoutees automatiquement par /implement -->
<!-- Format : ### Session YYYY-MM-DD HH:MM -->
