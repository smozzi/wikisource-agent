---
name: utiliser-api-wikisource
description: "Synchroniser, prévisualiser et publier prudemment via l’API Action de Wikisource francophone et une session Chrome CDP. Utiliser pour l’identité, les snapshots distants, manifestes, createonly, baserevid, conflits, limites de débit, journaux JSONL, reprises partielles et contrôles post-publication des espaces Livre:, Page:, Auteur: et principal."
---

# Utiliser l’API Wikisource francophone

## Verrouiller le contexte

Lire `PROJECT.toml` et exécuter les commandes via `./ws api ...`. Utiliser exclusivement `https://fr.wikisource.org/w/api.php`. Exiger `frwikisource`, une API inscriptible et l’utilisateur configuré. Ne jamais exporter ni journaliser cookies, jetons ou mots de passe.

Utiliser un profil Chrome dédié, hors du dépôt, avec débogage distant limité à `127.0.0.1`. Le client ne lance pas Chrome implicitement. Sonder d’abord avec `./ws api identity`; prévenir l’utilisateur avant tout lancement manuel d’un navigateur. Ne jamais attacher plusieurs agents au même Chrome.

### Ouvrir une session Chrome pour CDP

Ne lancer Chrome qu’après l’accord explicite de l’utilisateur. Vérifier que le profil choisi n’est utilisé par aucune autre instance. Pour une session temporaire graphique :

```bash
profile_dir="$(mktemp -d /tmp/wikisource-cdp-profile.XXXXXX)"
google-chrome \
  --no-first-run --no-default-browser-check \
  --user-data-dir="$profile_dir" \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port=0 \
  --new-window https://fr.wikisource.org/wiki/Wikisource:Accueil
```

Ne pas ajouter `--headless` si l’utilisateur doit voir la fenêtre et se connecter. Garder cette commande au premier plan dans une session persistante ; lancer Chrome avec `&` dans une commande courte peut faire disparaître le processus dès que le shell se termine. Un profil persistant dédié peut remplacer `/tmp/...`, mais doit rester hors du dépôt et ne doit pas être partagé avec un autre agent.

Si Chrome échoue avant de créer `DevToolsActivePort` avec une erreur Crashpad `Operation not permitted` dans l’environnement d’exécution, relancer seulement cette instance locale hors du bac à sable de l’agent, après autorisation, tout en conservant le bac à sable natif de Chrome. Ne pas ajouter `--no-sandbox` et ne jamais élargir l’écoute au-delà de `127.0.0.1`. Si aucune variable `DISPLAY` n’est disponible ou si Chrome échoue encore, utiliser une session graphique appropriée ou demander à l’utilisateur de lancer Chrome lui-même.

Attendre la création du fichier de découverte puis demander à l’utilisateur de terminer la connexion dans la fenêtre :

```bash
test -s "$profile_dir/DevToolsActivePort"
./ws api identity --chrome-user-data-dir "$profile_dir"
```

Le profil temporaire est vierge par défaut : une identité anonyme ou une identité différente de `expected_user` signifie que la connexion Wikisource n’est pas validée. Après la connexion, `identity` doit confirmer `wikiid: frwikisource`, l’utilisateur attendu et `writeapi: true`. Ne jamais extraire, afficher ou journaliser cookies, mots de passe ou jetons. Fermer Chrome avant de supprimer un profil temporaire.

## Synchroniser et préparer

Synchroniser en lecture seule avec :

```bash
./ws api sync synchronisation.json --output snapshot.json
```

Partir du snapshot frais pour toute modification d’une page existante. Décrire chaque création avec `create` et chaque modification avec `edit` plus un `baserevid` entier. Fournir exactement `text` ou `text_file`, un résumé non vide, l’API française et `assertuser` identique à `PROJECT.toml`.

Valider tôt avec `scripts/validate_manifest.py`, puis exécuter immédiatement avant publication :

```bash
./ws api preflight publication.json
```

Lire [references/manifests-and-recovery.md](references/manifests-and-recovery.md) pour les schémas, l’ordre des écritures et la reprise. Lire [references/api-officielle.md](references/api-officielle.md) seulement pour un paramètre ou une erreur API rare.

## Publier avec approbation

Présenter la liste exacte des cibles et obtenir l’approbation explicite. Publier au maximum huit opérations par manifeste :

```bash
./ws api publish publication.json --journal publication.journal.jsonl --approve
```

Le client doit conserver `createonly`, `baserevid`, `assert=user`, `assertuser`, prévisualisation, journal avant l’opération suivante et relecture exacte du wikicode enregistré. Arrêter sur conflit, changement d’auteur, identité inattendue, HTTP 429, réponse ambiguë, avertissement de rendu ou contenu distant différent.

Après un arrêt partiel, ne jamais rejouer aveuglément le manifeste. Relire les cibles ; le client n’ignore une opération journalisée que si sa révision et son wikicode sont toujours exactement ceux confirmés. Attendre la fenêtre de débit avant de reprendre les seules opérations restantes.

## Contrôler le résultat

Synchroniser un snapshot final et comparer titres, révisions, auteurs et contenus. Le contrôle technique ne remplace pas la relecture éditoriale : rendre la main au skill `contribute-wikisource-fr` pour les sections, transclusions, niveaux ProofreadPage, notes et raccords.
