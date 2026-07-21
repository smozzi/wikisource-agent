#!/usr/bin/env python3
import argparse
import base64
import hashlib
import json
import os
import re
import socket
import struct
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path


API = "https://fr.wikisource.org/w/api.php"
WIKI_ID = "frwikisource"
USER_AGENT = os.environ.get(
    "WIKISOURCE_USER_AGENT", "wikisource-agent/1.0 (local editorial workflow)"
)
MAX_WRITES_PER_WINDOW = 8


class PublicationError(RuntimeError):
    pass


class CDP:
    def __init__(self, chrome_user_data_dir=None):
        user_data_dir = chrome_user_data_dir or os.environ.get(
            "WIKISOURCE_CHROME_USER_DATA_DIR"
        )
        if not user_data_dir:
            raise PublicationError(
                "profil CDP absent : fournir --chrome-user-data-dir ou "
                "WIKISOURCE_CHROME_USER_DATA_DIR"
            )
        port, path = Path(user_data_dir).joinpath(
            "DevToolsActivePort"
        ).read_text().strip().splitlines()
        self.sock = socket.create_connection(("127.0.0.1", int(port)), timeout=15)
        self.sock.settimeout(15)
        key = base64.b64encode(os.urandom(16)).decode()
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: 127.0.0.1:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(request.encode())
        response = self._read_until(b"\r\n\r\n")
        if b" 101 " not in response.split(b"\r\n", 1)[0]:
            raise RuntimeError(response.decode(errors="replace"))
        accept = base64.b64encode(
            hashlib.sha1(
                (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()
            ).digest()
        )
        if accept not in response:
            raise RuntimeError("Réponse WebSocket DevTools invalide")
        self.next_id = 0

    def _read_until(self, marker):
        data = b""
        while marker not in data:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise RuntimeError("Connexion DevTools fermée")
            data += chunk
        return data

    def _recv_exact(self, size):
        data = b""
        while len(data) < size:
            data += self.sock.recv(size - len(data))
        return data

    def _send_frame(self, payload):
        payload = payload.encode()
        mask = os.urandom(4)
        size = len(payload)
        header = bytearray([0x81])
        if size < 126:
            header.append(0x80 | size)
        elif size < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", size))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", size))
        header.extend(mask)
        masked = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        self.sock.sendall(header + masked)

    def _recv_frame(self):
        first, second = self._recv_exact(2)
        opcode = first & 0x0F
        size = second & 0x7F
        if size == 126:
            size = struct.unpack("!H", self._recv_exact(2))[0]
        elif size == 127:
            size = struct.unpack("!Q", self._recv_exact(8))[0]
        if second & 0x80:
            mask = self._recv_exact(4)
        else:
            mask = None
        payload = self._recv_exact(size)
        if mask:
            payload = bytes(
                value ^ mask[index % 4] for index, value in enumerate(payload)
            )
        if opcode == 8:
            raise RuntimeError("Connexion DevTools fermée")
        if opcode == 9:
            self._send_frame(payload.decode())
            return self._recv_frame()
        return json.loads(payload)

    def call(self, method, params=None, session_id=None):
        self.next_id += 1
        request_id = self.next_id
        message = {"id": request_id, "method": method, "params": params or {}}
        if session_id:
            message["sessionId"] = session_id
        self._send_frame(json.dumps(message))
        while True:
            response = self._recv_frame()
            if response.get("id") == request_id:
                if "error" in response:
                    raise RuntimeError(json.dumps(response["error"], ensure_ascii=False))
                return response.get("result", {})


def attach_wikisource(cdp):
    targets = cdp.call("Target.getTargets")["targetInfos"]
    pages = [
        target
        for target in targets
        if target["type"] == "page" and "fr.wikisource.org" in target["url"]
    ]
    if not pages:
        target_id = cdp.call(
            "Target.createTarget", {"url": "https://fr.wikisource.org/wiki/Wikisource:Accueil"}
        )["targetId"]
        time.sleep(2)
    else:
        target_id = pages[0]["targetId"]
    return cdp.call(
        "Target.attachToTarget", {"targetId": target_id, "flatten": True}
    )["sessionId"]


def evaluate(cdp, session_id, expression):
    result = cdp.call(
        "Runtime.evaluate",
        {
            "expression": expression,
            "awaitPromise": True,
            "returnByValue": True,
        },
        session_id,
    )
    if "exceptionDetails" in result:
        raise RuntimeError(json.dumps(result["exceptionDetails"], ensure_ascii=False))
    return result["result"].get("value")


def api_call(cdp, session_id, params, method="POST"):
    payload = json.dumps(params, ensure_ascii=False)
    expression = f"""
    (async () => {{
      const params = {payload};
      const method = {json.dumps(method)};
      const options = {{
        method, credentials: 'same-origin',
        headers: {{'Api-User-Agent': {json.dumps(USER_AGENT)}}}
      }};
      let url = '/w/api.php';
      if (method === 'GET') url += '?' + new URLSearchParams(params);
      else {{
        options.headers['Content-Type'] = 'application/x-www-form-urlencoded;charset=UTF-8';
        options.body = new URLSearchParams(params);
      }}
      const response = await fetch(url, options);
      return {{
        httpStatus: response.status,
        retryAfter: response.headers.get('Retry-After'),
        data: await response.json()
      }};
    }})()
    """
    result = evaluate(cdp, session_id, expression)
    if not isinstance(result, dict) or not isinstance(result.get("data"), dict):
        raise PublicationError("Réponse API illisible")
    if result.get("httpStatus") == 429:
        raise PublicationError(
            f"HTTP 429 (Retry-After={result.get('retryAfter')!r}) ; arrêter et resynchroniser"
        )
    if not isinstance(result.get("httpStatus"), int) or result["httpStatus"] >= 400:
        raise PublicationError(f"Réponse HTTP ambiguë ou en échec : {result}")
    if "error" in result["data"]:
        raise PublicationError(json.dumps(result, ensure_ascii=False))
    return result["data"]


def identity(cdp, session_id):
    return api_call(cdp, session_id, {
        "action": "query", "meta": "siteinfo|userinfo",
        "siprop": "general", "uiprop": "rights|ratelimits",
        "format": "json", "formatversion": "2"
    }, "GET")


def validate_manifest(path):
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("api") != API:
        raise PublicationError("Le manifeste ne cible pas fr.wikisource.org")
    if not isinstance(manifest.get("assertuser"), str) or not manifest["assertuser"].strip():
        raise PublicationError("assertuser absent")
    raw = manifest.get("operations")
    if not isinstance(raw, list) or not raw:
        raise PublicationError("operations doit être une liste non vide")
    operations, seen = [], set()
    for number, operation in enumerate(raw, 1):
        op, title = operation.get("op"), operation.get("title")
        if op not in {"create", "edit"}:
            raise PublicationError(f"Opération {number}: op invalide")
        if not isinstance(title, str) or not title.strip() or title in seen:
            raise PublicationError(f"Opération {number}: titre absent ou dupliqué")
        if title != unicodedata.normalize("NFC", title):
            raise PublicationError(f"Opération {number}: titre non NFC")
        seen.add(title)
        if not isinstance(operation.get("summary"), str) or not operation["summary"].strip():
            raise PublicationError(f"Opération {number}: résumé absent")
        if op == "edit" and not isinstance(operation.get("baserevid"), int):
            raise PublicationError(f"Opération {number}: baserevid entier requis")
        if op == "create" and "baserevid" in operation:
            raise PublicationError(f"Opération {number}: baserevid interdit")
        has_text, has_file = "text" in operation, "text_file" in operation
        if has_text == has_file:
            raise PublicationError(f"Opération {number}: fournir exactement text ou text_file")
        prepared = dict(operation)
        if has_file:
            source = path.parent / operation["text_file"]
            if not source.is_file():
                raise PublicationError(f"Fichier introuvable: {source}")
            prepared["text"] = source.read_text(encoding="utf-8")
        prepared["text"] = unicodedata.normalize("NFC", prepared["text"])
        operations.append(prepared)
    return manifest, operations


def query_state(cdp, session_id, titles):
    states = {}
    current_timestamp = None
    for offset in range(0, len(titles), 50):
        data = api_call(cdp, session_id, {
            "action": "query", "prop": "revisions|info", "rvslots": "main",
            "rvprop": "ids|timestamp|user|content|contentmodel",
            "titles": "|".join(titles[offset:offset + 50]), "curtimestamp": "1",
            "format": "json", "formatversion": "2"
        })
        states.update({page["title"]: page for page in data["query"]["pages"]})
        current_timestamp = data["curtimestamp"]
    return states, current_timestamp


def validate_sync_spec(path):
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("api") != API:
        raise PublicationError("La synchronisation ne cible pas fr.wikisource.org")
    titles = spec.get("titles", [])
    ranges = spec.get("page_ranges", [])
    if not isinstance(titles, list) or not isinstance(ranges, list):
        raise PublicationError("titles et page_ranges doivent être des listes")
    expanded = list(titles)
    for number, item in enumerate(ranges, 1):
        if not isinstance(item, dict):
            raise PublicationError(f"Plage {number}: objet attendu")
        index = item.get("index")
        first, last = item.get("from"), item.get("to")
        if (
            not isinstance(index, str) or not index.strip()
            or not isinstance(first, int) or not isinstance(last, int)
            or first < 1 or last < first
        ):
            raise PublicationError(f"Plage {number}: index/from/to invalides")
        expanded.extend(f"Page:{index}/{page}" for page in range(first, last + 1))
    seen = set()
    normalized = []
    for number, title in enumerate(expanded, 1):
        if not isinstance(title, str) or not title.strip():
            raise PublicationError(f"Titre {number}: valeur invalide")
        title = unicodedata.normalize("NFC", title)
        if title not in seen:
            seen.add(title)
            normalized.append(title)
    if not normalized:
        raise PublicationError("Aucun titre à synchroniser")
    return spec, normalized


def query_revision_metadata(cdp, session_id, titles):
    states = {}
    current_timestamp = None
    for offset in range(0, len(titles), 50):
        data = api_call(cdp, session_id, {
            "action": "query", "prop": "revisions", "rvslots": "main",
            "rvprop": "ids|timestamp|user|contentmodel",
            "titles": "|".join(titles[offset:offset + 50]), "curtimestamp": "1",
            "format": "json", "formatversion": "2"
        })
        states.update({page["title"]: page for page in data["query"]["pages"]})
        current_timestamp = data["curtimestamp"]
    return states, current_timestamp


def sync_remote(cdp, session_id, spec_path, output_path):
    spec_path = Path(spec_path).resolve()
    _, titles = validate_sync_spec(spec_path)
    output_path = Path(output_path).resolve()
    cache = {}
    if output_path.is_file():
        previous = json.loads(output_path.read_text(encoding="utf-8"))
        if previous.get("api") != API or not isinstance(previous.get("pages"), dict):
            raise PublicationError(f"Cache de synchronisation invalide: {output_path}")
        cache = previous["pages"]

    metadata, timestamp = query_revision_metadata(cdp, session_id, titles)
    changed = []
    pages = {}
    for title in titles:
        page = metadata[title]
        if page.get("missing"):
            record = {"missing": True}
            if cache.get(title) != record:
                changed.append(title)
            pages[title] = record
            continue
        revision = page["revisions"][0]
        cached = cache.get(title, {})
        if cached.get("revid") == revision["revid"] and "content" in cached:
            pages[title] = cached
        else:
            changed.append(title)

    changed_existing = [
        title for title in changed if not metadata[title].get("missing")
    ]
    contents = {}
    if changed_existing:
        contents, _ = query_state(cdp, session_id, changed_existing)
    for title in changed_existing:
        revision = contents[title]["revisions"][0]
        pages[title] = {
            "revid": revision["revid"],
            "parentid": revision.get("parentid"),
            "timestamp": revision["timestamp"],
            "user": revision["user"],
            "contentmodel": revision.get("contentmodel"),
            "content": revision["slots"]["main"]["content"],
        }

    snapshot = {"api": API, "synced_at": timestamp, "pages": pages}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, output_path)
    return {
        "result": "SyncSuccess",
        "titles": len(titles),
        "changed": len(changed),
        "unchanged": len(titles) - len(changed),
        "output": str(output_path),
        "synced_at": timestamp,
    }


def has_render_error(html):
    """Détecte les erreurs MediaWiki rendues dans la prévisualisation."""
    class_values = re.findall(r"""class=["']([^"']*)["']""", html, re.IGNORECASE)
    error_class = any(
        token.lower() in {"error", "errorbox"}
        for value in class_values
        for token in value.split()
    )
    return error_class or "mw-ext-cite-error" in html


def preflight(cdp, session_id, manifest, operations):
    account = identity(cdp, session_id)
    general = account["query"]["general"]
    user = account["query"]["userinfo"]
    if general.get("wikiid") != WIKI_ID or not general.get("writeapi"):
        raise PublicationError(f"Wiki inattendu ou API en lecture seule: {general}")
    if user.get("anon") or user.get("name") != manifest["assertuser"]:
        raise PublicationError(f"Identité inattendue: {user}")
    required = {"edit", "createpage"}
    if missing := required - set(user.get("rights", [])):
        raise PublicationError(f"Droits manquants: {sorted(missing)}")
    states, started = query_state(cdp, session_id, [op["title"] for op in operations])
    for op in operations:
        page = states[op["title"]]
        if op["op"] == "create" and not page.get("missing"):
            rev = page.get("revisions", [{}])[0]
            raise PublicationError(f"Création refusée, page apparue: {op['title']} (révision {rev.get('revid')}, {rev.get('user')})")
        if op["op"] == "edit":
            if page.get("missing"):
                raise PublicationError(f"Modification refusée, page absente: {op['title']}")
            rev = page["revisions"][0]
            if rev["revid"] != op["baserevid"]:
                raise PublicationError(f"Conflit sur {op['title']}: attendu {op['baserevid']}, trouvé {rev['revid']} par {rev.get('user')}")
    for op in operations:
        preview = api_call(cdp, session_id, {
            "action": "parse", "title": op["title"], "text": op["text"],
            "preview": "1", "prop": "text|parsewarnings|templates|categories|properties",
            "format": "json", "formatversion": "2"
        })
        parsed = preview.get("parse", {})
        warnings = parsed.get("parsewarnings") or parsed.get("warnings") or []
        html = parsed.get("text", "")
        if warnings or has_render_error(html):
            raise PublicationError(f"Prévisualisation refusée pour {op['title']}: {warnings}")
    return started


def normalize_saved_wikitext(text):
    """Reproduit seulement les normalisations de sauvegarde observées de MediaWiki."""
    text = text.rstrip("\n")
    return re.sub(
        r"[ \t]*\n+(?=<noinclude>\s*<references\s*/>)",
        "",
        text,
    )


def append_journal(path, record):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def confirmed_operations(journal, operations):
    """Valider un journal partiel et séparer les opérations déjà confirmées."""
    if not journal.is_file():
        return [], operations
    by_title = {operation["title"]: operation for operation in operations}
    confirmed = []
    seen = set()
    for number, line in enumerate(journal.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PublicationError(f"Journal invalide à la ligne {number}") from exc
        title = record.get("title")
        if (
            title not in by_title
            or title in seen
            or record.get("result") != "Success"
            or not isinstance(record.get("newrevid"), int)
        ):
            raise PublicationError(f"Journal incohérent à la ligne {number}")
        seen.add(title)
        confirmed.append((record, by_title[title]))
    pending = [operation for operation in operations if operation["title"] not in seen]
    return confirmed, pending


def verify_confirmed(cdp, session_id, confirmed):
    """Refuser une reprise si une écriture journalisée n'est plus exactement distante."""
    if not confirmed:
        return
    states, _ = query_state(cdp, session_id, [record["title"] for record, _ in confirmed])
    for record, operation in confirmed:
        page = states[record["title"]]
        if page.get("missing"):
            raise PublicationError(f"Page journalisée désormais absente : {record['title']}")
        revision = page["revisions"][0]
        if revision["revid"] != record["newrevid"]:
            raise PublicationError(
                f"Page journalisée modifiée depuis la publication : {record['title']} "
                f"(révision {revision['revid']} par {revision.get('user')})"
            )
        remote = normalize_saved_wikitext(revision["slots"]["main"]["content"])
        local = normalize_saved_wikitext(operation["text"])
        if remote != local:
            raise PublicationError(f"Contenu journalisé différent : {record['title']}")


def publish(cdp, session_id, manifest_path, delay=2.0, journal_path=None, dry_run=False):
    path = Path(manifest_path).resolve()
    manifest, operations = validate_manifest(path)
    journal = Path(journal_path).resolve() if journal_path else path.with_suffix(path.suffix + ".journal.jsonl")
    confirmed, operations = confirmed_operations(journal, operations)
    verify_confirmed(cdp, session_id, confirmed)
    if not operations:
        return [{"result": "ResumeComplete", "operations": len(confirmed)}]
    if len(operations) > MAX_WRITES_PER_WINDOW:
        raise PublicationError(
            f"Publication limitée à {MAX_WRITES_PER_WINDOW} écritures par fenêtre ; scinder le manifeste"
        )
    started = preflight(cdp, session_id, manifest, operations)
    if dry_run:
        return [{"result": "PreflightSuccess", "operations": len(operations), "already_confirmed": len(confirmed)}]
    token = api_call(cdp, session_id, {
        "action": "query", "meta": "tokens", "type": "csrf",
        "assert": "user", "assertuser": manifest["assertuser"],
        "format": "json", "formatversion": "2"
    })["query"]["tokens"]["csrftoken"]
    results = []
    for index, op in enumerate(operations):
        states, _ = query_state(cdp, session_id, [op["title"]])
        page = states[op["title"]]
        if op["op"] == "create" and not page.get("missing"):
            raise PublicationError(f"Page apparue avant écriture: {op['title']}")
        if op["op"] == "edit" and page["revisions"][0]["revid"] != op["baserevid"]:
            raise PublicationError(f"Révision modifiée avant écriture: {op['title']}")
        params = {
            "action": "edit", "title": op["title"], "text": op["text"],
            "summary": op["summary"], "token": token, "format": "json",
            "formatversion": "2", "assert": "user",
            "assertuser": manifest["assertuser"], "maxlag": "5",
            "starttimestamp": started
        }
        if op["op"] == "create": params["createonly"] = "1"
        else: params["baserevid"] = str(op["baserevid"])
        edit = api_call(cdp, session_id, params)["edit"]
        record = {
            "index": index + 1, "title": op["title"], "result": edit["result"],
            "oldrevid": edit.get("oldrevid"), "newrevid": edit.get("newrevid"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        append_journal(journal, record)
        reread, _ = query_state(cdp, session_id, [op["title"]])
        revision = reread[op["title"]]["revisions"][0]
        if revision["revid"] != edit.get("newrevid"):
            raise PublicationError(f"Relecture incohérente après écriture: {op['title']}")
        remote_text = normalize_saved_wikitext(revision["slots"]["main"]["content"])
        local_text = normalize_saved_wikitext(op["text"])
        if remote_text != local_text:
            raise PublicationError(f"Contenu distant différent après écriture: {op['title']}")
        results.append(record)
        if index + 1 < len(operations): time.sleep(delay)
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["identity", "publish", "preflight", "sync"])
    parser.add_argument("manifest", nargs="?")
    parser.add_argument(
        "--chrome-user-data-dir",
        help=(
            "profil Chrome contenant DevToolsActivePort; sinon utiliser "
            "WIKISOURCE_CHROME_USER_DATA_DIR ou le profil Chrome standard"
        ),
    )
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--journal")
    parser.add_argument("--output")
    args = parser.parse_args()
    cdp = CDP(args.chrome_user_data_dir)
    session_id = attach_wikisource(cdp)
    account = identity(cdp, session_id)
    expected = os.environ.get("WIKISOURCE_EXPECTED_USER")
    actual = account.get("query", {}).get("userinfo", {}).get("name")
    if expected and actual != expected:
        raise PublicationError(
            f"Identité inattendue : attendu {expected!r}, trouvé {actual!r}"
        )
    if args.command == "identity":
        result = account
    elif args.command == "sync":
        if not args.manifest:
            parser.error("sync exige une spécification")
        if not args.output:
            parser.error("sync exige --output")
        result = sync_remote(cdp, session_id, args.manifest, args.output)
    else:
        if not args.manifest:
            parser.error(f"{args.command} exige un manifeste")
        result = publish(
            cdp, session_id, args.manifest, delay=max(0, args.delay),
            journal_path=args.journal, dry_run=args.command == "preflight"
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except PublicationError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
