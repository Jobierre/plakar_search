import torch
from PIL import Image
from sentence_transformers import SentenceTransformer
from transformers import AutoModel, AutoProcessor


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


class SigLIP2:
    def __init__(self):
        self._model = AutoModel.from_pretrained(
            "google/siglip2-base-patch16-224",
            torch_dtype=torch.bfloat16,
        )
        self._processor = AutoProcessor.from_pretrained(
            "google/siglip2-base-patch16-224"
        )
        self._model.eval()

    def encode_image(self, images: list[Image.Image]) -> list[list[float]]:
        inputs = self._processor(images=images, return_tensors="pt")
        inputs = {k: v.to(self._model.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self._model(**inputs)
        return outputs.image_embeds.cpu().float().tolist()

    def encode_text_query(self, texts: list[str]) -> list[list[float]]:
        inputs = self._processor(
            text=texts, return_tensors="pt", padding="max_length"
        )
        inputs = {k: v.to(self._model.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self._model(**inputs)
        return outputs.text_embeds.cpu().float().tolist()


_siglip: SigLIP2 | None = None


def get_siglip() -> SigLIP2:
    global _siglip
    if _siglip is None:
        _siglip = SigLIP2()
    return _siglip
