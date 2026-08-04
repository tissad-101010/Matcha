# Matcha — règles de code et de compréhension

Ce document doit être consulté avant chaque phase du build et pendant les revues de code.
L'objectif n'est pas seulement d'obtenir une application fonctionnelle : chaque choix et
chaque fichier doivent pouvoir être expliqués clairement pendant l'évaluation.

## 1. Principes prioritaires

1. Écrire la solution la plus simple qui respecte entièrement le sujet.
2. Ne pas ajouter d'abstraction, de dépendance ou de service sans besoin démontrable.
3. Un fichier possède un rôle principal identifiable par son nom.
4. Une fonction effectue une seule opération métier clairement décrite.
5. Le backend reste l'autorité pour la sécurité, les permissions et les règles métier.
6. Aucun code ne doit être conservé si personne dans l'équipe ne peut l'expliquer.

## 2. Taille et organisation des fichiers

Ces limites sont des seuils de revue, pas des règles mécaniques :

| Élément | Taille visée | Action si dépassée |
| --- | ---: | --- |
| Fonction Python ou TypeScript | 10 à 30 lignes | Extraire une étape portant un nom métier |
| Fichier backend | 80 à 200 lignes | Séparer route, service, requêtes ou validation |
| Composant React | 50 à 150 lignes | Extraire sous-composants et hooks ciblés |
| Fichier SQL de migration | Une évolution cohérente | Créer une nouvelle migration numérotée |
| Fichier de test | Un comportement ou module | Séparer par parcours fonctionnel |

- Éviter les fichiers génériques `utils.py`, `helpers.ts` ou `common.py` qui accumulent
  des responsabilités sans rapport.
- Préférer des noms précis comme `password_policy.py`, `match_queries.py` ou
  `useSocketNotifications.ts`.
- Ne pas créer un fichier pour une fonction triviale si cela rend la navigation plus dure.
- Ne jamais utiliser un fichier comme simple relais de réexportations difficiles à suivre.

## 3. Lisibilité et commentaires

- Le code explique **comment** ; les commentaires expliquent **pourquoi** une décision
  non évidente est nécessaire.
- Ajouter une courte docstring aux fonctions publiques, services métier et requêtes
  complexes : entrée, résultat, erreur importante et règle du sujet appliquée.
- Commenter les règles sensibles : compatibilité mutuelle, score de suggestion, unlike,
  blocage, consentement, présence et durée des jetons.
- Ne pas commenter une instruction évidente ligne par ligne.
- Éviter les acronymes et variables d'une lettre, sauf indices locaux très courts.
- Employer le vocabulaire de `TASKS.md` partout : `like`, `match`, `unlike`, `block`,
  `visit`, `consent`, `main_photo`.
- Écrire les noms du code en anglais de manière cohérente ; les textes affichés restent
  en français et sont centralisés côté frontend.

Exemple utile :

```python
def are_profiles_compatible(viewer: Profile, candidate: Profile) -> bool:
    """Return true only when both users accept the other's gender."""
    # The subject requires mutual compatibility; a one-way preference is insufficient.
    return (
        candidate.gender in viewer.effective_preferences
        and viewer.gender in candidate.effective_preferences
    )
```

## 4. Structure backend Flask

Une requête HTTP suit un chemin visible et constant :

```text
route → validation → service métier → requête SQL → réponse
```

- **Route** : lit la requête, appelle le service et produit la réponse HTTP.
- **Validation** : contrôle forme, types, longueurs et champs autorisés.
- **Service** : applique les permissions, transactions et règles métier.
- **Repository/query** : contient uniquement le SQL manuel avec psycopg.
- **Schema/serializer** : construit explicitement les données exposées au client.

Règles :

- Les routes restent courtes et ne contiennent pas de SQL.
- Les repositories ne prennent pas de décision d'autorisation.
- Les services ne dépendent pas de Flask lorsque ce n'est pas nécessaire, afin d'être
  testables simplement.
- Les erreurs métier utilisent des classes explicites, traduites en HTTP à un seul endroit.
- Les opérations liées — like réciproque et match, unlike, blocage, suppression — utilisent
  une transaction PostgreSQL.
- Les dépendances sont passées explicitement ; éviter les variables globales cachées.
- Ne pas introduire d'ORM, de système de comptes intégré ou de validateur automatique
  interdit par le sujet.

## 5. SQL et PostgreSQL

- Toutes les requêtes utilisent les paramètres psycopg ; aucune concaténation SQL avec une
  donnée utilisateur.
- Énumérer les colonnes dans les `SELECT` et `INSERT` ; éviter `SELECT *`.
- Placer les contraintes structurelles dans PostgreSQL : unicité, clés étrangères,
  limites cohérentes et photo principale unique.
- Nommer les migrations dans l'ordre, par exemple `001_create_accounts.sql`.
- Une migration appliquée n'est jamais réécrite : créer la suivante.
- Expliquer par un commentaire les index non évidents et la requête qu'ils accélèrent.
- Vérifier les requêtes complexes avec `EXPLAIN` sur le jeu de 500 profils minimum.
- Garder le SQL lisible : mots-clés cohérents, clauses alignées et CTE nommées selon leur rôle.

## 6. API et données exposées

- Utiliser des réponses JSON cohérentes pour succès, validation et erreur.
- Ne jamais sérialiser directement une ligne complète de base de données.
- Autoriser explicitement les champs modifiables afin d'empêcher le mass assignment.
- Ne jamais exposer mot de passe, hash, token, e-mail d'un autre membre, coordonnées GPS
  exactes, preuve de consentement ou information interne de modération.
- Documenter chaque endpoint : méthode, chemin, authentification, entrée, sortie et erreurs.
- Le frontend ne doit pas reconstruire une règle métier déjà décidée par le backend.

## 7. React et TypeScript

- Activer le mode strict TypeScript ; éviter `any` et les assertions forcées.
- Séparer : composants visuels, appels API, état serveur, formulaires et connexion Socket.IO.
- Un composant reçoit des propriétés simples et ne connaît pas toute l'application.
- Extraire un hook seulement lorsqu'il encapsule un vrai comportement réutilisé ou complexe.
- Ne pas copier la même règle de validation dans plusieurs formulaires.
- Tous les écrans implémentent les états utiles : chargement, vide, erreur, hors ligne et succès.
- Les boutons désactivés expliquent pourquoi, notamment le like sans photo principale.
- Utiliser de vrais boutons, labels, titres et liens HTML avant d'ajouter des rôles ARIA.
- Navigation clavier, focus visible et contraste sont vérifiés pendant le développement.
- Garder les composants indépendants de la maquette PNG : les règles viennent des documents
  textuels, les images servent seulement de direction visuelle.

## 8. Temps réel et concurrence

- Tout événement Socket.IO vérifie la session et l'autorisation côté serveur.
- Un message est affiché comme envoyé seulement après persistance confirmée.
- Prévoir un identifiant client idempotent pour éviter les doublons après reconnexion.
- Séparer clairement événement de domaine, notification persistée et diffusion temps réel.
- Après unlike ou blocage, le serveur refuse immédiatement tout nouvel envoi.
- La présence utilise Valkey et la fenêtre de deux minutes définie dans `TASKS.md`.
- Tester déconnexion, reconnexion, deux onglets, événement en double et course like/unlike.
- Ne pas augmenter le nombre de workers Gunicorn sans appliquer l'architecture multi-instance
  documentée dans `TASKS.md`.

## 9. Sécurité et protection des données

- Aucun secret dans Git, le code, les images, les tests ou les logs.
- Mots de passe hachés avec Argon2id, jamais journalisés ni renvoyés.
- Cookies de session `HttpOnly`, `Secure` en production et `SameSite` adapté.
- Protection CSRF sur toute action qui modifie l'état.
- Rate limiting sur connexion, inscription, e-mails, uploads et événements sensibles.
- Images vérifiées, décodées, EXIF supprimé puis réencodées avant stockage privé.
- Consentements préférences et GPS séparés, non précochés et auditables.
- Les logs utilisent des identifiants techniques utiles, sans contenu de message ni donnée
  sensible.
- Les messages d'authentification limitent l'énumération des comptes.
- Toute nouvelle donnée personnelle doit avoir une finalité et une durée de conservation.

## 10. Gestion des erreurs et journalisation

- Ne jamais ignorer silencieusement une exception.
- Fournir au client un message compréhensible et conserver le détail technique uniquement
  dans des logs sûrs.
- Utiliser un identifiant de corrélation pour suivre une requête entre Nginx et Flask.
- Ne pas employer `print` pour les logs applicatifs.
- Aucun traceback, warning ou détail SQL ne doit atteindre le navigateur.
- Une erreur partielle ne doit pas laisser la base ou MinIO dans un état incohérent.

## 11. Tests compréhensibles

Chaque test suit `Arrange → Act → Assert` et son nom décrit le comportement attendu :

```python
def test_like_without_main_photo_is_rejected():
    """A complete profile without a photo may browse but cannot like."""
```

- Tester les services métier indépendamment de HTTP lorsque possible.
- Ajouter des tests d'intégration pour PostgreSQL, Valkey, MinIO et Socket.IO.
- Ajouter un test de non-régression avec chaque correction de bug.
- Tester le refus et les permissions, pas seulement les parcours valides.
- Éviter les mocks qui remplacent précisément le comportement que le test doit vérifier.
- Les tests E2E couvrent les parcours critiques listés dans `SCENARIOS.md`.
- Les données de test sont déterministes ; aucune dépendance réseau n'est requise.

## 12. Dépendances et configuration

- Chaque dépendance ajoutée doit avoir un rôle documenté et être acceptable par le sujet.
- Préférer la bibliothèque standard pour une opération simple.
- Verrouiller les versions exactes et conserver les lockfiles.
- Centraliser les paramètres dans des objets de configuration validés au démarrage.
- Fournir une valeur locale sûre dans `.env.example` lorsque possible, jamais un secret réel.
- Aucun comportement métier ne dépend d'une constante dispersée dans plusieurs fichiers.

## 13. Git et revues

- Un commit représente une modification cohérente et explicable.
- Ne pas mélanger refactorisation massive et nouvelle fonctionnalité.
- Avant validation : formatage, lint, tests, vérification des migrations et `git diff`.
- Ne pas conserver code mort, fichiers temporaires, logs, médias locaux ou secrets.
- Une revue vérifie le sujet, la sécurité, la lisibilité et les cas d'erreur avant le style.

## 14. Documentation pour l'évaluation

Chaque module fonctionnel doit permettre de répondre à cinq questions :

1. Quel besoin du sujet couvre-t-il ?
2. Quel est le trajet de la donnée du navigateur à PostgreSQL ou Valkey ?
3. Quelle règle est vérifiée côté serveur ?
4. Quels abus ou erreurs sont refusés ?
5. Quels tests prouvent le comportement ?

Le README doit expliquer au minimum :

- architecture et rôle de chaque service ;
- lancement avec `make start` ;
- migrations et seed ;
- authentification par session et protections principales ;
- schéma des likes, matchs, unlike et blocages ;
- calcul de compatibilité, suggestions et popularité ;
- fonctionnement du chat et des notifications ;
- stockage des photos et consentements ;
- tests et limites connues.

Les décisions difficiles utilisent de courtes fiches ADR dans `docs/adr/`, contenant
contexte, décision, alternatives écartées et conséquences. Ne créer une ADR que lorsqu'une
décision ne peut pas être comprise directement dans le code ou `TASKS.md`.

## 15. Checklist avant de déclarer une tâche terminée

- [ ] Je peux expliquer le besoin du sujet couvert.
- [ ] Le nom et le rôle de chaque fichier modifié sont évidents.
- [ ] Les fonctions restent courtes et ne mélangent pas plusieurs responsabilités.
- [ ] Les commentaires expliquent les décisions non évidentes.
- [ ] Les entrées, autorisations et erreurs sont traitées côté serveur.
- [ ] Aucune donnée sensible ou secrète n'est exposée.
- [ ] Les cas nominal, refusé et erreur sont testés.
- [ ] Le code passe formatage, lint et tests sans warning.
- [ ] La documentation utile à la soutenance est à jour.
- [ ] Je peux retracer la donnée et expliquer le code sans réciter une boîte noire.

## 16. Signaux imposant une simplification

Arrêter et simplifier si :

- un fichier a plusieurs raisons indépendantes de changer ;
- une fonction nécessite un long commentaire pour expliquer son déroulement ;
- une abstraction n'a qu'un seul usage et masque le comportement ;
- un test doit simuler plus de composants qu'il n'en exécute ;
- la même règle métier existe côté frontend, dans une route et dans une requête SQL ;
- une fonctionnalité ne peut pas être expliquée avec un petit schéma et un exemple ;
- une dépendance fait davantage que ce qui est autorisé par le sujet.

Dans ce cas, revenir au flux explicite le plus court, ajouter un test, puis documenter la
raison du choix.
