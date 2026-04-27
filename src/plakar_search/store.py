import chromadb

from plakar_search.config import COLLECTION_TEXT, COLLECTION_IMAGES, store_chroma_path


class VectorStore:
    def __init__(self, repo: str):
        path = str(store_chroma_path(repo))
        self._client = chromadb.PersistentClient(path=path)
        self._text = self._client.get_or_create_collection(
            name=COLLECTION_TEXT,
            metadata={"hnsw:space": "cosine"},
        )
        self._images = self._client.get_or_create_collection(
            name=COLLECTION_IMAGES,
            metadata={"hnsw:space": "cosine"},
        )

    def add_text(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        self._text.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    def add_image(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        self._images.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

    def query_text(
        self,
        query_embedding: list[float],
        n_results: int = 20,
        where: dict | None = None,
    ) -> dict:
        return self._text.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

    def query_images(
        self,
        query_embedding: list[float],
        n_results: int = 20,
        where: dict | None = None,
    ) -> dict:
        return self._images.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["metadatas", "distances"],
        )

    def count_text(self) -> int:
        return self._text.count()

    def count_images(self) -> int:
        return self._images.count()
