#!/usr/bin/env python3
"""Validation Agent Skills minimale, sans dépendance externe."""

import re
import sys
from pathlib import Path


def validate(path: Path) -> tuple[bool, str]:
    skill = path / "SKILL.md"
    if not skill.is_file():
        return False, "SKILL.md absent"
    content = skill.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return False, "frontmatter invalide"
    fields = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            return False, f"ligne frontmatter invalide : {line}"
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    if set(fields) != {"name", "description"}:
        return False, "le frontmatter doit contenir uniquement name et description"
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fields["name"]) or len(fields["name"]) > 64:
        return False, "nom de skill invalide"
    if not fields["description"] or len(fields["description"]) > 1024 or any(c in fields["description"] for c in "<>"):
        return False, "description de skill invalide"
    if path.name != fields["name"]:
        return False, "le dossier et le nom du skill diffèrent"
    metadata = path / "agents/openai.yaml"
    if not metadata.is_file() or f"${fields['name']}" not in metadata.read_text(encoding="utf-8"):
        return False, "agents/openai.yaml absent ou default_prompt incorrect"
    return True, "Skill is valid!"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: quick_validate.py <skill-directory>")
    ok, message = validate(Path(sys.argv[1]))
    print(message)
    raise SystemExit(0 if ok else 1)
