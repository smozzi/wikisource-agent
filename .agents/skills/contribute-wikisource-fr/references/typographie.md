# Contrôle typographique

Prendre le fac-similé comme arbitre du texte et suivre le guide typographique officiel de Wikisource pour sa représentation. Conserver les choix éditoriaux de ponctuation, mais moderniser leur forme conformément aux conventions de Wikisource.

## Automatiser seulement les cas sûrs

- normaliser le texte en UTF-8 NFC et les fins de ligne ;
- supprimer les espaces horizontales en fin de ligne ;
- remplacer une apostrophe droite textuelle isolée par `’`.

Protéger impérativement la syntaxe wiki `''` et `'''`, les balises et leurs attributs, les commentaires, les blocs littéraux, les modèles, les liens internes et les URL. Ne jamais remplacer globalement toutes les apostrophes.

Après correction, une apostrophe droite ne peut rester que dans la syntaxe wiki ou dans un titre technique canonique.

## Signaler puis relire, sans corriger aveuglément

Contrôler chaque signal contre le fac-similé et le contexte :

- espaces avant `;`, `:`, `!`, `?` et autour de `« … »` ;
- absence d’espace avant `.`, `, `)`, `]` et après `(`, `[` ;
- espace après la ponctuation lorsque la phrase continue ;
- caractère unique `…`, sauf dispositif graphique ou fidélité éditoriale particulière ;
- guillemets français ou étrangers selon la langue citée ;
- tiret cadratin, demi-cadratin, trait d’union et césure selon leur fonction ;
- accents sur les capitales, cédilles et ligatures `œ`/`æ` ;
- espaces insécables et modèles sémantiques pour dates, unités, abréviations et noms ;
- ponctuation dans les modèles, liens, balises, références et paramètres techniques.

Ces règles sont ambiguës en automatisation : URL et titres d’espace contiennent des deux-points, les points appartiennent parfois aux abréviations, les langues étrangères ont leurs propres guillemets et apostrophes, et une ligature automatique peut corrompre un mot ou une balise.

## Ordre de contrôle

1. Exécuter le correcteur conservateur sur les fichiers préparés.
2. Examiner le diff : seules les transformations sûres doivent apparaître.
3. Lancer l’audit non destructif avec
   `correct_wikisource_typography.py --audit <fichiers>` ; il signale aussi
   certaines constructions sémantiquement suspectes, par exemple le mot
   « siècle » ajouté après un modèle `{{s}}`.
4. Relire chaque signal contre le fac-similé.
5. Prévisualiser le wikicode.
6. Publier, puis contrôler le rendu et les liaisons entre pages.
