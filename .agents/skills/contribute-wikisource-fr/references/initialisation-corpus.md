# Initialiser le corpus local d’un fac-similé

Appliquer cette préparation au début d’un projet portant sur un volume entier
ou appelé à être repris sur plusieurs sessions. Elle évite les téléchargements
et extractions répétés et fixe des références stables pour toute la relecture.

## Distinguer cadrage et initialisation

La création d’un répertoire et d’un `README.md` documentant l’édition ne
signifie pas que le corpus est initialisé. L’initialisation commence seulement
avec l’acquisition ou le verrouillage du fichier source et la production des
artefacts décrits ci-dessous.

Si l’utilisateur demande un projet préparatoire sans OCR ni corpus local,
s’arrêter après le cadrage documentaire. Inscrire explicitement « corpus non
initialisé » afin qu’une reprise ultérieure ne suppose pas à tort que les
empreintes, vues, textes ou manifestes existent déjà.

## Réutiliser le corpus initialisé

N’exécuter cette initialisation qu’une seule fois pour une version donnée du
fac-similé et des paramètres d’extraction. À chaque reprise du projet, vérifier
le manifeste et les sommes de contrôle, puis réutiliser directement les textes,
images et sorties OCR existants. Ne pas relancer une extraction ou un OCR
simplement parce qu’un nouveau lot de pages commence.

Ne régénérer que les artefacts invalidés, et consigner la cause :

- fichier source remplacé ou modifié ;
- extraction absente, incomplète, corrompue ou décalée ;
- paramètres volontairement changés, par exemple résolution ou modèle OCR ;
- qualité insuffisante constatée lors du contrôle.

Si seule une partie est invalidée, reprendre uniquement les vues concernées.
Conserver les sorties antérieures lorsqu’elles sont utiles à la traçabilité et
mettre à jour le manifeste afin que la version active soit sans ambiguïté.

## Verrouiller la source

1. Identifier le fichier exact utilisé par l’index Wikisource : nom Commons,
   format, nombre de vues et URL pérenne.
2. Télécharger et conserver ce fichier original sans le modifier. Le DJVU ou
   PDF associé à l’index reste la source de vérité, même si un PDF dérivé est
   produit pour un service OCR.
3. Calculer une somme de contrôle cryptographique du fichier et l’inscrire dans
   le manifeste avec sa taille, son origine et sa date de récupération.
4. Ne pas substituer silencieusement un autre exemplaire. Consigner tout
   remplacement et reconstruire les dérivés concernés.

## Produire des dérivés page par page

Employer un identifiant de vue stable, à largeur fixe, fondé sur l’ordre du
fichier source, par exemple `page-0001`. Ne jamais employer la seule pagination
imprimée comme nom de fichier.

Produire séparément :

- la couche texte embarquée, sans correction, dans un fichier texte par vue ;
- une image fidèle par vue, à une résolution suffisante pour la relecture ;
- si nécessaire, un PDF dérivé destiné à l’OCR externe ;
- un manifeste reliant chaque vue au texte, à l’image, à la pagination imprimée
  et, plus tard, à la page ProofreadPage.

Préserver les vues sans texte, les pages blanches, couvertures, planches et
pages non paginées. Ne jamais décaler la numérotation parce qu’une vue semble
inutile.

Une organisation possible est :

```text
facsimile/
  source/
  derived/
  images/
  text-layer/
pages/
  raw/
    external-ocr/
      markdown/
      json/
```

Adapter les noms aux conventions du projet. Séparer dans tous les cas les
sources immuables, les dérivés reproductibles, l’OCR brut et le wikicode relu.
Exclure du contrôle de version les fichiers volumineux reproductibles lorsque
le projet le prévoit, mais versionner les manifestes, paramètres, sommes de
contrôle et diagnostics nécessaires à leur reconstruction.

## Préparer l’OCR externe

Lire [ocr-externe.md](ocr-externe.md) avant tout appel à un service. Commencer
par un échantillon de 5 à 10 vues représentatives : titre, texte courant,
notes, changement de chapitre, chiffres romains, langues ou colonnes multiples,
illustration et page dégradée. Examiner le résultat contre les images avant de
décider du traitement intégral.

Conserver pour chaque vue :

- la sortie textuelle ou Markdown brute ;
- la réponse JSON brute et les métadonnées utiles ;
- le modèle et les paramètres employés ;
- le lien avec l’identifiant stable de la vue ;
- les erreurs, absences et reprises éventuelles.

Ne placer aucune clé API dans le corpus, les journaux ou le dépôt. Obtenir
l’accord de l’utilisateur avant une opération payante ou un téléversement
externe non déjà autorisé.

## Contrôler l’initialisation

Avant de déclarer le corpus prêt :

1. comparer le nombre de vues du fac-similé, d’images et de fichiers texte ;
2. vérifier la première vue, la dernière et plusieurs vues réparties dans le
   volume ;
3. détecter les numéros manquants, doublons, fichiers vides inattendus et
   décalages d’une vue ;
4. contrôler visuellement l’orientation, le recadrage, la lisibilité et l’ordre
   des images ;
5. établir la correspondance entre vues et pagination imprimée, y compris les
   chiffres romains, planches, pages blanches et pages non paginées ;
6. consigner les outils, versions et commandes ou paramètres permettant de
   reproduire chaque dérivé.

Ne jamais classer une vue d’après le seul OCR. Un libellé générique tel que
« image » peut être une hallucination du moteur sur une page blanche, tandis
qu’une couverture, une planche ou un fac-similé photographique constitue un
élément éditorial même lorsque sa couche texte est vide.

Cette initialisation ne constitue ni une correction OCR ni une relecture. Le
wikicode doit ensuite être préparé et relu page par page contre le fac-similé,
avec contrôle de chaque raccord, conformément au parcours principal du skill.
