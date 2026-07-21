#!/usr/bin/env python3
"""Corrections typographiques conservatrices pour des pages Wikisource.

Le script ne modifie automatiquement que les cas sans ambiguïté :

- normalisation Unicode NFC ;
- normalisation des fins de ligne en LF ;
- suppression des espaces horizontales en fin de ligne ;
- apostrophes droites isolées dans le texte en apostrophes typographiques.

Les constructions wiki et HTML sont protégées. Les ponctuations potentiellement
mal espacées sont seulement signalées : leur correction exige une relecture.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path


PROTECTED = re.compile(
    r"""
    <!--.*?-->
    |<(?P<tag>nowiki|pre|code|syntaxhighlight|math)\b[^>]*>.*?</(?P=tag)\s*>
    |<[^>]*>
    |\{\{.*?\}\}
    |\[\[.*?\]\]
    |\[(?:https?|ftp)://[^\]\n]*\]
    |'{2,}
    """,
    re.IGNORECASE | re.DOTALL | re.VERBOSE,
)

STRAIGHT_TEXT_APOSTROPHE = re.compile(r"(?<!')'(?!')")

AUDITS = (
    (
        "espace manquante avant ponctuation double",
        re.compile(r"(?<=[\w»)\]])[;!?]"),
    ),
    (
        "espace potentiellement manquante avant deux-points",
        re.compile(r"(?<=[^\W\d_]):(?=[^\d/])", re.UNICODE),
    ),
    (
        "espace potentiellement manquante après ponctuation",
        re.compile(r"[;:!?](?=[^\s\d/}\])»])"),
    ),
    (
        "guillemet français potentiellement mal espacé",
        re.compile(r"(?:«(?=\S)|(?<=\S)»)"),
    ),
    (
        "trois points au lieu du caractère points de suspension",
        re.compile(r"(?<!\.)\.{3}(?!\.)"),
    ),
)

WIKITEXT_AUDITS = (
    (
        "mot siècle dupliqué après le modèle {{s}}",
        re.compile(
            r"\{\{\s*s\s*\|[^|{}\n]+(?:\|[^|{}\n]+)?\}\}"
            r"[ \t]+(?:siècles?\b|s\.(?!\w))",
            re.IGNORECASE,
        ),
    ),
)


@dataclass
class Result:
    content: str
    apostrophes: int
    normalized: bool
    trailing_spaces: int

    @property
    def changed(self) -> bool:
        return self.apostrophes > 0 or self.normalized or self.trailing_spaces > 0


def transform_plain_text(text: str) -> tuple[str, int]:
    return STRAIGHT_TEXT_APOSTROPHE.subn("’", text)


def transform_wikitext(content: str) -> Result:
    original = content
    content = unicodedata.normalize("NFC", content.replace("\r\n", "\n").replace("\r", "\n"))
    normalized = content != original

    output: list[str] = []
    apostrophes = 0
    cursor = 0
    for match in PROTECTED.finditer(content):
        plain, count = transform_plain_text(content[cursor : match.start()])
        output.extend((plain, match.group(0)))
        apostrophes += count
        cursor = match.end()
    plain, count = transform_plain_text(content[cursor:])
    output.append(plain)
    apostrophes += count
    content = "".join(output)

    content, trailing_spaces = re.subn(r"[ \t]+(?=\n|$)", "", content)
    return Result(content, apostrophes, normalized, trailing_spaces)


def unprotected_text(content: str) -> str:
    return PROTECTED.sub(lambda match: " " * len(match.group(0)), content)


def audit(content: str) -> list[tuple[int, str, str]]:
    plain = unprotected_text(content)
    findings: list[tuple[int, str, str]] = []
    for label, pattern in WIKITEXT_AUDITS:
        for match in pattern.finditer(content):
            line = content.count("\n", 0, match.start()) + 1
            excerpt = content.splitlines()[line - 1].strip()
            findings.append((line, label, excerpt))
    for label, pattern in AUDITS:
        for match in pattern.finditer(plain):
            line = plain.count("\n", 0, match.start()) + 1
            excerpt = content.splitlines()[line - 1].strip()
            findings.append((line, label, excerpt))
    return findings


def process(path: Path, *, check: bool, show_audit: bool) -> bool:
    original = path.read_text(encoding="utf-8")
    result = transform_wikitext(original)

    if result.changed and not check:
        path.write_text(result.content, encoding="utf-8", newline="\n")

    state = "à corriger" if check and result.changed else "corrigé" if result.changed else "inchangé"
    print(
        f"{path}: {state} "
        f"(apostrophes={result.apostrophes}, "
        f"espaces_finales={result.trailing_spaces}, NFC/EOL={int(result.normalized)})"
    )

    if show_audit:
        for line, label, excerpt in audit(result.content):
            print(f"  L{line}: {label}: {excerpt}", file=sys.stderr)
    return result.changed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Corrige prudemment la typographie de fichiers wikitexte Wikisource."
    )
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="ne rien écrire et retourner 1 si une correction serait appliquée",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="signaler les anomalies ambiguës sans les modifier",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    changed = False
    for path in args.paths:
        if not path.is_file():
            print(f"{path}: fichier introuvable", file=sys.stderr)
            return 2
        changed |= process(path, check=args.check, show_audit=args.audit)
    return int(args.check and changed)


if __name__ == "__main__":
    raise SystemExit(main())
