# Référence API utile

Sources officielles consultées :

- https://www.mediawiki.org/wiki/API:Etiquette
- https://www.mediawiki.org/wiki/API:Assert
- https://www.mediawiki.org/wiki/API:Tokens
- https://www.mediawiki.org/wiki/API:Edit
- https://www.mediawiki.org/wiki/API:Revisions
- https://www.mediawiki.org/wiki/API:Parsing_wikitext
- https://www.mediawiki.org/wiki/API:Login
- https://www.mediawiki.org/wiki/Manual:Maxlag_parameter
- https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits
- https://www.mediawiki.org/wiki/Extension:ProofreadPage/Proofread_props_API
- https://fr.wikisource.org/w/api.php

## Paramètres communs

Toujours utiliser `format=json`, `formatversion=2` et, pour une écriture, `assert=user`, `assertuser=<nom>` et `maxlag=5`.

Lecture d’état : `action=query`, `prop=revisions|info`, `rvprop=ids|timestamp|content|contentmodel`, `rvslots=main`, plusieurs titres séparés par `|`, `curtimestamp=1`.

Prévisualisation : `action=parse`, `text`, `title`, `contentmodel`, `preview=1`, `prop=text|parsewarnings|templates|categories`.

Jeton : `action=query`, `meta=tokens`, `type=csrf`. Un même jeton CSRF peut servir pendant la session sur le même wiki ; le renouveler après `badtoken`.

Création : `action=edit`, `title`, `text`, `createonly=1`, `summary`, assertions, jeton.

Modification : mêmes paramètres, avec `baserevid=<révision lue>`. Utiliser aussi `starttimestamp` lorsque le workflow conserve l’instant du début de l’édition.

## Authentification

Pour un outil autonome, OAuth est préférable. `action=login` doit être réservé aux mots de passe de robot ; le mot de passe principal est déconseillé et peut être refusé. Conserver les cookies pour les connexions par mot de passe de robot. Pour une session navigateur, effectuer les appels sur le même domaine sans exporter les cookies.

## Charge et limites

Les lectures doivent utiliser GET lorsqu’elles sont courtes et cacheables. Un long `action=parse` peut utiliser POST avec l’en-tête `Promise-Non-Write-API-Action: true`. Les écritures utilisent POST.

Définir un agent utilisateur descriptif avec contact. Sérialiser les requêtes. Grouper les titres en lecture. Pour les tâches non interactives, utiliser `maxlag=5`. Sur 429, respecter `Retry-After`. Sur `ratelimited`, arrêter le lot et relire tous les titres avant toute reprise. La limite observée peut être plus restrictive que la cadence théorique renvoyée par `uiprop=ratelimits`. Avec la session navigateur actuelle, considérer empiriquement une fenêtre glissante proche de huit écritures par minute : former des sous-lots d’au plus huit opérations, attendre environ une minute entre eux et conserver les écritures séquentielles. Une temporisation de 1 à 3 secondes ne suffit pas à elle seule à éviter cette fenêtre. Réévaluer cette valeur si le comportement du wiki change.

## Règles de reprise

Un lot séquentiel peut être partiellement enregistré avant une erreur `ratelimited`. Journaliser chaque succès avant l’écriture suivante. Après l’erreur, effectuer une lecture groupée de tous les titres du manifeste, identifier les créations et modifications réellement confirmées, attendre la fin de la fenêtre de débit, puis construire une reprise ne contenant que les opérations manquantes. Ne jamais rejouer aveuglément les créations déjà réussies.

Une absence de réponse ne signifie jamais échec. Relire le titre et sa dernière révision avant de réessayer. Une création rejouée doit rester protégée par `createonly`. Une modification rejouée doit conserver ou recalculer consciemment `baserevid` après comparaison.
