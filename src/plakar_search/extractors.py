import pymupdf


def _extract_text(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")


def _extract_pdf(data: bytes) -> str:
    doc = pymupdf.open(stream=data)
    texts = []
    for page in doc:
        t = page.get_text()
        if t:
            texts.append(t)
    doc.close()
    return "\n".join(texts)


EXTENSIONS: dict[str, object] = {
    ".txt": _extract_text,
    ".md": _extract_text,
    ".csv": _extract_text,
    ".py": _extract_text,
    ".js": _extract_text,
    ".html": _extract_text,
    ".css": _extract_text,
    ".json": _extract_text,
    ".yaml": _extract_text,
    ".yml": _extract_text,
    ".xml": _extract_text,
    ".pdf": _extract_pdf,
}

SKIP_EXTENSIONS: set[str] = {
    ".exe", ".dll", ".so", ".bin",
    ".zip", ".tar", ".gz", ".bz2", ".xz",
    ".7z", ".rar",
    ".mp3", ".mp4", ".avi", ".mov", ".mkv",
    ".ttf", ".otf", ".woff", ".woff2",
    ".iso", ".dmg",
}
