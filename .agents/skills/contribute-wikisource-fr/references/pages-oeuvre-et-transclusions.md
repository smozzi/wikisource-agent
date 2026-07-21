# Pages d’œuvre et transclusions

Employer cette procédure lorsqu’un texte corrigé dans l’espace `Page:` doit
être publié dans l’espace principal avec une page racine, un sommaire, des
sous-pages logiques et une lecture sur une seule page.

Références Wikisource à revérifier avant une opération inhabituelle :

- [Aide:Transclusion](https://fr.wikisource.org/wiki/Aide:Transclusion) ;
- [Aide:Table des matières](https://fr.wikisource.org/wiki/Aide:Table_des_mati%C3%A8res) ;
- [Aide:Finalisation](https://fr.wikisource.org/wiki/Aide:Finalisation) ;
- [Aide:Publier un livre](https://fr.wikisource.org/wiki/Aide:Publier_un_livre).

## Vérifier que l’œuvre est prête

1. Rechercher le titre et ses variantes avant toute création. Ne pas créer une
   autre édition sous un titre concurrent sans décision explicite.
2. Confirmer que toutes les pages destinées à la transclusion ont été relues
   contre le fac-similé et possèdent le niveau approprié.
3. Établir les bornes d’après le contenu réel des vues, non d’après la seule
   pagination imprimée ni la table.
4. Exclure les faux-titres, versos blancs, publicités et œuvres voisines qui
   ne font pas partie de la composante logique concernée.
5. Distinguer les éléments réellement autonomes : notice, préface,
   introduction, parties, chapitres, annexes. Ne pas fabriquer un découpage
   absent lorsque l’œuvre forme un texte continu.

## Concevoir l’arborescence

Utiliser en général :

```text
Titre de l’œuvre
Titre de l’œuvre/Notice
Titre de l’œuvre/Préface
Titre de l’œuvre/Partie ou chapitre
Titre de l’œuvre/Texte entier
```

La page racine sert de sommaire et de point d’entrée pour l’export. Chaque
sous-page correspond à une unité de lecture réelle. Une œuvre courte et
continue peut être transcluse directement sur sa page racine ; ne créer des
sous-pages que si elles améliorent effectivement la lecture ou l’export.

Choisir les titres d’après l’édition et les conventions de nommage actuelles.
Employer des libellés cohérents entre la table du `Livre:`, la page racine et
les sous-pages. Ne créer aucun lien rouge vers une composante non prête.

## Préparer la table ou le sommaire

Si l’ouvrage possède une table imprimée, la transcrire dans l’espace `Page:`
avec `{{Table}}`, puis relier uniquement les composantes prêtes.

Quand une vue de table contient les entrées de plusieurs œuvres, encadrer
seulement les lignes de l’œuvre concernée :

```wiki
<section begin="nom-oeuvre" />
{{Table|titre=[[Titre de l’œuvre/Sous-page|Libellé imprimé]]|page=12}}
<section end="nom-oeuvre" />
```

La page racine peut alors transclure cette portion avec `onlysection`. Une
section est justifiée ici parce que la vue est réellement partagée entre
plusieurs sommaires. Ne pas conserver de section à une simple frontière entre
pages.

Si la table imprimée ne fournit pas tous les accès nécessaires, ajouter à la
page racine le minimum de liens éditoriaux utiles, en distinguant clairement
ces ajouts du fac-similé. Ne pas répéter un lien fourni automatiquement par
l’en-tête Wikisource.

## Créer la page racine

Pour une page racine fondée sur une section de table :

```wiki
{{TextQuality|100%}}
<pages
 index="Nom exact du fichier.djvu"
 from=500
 to=500
 onlysection="nom-oeuvre"
 header=Sommaire
 auteur="[[Auteur:Nom|Nom]]"
 traducteur="[[Auteur:Nom|Nom]]"
 titre="Titre de l’œuvre"
 volume="Titre du recueil, tome N"
/>
```

Adapter l’indicateur de qualité à l’état réel. Ne pas ajouter avant la
transclusion un titre générique tel que `TABLE DES MATIÈRES` si le rendu
`header=Sommaire` et la table transcluse fournissent déjà la structure
visuelle nécessaire.

`header=Sommaire` produit une boîte de titre sans navigateur. Il reprend les
métadonnées du `Livre:` ; dans un recueil, surcharger explicitement `auteur`,
`traducteur`, `titre`, `volume` ou les autres champs qui diffèrent de l’index
global.

## Créer les sous-pages

Une sous-page transcluant des vues entières suit normalement cette forme :

```wiki
<pages
 index="Nom exact du fichier.djvu"
 from=20
 to=35
 header=1
 auteur="[[Auteur:Nom|Nom]]"
 traducteur="[[Auteur:Nom|Nom]]"
 titre="[[Titre de l’œuvre]]"
/>
```

`header=1` ajoute la boîte de titre et le navigateur. Les liens précédent et
suivant proviennent du sommaire du `Livre:` : vérifier que celui-ci pointe
vers les bonnes sous-pages et dans le bon ordre.

Employer les numéros de vues ProofreadPage, pas les folios imprimés. À une
frontière exacte entre pages, utiliser seulement `from` et `to`. Si deux
composantes partagent une vue, poser des sections sur le contenu réel et
utiliser `fromsection` ou `tosection`. Employer `onlysection` seulement
lorsque la même section est bien présente sur toutes les pages demandées ;
pour une section unique de table, fixer `from` et `to` à la même vue.

Ne jamais inclure une page blanche finale pour allonger artificiellement une
borne. Contrôler aussi que la dernière vue ne contient pas le début de la
composante suivante.

## Créer `/Texte entier`

Pour une œuvre découpée en sous-pages, créer :

```wiki
<pages index="Nom exact du fichier.djvu" from=20 to=120 />

[[Catégorie:Textes entiers]]
```

Inclure toutes les pages utiles de l’œuvre, mais exclure pages publicitaires,
éléments d’un autre texte et blancs extérieurs sans fonction éditoriale.
Conserver les blancs intérieurs seulement s’ils appartiennent réellement à la
séquence et n’altèrent pas le rendu.

Lorsque la sous-page `/Texte entier` existe, son lien apparaît
automatiquement sur la page racine utilisant l’en-tête de sommaire. Ne pas
ajouter une seconde fois un lien manuel « Texte sur une seule page ».

## Publier dans un ordre cohérent

Avant publication, synchroniser la page racine, toutes les sous-pages, les
pages de table modifiées et les variantes plausibles du titre.

Pour des créations coordonnées :

1. créer les sous-pages ordinaires ;
2. créer `/Texte entier` ;
3. modifier la table ou ses sections avec `baserevid` ;
4. créer la page racine en dernier.

Cet ordre évite une page racine remplie de liens rouges ou dépendant d’une
section encore absente. Employer `createonly` pour toute nouvelle page,
`baserevid` pour chaque modification, puis exécuter le preflight immédiatement
avant les écritures selon le skill `utiliser-api-wikisource`.

## Contrôler après publication

Resynchroniser toutes les cibles et vérifier :

- l’identité exacte des wikicodes sauvegardés ;
- le rendu non vide de chaque transclusion ;
- les bornes, notamment l’exclusion des blancs extérieurs et du texte voisin ;
- le navigateur des sous-pages et l’ordre des liens ;
- le sommaire de la page racine, sans titre ni lien automatique dupliqué ;
- l’apparition automatique du lien `/Texte entier` ;
- les notes, ancres, tableaux et sections partagées ;
- l’absence de lien rouge vers une composante non prête ;
- la cohérence de l’export EPUB avant d’ajouter `Bon pour export`.

Archiver les snapshots frais et post-publication, le manifeste, le journal et
les bornes retenues. Si un contributeur ajuste ensuite le rendu sur Wikisource,
resynchroniser sa révision et la prendre comme nouvelle source locale avant
toute autre modification.
