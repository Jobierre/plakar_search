import io
import logging
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from PIL import Image

from plakar_search.config import DEFAULT_MAX_WORKERS, store_state_path
from plakar_search.embedder import get_egemma, get_siglip
from plakar_search.extractors import EXTENSIONS, SKIP_EXTENSIONS
from plakar_search.plakar_client import PlakarClient, PlakarError
from plakar_search.state import IndexState
from plakar_search.store import VectorStore

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic"}
TEXT_BATCH_SIZE = 32
IMAGE_BATCH_SIZE = 16
MAX_TEXT_BYTES = 1024 * 1024


class Indexer:
    def __init__(
        self,
        repo: str,
        passphrase: str | None = None,
        verbose: bool = False,
    ):
        self.repo = repo
        self.verbose = verbose
        self.client = PlakarClient(repo, passphrase)
        self.store = VectorStore(repo)
        self.state = IndexState.load(repo, store_state_path(repo))
        self._interrupted = False

        if verbose:
            logging.basicConfig(level=logging.DEBUG)

    def _on_interrupt(self, signum, frame):
        self._interrupted = True
        logger.warning("Interruption detectee, finalisation du batch en cours...")

    def index(self, progress=None) -> None:
        previous = signal.signal(signal.SIGINT, self._on_interrupt)

        try:
            snapshots = self.client.list_snapshots()
        except PlakarError as e:
            logger.error("Store %s inaccessible : %s", self.repo, e)
            return

        pending = [s for s in snapshots if not self.state.is_done(s.get("id", ""))]

        overall_task = None
        if progress is not None:
            overall_task = progress.add_task(
                "[bold blue]Snapshots",
                total=len(snapshots),
                completed=self.state.done_count,
            )

        for snap in pending:
            if self._interrupted:
                self.state.save()
                break

            snap_id = snap.get("id", "")
            self.state.mark_in_progress(snap_id)
            self.state.save()

            try:
                files = self.client.list_files(snap_id)
            except PlakarError as e:
                logger.error("Snapshot %s : %s", snap_id[:8], e)
                self.state.snapshots.pop(snap_id, None)
                self.state.save()
                continue

            self._process_snapshot(snap_id, files, progress)

            if not self._interrupted:
                self.state.mark_done(snap_id)
                self.state.save()

            if overall_task is not None and progress is not None:
                progress.advance(overall_task)

        signal.signal(signal.SIGINT, previous)

    def _process_snapshot(
        self,
        snapshot_id: str,
        files: list[dict],
        progress=None,
    ) -> None:
        text_batch = []
        image_batch = []

        for f in files:
            path = f.get("path", "")
            ext = Path(path).suffix.lower()

            if ext in SKIP_EXTENSIONS:
                logger.debug("Ignore : %s", path)
                continue

            if ext in IMAGE_EXTENSIONS:
                image_batch.append(f)
            elif ext in EXTENSIONS:
                text_batch.append(f)
            else:
                logger.debug("Extension non supportee : %s (%s)", path, ext)

        total = len(text_batch) + len(image_batch)

        snap_task = None
        if progress is not None and total > 0:
            snap_task = progress.add_task(
                f"[cyan]  {snapshot_id[:8]}",
                total=total,
            )

        if text_batch:
            self._process_text_files(snapshot_id, text_batch, progress, snap_task)

        if image_batch:
            self._process_image_files(snapshot_id, image_batch, progress, snap_task)

        if snap_task is not None and progress is not None:
            progress.remove_task(snap_task)

    def _process_text_files(
        self,
        snapshot_id: str,
        files: list[dict],
        progress=None,
        task_id=None,
    ) -> None:
        egemma = get_egemma()

        with ThreadPoolExecutor(max_workers=DEFAULT_MAX_WORKERS) as executor:
            for i in range(0, len(files), TEXT_BATCH_SIZE):
                if self._interrupted:
                    break

                batch = files[i : i + TEXT_BATCH_SIZE]

                futures = {}
                for f in batch:
                    path = f.get("path", "")
                    ext = Path(path).suffix.lower()
                    extractor = EXTENSIONS[ext]
                    futures[
                        executor.submit(self._cat_and_extract, snapshot_id, path, extractor)
                    ] = f

                ids = []
                docs = []
                metadatas = []

                for future in as_completed(futures):
                    f = futures[future]
                    path = f.get("path", "")
                    try:
                        text = future.result()
                    except Exception as e:
                        logger.error("Extraction echouee %s : %s", path, e)
                        continue

                    if not text:
                        logger.debug("Texte vide pour %s", path)
                        continue

                    ids.append(f"{snapshot_id}:{path}")
                    docs.append(text)
                    metadatas.append({
                        "snapshot_id": snapshot_id,
                        "path": path,
                        "mime": f.get("mime_type", ""),
                    })

                if ids:
                    embeddings = egemma.encode_text_documents(docs)
                    self.store.add_text(
                        ids=ids,
                        embeddings=embeddings,
                        documents=docs,
                        metadatas=metadatas,
                    )

                if task_id is not None and progress is not None:
                    progress.advance(task_id, len(batch))

    def _process_image_files(
        self,
        snapshot_id: str,
        files: list[dict],
        progress=None,
        task_id=None,
    ) -> None:
        egemma = get_egemma()
        siglip = get_siglip()

        with ThreadPoolExecutor(max_workers=DEFAULT_MAX_WORKERS) as executor:
            for i in range(0, len(files), IMAGE_BATCH_SIZE):
                if self._interrupted:
                    break

                batch = files[i : i + IMAGE_BATCH_SIZE]

                futures = {}
                for f in batch:
                    path = f.get("path", "")
                    futures[
                        executor.submit(self._cat_and_process_image, snapshot_id, path)
                    ] = f

                text_ids = []
                text_docs = []
                text_metadatas = []

                img_list = []
                img_ids = []
                img_metadatas = []

                for future in as_completed(futures):
                    f = futures[future]
                    path = f.get("path", "")
                    try:
                        exif_text, pil_image = future.result()
                    except Exception as e:
                        logger.error("Image inexploitable %s : %s", path, e)
                        continue

                    uid = f"{snapshot_id}:{path}"
                    meta = {
                        "snapshot_id": snapshot_id,
                        "path": path,
                        "mime": f.get("mime_type", ""),
                    }

                    if exif_text:
                        text_ids.append(uid)
                        text_docs.append(exif_text)
                        text_metadatas.append(meta)

                    if pil_image is not None:
                        img_list.append(pil_image)
                        img_ids.append(uid)
                        img_metadatas.append(meta)

                if text_ids:
                    text_embeddings = egemma.encode_text_documents(text_docs)
                    self.store.add_text(
                        ids=text_ids,
                        embeddings=text_embeddings,
                        documents=text_docs,
                        metadatas=text_metadatas,
                    )

                if img_list:
                    img_embeddings = siglip.encode_image(img_list)
                    self.store.add_image(
                        ids=img_ids,
                        embeddings=img_embeddings,
                        metadatas=img_metadatas,
                    )

                if task_id is not None and progress is not None:
                    progress.advance(task_id, len(batch))

    def _cat_and_extract(self, snapshot_id: str, path: str, extractor) -> str:
        data = self.client.cat(snapshot_id, path)
        data = data[:MAX_TEXT_BYTES]
        return extractor(data)

    def _cat_and_process_image(self, snapshot_id: str, path: str) -> tuple[str, object]:
        data = self.client.cat(snapshot_id, path)

        ext = Path(path).suffix.lower()
        extractor = EXTENSIONS.get(ext)

        exif_text = ""
        if extractor is not None:
            try:
                exif_text = extractor(data)
            except Exception:
                logger.debug("EXIF absent ou illisible pour %s", path)

        if exif_text:
            exif_text = f"path: {path}\n{exif_text}"

        pil_image = None
        try:
            pil_image = Image.open(io.BytesIO(data))
        except Exception:
            logger.debug("Fichier image corrompu %s", path)

        return exif_text, pil_image
