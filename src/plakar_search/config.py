from pathlib import Path

HOME_DIR = Path.home() / ".plakar-search"
STORES_DIR = HOME_DIR / "stores"

COLLECTION_TEXT = "text"
COLLECTION_IMAGES = "images"
VECTOR_DIM = 768

DEFAULT_LIMIT = 20
DEFAULT_MAX_WORKERS = 4


def store_dir_name(repo: str) -> str:
    if repo.startswith("@"):
        name = repo[1:]
    else:
        name = repo.lstrip("/").replace("/", "_")
    if not name:
        raise ValueError(f"Le repository '{repo}' produit un nom de store vide.")
    return name


def store_path(repo: str) -> Path:
    return STORES_DIR / store_dir_name(repo)


def store_chroma_path(repo: str) -> Path:
    return store_path(repo) / "chromadb"


def store_state_path(repo: str) -> Path:
    return store_path(repo) / "state.json"


def list_stores() -> list[str]:
    if not STORES_DIR.exists():
        return []
    return sorted(
        d.name
        for d in STORES_DIR.iterdir()
        if d.is_dir()
    )
