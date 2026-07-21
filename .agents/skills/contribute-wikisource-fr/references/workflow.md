# États reproductibles

Dernière vérification : 2026-07-21.

## Cadré

Exiger `PROJECT.toml`, `PROJECT.md`, `SOURCES.md`, `RIGHTS.md` et `METADATA.md`. Identifier précisément l’édition, la source, l’index cible et le compte attendu. N’inscrire aucun secret.

## Corpus initialisé

Exiger le fac-similé inchangé, `CORPUS_MANIFEST.json`, une image et une couche texte par vue, avec sommes SHA-256. Employer `page-NNNN` partout. Faire échouer la vérification sur une source modifiée, une vue absente ou une somme différente.

## Lot préparé

Exiger un lot borné, son périmètre, le snapshot préalable, le manifeste, le journal, le snapshot final, le rapport, l’audit typographique et chaque fichier `pages/corrected/page-NNNN.txt`. Vérifier les raccords avant et après le lot. L’attestation humaine `Préparation vérifiée: oui` est obligatoire.

## Lot publié

Exiger un journal complet, un snapshot distant final et un contrôle de rendu. Inscrire `Publication vérifiée: oui` seulement après comparaison du wikicode sauvegardé et vérification éditoriale.

## Œuvre finalisée

Exiger l’index, les pages Auteur, la racine, les sous-pages et `/Texte entier` nécessaires, sans liens rouges artificiels. Contrôler métadonnées, transclusions, Wikidata, rendu mobile et export. Créer `publication/FINALIZED` seulement après la checklist finale.
