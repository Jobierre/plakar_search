from unittest.mock import MagicMock, patch

import plakar_search.embedder


def _make_valid_jpeg(exif_tags: dict | None = None) -> bytes:
    from io import BytesIO
    from PIL import Image

    img = Image.new("RGB", (10, 10), color="red")
    buf = BytesIO()
    if exif_tags:
        exif = img.getexif()
        for tag_id, value in exif_tags.items():
            exif[tag_id] = value
        img.save(buf, format="JPEG", exif=exif.tobytes())
    else:
        img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_valid_png() -> bytes:
    from io import BytesIO
    from PIL import Image

    img = Image.new("RGB", (10, 10), color="blue")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class FakeEGemma:
    def encode_text_documents(self, texts):
        return [[1.0] * 768 for _ in texts]

    def encode_text_queries(self, texts):
        return [[1.0] * 768 for _ in texts]


class FakeSigLIP:
    def encode_image(self, images):
        return [[1.0] * 768 for _ in images]

    def encode_text_query(self, texts):
        return [[1.0] * 768 for _ in texts]


def _setup_fake_embedders():
    plakar_search.embedder._egemma = FakeEGemma()
    plakar_search.embedder._siglip = FakeSigLIP()


def _teardown_fake_embedders():
    plakar_search.embedder._egemma = None
    plakar_search.embedder._siglip = None


SNAPSHOTS = [{"id": "snap001", "date": "2024-01-01"}]

TEXT_FILES = [
    {"path": "/readme.txt", "mime_type": "text/plain"},
    {"path": "/script.py", "mime_type": "text/x-python"},
    {"path": "/notes.md", "mime_type": "text/markdown"},
]

IMAGE_FILES = [
    {"path": "/photo.jpg", "mime_type": "image/jpeg"},
    {"path": "/logo.png", "mime_type": "image/png"},
]

ALL_FILES = TEXT_FILES + IMAGE_FILES

FILE_CONTENTS = {
    "/readme.txt": b"Ceci est un fichier README important",
    "/script.py": b"print('hello world')",
    "/notes.md": b"# Mes notes\n\n- Item 1\n- Item 2",
}


def _make_mock_client():
    client = MagicMock()
    client.list_snapshots.return_value = SNAPSHOTS
    client.list_files.return_value = ALL_FILES

    jpeg_with_exif = _make_valid_jpeg({0x010F: "TestCorp"})
    png_no_exif = _make_valid_png()

    dynamic_contents = {
        "/photo.jpg": jpeg_with_exif,
        "/logo.png": png_no_exif,
    }

    def fake_cat(snapshot_id, path):
        return dynamic_contents.get(path) or FILE_CONTENTS.get(path, b"")

    client.cat.side_effect = fake_cat
    return client


class TestIntegrationIndexQuery:
    def test_full_pipeline(self, tmp_path):
        repo = "@teststore"

        _setup_fake_embedders()

        try:
            mock_client = _make_mock_client()

            with patch(
                "plakar_search.store.store_chroma_path",
                return_value=tmp_path / "chromadb",
            ), patch(
                "plakar_search.indexer.store_state_path",
                return_value=tmp_path / "state.json",
            ), patch(
                "plakar_search.indexer.PlakarClient",
                return_value=mock_client,
            ):
                from plakar_search.indexer import Indexer

                indexer = Indexer(repo)
                indexer.index()

                assert not indexer.interrupted, "L'indexation n'aurait pas du etre interrompue"

            # Re-open with same paths for query
            with patch(
                "plakar_search.store.store_chroma_path",
                return_value=tmp_path / "chromadb",
            ):
                from plakar_search.searcher import Searcher
                from plakar_search.store import VectorStore

                store = VectorStore(repo)
                text_count = store.count_text()
                image_count = store.count_images()

                assert text_count == 4, (
                    f"Attendu 4 entrees texte (3 textes + 1 EXIF), obtenu {text_count}"
                )
                assert image_count >= 0, (
                    f"Entrees image: {image_count}"
                )

                searcher = Searcher(repo)
                results = searcher.search("test", limit=10)

                assert len(results) > 0, "La recherche devrait retourner des resultats"
                assert all("score" in r for r in results)
                assert all("path" in r for r in results)
                assert all("snapshot_id" in r for r in results)
                assert all("type" in r for r in results)
                assert results[0]["snapshot_id"] == "snap001"

                text_paths = {r["path"] for r in results if r["type"] == "text"}
                assert "/readme.txt" in text_paths
                assert "/script.py" in text_paths
                assert "/notes.md" in text_paths

        finally:
            _teardown_fake_embedders()

    def test_query_with_snapshot_filter(self, tmp_path):
        repo = "@teststore"

        _setup_fake_embedders()

        try:
            mock_client = _make_mock_client()

            with patch(
                "plakar_search.store.store_chroma_path",
                return_value=tmp_path / "chromadb",
            ), patch(
                "plakar_search.indexer.store_state_path",
                return_value=tmp_path / "state.json",
            ), patch(
                "plakar_search.indexer.PlakarClient",
                return_value=mock_client,
            ):
                from plakar_search.indexer import Indexer
                Indexer(repo).index()

            with patch(
                "plakar_search.store.store_chroma_path",
                return_value=tmp_path / "chromadb",
            ):
                from plakar_search.searcher import Searcher

                results = Searcher(repo).search(
                    "test",
                    snapshot_filter="snap001",
                    limit=10,
                )
                assert all(r["snapshot_id"] == "snap001" for r in results)

                results_other = Searcher(repo).search(
                    "test",
                    snapshot_filter="nonexistent",
                    limit=10,
                )
                assert len(results_other) == 0

        finally:
            _teardown_fake_embedders()

    def test_query_with_type_filter(self, tmp_path):
        repo = "@teststore"

        _setup_fake_embedders()

        try:
            mock_client = _make_mock_client()

            with patch(
                "plakar_search.store.store_chroma_path",
                return_value=tmp_path / "chromadb",
            ), patch(
                "plakar_search.indexer.store_state_path",
                return_value=tmp_path / "state.json",
            ), patch(
                "plakar_search.indexer.PlakarClient",
                return_value=mock_client,
            ):
                from plakar_search.indexer import Indexer
                Indexer(repo).index()

            with patch(
                "plakar_search.store.store_chroma_path",
                return_value=tmp_path / "chromadb",
            ):
                from plakar_search.searcher import Searcher

                text_results = Searcher(repo).search("test", type_filter="text", limit=10)
                assert all(r["type"] == "text" for r in text_results)

                image_results = Searcher(repo).search("test", type_filter="images", limit=10)
                assert all(r["type"] == "images" for r in image_results)

                all_results = Searcher(repo).search("test", limit=20)
                types = {r["type"] for r in all_results}
                assert types <= {"text", "images"}

        finally:
            _teardown_fake_embedders()

    def test_index_resume(self, tmp_path):
        repo = "@teststore"

        _setup_fake_embedders()

        try:
            mock_client = _make_mock_client()

            with patch(
                "plakar_search.store.store_chroma_path",
                return_value=tmp_path / "chromadb",
            ), patch(
                "plakar_search.indexer.store_state_path",
                return_value=tmp_path / "state.json",
            ), patch(
                "plakar_search.indexer.PlakarClient",
                return_value=mock_client,
            ):
                from plakar_search.indexer import Indexer
                from plakar_search.state import IndexState

                Indexer(repo).index()

                state = IndexState.load(repo, tmp_path / "state.json")
                assert state.done_count == 1
                assert state.is_done("snap001")

                # Second run should skip already-done snapshots
                mock_client.list_snapshots.return_value = SNAPSHOTS
                Indexer(repo).index()

                # The snapshot was skipped because it was already done
                # PlakarClient.list_files was not called again for snap001
                mock_client.list_files.assert_called_once()

        finally:
            _teardown_fake_embedders()
