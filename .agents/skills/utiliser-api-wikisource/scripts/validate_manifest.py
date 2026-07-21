#!/usr/bin/env python3
"""Valide un manifeste d’écritures pour fr.wikisource.org, sans accès réseau."""
import json, sys, unicodedata
from pathlib import Path

VALID_OPS = {"create", "edit"}

def fail(message):
    print(f"ERREUR: {message}", file=sys.stderr)
    raise SystemExit(1)

def main():
    if len(sys.argv) != 2:
        fail("usage: validate_manifest.py MANIFESTE.json")
    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("api") != "https://fr.wikisource.org/w/api.php":
        fail("endpoint API différent de fr.wikisource.org")
    user = data.get("assertuser")
    if not isinstance(user, str) or not user.strip():
        fail("assertuser manque")
    ops = data.get("operations")
    if not isinstance(ops, list) or not ops:
        fail("operations doit être une liste non vide")
    seen = set()
    for i, op in enumerate(ops, 1):
        if op.get("op") not in VALID_OPS:
            fail(f"opération {i}: op doit être create ou edit")
        title = op.get("title")
        if not isinstance(title, str) or not title.strip():
            fail(f"opération {i}: titre absent")
        if title != unicodedata.normalize("NFC", title):
            fail(f"opération {i}: titre non normalisé NFC")
        if title in seen:
            fail(f"opération {i}: titre dupliqué: {title}")
        seen.add(title)
        text = op.get("text")
        source = op.get("text_file")
        if bool(text is not None) == bool(source):
            fail(f"opération {i}: fournir exactement text ou text_file")
        if source and not (path.parent / source).is_file():
            fail(f"opération {i}: fichier introuvable: {source}")
        if not isinstance(op.get("summary"), str) or not op["summary"].strip():
            fail(f"opération {i}: résumé absent")
        if op["op"] == "create" and "baserevid" in op:
            fail(f"opération {i}: une création ne doit pas avoir baserevid")
        if op["op"] == "edit" and not isinstance(op.get("baserevid"), int):
            fail(f"opération {i}: une modification exige baserevid entier")
    print(f"OK: {len(ops)} opérations, endpoint frwikisource, identité {user}")

if __name__ == "__main__":
    main()
