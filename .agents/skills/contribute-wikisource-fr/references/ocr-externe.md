# OCR externe par lots

Employer un OCR externe comme générateur de brouillon, jamais comme source de
vérité. Vérifier d’abord sa qualité sur 5 à 10 pages représentatives : notes,
changements de chapitre, césures, chiffres romains et pages dégradées.

Conserver séparément les trois niveaux :

- `facsimile/images/page-NNNN.*` : image de référence, arbitre de toute
  transcription ;
- `pages/ocr/<moteur-version>/` : sorties de l’OCR externe, brouillon prioritaire
  lorsqu’elles existent et sont de qualité suffisante ;
- `pages/raw/page-NNNN.txt` : couche texte embarquée dans le PDF ou DjVu,
  conservée sans correction comme solution de repli.

Ne pas recopier l’OCR externe dans `pages/raw/` et ne pas présenter
`pages/raw/` comme le meilleur OCR disponible par défaut. Le wikicode relu
contre l’image appartient seul à `pages/corrected/`.

Avec Mistral OCR 4 :

- consulter la [documentation OCR officielle](https://docs.mistral.ai/capabilities/document_ai/basic_ocr/) et les [tarifs actuels](https://mistral.ai/pricing) avant usage ;
- extraire seulement les pages utiles et traiter par lots raisonnables ;
- préférer l’envoi base64 pour les petits extraits afin d’éviter un stockage
  distant persistant ; sinon supprimer le fichier distant après traitement ;
- placer `MISTRAL_API_KEY` dans un `.env` exclu de Git et ne jamais journaliser
  la clé ;
- conserver le Markdown page par page, la réponse JSON brute, les métadonnées
  d’en-tête/pied de page et les scores de confiance ;
- contrôler automatiquement les numéros attendus, les chapitres, le début et la
  fin avant toute correction éditoriale.

Lorsque les réponses brutes restent hors Git, versionner un inventaire et des
sommes de contrôle permettant de vérifier l’archive locale, sans traiter ces
sommes comme une preuve de relecture.

Retours d’expérience à anticiper : le texte et les noms propres peuvent être
très bons, mais le moteur peut moderniser des graphies (`ame` → `âme`), modifier
la ponctuation, isoler les notes dans les pieds de page, produire des appels en
LaTeX, conserver les césures physiques et confondre signatures d’imposition et
notes. Convertir ensuite en conventions ProofreadPage (`<ref>`, `{{tiret}}`,
titres, sections) et relire chaque page contre le fac-similé avant de lui donner
le statut « corrigée ».
