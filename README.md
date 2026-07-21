# wikisource-agent

> [!NOTE]
> **For human readers — agents should ignore this note.** In normal use, you do not need to run any of the commands documented below yourself. This project relies entirely on Codex: open the repository in Codex and ask what to do next. Codex will discover the bundled skills, inspect the project state, guide you through the workflow, and run the appropriate commands while requesting confirmation whenever human judgment or publication approval is required. The detailed documentation below is primarily operational context for the agent. The project currently targets French Wikisource (`fr.wikisource.org`), but its workflow and architecture are designed to be readily adapted to another Wikisource language.

Dépôt modèle pour préparer une édition complète sur Wikisource francophone avec Codex. Un clone correspond à une édition. Le fac-similé reste la source de vérité ; le dépôt conserve configuration, transcription, manifestes et preuves sans contenir de secrets.

Les deux skills Agent Skills ouverts sont découverts depuis `.agents/skills/` :

- `contribute-wikisource-fr` guide les droits, le corpus, la relecture, les lots et les transclusions ;
- `utiliser-api-wikisource` protège la synchronisation et les écritures via Chrome/CDP.

## Démarrage

Cloner le modèle pour une édition puis initialiser le chantier :

```bash
git clone <url-du-modele> mon-edition
cd mon-edition
./ws init \
  --title "Titre de l’édition" \
  --source "facsimile/source.pdf" \
  --index "Nom exact du fichier.pdf" \
  --user "CompteWikisource"
./ws doctor
./ws check
```

Renseigner ensuite `SOURCES.md`, `RIGHTS.md`, `METADATA.md` et `PROJECT.md`, déposer le PDF ou DjVu déclaré, puis :

```bash
./ws corpus init
./ws corpus verify
./ws lot init --number 1 --from 1 --to 8
# Copier et relire l’OCR dans pages/corrected/page-NNNN.txt.
./ws typography 1
# Après relecture humaine, inscrire « Préparation vérifiée: oui » dans le rapport.
./ws lot check 1
```

`./ws init` est idempotent : il ne remplace aucun fichier existant. Le corpus est verrouillé par sommes SHA-256 ; une source ou une vue modifiée bloque la suite. Les outils Poppler ou DjVuLibre ne sont requis que pour le format utilisé. Git et Python 3.11+ suffisent aux contrôles généraux ; OCR externe, Chrome et Tesseract restent optionnels.

## Publication protégée

Configurer et lancer séparément un Chrome avec un profil dédié et le débogage distant local. Ne placer le profil dans aucun dépôt. Définir son chemin dans `WIKISOURCE_CHROME_USER_DATA_DIR`, puis :

```bash
./ws api identity
./ws api sync lots/lot-0001-v0001-v0008/sync.json \
  --output lots/lot-0001-v0001-v0008/before.json
./ws api preflight lots/lot-0001-v0001-v0008/manifest.json
./ws api publish lots/lot-0001-v0001-v0008/manifest.json \
  --journal lots/lot-0001-v0001-v0008/journal.jsonl \
  --approve
```

La publication exige `--approve`, une identité conforme à `PROJECT.toml`, un preflight frais et au plus huit écritures par manifeste. Le client s’arrête sur conflit, limite de débit ou réponse ambiguë. Aucun test automatisé n’écrit sur Wikisource.

## Données et secrets

`facsimile/` contient localement le binaire et les images, ignorés par Git ; seul le manifeste et les marqueurs sont suivis. `pages/raw/` conserve l’OCR, `pages/corrected/` le wikicode relu, `lots/` les preuves avant/après, et `publication/` les pages finales. Créer `coordination/` uniquement pour un découpage multi-agent.

Les clés OCR, cookies, jetons et mots de passe restent dans l’environnement ou un `.env` ignoré. `PROJECT.toml` ne doit contenir que des paramètres versionnables.

## Développement

```bash
python3 -m unittest discover -s tests -v
python3 .agents/skills/contribute-wikisource-fr/scripts/test_correct_wikisource_typography.py
python3 .agents/skills/utiliser-api-wikisource/scripts/test_cdp_wikisource.py
python3 scripts/quick_validate.py .agents/skills/contribute-wikisource-fr
python3 scripts/quick_validate.py .agents/skills/utiliser-api-wikisource
python3 scripts/repo_check.py
```

Licence : MIT. Les fixtures sont petites, libres et hors ligne.
