#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import unittest

from correct_wikisource_typography import transform_wikitext


class TypographyTests(unittest.TestCase):
    def test_plain_apostrophe(self):
        self.assertEqual(transform_wikitext("l'homme").content, "l’homme")

    def test_wiki_emphasis_is_preserved(self):
        source = "''l'homme'' et '''l'autre'''"
        expected = "''l’homme'' et '''l’autre'''"
        self.assertEqual(transform_wikitext(source).content, expected)

    def test_wiki_constructs_are_protected(self):
        source = (
            "[[Page:L'histoire|l'histoire]] "
            "{{modèle|l'histoire}} <ref name='note'>l'histoire</ref>"
        )
        expected = (
            "[[Page:L'histoire|l'histoire]] "
            "{{modèle|l'histoire}} <ref name='note'>l’histoire</ref>"
        )
        self.assertEqual(transform_wikitext(source).content, expected)

    def test_comments_and_nowiki_are_protected(self):
        source = "<!-- l'homme --><nowiki>l'homme</nowiki> l'homme"
        expected = "<!-- l'homme --><nowiki>l'homme</nowiki> l’homme"
        self.assertEqual(transform_wikitext(source).content, expected)

    def test_trailing_spaces_and_line_endings(self):
        source = "texte  \r\nsuite\t\r\n"
        self.assertEqual(transform_wikitext(source).content, "texte\nsuite\n")


if __name__ == "__main__":
    unittest.main()
