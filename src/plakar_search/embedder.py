import torch
from sentence_transformers import SentenceTransformer


class EmbeddingGemma:
    def __init__(self):
        self._model = SentenceTransformer(
            "google/embeddinggemma-300m",
            model_kwargs={"torch_dtype": torch.bfloat16},
        )

    def encode_text_queries(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()

    def encode_text_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()


_egemma: EmbeddingGemma | None = None


def get_egemma() -> EmbeddingGemma:
    global _egemma
    if _egemma is None:
        _egemma = EmbeddingGemma()
    return _egemma
