# Éditions bilingues alternées

Appliquer ces contrôles lorsqu’un fac-similé alterne deux langues d’une vue à
l’autre, notamment latin et français.

## Établir les deux flux

Identifier séparément le flux de chaque langue et vérifier si l’alternance
reste régulière. Pour un pas de deux, contrôler les raccords `n → n+2` en plus
des frontières physiques `n → n+1`. Synchroniser au moins deux vues de contexte
de chaque côté du lot.

Tester sur un lot d’étalonnage contenant un titre, des pages des deux langues,
des notes, une césure et une frontière de division. Prévisualiser les modèles
avant de généraliser la convention.

Employer `step=2` dans `<pages>` seulement après avoir vérifié que chaque flux
reste autonome : texte, titres, notes et bornes doivent demeurer complets quand
l’autre langue est omise.

## Rattacher les notes communes

Une édition en regard peut imprimer une note commune une seule fois et la faire
déborder matériellement sur la vue opposée. Dans l’espace `Page:`, rattacher la
note complète à son appel sémantique. Si les deux versions portent le même
appel et doivent être transcluses séparément, répéter fidèlement la note dans
chaque flux plutôt que de conserver un fragment inutilisable sur la vue où
l’imprimeur l’a placé.

Vérifier l’identité des répétitions et consigner ce choix éditorial. Employer
`lower-alpha` pour un apparat à appels alphabétiques et des références
ordinaires pour les notes numériques.

## Encoder le latin

Conserver exactement les graphies, ligatures, crochets, corrections et
variantes de l’édition. Ne pas latiniser, classiciser ni normaliser depuis
l’OCR. Examiner particulièrement `ę`/`ae`, `i`/`j`, noms propres, abréviations,
chiffres romains et lettres d’apparat.

Pour un bloc long, employer `{{lang|la|2=…}}` : `la` occupe le premier
paramètre et le texte le second. Le nommer explicitement évite que les signes
`=` des balises et attributs internes soient interprétés comme des paramètres.
Prévisualiser impérativement ; un avertissement « plus d’une valeur pour le
paramètre 1 » signale généralement l’emploi erroné de `1=`.

À une césure entre deux vues du même flux linguistique, utiliser les vues
`n → n+2` pour déterminer `{{tiret}}` et `{{tiret2}}`.

## Canoniser les fichiers ProofreadPage

Préparer chaque wikicode avec un en-tête et un pied `noinclude` explicites,
même vide, et sans saut de ligne terminal. ProofreadPage peut ajouter
`<noinclude></noinclude>` ou supprimer ce saut lors de l’enregistrement ; cette
normalisation ferait échouer une comparaison octet pour octet après écriture.

Après une réponse ambiguë, ne jamais rejouer le lot complet : relire la cible,
aligner la copie locale sur la révision réellement enregistrée et reprendre
uniquement les opérations encore absentes.
