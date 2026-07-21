#!/usr/bin/env python3
"""Contrôles statiques légers destinés à la CI."""

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", "__pycache__"}
TEXT_SUFFIXES = {"", ".md", ".py", ".toml", ".yaml", ".yml", ".json", ".jsonl", ".txt", ".sh", ".gitignore"}
PATTERNS = {
    "chemin personnel absolu": re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+/"),
    "identité historique codée en dur": re.compile("Smo" + "zzi", re.IGNORECASE),
    "clé API probable": re.compile(r"(?:sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16})"),
}


def files():
    for path in ROOT.rglob("*"):
        if path.is_file() and not any(part in SKIP for part in path.parts) and path.suffix in TEXT_SUFFIXES:
            yield path


def main() -> int:
    failures = []
    for path in files():
        content = path.read_text(encoding="utf-8")
        for label, pattern in PATTERNS.items():
            if pattern.search(content):
                failures.append(f"{path.relative_to(ROOT)}: {label}")
    fixtures = ROOT / "tests/fixtures"
    for path in fixtures.rglob("*"):
        if path.is_file() and path.stat().st_size > 20_000:
            failures.append(f"{path.relative_to(ROOT)}: fixture trop volumineux")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("Repository checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
