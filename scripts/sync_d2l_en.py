#!/usr/bin/env python3
"""
Sparse-clone d2l-ai/d2l-en with only chapter_* trees (plus index + license files).

Requires: git on PATH.

Default destination: data/corpus/d2l-en/
The RAG loader scans data/corpus/** recursively, so Markdown under chapter folders is indexed.

Book licensing: see upstream LICENSE (CC BY-SA–style for prose). Attribute the project when
redistributing derived material; this script only clones for local indexing.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_REPO = "https://github.com/d2l-ai/d2l-en.git"


def _run(cmd: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def _top_level_sparse_paths(dest: Path) -> list[str]:
    """Paths at repo root to include: all chapter_* dirs plus index and license files."""
    res = subprocess.run(
        ["git", "-C", str(dest), "ls-tree", "--name-only", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    names = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
    chapters = [n for n in names if n.startswith("chapter_")]
    if not chapters:
        sys.exit(
            "No chapter_* directories found at repo root. "
            "Upstream layout may have changed; inspect d2l-ai/d2l-en on GitHub."
        )
    # Leading "/" + trailing "/" on dirs matches only repo-root trees (see git sparse-checkout NON-CONE).
    # Root files must be "/index.md" not "index.md" or every nested index.md is included (e.g. under contrib/).
    out: list[str] = [f"/{n}/" for n in chapters]
    for extra in ("index.md", "LICENSE", "LICENSE-SUMMARY"):
        if extra in names:
            out.append(f"/{extra}")
    return out


def sync(*, dest: Path, repo: str, clean: bool) -> None:
    dest = dest.resolve()
    if clean and dest.exists():
        shutil.rmtree(dest)

    if dest.exists() and not (dest / ".git").is_dir():
        try:
            if any(dest.iterdir()):
                sys.exit(
                    f"Refusing to clone: {dest} exists, is not a git repo, and is not empty. "
                    "Remove it or pass --clean to delete and re-clone."
                )
        except OSError as exc:
            sys.exit(f"Cannot read destination directory {dest}: {exc}")
        dest.rmdir()

    dest.parent.mkdir(parents=True, exist_ok=True)

    if not (dest / ".git").is_dir():
        _run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--filter=blob:none",
                "--sparse",
                repo,
                str(dest),
            ]
        )
    else:
        _run(["git", "-C", str(dest), "fetch", "--depth", "1", "origin"])
        _run(["git", "-C", str(dest), "pull", "--ff-only"])

    paths = _top_level_sparse_paths(dest)
    _run(["git", "-C", str(dest), "sparse-checkout", "set", "--no-cone", *paths])

    print(
        f"\nDone. Chapter sources are under:\n  {dest}\n"
        "Next: open the Streamlit app and click **Rebuild index**.\n",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sparse-clone d2l-ai/d2l-en (chapter folders only) into the corpus."
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=PROJECT_ROOT / "data" / "corpus" / "d2l-en",
        help="Clone location (default: data/corpus/d2l-en)",
    )
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help="Git remote URL",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete destination before cloning (fresh download).",
    )
    args = parser.parse_args()

    try:
        sync(dest=args.dest, repo=args.repo, clean=args.clean)
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
    except FileNotFoundError:
        sys.exit("git executable not found. Install Git for Windows and ensure it is on PATH.")


if __name__ == "__main__":
    main()
