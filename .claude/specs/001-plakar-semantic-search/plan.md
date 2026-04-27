# Plan Technique - 001 Plakar Semantic Search

## Contexte Technique
- **Stack** : Python 3.11+, typer (CLI), rich (UI), sentence-transformers (EmbeddingGemma), transformers (SigLIP2), chromadb (vector store)
- **Fichiers impactes** : Greenfield — tous les fichiers sont a creer
- **Dependencies existantes** : Aucune (projet vierge)
- **Dependencies nouvelles** :
  - `typer>=0.15`, `rich>=13` — CLI + barre de progression
  - `sentence-transformers>=3.0` — EmbeddingGemma-300M
  - `transformers>=4.50`, `torch>=2.6`, `accelerate` — SigLIP2
  - `chromadb>=0.5` — Vector store local
  - `pymupdf>=1.24` — PDF text extraction
  - `python-docx>=1.1` — .docx extraction
  - `openpyxl>=3.1` — .xlsx extraction
  - `Pillow>=11` — Image loading + EXIF
  - `python-magic>=0.4` — MIME type detection

## Approche

Projet Python standalone (pas de fork Plakar, pas de SDK Go) qui communique avec Plakar via `subprocess`. L'outil s'aligne sur la syntaxe `plakar at <repo>` : le repository (path ou @destination) est le premier argument apres la commande. L'indexation est stateful (state.json par store) pour permettre la reprise. Deux modeles d'embedding (EmbeddingGemma pour texte, SigLIP2 pour images) produisent des vecteurs 768d stockes dans deux collections ChromaDB distinctes. La recherche hybride fusionne les resultats des deux collections avec normalisation des scores. L'extraction de texte utilise un pattern "registry" par extension/MIME — simple a etendre.

## Decisions Techniques

| Decision | Choix | Raison | Alternatives rejetees |
|----------|-------|--------|-----------------------|
| **Pattern CLI** | `typer` + `rich` | Le plus standard en Python moderne, belle UI terminal sans effort | click (moins moderne), argparse (trop verbeux) |
| **ChromaDB mode** | `PersistentClient` (embedded) | Zéro infra, un dossier par store, pas de serveur | HttpClient (overkill), LanceDB (moins mature) |
| **Embedding approach** | Embeddings explicites (`provide_embeddings`) | Controle total du modele, pas de dependance ChromaDB→modele | `embedding_function=` ChromaDB (couplage fort) |
| **SigLIP2 chargement** | `transformers.AutoModel` + `AutoProcessor` | API standard HuggingFace, support officiel Google | sentence-transformers CLIP (pas multilingue) |
| **Extraction texte** | Registry dict `{extension: extractor_fn}` | Simple, extensible, zero abstraction inutile | Parser MIME generique (trop complexe) |
| **Parallellisme** | `concurrent.futures.ThreadPoolExecutor` | I/O-bound (subprocess + encode), pas besoin d'asyncio | multiprocessing (trop lourd), asyncio (pas necessaire) |
| **State format** | JSON (`state.json` par store) | Lisible, debugable, pas besoin de SQLite | SQLite (overkill pour un fichier de progression) |
| **Passphrase** | Variable d'env `PLAKAR_PASSPHRASE` + flag `--passphrase` | Aligne sur le fonctionnement Plakar, standard Unix | Prompt interactif (casse le scripting) |
| **Stockage index** | `~/.plakar-search/stores/<name>/` | Isolé par store, nom derive du repository | ~/.plakar-search/ (plat, conflit multi-stores) |

## Structure des Changements

### Fichiers a creer

```
plakar_search/
├── pyproject.toml                         # Meta-donnees + dependances
├── README.md                              # Deja existant — a mettre a jour
├── src/
│   └── plakar_search/
│       ├── __init__.py                    # Package marker + version
│       ├── __main__.py                    # Entry point: app()
│       ├── cli.py                         # Commandes typer: index, query, status, version
│       ├── plakar_client.py               # Wrapper subprocess plakar at <repo> <cmd>
│       ├── indexer.py                     # Orchestrateur d'indexation (snapshot list → files → embeddings)
│       ├── embedder.py                    # Singleton model manager (EmbeddingGemma + SigLIP2)
│       ├── store.py                       # ChromaDB wrapper (get_or_create, add, query)
│       ├── searcher.py                    # Recherche hybride + fusion scores
│       ├── extractors.py                  # Registry extraction texte par extension
│       ├── config.py                      # Chemins, settings, defaults
│       └── state.py                       # Gestion state.json (lecture/ecriture)
```

### Aucun fichier a modifier ou supprimer (projet vierge)

## Mapping Requirements → Implementation

### P1 - Fondations

| Requirement | Fichier(s) | Approche |
|-------------|-----------|----------|
| REQ-001 | `cli.py` | `typer.Argument` pour le repository, validation regex `^(@|/)?` |
| REQ-002 | `cli.py`, `indexer.py`, `plakar_client.py` | `PlakarClient.list_snapshots()` → boucle → `Indexer.index_snapshot()` |
| REQ-003 | `cli.py`, `searcher.py` | `Embedder.embed_query()` → `Store.query_both()` → `Searcher.merge()` |
| REQ-004 | `cli.py`, `state.py` | `State.load()` → afficher stats (rich table) |
| REQ-005 | `cli.py` | Decorateurs `@app.command(help="...")` typer |

### P1 - Extraction de contenu

| Requirement | Fichier(s) | Approche |
|-------------|-----------|----------|
| REQ-010 | `extractors.py` | `extractors[".txt"] = lambda b: b.decode("utf-8", errors="ignore")` |
| REQ-011 | `extractors.py` | Meme approche pour les formats texte brut |
| REQ-012 | `extractors.py` | `pymupdf.open(stream=b)` → join page texts |
| REQ-013 | `extractors.py` | `docx.Document(io.BytesIO(b))` → join paragraph texts |
| REQ-014 | `extractors.py` | `openpyxl.load_workbook(io.BytesIO(b))` → itérer cellules |
| REQ-015 | `extractors.py` | `PIL.Image.open(io.BytesIO(b))._getexif()` → dict → format texte |
| REQ-016 | `indexer.py` | `SKIP_EXTENSIONS` set, vérifié avant extraction |

### P1 - Embedding

| Requirement | Fichier(s) | Approche |
|-------------|-----------|----------|
| REQ-020 | `embedder.py` | `SentenceTransformer("google/embeddinggemma-300m")` avec `model_dtype=torch.bfloat16` |
| REQ-021 | `embedder.py` | `AutoModel.from_pretrained("google/siglip2-base-patch16-224")` + `AutoProcessor` |
| REQ-022 | `embedder.py` | `.from_pretrained()` HuggingFace telecharge automatiquement |
| REQ-023 | `embedder.py` | Pas d'appel API externe, tout en local |

### P1 - Stockage vectoriel

| Requirement | Fichier(s) | Approche |
|-------------|-----------|----------|
| REQ-030 | `store.py` | `PersistentClient(path=...).get_or_create_collection("text", metadata={"hnsw:space": "cosine"})` |
| REQ-031 | `store.py` | Idem pour collection "images" |
| REQ-032 | `indexer.py` | Metadonnees ChromaDB : `{"snapshot_id": ..., "path": ..., "mime": ...}` |
| REQ-033 | `config.py` | `~/.plakar-search/stores/<store_name>/chromadb/` (nom derive du repo via `_store_dir_name()`) |
| REQ-034 | `state.py` | `{"store": "@gdrive", "snapshots": {"abc1234": "done", "def5678": "in_progress"}, "last_updated": "..."}` |

### P1 - Recherche

| Requirement | Fichier(s) | Approche |
|-------------|-----------|----------|
| REQ-040 | `searcher.py` | `Embedder.embed_query_egemma(query)` → `Store.query_text()` |
| REQ-041 | `searcher.py` | `Embedder.embed_query_siglip(query)` → `Store.query_images()` |
| REQ-042 | `searcher.py` | `merge_hybrid(text_results, image_results)` : normalisation min-max des distances, tri global |
| REQ-043 | `cli.py` | Table rich avec colonnes Score, Snapshot, Path, Type |

### P1 - Interface Plakar

| Requirement | Fichier(s) | Approche |
|-------------|-----------|----------|
| REQ-050 | `plakar_client.py` | `subprocess.run(["plakar", "at", self.repo, *args], env=env, capture_output=True)` |
| REQ-051 | `plakar_client.py` | `self._run("ls", "--json")` → `json.loads()` |
| REQ-052 | `plakar_client.py` | `self._run("ls", snapshot, "--json")` → `json.loads()` |
| REQ-053 | `plakar_client.py` | `self._run("cat", f"{snapshot}:{path}")` → `stdout.encode()` |
| REQ-054 | `plakar_client.py` | Si repo commence par `@` → pas de passphrase, sinon env `PLAKAR_PASSPHRASE` |

### P1 - Robustesse

| Requirement | Fichier(s) | Approche |
|-------------|-----------|----------|
| REQ-060 | `state.py`, `indexer.py` | `signal.SIGINT` handler → `state.save()` avant exit. Au redemarrage, `state.load()` → skip deja indexes |
| REQ-061 | `indexer.py` | try/except par fichier, log l'erreur (stderr ou --verbose), continue |
| REQ-062 | `plakar_client.py` | `subprocess.CalledProcessError` → message explicite + exit code |
| REQ-063 | `indexer.py` | `ThreadPoolExecutor(max_workers=4)` pour le traitement de fichiers par lot |

### P2 - Multi-stores

| Requirement | Fichier(s) | Approche |
|-------------|-----------|----------|
| REQ-070 | `config.py` | `_store_dir_name("@gdrive")` → `"gdrive"`, pour `/var/backups` → `"var_backups"` |
| REQ-071 | `cli.py`, `state.py` | `status` sans argument → lister `~/.plakar-search/stores/` et afficher state.json de chaque |
| REQ-072 | `store.py` | Chaque store a son propre `PersistentClient` avec path unique |

### P2 - Filtres de recherche

| Requirement | Fichier(s) | Approche |
|-------------|-----------|----------|
| REQ-080 | `searcher.py` | `chromadb.where={"snapshot_id": snapshot_id}` dans le query |
| REQ-081 | `searcher.py` | Si `--type images` → query seulement "images", si `--type text` → seulement "text" |
| REQ-082 | `searcher.py`, `cli.py` | Parametre `n_results` de ChromaDB, defaut 20 |

### P2 - Experience

| Requirement | Fichier(s) | Approche |
|-------------|-----------|----------|
| REQ-090 | `cli.py` | `rich.progress.Progress` avec barre par snapshot + barre globale |
| REQ-091 | `cli.py` | `typer.Option("--verbose", "-v")` → `logging.basicConfig(level=DEBUG)` |
| REQ-092 | `cli.py` | `plakar-search version` → affiche version, modeles charges, dimensions |

## Risques et Mitigations

| Risque | Impact | Probabilite | Mitigation |
|--------|--------|-------------|------------|
| `plakar ls --json` n'existe pas / change de format | Haut | Moyen | Test au startup (`Ping`), wrapper tolerant aux champs manquants |
| Modele SigLIP2 trop lent sur CPU | Moyen | Moyen | bfloat16, batch inference, option `--no-images` pour desactiver |
| ChromaDB corruption si interruption brutale | Moyen | Bas | `state.json` atomique (write → rename), pas de corruption ChromaDB connue en mode Persistent |
| RAM > 2 Go avec les 2 modeles | Haut | Bas | bfloat16 reduit de moitie, garbage collect apres chaque batch |
| `plakar cat` tres lent pour gros fichiers | Bas | Moyen | Truncate a 1 Mo pour l'extraction texte (un fichier texte de +1 Mo est un edge case) |
| Licence Google (Gemma/SigLIP2) bloquante | Moyen | Bas | Fallback sur `all-MiniLM-L6-v2` + `clip-ViT-B-32` (MIT/Apache) |

## Questions Ouvertes

- Aucune — toutes les decisions ont ete couvertes dans la spec et la discussion preparatoire.
