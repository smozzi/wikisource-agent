import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ws_module", REPO / "scripts/ws.py")
ws = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ws)


class ProjectTests(unittest.TestCase):
    def temporary_project(self):
        directory = tempfile.TemporaryDirectory()
        root = Path(directory.name)
        self.addCleanup(directory.cleanup)
        environment = mock.patch.dict(os.environ, {"WIKISOURCE_PROJECT_ROOT": str(root)})
        environment.start()
        self.addCleanup(environment.stop)
        ws.command_init(argparse.Namespace(title="Exemple", source="facsimile/source.pdf", index="Exemple.pdf", user="UtilisateurExemple"))
        return root

    def prepare_manifest(self, root, count=2):
        source = root / "facsimile/source.pdf"
        source.write_bytes(b"fixture-pdf-placeholder")
        views = []
        for number in range(1, count + 1):
            identifier = f"page-{number:04d}"
            image = root / f"facsimile/images/{identifier}.png"
            text = root / f"pages/raw/{identifier}.txt"
            image.parent.mkdir(parents=True, exist_ok=True)
            text.parent.mkdir(parents=True, exist_ok=True)
            image.write_bytes(f"image-{number}".encode())
            text.write_text(f"texte {number}\n", encoding="utf-8")
            views.append({
                "id": identifier,
                "number": number,
                "image": str(image.relative_to(root)),
                "image_sha256": ws.sha256(image),
                "text": str(text.relative_to(root)),
                "text_sha256": ws.sha256(text),
            })
        ws.atomic_json(root / "facsimile/CORPUS_MANIFEST.json", {
            "schema": 1,
            "source": {"path": "facsimile/source.pdf", "kind": "pdf", "sha256": ws.sha256(source), "size": source.stat().st_size},
            "view_count": count,
            "views": views,
        })
        return source

    def make_minimal_pdf(self, path):
        stream = b"BT /F1 12 Tf 20 100 Td (Fixture libre) Tj ET"
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        ]
        content = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for number, value in enumerate(objects, 1):
            offsets.append(len(content))
            content.extend(f"{number} 0 obj\n".encode() + value + b"\nendobj\n")
        xref = len(content)
        content.extend(f"xref\n0 {len(objects) + 1}\n".encode())
        content.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            content.extend(f"{offset:010d} 00000 n \n".encode())
        content.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
        path.write_bytes(content)

    def test_init_is_idempotent_and_does_not_overwrite(self):
        root = self.temporary_project()
        (root / "PROJECT.md").write_text("Décision locale\n", encoding="utf-8")
        ws.command_init(argparse.Namespace(title="Autre", source=None, index=None, user=None))
        self.assertEqual((root / "PROJECT.md").read_text(encoding="utf-8"), "Décision locale\n")
        self.assertIn('title = "Exemple"', (root / "PROJECT.toml").read_text(encoding="utf-8"))

    def test_configuration_rejects_more_than_eight_writes(self):
        root = self.temporary_project()
        path = root / "PROJECT.toml"
        path.write_text(path.read_text(encoding="utf-8").replace("max_writes_per_minute = 8", "max_writes_per_minute = 9"), encoding="utf-8")
        with self.assertRaises(ws.WSError):
            ws.load_config(root)

    def test_corpus_verify_accepts_complete_manifest(self):
        root = self.temporary_project()
        self.prepare_manifest(root)
        self.assertEqual(ws.verify_corpus(root, ws.load_config(root))["view_count"], 2)

    def test_corpus_verify_detects_modified_source(self):
        root = self.temporary_project()
        source = self.prepare_manifest(root)
        source.write_bytes(b"changed")
        with self.assertRaisesRegex(ws.WSError, "source a changé"):
            ws.verify_corpus(root, ws.load_config(root))

    def test_corpus_verify_detects_missing_view(self):
        root = self.temporary_project()
        self.prepare_manifest(root)
        (root / "facsimile/images/page-0002.png").unlink()
        with self.assertRaisesRegex(ws.WSError, "fichier absent"):
            ws.verify_corpus(root, ws.load_config(root))

    def test_corpus_init_reports_missing_system_tool(self):
        root = self.temporary_project()
        (root / "facsimile/source.pdf").write_bytes(b"not-a-real-pdf")
        with mock.patch.object(ws.shutil, "which", return_value=None):
            with self.assertRaisesRegex(ws.WSError, "outil système absent"):
                ws.command_corpus_init(argparse.Namespace())

    @unittest.skipUnless(
        shutil.which("pdfinfo") and shutil.which("pdftoppm") and shutil.which("pdftotext"),
        "Poppler absent",
    )
    def test_corpus_init_and_reexecution_with_poppler(self):
        root = self.temporary_project()
        self.make_minimal_pdf(root / "facsimile/source.pdf")
        ws.command_corpus_init(argparse.Namespace())
        ws.command_corpus_init(argparse.Namespace())
        manifest = ws.verify_corpus(root, ws.load_config(root))
        self.assertEqual(manifest["view_count"], 1)
        self.assertTrue((root / "facsimile/images/page-0001.png").is_file())

    def test_lot_limit_is_enforced(self):
        root = self.temporary_project()
        self.prepare_manifest(root, count=9)
        with self.assertRaisesRegex(ws.WSError, "lot trop grand"):
            ws.command_lot_init(argparse.Namespace(number=1, first=1, last=9))

    def test_lot_check_requires_corrected_pages_and_attestation(self):
        root = self.temporary_project()
        self.prepare_manifest(root)
        args = argparse.Namespace(number=1, first=1, last=2)
        ws.command_lot_init(args)
        directory = root / "lots/lot-0001-v0001-v0002"
        with self.assertRaisesRegex(ws.WSError, "pages corrigées absentes"):
            ws.check_lot(root, ws.load_config(root), directory)
        for number in (1, 2):
            (root / f"pages/corrected/page-{number:04d}.txt").write_text("Relu\n", encoding="utf-8")
        (directory / "TYPOGRAPHY_AUDIT.txt").write_text("Audit exécuté\n", encoding="utf-8")
        with self.assertRaisesRegex(ws.WSError, "Préparation vérifiée"):
            ws.check_lot(root, ws.load_config(root), directory)

    def test_sliding_window_counts_only_recent_successes(self):
        root = self.temporary_project()
        now = ws.datetime.now(ws.timezone.utc)
        journal = root / "lots/publication.jsonl"
        journal.parent.mkdir(parents=True, exist_ok=True)
        journal.write_text(
            "\n".join([
                json.dumps({"result": "Success", "timestamp": (now - ws.timedelta(seconds=20)).isoformat()}),
                json.dumps({"result": "Success", "timestamp": (now - ws.timedelta(minutes=2)).isoformat()}),
                json.dumps({"result": "Failure", "timestamp": now.isoformat()}),
            ]) + "\n",
            encoding="utf-8",
        )
        self.assertEqual(ws.recent_successes(root, now), 1)


if __name__ == "__main__":
    unittest.main()
