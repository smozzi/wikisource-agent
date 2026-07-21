#!/usr/bin/env python3
"""Lanceur sans dépendances pour un chantier Wikisource francophone."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - message utile sous Python < 3.11
    tomllib = None


ROOT = Path(__file__).resolve().parents[1]
API = "https://fr.wikisource.org/w/api.php"
STATUS_ORDER = [
    "non initialisé",
    "cadré",
    "corpus initialisé",
    "lot préparé",
    "lot publié",
    "œuvre finalisée",
]


class WSError(RuntimeError):
    pass


def project_root() -> Path:
    override = os.environ.get("WIKISOURCE_PROJECT_ROOT")
    return Path(override).resolve() if override else Path.cwd().resolve()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        temporary = Path(stream.name)
    os.replace(temporary, path)


def write_once(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return True


def load_config(root: Path | None = None) -> dict:
    root = root or project_root()
    path = root / "PROJECT.toml"
    if not path.is_file():
        raise WSError("PROJECT.toml absent ; exécuter ./ws init")
    if tomllib is None:
        raise WSError("Python 3.11 ou plus récent est requis (module tomllib)")
    try:
        config = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise WSError(f"PROJECT.toml invalide : {exc}") from exc
    required = {
        "edition": ("title", "language"),
        "source": ("file",),
        "wikisource": ("api", "index", "expected_user"),
        "publication": ("require_approval", "max_writes_per_minute", "max_lot_views"),
    }
    for section, keys in required.items():
        value = config.get(section)
        if not isinstance(value, dict):
            raise WSError(f"section [{section}] absente de PROJECT.toml")
        for key in keys:
            if key not in value:
                raise WSError(f"clé {section}.{key} absente de PROJECT.toml")
    if config["wikisource"]["api"] != API:
        raise WSError("la v1 cible exclusivement fr.wikisource.org")
    if config["publication"]["require_approval"] is not True:
        raise WSError("publication.require_approval doit rester à true")
    maximum = config["publication"]["max_writes_per_minute"]
    if not isinstance(maximum, int) or not 1 <= maximum <= 8:
        raise WSError("max_writes_per_minute doit être compris entre 1 et 8")
    return config


def status(root: Path) -> str:
    if not (root / "PROJECT.toml").is_file():
        return STATUS_ORDER[0]
    corpus = root / "facsimile/CORPUS_MANIFEST.json"
    if not corpus.is_file():
        return STATUS_ORDER[1]
    lots = sorted((root / "lots").glob("lot-*/REPORT.md")) if (root / "lots").is_dir() else []
    final = root / "publication/FINALIZED"
    if final.is_file():
        return STATUS_ORDER[5]
    if any("publication vérifiée: oui" in p.read_text(encoding="utf-8").lower() for p in lots):
        return STATUS_ORDER[4]
    if any("préparation vérifiée: oui" in p.read_text(encoding="utf-8").lower() for p in lots):
        return STATUS_ORDER[3]
    return STATUS_ORDER[2]


def update_status(root: Path) -> None:
    current = status(root)
    content = (
        "# État du chantier\n\n"
        f"État reproductible : **{current}**\n\n"
        "États : cadré → corpus initialisé → lot préparé → lot publié → œuvre finalisée.\n\n"
        "Ce fichier est régénéré par `./ws check` et les commandes qui changent d’état.\n"
    )
    (root / "PROJECT_STATUS.md").write_text(content, encoding="utf-8", newline="\n")


def command_init(args: argparse.Namespace) -> None:
    root = project_root()
    root.mkdir(parents=True, exist_ok=True)
    title = args.title or "À renseigner"
    source = args.source or "facsimile/source.pdf"
    index = args.index or "À renseigner.djvu"
    user = args.user or "À renseigner"
    toml = f'''# Configuration versionnée ; ne placer aucun secret ici.
[edition]
title = {json.dumps(title, ensure_ascii=False)}
language = "fr"
year = ""
authors = []

[source]
file = {json.dumps(source, ensure_ascii=False)}
origin_url = ""
license = ""

[wikisource]
api = "{API}"
index = {json.dumps(index, ensure_ascii=False)}
expected_user = {json.dumps(user, ensure_ascii=False)}
upload_target = "commons"

[publication]
require_approval = true
max_writes_per_minute = 8
max_lot_views = 8
'''
    created = []
    templates = {
        "PROJECT.toml": toml,
        "PROJECT.md": "# Projet\n\nDécrire l’édition retenue, le périmètre et les décisions éditoriales.\n",
        "SOURCES.md": "# Sources\n\nConsigner la bibliographie, la provenance et les liens pérennes.\n",
        "RIGHTS.md": "# Droits\n\nÉtablir le domaine public en France et le copyright américain avant import.\n",
        "METADATA.md": "# Métadonnées\n\nConsigner auteur, traducteur, éditeur, lieu, date et identifiants.\n",
    }
    for relative, content in templates.items():
        if write_once(root / relative, content):
            created.append(relative)
    for directory in (
        "facsimile", "pages/raw", "pages/corrected", "lots", "publication/index",
        "publication/authors", "publication/main", "publication/transclusions",
    ):
        marker = root / directory / ".gitkeep"
        if write_once(marker, ""):
            created.append(str(marker.relative_to(root)))
    update_status(root)
    print(f"Chantier initialisé ({len(created)} fichiers créés, fichiers existants préservés).")


def tool_version(name: str, args: list[str]) -> tuple[bool, str]:
    executable = shutil.which(name)
    if not executable:
        return False, "absent"
    try:
        result = subprocess.run(
            [executable, *args], text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=5, check=False,
        )
        first = (result.stdout or "présent").splitlines()[0]
    except (OSError, subprocess.TimeoutExpired):
        first = "présent (version indisponible)"
    return True, first[:120]


def doctor_results() -> list[tuple[str, bool, bool, str]]:
    checks = [
        ("python", True, sys.version_info >= (3, 11), sys.version.split()[0]),
    ]
    tools = [
        ("git", True, ["--version"]),
        ("pdfinfo", False, ["-v"]),
        ("pdftoppm", False, ["-v"]),
        ("pdftotext", False, ["-v"]),
        ("djvused", False, ["--help"]),
        ("ddjvu", False, ["--help"]),
        ("djvutxt", False, ["--help"]),
        ("google-chrome", False, ["--version"]),
        ("tesseract", False, ["--version"]),
    ]
    for name, required, version_args in tools:
        ok, detail = tool_version(name, version_args)
        checks.append((name, required, ok, detail))
    profile = os.environ.get("WIKISOURCE_CHROME_USER_DATA_DIR")
    active = bool(profile and Path(profile, "DevToolsActivePort").is_file())
    checks.append(("chrome-cdp", False, active, "joignable à vérifier" if active else "non configuré"))
    checks.append(("MISTRAL_API_KEY", False, bool(os.environ.get("MISTRAL_API_KEY")), "configurée" if os.environ.get("MISTRAL_API_KEY") else "absente"))
    return checks


def command_doctor(_: argparse.Namespace) -> None:
    failed = False
    for name, required, ok, detail in doctor_results():
        label = "OK" if ok else "REQUIS" if required else "optionnel"
        print(f"[{label:9}] {name}: {detail}")
        failed |= required and not ok
    if failed:
        raise WSError("un outil obligatoire manque")


def require_tool(name: str, purpose: str) -> str:
    executable = shutil.which(name)
    if not executable:
        raise WSError(f"outil système absent pour {purpose} : {name} (voir ./ws doctor)")
    return executable


def run_checked(command: list[str], *, capture: bool = False) -> str:
    try:
        result = subprocess.run(
            command, check=True, text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise WSError(f"commande en échec ({command[0]}) : {detail}") from exc
    return result.stdout if capture else ""


def corpus_manifest_path(root: Path) -> Path:
    return root / "facsimile/CORPUS_MANIFEST.json"


def resolve_source(root: Path, config: dict) -> Path:
    source = Path(config["source"]["file"])
    source = source if source.is_absolute() else root / source
    if not source.is_file():
        raise WSError(f"fac-similé introuvable : {source}")
    return source.resolve()


def pdf_page_count(source: Path) -> int:
    output = run_checked([require_tool("pdfinfo", "lire un PDF"), str(source)], capture=True)
    for line in output.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise WSError("nombre de pages PDF introuvable")


def djvu_page_count(source: Path) -> int:
    output = run_checked([require_tool("djvused", "lire un DjVu"), str(source), "-e", "n"], capture=True)
    return int(output.strip())


def command_corpus_init(_: argparse.Namespace) -> None:
    root, config = project_root(), load_config()
    source = resolve_source(root, config)
    manifest_path = corpus_manifest_path(root)
    source_hash = sha256(source)
    if manifest_path.is_file():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing.get("source", {}).get("sha256") != source_hash:
            raise WSError("le fac-similé verrouillé a changé ; conserver l’original ou recréer explicitement le chantier")
        verify_corpus(root, config)
        print("Corpus déjà initialisé et vérifié.")
        return
    suffix = source.suffix.lower()
    if suffix == ".pdf":
        kind, count = "pdf", pdf_page_count(source)
        image_tool = require_tool("pdftoppm", "extraire les vues PDF")
        text_tool = require_tool("pdftotext", "extraire le texte PDF")
    elif suffix in {".djvu", ".djv"}:
        kind, count = "djvu", djvu_page_count(source)
        image_tool = require_tool("ddjvu", "extraire les vues DjVu")
        text_tool = require_tool("djvutxt", "extraire le texte DjVu")
    else:
        raise WSError("format non pris en charge : utiliser un PDF ou un DjVu")
    images = root / "facsimile/images"
    raw = root / "pages/raw"
    images.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    views = []
    for number in range(1, count + 1):
        identifier = f"page-{number:04d}"
        text_path = raw / f"{identifier}.txt"
        if kind == "pdf":
            prefix = images / identifier
            run_checked([image_tool, "-f", str(number), "-l", str(number), "-singlefile", "-png", "-r", "150", str(source), str(prefix)])
            image_path = prefix.with_suffix(".png")
            run_checked([text_tool, "-f", str(number), "-l", str(number), "-layout", str(source), str(text_path)])
        else:
            image_path = images / f"{identifier}.ppm"
            run_checked([image_tool, "-format=ppm", f"-page={number}", str(source), str(image_path)])
            text_path.write_text(run_checked([text_tool, f"-page={number}", str(source)], capture=True), encoding="utf-8", newline="\n")
        views.append({
            "id": identifier,
            "number": number,
            "image": str(image_path.relative_to(root)),
            "image_sha256": sha256(image_path),
            "text": str(text_path.relative_to(root)),
            "text_sha256": sha256(text_path),
        })
    manifest = {
        "schema": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": {"path": str(source.relative_to(root)) if source.is_relative_to(root) else str(source), "kind": kind, "sha256": source_hash, "size": source.stat().st_size},
        "view_count": count,
        "views": views,
    }
    atomic_json(manifest_path, manifest)
    verify_corpus(root, config)
    update_status(root)
    print(f"Corpus verrouillé : {count} vues, manifeste {manifest_path.relative_to(root)}.")


def verify_corpus(root: Path, config: dict) -> dict:
    path = corpus_manifest_path(root)
    if not path.is_file():
        raise WSError("CORPUS_MANIFEST.json absent ; exécuter ./ws corpus init")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise WSError(f"manifeste de corpus invalide : {exc}") from exc
    source = resolve_source(root, config)
    if sha256(source) != manifest.get("source", {}).get("sha256"):
        raise WSError("le fac-similé source a changé depuis l’initialisation")
    views = manifest.get("views")
    if not isinstance(views, list) or manifest.get("view_count") != len(views) or not views:
        raise WSError("liste de vues incohérente dans le manifeste")
    expected_ids = [f"page-{number:04d}" for number in range(1, len(views) + 1)]
    if [view.get("id") for view in views] != expected_ids:
        raise WSError("identifiants ou ordre des vues incohérents")
    for view in views:
        for key, checksum in (("image", "image_sha256"), ("text", "text_sha256")):
            artifact = root / view.get(key, "")
            if not artifact.is_file():
                raise WSError(f"vue incomplète, fichier absent : {artifact.relative_to(root)}")
            if sha256(artifact) != view.get(checksum):
                raise WSError(f"artefact modifié : {artifact.relative_to(root)}")
    return manifest


def command_corpus_verify(_: argparse.Namespace) -> None:
    root, config = project_root(), load_config()
    manifest = verify_corpus(root, config)
    update_status(root)
    print(f"Corpus vérifié : {manifest['view_count']} vues et toutes les sommes SHA-256 concordent.")


def lot_name(number: int, first: int, last: int) -> str:
    return f"lot-{number:04d}-v{first:04d}-v{last:04d}"


def command_lot_init(args: argparse.Namespace) -> None:
    root, config = project_root(), load_config()
    manifest = verify_corpus(root, config)
    if args.first < 1 or args.last < args.first or args.last > manifest["view_count"]:
        raise WSError("bornes du lot hors du corpus")
    if args.last - args.first + 1 > config["publication"]["max_lot_views"]:
        raise WSError("lot trop grand pour publication sûre")
    directory = root / "lots" / lot_name(args.number, args.first, args.last)
    directory.mkdir(parents=True, exist_ok=True)
    files = {
        "scope.json": {"schema": 1, "lot": args.number, "from": args.first, "to": args.last, "views": [f"page-{n:04d}" for n in range(args.first, args.last + 1)]},
        "before.json": {"api": API, "pages": {}},
        "manifest.json": {"api": API, "assertuser": config["wikisource"]["expected_user"], "operations": []},
        "after.json": {"api": API, "pages": {}},
    }
    for name, data in files.items():
        path = directory / name
        if not path.exists():
            atomic_json(path, data)
    write_once(directory / "journal.jsonl", "")
    write_once(directory / "TYPOGRAPHY_AUDIT.txt", "")
    write_once(directory / "REPORT.md", "# Rapport de lot\n\nPréparation vérifiée: non\n\nPublication vérifiée: non\n\n## Raccords et incertitudes\n\nÀ renseigner.\n")
    print(f"Lot initialisé : {directory.relative_to(root)}")


def find_lot(root: Path, value: str) -> Path:
    direct = root / "lots" / value
    matches = [direct] if direct.is_dir() else list((root / "lots").glob(f"lot-{int(value):04d}-*")) if value.isdigit() else []
    if len(matches) != 1:
        raise WSError(f"lot introuvable ou ambigu : {value}")
    return matches[0]


def check_lot(root: Path, config: dict, directory: Path) -> dict:
    corpus = verify_corpus(root, config)
    required = ["scope.json", "before.json", "manifest.json", "journal.jsonl", "after.json", "REPORT.md", "TYPOGRAPHY_AUDIT.txt"]
    for name in required:
        if not (directory / name).is_file():
            raise WSError(f"artefact de lot absent : {name}")
    scope = json.loads((directory / "scope.json").read_text(encoding="utf-8"))
    first, last = scope.get("from"), scope.get("to")
    if not isinstance(first, int) or not isinstance(last, int) or first < 1 or last < first or last > corpus["view_count"]:
        raise WSError("périmètre du lot invalide")
    if last - first + 1 > config["publication"]["max_lot_views"]:
        raise WSError("lot supérieur à la limite configurée")
    missing = [f"pages/corrected/page-{n:04d}.txt" for n in range(first, last + 1) if not (root / f"pages/corrected/page-{n:04d}.txt").is_file()]
    if missing:
        raise WSError("pages corrigées absentes : " + ", ".join(missing))
    if not (directory / "TYPOGRAPHY_AUDIT.txt").read_text(encoding="utf-8").strip():
        raise WSError("audit typographique absent ; exécuter ./ws typography pour ce lot")
    report = (directory / "REPORT.md").read_text(encoding="utf-8")
    if "Préparation vérifiée: oui" not in report:
        raise WSError("le rapport doit attester « Préparation vérifiée: oui » après relecture humaine")
    return scope


def command_lot_check(args: argparse.Namespace) -> None:
    root, config = project_root(), load_config()
    directory = find_lot(root, args.lot)
    scope = check_lot(root, config, directory)
    update_status(root)
    print(f"Lot préparé vérifié : vues {scope['from']} à {scope['to']}.")


def command_typography(args: argparse.Namespace) -> None:
    root, config = project_root(), load_config()
    directory = find_lot(root, args.lot)
    scope = json.loads((directory / "scope.json").read_text(encoding="utf-8"))
    paths = [root / f"pages/corrected/page-{n:04d}.txt" for n in range(scope["from"], scope["to"] + 1)]
    missing = [str(p.relative_to(root)) for p in paths if not p.is_file()]
    if missing:
        raise WSError("pages corrigées absentes : " + ", ".join(missing))
    script = ROOT / ".agents/skills/contribute-wikisource-fr/scripts/correct_wikisource_typography.py"
    result = subprocess.run([sys.executable, str(script), "--audit", *map(str, paths)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    (directory / "TYPOGRAPHY_AUDIT.txt").write_text(result.stdout, encoding="utf-8", newline="\n")
    if result.returncode:
        raise WSError("le correcteur typographique a échoué")
    print(result.stdout, end="")
    print(f"Audit consigné dans {directory.relative_to(root)}/TYPOGRAPHY_AUDIT.txt")


def command_check(_: argparse.Namespace) -> None:
    root, config = project_root(), load_config()
    errors = []
    source_value = config["source"]["file"]
    if Path(source_value).is_absolute():
        errors.append("source.file doit être relatif au chantier")
    if config["wikisource"]["expected_user"] == "À renseigner":
        errors.append("wikisource.expected_user reste à renseigner")
    if config["wikisource"]["index"] == "À renseigner.djvu":
        errors.append("wikisource.index reste à renseigner")
    for secret in ("MISTRAL_API_KEY", "MEDIAWIKI_TOKEN", "WIKISOURCE_PASSWORD"):
        if secret in (root / "PROJECT.toml").read_text(encoding="utf-8"):
            errors.append(f"nom de secret interdit dans PROJECT.toml : {secret}")
    if errors:
        raise WSError("contrôle hors ligne en échec :\n- " + "\n- ".join(errors))
    update_status(root)
    print(f"Contrôle hors ligne réussi. État : {status(root)}.")


def recent_successes(root: Path, now: datetime | None = None) -> int:
    """Compter les écritures journalisées dans la dernière minute glissante."""
    now = now or datetime.now(timezone.utc)
    threshold = now - timedelta(minutes=1)
    count = 0
    for journal in root.rglob("*.jsonl"):
        try:
            lines = journal.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for line in lines:
            try:
                record = json.loads(line)
                timestamp = datetime.fromisoformat(record["timestamp"])
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
            if record.get("result") == "Success" and timestamp >= threshold:
                count += 1
    return count


def pending_manifest_operations(manifest: dict, journal: Path) -> int:
    confirmed = set()
    if journal.is_file():
        for line in journal.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise WSError(f"journal JSONL invalide : {journal}") from exc
            if record.get("result") == "Success" and isinstance(record.get("title"), str):
                confirmed.add(record["title"])
    operations = manifest.get("operations")
    if not isinstance(operations, list) or not all(isinstance(item, dict) for item in operations):
        raise WSError("operations doit être une liste d’objets")
    return sum(1 for operation in operations if operation.get("title") not in confirmed)


def command_api(args: argparse.Namespace) -> None:
    root, config = project_root(), load_config()
    expected = config["wikisource"]["expected_user"]
    if not expected or expected == "À renseigner":
        raise WSError("configurer wikisource.expected_user avant tout accès API")
    script = ROOT / ".agents/skills/utiliser-api-wikisource/scripts/cdp_wikisource.py"
    command = [sys.executable, str(script), args.api_command]
    if args.manifest:
        command.append(args.manifest)
    if args.output:
        command += ["--output", args.output]
    if args.journal:
        command += ["--journal", args.journal]
    if args.chrome_user_data_dir:
        command += ["--chrome-user-data-dir", args.chrome_user_data_dir]
    environment = os.environ.copy()
    environment["WIKISOURCE_EXPECTED_USER"] = expected
    environment.setdefault("WIKISOURCE_USER_AGENT", "wikisource-agent/1.0 (local editorial workflow)")
    if args.api_command in {"preflight", "publish"}:
        manifest_path = Path(args.manifest or "")
        manifest_path = manifest_path if manifest_path.is_absolute() else root / manifest_path
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("assertuser") != expected:
            raise WSError("assertuser du manifeste ne correspond pas à PROJECT.toml")
    if args.api_command == "publish":
        if not args.approve:
            raise WSError("publication refusée sans --approve explicite")
        operations = manifest.get("operations", [])
        journal = Path(args.journal) if args.journal else manifest_path.with_suffix(manifest_path.suffix + ".journal.jsonl")
        journal = journal if journal.is_absolute() else root / journal
        pending = pending_manifest_operations(manifest, journal)
        recent = recent_successes(root)
        if pending > config["publication"]["max_writes_per_minute"]:
            raise WSError("le manifeste dépasse la fenêtre de publication configurée")
        if recent + pending > config["publication"]["max_writes_per_minute"]:
            raise WSError(
                f"fenêtre glissante saturée ({recent} écriture(s) récente(s), {pending} en attente) ; attendre avant de publier"
            )
    result = subprocess.run(command, cwd=root, env=environment, check=False)
    if result.returncode:
        raise WSError(f"commande CDP en échec (code {result.returncode})")


def parser() -> argparse.ArgumentParser:
    main = argparse.ArgumentParser(prog="ws", description="Piloter un chantier Wikisource reproductible.")
    sub = main.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="initialiser les fichiers du chantier")
    init.add_argument("--title")
    init.add_argument("--source")
    init.add_argument("--index")
    init.add_argument("--user")
    init.set_defaults(function=command_init)
    sub.add_parser("doctor", help="diagnostiquer les outils").set_defaults(function=command_doctor)
    sub.add_parser("check", help="contrôle complet hors ligne").set_defaults(function=command_check)
    corpus = sub.add_parser("corpus", help="gérer le corpus").add_subparsers(dest="corpus_command", required=True)
    corpus.add_parser("init").set_defaults(function=command_corpus_init)
    corpus.add_parser("verify").set_defaults(function=command_corpus_verify)
    lot = sub.add_parser("lot", help="gérer les lots").add_subparsers(dest="lot_command", required=True)
    lot_init = lot.add_parser("init")
    lot_init.add_argument("--number", type=int, required=True)
    lot_init.add_argument("--from", dest="first", type=int, required=True)
    lot_init.add_argument("--to", dest="last", type=int, required=True)
    lot_init.set_defaults(function=command_lot_init)
    lot_check = lot.add_parser("check")
    lot_check.add_argument("lot")
    lot_check.set_defaults(function=command_lot_check)
    typo = sub.add_parser("typography", help="corriger prudemment et auditer un lot")
    typo.add_argument("lot")
    typo.set_defaults(function=command_typography)
    api = sub.add_parser("api", help="encapsuler le client CDP").add_subparsers(dest="api_command", required=True)
    for name in ("identity", "sync", "preflight", "publish"):
        item = api.add_parser(name)
        if name != "identity":
            item.add_argument("manifest")
        else:
            item.set_defaults(manifest=None)
        item.add_argument("--output")
        item.add_argument("--journal")
        item.add_argument("--chrome-user-data-dir")
        item.add_argument("--approve", action="store_true")
        item.set_defaults(function=command_api)
    return main


def main(argv: list[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
        args.function(args)
        return 0
    except (WSError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
