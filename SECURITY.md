# Sécurité

Signaler une vulnérabilité en privé au mainteneur du dépôt, sans ouvrir d’issue publique lorsqu’elle concerne des jetons, cookies, contournements d’identité ou risques d’écrasement sur Wikisource.

Ne jamais joindre de profil Chrome, `.env`, journal contenant un jeton, capture de cookie ou manifeste avec un secret. Révoquer immédiatement tout secret exposé et retirer l’artefact de l’historique avec l’aide du mainteneur.

Le client CDP doit rester limité à `127.0.0.1`, utiliser un profil dédié et ne jamais lancer implicitement un navigateur. Toute publication requiert une approbation explicite et doit conserver `assertuser`, `createonly` ou `baserevid` selon l’opération.

Versions prises en charge : branche principale courante, Python 3.11 à 3.13.
