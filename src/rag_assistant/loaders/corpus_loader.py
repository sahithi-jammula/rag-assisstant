"""Load plain text, Markdown, and PDF files from configured directories."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

from rag_assistant.config import (
    CORPUS_DIR,
    PDF_EXTENSIONS,
    PROJECT_ROOT,
    SAMPLES_DIR,
    TEXT_EXTENSIONS,
    UPLOADS_DIR,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RawDocument:
    """One logical document loaded from disk."""

    text: str
    source: str


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
        except Exception as exc:  # noqa: BLE001 — surface per-page PDF issues
            logger.warning("PDF extract failed for %s page: %s", path, exc)
            t = ""
        parts.append(t)
    return "\n\n".join(parts).strip()


def load_file(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return _read_text_file(path)
    if suffix in PDF_EXTENSIONS:
        return _read_pdf(path)
    logger.debug("Skipping unsupported file type: %s", path)
    return None


def iter_document_files(root: Path) -> Iterable[Path]:
    if not root.is_dir():
        return iter(())
    return (p for p in sorted(root.rglob("*")) if p.is_file() and not p.name.startswith("."))


def load_all_documents(
    extra_roots: list[Path] | None = None,
) -> tuple[list[RawDocument], list[dict[str, str]]]:
    """
    Load from corpus, uploads, samples, and any extra_roots.

    Returns (documents, source_manifest) where manifest entries are
    {path, sha256} for files that contributed (best-effort).
    """
    roots: list[Path] = []
    for d in (CORPUS_DIR, UPLOADS_DIR, SAMPLES_DIR):
        roots.append(d)
    if extra_roots:
        roots.extend(extra_roots)

    seen_sources: set[str] = set()
    all_docs: list[RawDocument] = []
    manifest: list[dict[str, str]] = []

    for root in roots:
        if not root.exists():
            continue
        for path in iter_document_files(root):
            text = load_file(path)
            if text is None:
                continue
            cleaned = text.strip()
            if not cleaned:
                continue
            try:
                rel = path.relative_to(PROJECT_ROOT)
            except ValueError:
                rel = path
            source = str(rel).replace("\\", "/")
            if source in seen_sources:
                continue
            seen_sources.add(source)
            all_docs.append(RawDocument(text=cleaned, source=source))
            if path.is_file():
                try:
                    digest = _sha256_file(path)
                except OSError as exc:
                    logger.warning("Could not hash %s: %s", path, exc)
                    digest = ""
                manifest.append({"path": source, "sha256": digest})

    return all_docs, manifest
