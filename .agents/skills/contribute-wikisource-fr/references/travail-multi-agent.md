# Travail multi-agent par lots

Employer ce mode lorsqu’une édition assez longue peut être divisée en lots
éditoriaux indépendants. Paralléliser la préparation, jamais les écritures sur
les wikis. Ne créer `coordination/` que lorsque plusieurs agents travaillent
réellement sur des lots séparés.

## Préparer le dépôt

- Établir un commit de référence avant de créer les branches.
- Créer un worktree et une branche propres par lot. Cette préparation relève du
  coordinateur et précède toute délégation.
- Attribuer des lots explicitement disjoints, de taille compatible avec la
  limite de publication ; huit vues constituent un bon défaut.
- Donner à chaque lot au moins deux vues de contexte de chaque côté. Ces vues
  servent aux raccords et ne font pas partie des fichiers à modifier.
- Rendre accessibles en lecture seule, de préférence par liens symboliques, les
  images du fac-similé et l’OCR externe local sous `pages/ocr/`. L’agent prend
  cet OCR comme brouillon prioritaire, puis `pages/raw/` comme couche texte de
  repli ; l’image reste toujours l’arbitre.
- Pour permettre `./ws check` et `./ws lot check`, rendre également accessible
  le seul fichier PDF ou DjVu déclaré dans `PROJECT.toml`, à son chemin exact.
  Ne pas partager les autres sources ou dérivés intermédiaires dont le lot n’a
  pas besoin.
- Réserver à chaque lot ses propres noms de snapshots, manifestes, journaux et
  comptes rendus.
- Créer dans le dépôt principal un fichier de prompt par lot, sous un
  répertoire de coordination appartenant au coordinateur, par exemple
  `coordination/agent-prompts/lot-02.md`. Ne pas placer ce fichier comme
  élément non suivi dans le worktree de l’agent : celui-ci doit pouvoir rester
  propre après son commit.

## Fournir les commandes de lancement Codex

Lorsque l’environnement permet d’invoquer directement des sous-agents dans des
espaces de travail isolés, le coordinateur les lance lui-même avec le worktree
et le prompt du lot. Il consulte l’interface disponible sans supposer le nom
d’un outil, ses paramètres ou un mode de partage.

Lorsque des sessions CLI externes sont nécessaires, après avoir créé les
worktrees et rédigé les prompts, ne pas demander à l’utilisateur de recomposer
les commandes, de retrouver les répertoires ou de copier séparément le contenu
des prompts. Vérifier d’abord la syntaxe de la CLI installée avec
`codex --help`, puis fournir une commande complète et directement exécutable
par lot.

Pour une session interactive, employer normalement :

```bash
codex -C '/chemin/absolu/du/worktree' "$(cat '/chemin/absolu/du/depot-principal/coordination/agent-prompts/lot-02.md')"
```

Remplacer tous les exemples et variables par les chemins absolus réels avant
de présenter la commande. Fournir une ligne distincte pour chaque agent,
étiquetée par numéro de lot. La seule action laissée à l’utilisateur doit être
de copier puis exécuter la ligne correspondante dans le terminal destiné à
l’agent.

Employer `codex exec` seulement si l’utilisateur demande explicitement une
exécution non interactive. Ne pas ajouter
`--dangerously-bypass-approvals-and-sandbox`, ne pas relâcher la politique
d’approbation et ne pas lancer automatiquement les commandes CLI à la place de
l’utilisateur sauf demande explicite.

Avant remise, contrôler pour chaque commande :

- que le chemin passé à `-C` est le worktree du bon lot ;
- que le fichier de prompt existe dans le dépôt principal et correspond aux
  mêmes bornes ;
- que la branche et le worktree sont propres au départ ;
- que les guillemets protègent les espaces et caractères spéciaux ;
- que les commandes n’emploient ni prompt abrégé ni répertoire implicite.

## Définir les rôles

L’agent de lot doit :

1. lire les consignes du projet et les skills requis ;
2. partir du snapshot de sa tranche et de ses vues de contexte fourni par le
   coordinateur ;
3. préparer depuis l’OCR externe disponible, ou `pages/raw/` à défaut, et
   relire chaque vue contre l’image du fac-similé ;
4. préparer uniquement les pages, snapshots, manifeste et compte rendu de son
   lot ;
5. exécuter le correcteur canonique, les audits et la validation hors ligne ;
6. ne pas publier et ne pas modifier les documents globaux ;
7. produire un commit limité au lot et signaler son hash, ses raccords, ses
   incertitudes et ses contrôles.

L’agent coordinateur doit :

1. ne traiter lui-même aucun lot éditorial : il doit confier chaque lot à un
   agent de lot distinct et se limiter à l’orchestration, au contrôle et à
   l’intégration ;
2. créer les worktrees, attribuer des lots non chevauchants, enregistrer les
   prompts et invoquer les sous-agents ou fournir les commandes `codex`
   complètes permettant de les lancer directement ;
3. auditer puis intégrer les commits un à un, sans reprendre aveuglément les
   conflits ;
4. contrôler les raccords entre lots voisins et avec les vues de contexte
   après intégration ;
5. centraliser l’identité et toutes les opérations distantes :
   synchronisations, preflights, écritures et snapshots post-publication ;
6. présenter les cibles, raccords et contrôles intégrés, puis obtenir
   l’approbation explicite de l’utilisateur avant toute publication ;
7. publier les lots séquentiellement en respectant la limite de débit ;
8. archiver les preuves de publication avant de retirer éventuellement les
   worktrees.

Cette séparation est stricte, y compris lorsqu’un créneau d’agent est
indisponible ou qu’un lot paraît simple : le coordinateur attend qu’un
sous-agent puisse prendre le lot, ou réorganise la délégation, mais ne prépare
pas lui-même les pages, le manifeste ou le rapport d’un lot. Il peut corriger
après intégration une erreur ponctuelle révélée par son audit, à condition de
la documenter comme correction de coordination et de ne pas transformer cette
exception en traitement complet du lot.

## Intégrer chaque lot

Avant d’intégrer un commit, vérifier :

- son hash, sa branche de départ et la propreté du worktree de lot ;
- la liste exacte des fichiers modifiés et l’absence de fichiers globaux,
  partagés ou étrangers au lot ;
- la présence des huit pages attendues, du manifeste, du snapshot préparatoire
  et du compte rendu ;
- le résultat des validations hors ligne et les incertitudes signalées.

Intégrer les commits dans l’ordre des vues, un à un. Après chaque intégration,
contrôler le diff obtenu et les conflits éventuels avant de passer au suivant.
Ne pas confondre une particularité explicitement imprimée ou commentée par
l’éditeur avec une incertitude de transcription : la consigner, puis décider
si elle bloque réellement la publication.

Établir ensuite une matrice concise des raccords. Elle doit couvrir les
frontières internes, les frontières entre lots et les vues de contexte
extérieures. Pour une édition bilingue alternée, suivre séparément chaque flux
à son pas réel ; vérifier notamment césures, phrases, paragraphes, notes,
citations et changements de division.

## Reprendre la main avant publication

Le snapshot produit par un agent prouve seulement l’état observé pendant la
préparation. Il ne constitue jamais la base finale de publication. Après
intégration, le coordinateur doit :

1. effectuer une nouvelle synchronisation des cibles et de leurs vues de
   contexte, avec un nom de snapshot propre au coordinateur ;
2. confirmer que les créations sont toujours absentes ou que les révisions de
   base des modifications sont inchangées ;
3. revérifier l’identité et l’accès en écriture ;
4. exécuter le `preflight` immédiatement avant le `publish` ;
5. présenter à l’utilisateur les lots, cibles, raccords, incertitudes et
   résultats des contrôles, puis s’arrêter ;
6. attendre son approbation explicite avant de publier un seul lot, puis
   attendre la fenêtre de débit avant le suivant.

Une approbation porte seulement sur les cibles et manifestes présentés. Si
l’état distant change ou si une nouvelle cible apparaît, demander une nouvelle
approbation.

Une demande d’autorisation du navigateur peut expirer sans écriture. Annoncer
chaque attachement CDP au moment où il est lancé et, en cas d’échec, relancer
seulement l’opération de lecture ou de contrôle concernée.

Après chaque publication, resynchroniser le même périmètre et comparer
exactement, pour chaque cible, le wikicode local et distant, l’auteur, la
révision et le niveau ProofreadPage. Conserver des noms distincts pour le
snapshot préparatoire, le snapshot frais du coordinateur, le snapshot
post-publication et le journal d’écriture.

Archiver ces preuves dans un commit de coordination lorsque l’environnement
Git le permet. Si les métadonnées Git sont momentanément non inscriptibles,
laisser les fichiers intacts et signaler explicitement leur état non suivi :
ne pas les supprimer pour rendre artificiellement l’arbre propre.

## Éviter les conflits

- Ne jamais connecter plusieurs agents au même Chrome/CDP simultanément.
- Sérialiser les synchronisations nécessitant une autorisation Chrome, puis
  laisser les relectures locales s’exécuter en parallèle.
- Ne pas faire modifier concurremment les procédures, métadonnées, plans de
  divisions ou autres fichiers globaux. Faire remonter les enseignements au
  coordinateur.
- Ne jamais confier la même page à deux agents pour modification. Une seconde
  lecture indépendante éventuelle doit intervenir comme validation distincte.
- Après intégration, repartir des commits et révisions exacts ; ne pas copier
  manuellement des répertoires entiers entre worktrees.
- Ne retirer un worktree ou sa branche qu’après intégration, publication,
  contrôle post-publication et archivage des preuves, et seulement si cette
  suppression a été explicitement décidée. Leur présence n’autorise jamais à
  supprimer des fichiers partagés.

## Prompt minimal d’un agent de lot

Indiquer au minimum : l’édition exacte, le commit de référence, les bornes du
lot, les vues de contexte, les flux et leur pas éventuel, les skills à lire,
les fichiers autorisés, l’interdiction de publier, l’interdiction de modifier
le corpus partagé et les fichiers globaux, les contrôles attendus et
l’obligation de terminer par un commit limité au lot.

Demander en sortie : le hash du commit, la liste des raccords internes et
externes, les césures, notes ou divisions particulières, les incertitudes
résiduelles, les contrôles exécutés et la confirmation que le worktree est
propre. Cette forme normalisée permet au coordinateur d’auditer plusieurs lots
sans rouvrir inutilement tout le raisonnement de chaque agent.
