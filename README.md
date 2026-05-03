# plakar-search

Recherche sémantique par contexte dans un store Plakar.

Tu ne te souviens plus où tu as rangé ce fichier ? Tu sais qu'il parlait de « facture électricité 2024 » mais pas son nom ? **plakar-search** indexe le contenu de tes backups Plakar dans une base vectorielle locale (ChromaDB) et te permet de retrouver n'importe quel fichier en langage naturel — sans connaître son nom ni son emplacement exact.

```
plakar-search index @gdrive
plakar-search query @gdrive "facture électricité janvier 2024"
```

## Comment ça marche

```
plakar at @store cat    ──►  Extraction texte  ──►  EmbeddingGemma-300M  ──►  ChromaDB "text"
                             (txt, pdf, docx...)      (vecteurs 768d)

plakar at @store cat    ──►  Chargement image    ──►  SigLIP2              ──►  ChromaDB "images"
                             (jpg, png, heic...)      (vecteurs 768d)

plakar at @store cat    ──►  EXIF + filename     ──►  EmbeddingGemma-300M  ──►  ChromaDB "text"
                             (metadonnees images)
```

Deux modèles tournent **exclusivement en local** (pas d'API externe, pas de cloud) :
- `google/embeddinggemma-300m` — encodage du texte (768 dimensions)
- `google/siglip2-base-patch16-224` — encodage des images (768 dimensions)

Téléchargés automatiquement au premier lancement via HuggingFace (~1 Go chacun).

## Installation

**Prérequis :** Python 3.11+, Plakar installé et dans le PATH.

```bash
git clone https://github.com/.../plakar_search.git
cd plakar_search
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Accepter la licence Google Gemma avant le premier usage (HuggingFace te la présentera).

## Utilisation

### Indexer un store

```bash
# Store nommé (Plakar gère la passphrase)
plakar-search index @gdrive

# Store par chemin (passphrase obligatoire)
plakar-search index /var/backups --passphrase "secret"

# Mode verbeux (voir les fichiers ignorés)
plakar-search index @s3 --verbose
```

L'indexation est **interruptible** (Ctrl+C) et **reprenable** : relance la même commande, elle reprend là où elle s'était arrêtée grâce à `state.json`.

### Rechercher

```bash
# Recherche dans les deux collections (texte + images)
plakar-search query @gdrive "photos vacances plage 2024"

# Seulement les images
plakar-search query @s3 --type images "chat"

# Seulement le texte
plakar-search query @gdrive --type text "configuration réseau"

# Filtrer par snapshot
plakar-search query @gdrive --snapshot abc1234 "rapport"

# Limiter le nombre de résultats (défaut : 20)
plakar-search query @gdrive -n 5 "important"
```

### Consulter l'état

```bash
# Détail d'un store
plakar-search status @gdrive

# Tous les stores indexés
plakar-search status
```

### Version

```bash
plakar-search version
```

## Formats supportés

| Catégorie | Extensions |
|-----------|-----------|
| Texte brut | `.txt` `.md` `.csv` `.py` `.js` `.html` `.css` `.json` `.yaml` `.yml` `.xml` |
| Documents | `.pdf` `.docx` `.xlsx` |
| Images (EXIF) | `.jpg` `.jpeg` `.png` `.heic` |
| Images (visuel) | `.jpg` `.jpeg` `.png` `.heic` |

Les fichiers binaires (`.exe` `.dll` `.zip` `.mp4` `.iso`...) sont ignorés automatiquement.

## Fichiers et stockage

Tout est stocké dans `~/.plakar-search/stores/<nom_du_store>/` :

```
~/.plakar-search/stores/
├── gdrive/
│   ├── chromadb/       # Base vectorielle ChromaDB
│   └── state.json      # Progression d'indexation
├── s3/
│   ├── chromadb/
│   └── state.json
└── var_backups/
    ├── chromadb/
    └── state.json
```

Chaque store est **complètement isolé** — pas de conflit entre @gdrive et @s3.

## Développement

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## Licence

MIT
