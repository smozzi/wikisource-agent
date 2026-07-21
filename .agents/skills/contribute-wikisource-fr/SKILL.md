---
name: contribute-wikisource-fr
description: Préparer, relire et finaliser une édition sur Wikisource francophone depuis un fac-similé libre. Utiliser pour cadrer la bibliographie et les droits, initialiser un corpus PDF ou DjVu, corriger l’OCR, préparer des lots Page:, construire Livre:, Auteur: et les transclusions, ou contrôler une œuvre publiée.
---

# Contribuer à Wikisource francophone

## Piloter le chantier

Travailler depuis la racine du clone. Lire `PROJECT.toml` et exécuter `./ws check` avant toute préparation. Considérer le fac-similé verrouillé par `facsimile/CORPUS_MANIFEST.json` comme source de vérité ; conserver les identifiants `page-NNNN` et ne jamais déduire la pagination imprimée du seul numéro de vue.

Respecter les états dans cet ordre : cadré, corpus initialisé, lot préparé, lot publié, œuvre finalisée. Ne pas contourner un refus du lanceur. Lire [references/workflow.md](references/workflow.md) pour les préconditions et artefacts de chaque état.

## Cadrer puis initialiser

Établir la bibliographie, la provenance et les droits français et américains dans `SOURCES.md` et `RIGHTS.md`. Lire [references/import-et-droits.md](references/import-et-droits.md) avant de choisir Commons ou un import local Wikisource. Ne pas automatiser l’envoi binaire.

Configurer `PROJECT.toml`, déposer le PDF ou DjVu au chemin déclaré, puis exécuter `./ws corpus init` une seule fois. Lire [references/initialisation-corpus.md](references/initialisation-corpus.md). Pour un OCR externe, lire [references/ocr-externe.md](references/ocr-externe.md) ; traiter Mistral comme une option, conserver le JSON brut, échantillonner avant un grand lot et ne jamais versionner la clé.

## Préparer et relire un lot

Créer un lot borné avec `./ws lot init`. Conserver l’OCR dans `pages/raw/` et le wikicode relu dans `pages/corrected/`. Appliquer `./ws typography <lot>` avant la relecture humaine ; le script corrige seulement des cas sûrs et son audit ne prouve jamais la correction éditoriale.

Lire puis appliquer :

- [references/transcription.md](references/transcription.md) pour le wikicode, les notes, en-têtes, pieds, césures et raccords ;
- [references/typographie.md](references/typographie.md) pour la correction conservatrice ;
- [references/editions-bilingues.md](references/editions-bilingues.md) pour deux flux alternés ;
- [references/pages-oeuvre-et-transclusions.md](references/pages-oeuvre-et-transclusions.md) pour les bornes et sections.

Relire chaque page contre l’image, dans son contexte. Vérifier mots, noms propres, sens, ponctuation, paragraphes, citations, notes, italiques, titres et raccords. Conserver la langue de l’édition ; ne jamais moderniser silencieusement. N’attester `Préparation vérifiée: oui` dans le rapport qu’après cette lecture complète. Réserver le niveau « Validée » à une seconde relecture indépendante.

## Publier et finaliser

Préparer les wikicodes dans `publication/`, les manifestes et preuves dans le lot. Présenter les cibles exactes et obtenir une approbation explicite. Déléguer toute synchronisation, prévisualisation ou écriture au skill `utiliser-api-wikisource`.

Après publication, relire le wikicode distant et le rendu : niveaux ProofreadPage, raccords, notes, sections, bornes, absence de chapitre voisin et pages exclues. Lire [references/checklist.md](references/checklist.md) avant de marquer le lot publié ou l’œuvre finalisée.

Pour un découpage réellement multi-agent, lire [references/travail-multi-agent.md](references/travail-multi-agent.md). Réserver les écritures à un coordinateur unique et utiliser `coordination/` seulement dans ce cas.

## Maintenir les règles

Préférer les liens officiels à leur copie. Lire [references/maintenance.md](references/maintenance.md) avant d’adopter une syntaxe ou une règle inhabituelle et mettre à jour sa date de vérification.
