# Règles de transcription

Suivre [Aide:Transcription](https://fr.wikisource.org/wiki/Aide:Transcription) et la documentation du modèle concerné. Prendre le fac-similé comme source du texte, tout en appliquant la typographie moderne prescrite par Wikisource.

## Distinguer texte et typographie

- conserver l’orthographe, le vocabulaire, la syntaxe et les choix de ponctuation de l’édition ;
- moderniser leur représentation typographique : espaces avant `:`, `;`, `!`, `?`, guillemets français, apostrophes courbes, caractère `…`, accents sur les capitales et distinction entre traits d’union et tirets ;
- ne corriger une véritable coquille de l’imprimeur qu’avec `{{corr|forme imprimée|forme corrigée}}` ; corriger normalement, sans `{{corr}}`, une erreur introduite par l’OCR ou la transcription.

## Organiser la page

- ne pas placer les en-têtes courants, pieds de page ni numéros de page dans le corps transclus ; leur saisie dans les champs dédiés est facultative ; lorsqu’ils sont transcrits, employer notamment `{{nr|gauche|centre|droite}}` dans le `noinclude` initial, reproduire seulement les éléments réellement imprimés et placer le folio du bon côté d’après le fac-similé, conformément à [Aide:Entête et pied de page](https://fr.wikisource.org/wiki/Aide:Ent%C3%AAte_et_pied_de_page) ;
- employer `{{t2}}` à `{{t6}}` dans l’espace `Page:` en respectant la hiérarchie ; réserver les boîtes de titre éditoriales telles que `{{titre}}` à l’espace principal ;
- les modèles `{{t2}}` à `{{t6}}` ne mettent pas le texte en gras par défaut ; lorsque le fac-similé imprime un titre gras, l’indiquer explicitement, par exemple avec `|fw=bold` ou `'''…'''`, puis contrôler le rendu ;
- laisser les alinéas ordinaires au rendu automatique ; employer `{{Alinéa}}` ou `{{SA}}` seulement lorsque la mise en page l’exige ;
- quand un nouveau paragraphe avec alinéa commence en tête de page ou après un titre ou un séparateur, placer `<nowiki />`, puis une ligne vide, afin de préserver cette indentation conformément à [Aide:Nowiki](https://fr.wikisource.org/wiki/Aide:Nowiki) ; ne pas le faire si le texte poursuit le paragraphe précédent ou dans un contexte, tel que `<poem>`, où la documentation l’exclut ;
- éviter les retours à la ligne internes à un paragraphe, notamment autour des illustrations, car ils peuvent créer des retraits parasites.

## Encoder les notes

- placer la note dans `<ref>…</ref>` à l’emplacement de son appel ; ne pas ajouter `<references />` dans le corps de la page ;
- employer `follow` pour une note répartie sur plusieurs pages et vérifier le paragraphe créé par cette déclaration ;
- employer `group` lorsque plusieurs séries de notes doivent rester distinctes ;
- préserver une éventuelle espace avant l’appel avec une espace insécable conforme aux usages.

## Balisage sémantique

- indiquer la langue des passages étrangers avec `{{lang}}` ou le paramètre
  `lang` du modèle de mise en forme retenu ; conserver le texte exact de
  l’édition et employer un code de langue vérifié ;
- choisir un modèle documenté qui décrit la nature du passage — notamment
  poésie, citation en retrait ou texte en langue étrangère — plutôt qu’un
  assemblage de centrage, de retraits et de sauts de ligne purement visuels ;
- lorsqu’un passage structuré traverse plusieurs pages, employer les mécanismes
  de continuation prévus par ce modèle et contrôler la transclusion complète ;
  ne pas reproduire mécaniquement chaque fin de ligne imprimée avec `<br />` ;
- prévisualiser tout modèle peu familier et n’en généraliser les paramètres
  qu’après comparaison avec plusieurs occurrences du fac-similé.

## Traiter les césures

- supprimer les césures purement typographiques de fin de ligne en recopiant le mot entier ;
- à une frontière de pages, la syntaxe simple `fragment-` puis `suite` convient seulement si le tiret est le dernier caractère utile de la première page et si la coupure ne porte pas sur un mot composé ;
- dans les autres cas, employer `{{tiret|première partie|seconde partie}}` puis `{{tiret2|première partie|seconde partie}}` ;
- inclure toute la chaîne dans les modèles, apostrophe comprise : `{{tiret|d’inhos|pitalité}}`, et non `d’{{tiret|inhos|pitalité}}` ;
- pour une coupure au trait d’union d’un mot composé, placer celui-ci dans les paramètres : `{{tiret|c’est-à|-dire}}` puis `{{tiret2|c’est-à-|dire}}` ;
- contrôler systématiquement le rendu transclus des deux pages.

## Contrôler les illustrations

Employer les modèles d’image documentés et vérifier le rendu avec le texte adjacent. Corriger les retraits indésirables avec les modèles prévus, notamment `{{br0}}`, seulement après avoir éliminé les retours de ligne internes au paragraphe.

## Classer les vues sans texte courant

- examiner directement chaque vue : ne jamais déduire sa nature d’un marqueur
  OCR générique, de l’absence de couche texte ou de la seule pagination ;
- réserver le niveau ProofreadPage `0` (« sans texte ») aux véritables pages
  blanches ou vues sans contenu éditorial à transcrire ;
- ne pas classer comme « sans texte » une couverture, une planche, une carte,
  une illustration ou la reproduction photographique d’un document ;
- pour ces éléments, restituer l’objet éditorial avec le modèle d’image
  documenté, un texte alternatif utile et un niveau correspondant à la
  relecture réellement effectuée ;
- distinguer les poussières, bords de numérisation, mires et marques ajoutées
  par le numériseur du contenu appartenant à l’édition.
