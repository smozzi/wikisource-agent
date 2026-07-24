# Manifestes et reprise

Dernière vérification : 2026-07-21.

## Publication

```json
{
  "api": "https://fr.wikisource.org/w/api.php",
  "assertuser": "Utilisateur attendu",
  "operations": [
    {"op": "create", "title": "Page:Index.djvu/1", "text_file": "../../pages/corrected/page-0001.txt", "summary": "Création après relecture"},
    {"op": "edit", "title": "Livre:Index.djvu", "baserevid": 123, "text": "...", "summary": "Mise à jour contrôlée"}
  ]
}
```

Limiter le manifeste à huit opérations. Les chemins spécifiés dans `text_file` sont **relatifs à l’emplacement du fichier manifeste lui-même** (par exemple `../pages/corrected/page-0001.txt` pour `publication/manifest.json`, ou `../../pages/corrected/...` pour un manifeste au sein d’un dossier `lots/lot-XXXX/`). Pour `Page:`, fournir les zones `noinclude` canoniques ; la normalisation automatique du `<noinclude></noinclude>` final par MediaWiki est gérée par le client.


## Synchronisation

Employer `titles` et/ou `page_ranges`, chaque plage contenant `index`, `from` et `to`. Conserver le contenu local si le `revid` distant est inchangé ; réécrire le snapshot atomiquement.

## Reprise

Après une erreur ou une réponse ambiguë : arrêter, attendre si nécessaire, synchroniser toutes les cibles et examiner le JSONL. Accepter comme terminée seulement une ligne `Success` dont `newrevid`, titre et contenu correspondent encore exactement au wiki. Refuser les journaux mal formés, titres dupliqués, changements ultérieurs et contenus divergents. Refaire un preflight sur les seules opérations restantes.
