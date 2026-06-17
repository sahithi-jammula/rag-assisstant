"""Simple lexical tokens for BM25 (English-friendly)."""

from __future__ import annotations

import re


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[A-Za-z0-9]+", text.lower()) if len(t) > 1]
