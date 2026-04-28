from plakar_search.config import DEFAULT_LIMIT
from plakar_search.embedder import get_egemma, get_siglip
from plakar_search.store import VectorStore


class Searcher:
    def __init__(self, repo: str):
        self.repo = repo
        self.store = VectorStore(repo)

    def search(
        self,
        query: str,
        limit: int = DEFAULT_LIMIT,
        type_filter: str | None = None,
        snapshot_filter: str | None = None,
    ) -> list[dict]:
        where = None
        if snapshot_filter:
            where = {"snapshot_id": snapshot_filter}

        text_results = []
        image_results = []

        if type_filter is None or type_filter == "text":
            text_results = self._query_text(query, limit, where)

        if type_filter is None or type_filter == "images":
            image_results = self._query_images(query, limit, where)

        if type_filter is None:
            merged = self._merge_hybrid(text_results, image_results)
        else:
            merged = text_results + image_results

        merged.sort(key=lambda r: r["score"], reverse=True)
        return merged[:limit]

    def _query_text(self, query: str, limit: int, where: dict | None) -> list[dict]:
        egemma = get_egemma()
        query_embedding = egemma.encode_text_queries([query])[0]

        raw = self.store.query_text(query_embedding, n_results=limit, where=where)

        return self._parse_results(raw, "text")

    def _query_images(self, query: str, limit: int, where: dict | None) -> list[dict]:
        siglip = get_siglip()
        query_embedding = siglip.encode_text_query([query])[0]

        raw = self.store.query_images(query_embedding, n_results=limit, where=where)

        return self._parse_results(raw, "images")

    def _parse_results(self, raw: dict, result_type: str) -> list[dict]:
        results = []
        ids = raw.get("ids", [[]])[0]
        distances = raw.get("distances", [[]])[0]
        metadatas = raw.get("metadatas", [[]])[0]

        for i, doc_id in enumerate(ids):
            distance = distances[i] if i < len(distances) else 0.0
            meta = metadatas[i] if i < len(metadatas) else {}
            results.append({
                "id": doc_id,
                "score": 1.0 - distance,
                "snapshot_id": meta.get("snapshot_id", ""),
                "path": meta.get("path", ""),
                "type": result_type,
            })

        return results

    def _merge_hybrid(
        self,
        text_results: list[dict],
        image_results: list[dict],
    ) -> list[dict]:
        text_results = self._normalize_scores(text_results)
        image_results = self._normalize_scores(image_results)
        return text_results + image_results

    @staticmethod
    def _normalize_scores(results: list[dict]) -> list[dict]:
        if len(results) < 2:
            for r in results:
                r["score"] = 1.0
            return results

        scores = [r["score"] for r in results]
        min_s = min(scores)
        max_s = max(scores)
        spread = max_s - min_s

        for r in results:
            if spread > 0:
                r["score"] = (r["score"] - min_s) / spread
            else:
                r["score"] = 1.0

        return results
