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
        return repo[1:]
    return repo.lstrip("/").replace("/", "_")


def store_path(repo: str) -> Path:
    return STORES_DIR / store_dir_name(repo)


def store_chroma_path(repo: str) -> Path:
    return store_path(repo) / "chromadb"


def store_state_path(repo: str) -> Path:
    return store_path(repo) / "state.json"
