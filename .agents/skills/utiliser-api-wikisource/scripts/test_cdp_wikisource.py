#!/usr/bin/env python3

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import cdp_wikisource as module


class ManifestTests(unittest.TestCase):
    def make_manifest(self, data):
        directory = tempfile.TemporaryDirectory()
        path = Path(directory.name) / "manifest.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.addCleanup(directory.cleanup)
        return path

    def test_valid_inline_create(self):
        path = self.make_manifest(
            {
                "api": module.API,
                "assertuser": "UtilisateurExemple",
                "operations": [
                    {
                        "op": "create",
                        "title": "Page:Exemple/1",
                        "text": "Texte",
                        "summary": "Test",
                    }
                ],
            }
        )
        manifest, operations = module.validate_manifest(path)
        self.assertEqual(manifest["assertuser"], "UtilisateurExemple")
        self.assertEqual(operations[0]["text"], "Texte")

    def test_duplicate_title_is_rejected(self):
        operation = {
            "op": "create",
            "title": "Page:Exemple/1",
            "text": "Texte",
            "summary": "Test",
        }
        path = self.make_manifest(
            {
                "api": module.API,
                "assertuser": "UtilisateurExemple",
                "operations": [operation, operation],
            }
        )
        with self.assertRaises(module.PublicationError):
            module.validate_manifest(path)

    def test_edit_requires_baserevid(self):
        path = self.make_manifest(
            {
                "api": module.API,
                "assertuser": "UtilisateurExemple",
                "operations": [
                    {
                        "op": "edit",
                        "title": "Exemple",
                        "text": "Texte",
                        "summary": "Test",
                    }
                ],
            }
        )
        with self.assertRaises(module.PublicationError):
            module.validate_manifest(path)

    def test_journal_is_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "journal.jsonl"
            module.append_journal(path, {"title": "Exemple", "newrevid": 42})
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                {"title": "Exemple", "newrevid": 42},
            )

    def test_partial_journal_leaves_only_unpublished_operations(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "journal.jsonl"
            journal.write_text(
                json.dumps({"title": "Page:Exemple/1", "result": "Success", "newrevid": 42}) + "\n",
                encoding="utf-8",
            )
            operations = [
                {"title": "Page:Exemple/1", "text": "Un"},
                {"title": "Page:Exemple/2", "text": "Deux"},
            ]
            confirmed, pending = module.confirmed_operations(journal, operations)
            self.assertEqual(confirmed[0][0]["newrevid"], 42)
            self.assertEqual([item["title"] for item in pending], ["Page:Exemple/2"])

    def test_incoherent_partial_journal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "journal.jsonl"
            journal.write_text(
                json.dumps({"title": "Titre étranger", "result": "Success", "newrevid": 42}) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(module.PublicationError):
                module.confirmed_operations(journal, [{"title": "Exemple", "text": "Texte"}])

    def test_mediawiki_footer_normalization(self):
        local = "Texte\n\n<noinclude>\n<references/></noinclude>\n"
        remote = "Texte<noinclude>\n<references/></noinclude>"
        self.assertEqual(
            module.normalize_saved_wikitext(local),
            module.normalize_saved_wikitext(remote),
        )

    def test_body_whitespace_is_not_ignored(self):
        self.assertNotEqual(
            module.normalize_saved_wikitext("un  texte"),
            module.normalize_saved_wikitext("un texte"),
        )

    def test_render_error_class_is_detected(self):
        self.assertTrue(
            module.has_render_error(
                '<strong class="error">Erreur : l’index n’a pas été trouvé</strong>'
            )
        )

    def test_unrelated_class_is_not_a_render_error(self):
        self.assertFalse(module.has_render_error('<div class="error-free">Texte</div>'))

    def test_simulated_http_429_stops_immediately(self):
        original = module.evaluate
        module.evaluate = lambda *_: {
            "httpStatus": 429,
            "retryAfter": "60",
            "data": {"error": {"code": "ratelimited"}},
        }
        self.addCleanup(setattr, module, "evaluate", original)
        with self.assertRaisesRegex(module.PublicationError, "HTTP 429"):
            module.api_call(None, None, {"action": "query"})


    def test_query_state_chunks_more_than_fifty_titles(self):
        calls = []

        def fake_api_call(cdp, session_id, params):
            titles = params["titles"].split("|")
            calls.append(titles)
            return {
                "query": {"pages": [{"title": title, "missing": True} for title in titles]},
                "curtimestamp": f"timestamp-{len(calls)}",
            }

        original = module.api_call
        module.api_call = fake_api_call
        self.addCleanup(setattr, module, "api_call", original)
        states, timestamp = module.query_state(None, None, [f"Page:{n}" for n in range(65)])
        self.assertEqual([len(call) for call in calls], [50, 15])
        self.assertEqual(len(states), 65)
        self.assertEqual(timestamp, "timestamp-2")

    def test_sync_spec_expands_page_ranges_and_deduplicates(self):
        path = self.make_manifest(
            {
                "api": module.API,
                "titles": ["Vie de Louis-le-Gros", "Page:Index.pdf/2"],
                "page_ranges": [{"index": "Index.pdf", "from": 1, "to": 2}],
            }
        )
        _, titles = module.validate_sync_spec(path)
        self.assertEqual(
            titles,
            ["Vie de Louis-le-Gros", "Page:Index.pdf/2", "Page:Index.pdf/1"],
        )

    def test_sync_reuses_content_when_revid_is_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            spec = directory / "sync.json"
            output = directory / "snapshot.json"
            spec.write_text(
                json.dumps({"api": module.API, "titles": ["Exemple"]}),
                encoding="utf-8",
            )
            output.write_text(
                json.dumps({
                    "api": module.API,
                    "pages": {"Exemple": {"revid": 42, "content": "Texte"}},
                }),
                encoding="utf-8",
            )
            original_metadata = module.query_revision_metadata
            original_state = module.query_state
            module.query_revision_metadata = lambda *_: (
                {"Exemple": {"title": "Exemple", "revisions": [{"revid": 42}]}},
                "2026-07-17T12:00:00Z",
            )
            module.query_state = lambda *_: self.fail(
                "Le contenu inchangé ne doit pas être retéléchargé"
            )
            self.addCleanup(
                setattr, module, "query_revision_metadata", original_metadata
            )
            self.addCleanup(setattr, module, "query_state", original_state)
            result = module.sync_remote(None, None, spec, output)
            self.assertEqual(result["changed"], 0)
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8"))["pages"]["Exemple"],
                {"revid": 42, "content": "Texte"},
            )


if __name__ == "__main__":
    unittest.main()
