# Matcha — feuille de route complète

Ce document transforme le sujet Matcha v6.0 en tâches de développement vérifiables.
Toutes les sections marquées **Obligatoire** doivent être terminées. Les bonus ne doivent
être commencés qu'après validation complète de la partie obligatoire.

## Stack technique validée

Les choix suivants sont retenus pour toute l'implémentation :

| Domaine | Technologie retenue | Usage | Justification par rapport au sujet |
| --- | --- | --- | --- |
| Backend | Python + Flask | API HTTP JSON et logique métier | Flask est explicitement suggéré par le sujet comme micro-framework Python. Il fournit le routage sans imposer d'ORM, de validation ou de gestion des comptes, ce qui permet d'implémenter manuellement les éléments exigés. |
| Production backend | Gunicorn | Serveur WSGI de production | Le sujet laisse le choix du serveur web. Gunicorn exécute Flask de manière plus fiable qu'un serveur de développement sans ajouter de framework interdit. Le type et le nombre de workers devront être validés avec Flask-SocketIO avant d'activer le multi-worker. |
| Base de données | PostgreSQL | Stockage relationnel principal | Le sujet exige une base relationnelle ou orientée graphe gratuite et cite PostgreSQL parmi les choix acceptés. Ses index, transactions et contraintes conviennent aux 500 profils et aux interactions concurrentes. |
| Accès à la base | psycopg 3 | Requêtes SQL manuelles et paramétrées, sans ORM | psycopg est un pilote PostgreSQL, pas un ORM. Il permet d'écrire toutes les requêtes manuellement et de les paramétrer, comme demandé, tout en protégeant l'application contre les injections SQL. |
| Migrations | Fichiers SQL maison | Création et évolution reproductible du schéma | Des migrations SQL explicites rendent le schéma reproductible sans dépendre d'un ORM ou d'un outil susceptible de générer les requêtes à notre place. Elles facilitent aussi l'explication du modèle pendant la soutenance. |
| Frontend | React + TypeScript + Vite | Application web dynamique | React est explicitement autorisé par le sujet. TypeScript réduit les erreurs côté client et Vite fournit un environnement moderne sans imposer de logique backend, d'ORM ou de gestion des utilisateurs. |
| Styles | Tailwind CSS | Design responsive et système visuel cohérent | Le sujet autorise les bibliothèques d'interface et exige une mise en page structurée, mobile et acceptable sur petits écrans. Tailwind facilite ces contraintes sans modifier la logique métier. |
| Temps réel | Flask-SocketIO | Chat, notifications et présence en ligne | Le chat et les notifications doivent parvenir en moins de 10 secondes depuis toute page. Une connexion WebSocket permet une diffusion immédiate, tandis que Flask-SocketIO s'intègre au micro-framework retenu sans fournir d'ORM ni de comptes utilisateurs. |
| État éphémère partagé | Valkey | Sessions serveur, présence, limitation de débit et bus Pub/Sub Socket.IO | Valkey est gratuit, open source et compatible avec le protocole Redis utilisé par les clients Python et Flask-SocketIO. Il complète PostgreSQL sans le remplacer : toutes les données métier durables restent dans la base relationnelle exigée par le sujet. |
| Authentification | Flask-Session + Valkey + cookies sécurisés | Sessions serveur partagées, autorisations et révocation | Flask-Session est une bibliothèque spécialisée, pas un gestionnaire de comptes ni un ORM. Les sessions partagées permettent une déconnexion immédiate, tandis que les cookies `HttpOnly`, `Secure` et `SameSite`, associés à CSRF, répondent aux exigences de sécurité du sujet. |
| Reverse proxy | Nginx | Sert le build React et route `/api` et `/socket.io` sous un même domaine | Le sujet cite Nginx parmi les serveurs web possibles. Il sert efficacement les fichiers statiques, évite les problèmes CORS et prend officiellement en charge le proxy WebSocket avec une configuration explicite. |
| Mots de passe | Argon2id avec `argon2-cffi` | Hachage sécurisé des mots de passe | Le sujet interdit explicitement le stockage des mots de passe en clair. Argon2id est un algorithme de hachage lent et salé conçu pour résister aux attaques par force brute ; la politique refusant les mots anglais courants sera ajoutée séparément. |
| Dictionnaire de mots de passe | Liste anglaise locale versionnée | Refus des mots anglais courants sans dépendance réseau | Le sujet exige explicitement le refus des mots anglais courants. Une liste locale à provenance et licence documentées donne un comportement déterministe et testable pendant la soutenance. |
| E-mails | SMTP + Mailpit en développement | Activation et réinitialisation de mot de passe | Le sujet impose un e-mail d'activation avec lien unique et un e-mail de réinitialisation. SMTP reste indépendant du fournisseur et Mailpit permet de tester localement ces parcours sans envoyer de vrais messages. |
| Géocodage | Catalogue local + Nominatim optionnel | Ville/quartier, géocodage inverse et saisie manuelle | Le catalogue local garantit le fonctionnement hors ligne et la saisie obligatoire si le GPS est refusé. Nominatim sert uniquement d'enrichissement à la demande avec cache, attribution et limite stricte, afin de ne pas rendre le matching dépendant d'un service externe. |
| SMTP de production | Brevo SMTP optionnel | Envoi réel des e-mails transactionnels hors environnement local | Brevo fournit un relais SMTP adapté aux e-mails d'activation et de réinitialisation. Il reste optionnel : Mailpit garantit que la mandatory et la soutenance fonctionnent sans compte externe. |
| Images | Pillow | Validation, réencodage et redimensionnement | Le sujet impose jusqu'à cinq photos et interdit les téléversements non autorisés. Pillow permet de décoder puis réencoder les images, d'en contrôler le format et les dimensions et de ne pas se fier uniquement à l'extension fournie. |
| Stockage des images | MinIO local + API S3 compatible | Buckets privés pour les photos de profil et la galerie | Le sujet interdit les téléversements non autorisés et exige une installation reproductible. MinIO est gratuit, open source, exécutable avec Podman et utilisable hors ligne pendant la soutenance. L'API S3 permet de remplacer le stockage local sans réécrire la logique métier. |
| Stockage distant optionnel | Cloudflare R2 | Backend S3 compatible pour un déploiement public éventuel | R2 possède une offre gratuite adaptée à une démonstration et évite les coûts de transfert sortant direct dans les limites annoncées. Il reste optionnel afin que la mandatory fonctionne sans compte cloud ni connexion Internet. |
| Données de démonstration | Faker + script Python maison | Génération reproductible d'au moins 500 profils fictifs | Le sujet exige au minimum 500 profils distincts dans la base lors de l'évaluation. Faker génère des identités fictives tandis qu'un script Python contrôlé applique nos règles métier et exécute du SQL manuel avec psycopg, sans ORM. |
| Tests backend | pytest | Tests unitaires et d'intégration Python | Le sujet interdit toute erreur, warning, notice ou faille de sécurité. pytest permet de vérifier les règles métier, les requêtes SQL, les autorisations et les validations de façon reproductible. |
| Tests frontend | Vitest + Testing Library | Tests des composants React | Ces outils permettent de vérifier formulaires, états, filtres et interactions utilisateur afin de limiter les erreurs côté client explicitement interdites par le sujet. |
| Tests end-to-end | Playwright | Parcours complets et scénarios multi-utilisateurs | Matcha nécessite des scénarios impliquant deux utilisateurs, deux sessions, des matchs et du temps réel. Playwright permet de les automatiser ; la validation finale utilisera explicitement Google Chrome et Firefox récents, comme demandé par le sujet, et pas uniquement Chromium. |
| Environnement local | Podman + Podman Compose | Conteneurs rootless pour Flask, PostgreSQL, Mailpit et les services locaux | Le sujet n'impose aucun moteur de conteneurs et laisse le choix du serveur. Podman est gratuit, open source, compatible avec le format Compose et permet une installation reproductible avec une isolation rootless adaptée aux exigences de sécurité. |
| Automatisation | GNU Make + `Makefile` | Interface unique pour construire, configurer, lancer, tester et arrêter le projet | Le sujet exige un projet installable et reproductible. Un `Makefile` documente les commandes, réduit les erreurs de configuration pendant la soutenance et orchestre Podman sans masquer le fonctionnement de l'application. |
| Qualité Python | Ruff | Lint et formatage Python | Le sujet exige zéro erreur, warning ou notice côté serveur. Ruff détecte en amont les erreurs courantes et maintient un code Python homogène sans ajouter de dépendance d'exécution à l'application. |
| Qualité frontend | ESLint + Prettier | Lint et formatage TypeScript/React | ESLint détecte les erreurs et mauvaises pratiques susceptibles d'apparaître dans la console navigateur, tandis que Prettier maintient un format homogène. Cela soutient l'exigence de zéro erreur et warning côté client. |

### Contraintes techniques arrêtées

- Aucun ORM : pas de SQLAlchemy, Flask-SQLAlchemy, Django ORM ou équivalent.
- Toutes les requêtes SQL sont écrites manuellement avec les paramètres de psycopg.
- Aucun framework backend complet de gestion des utilisateurs ou de validation automatique.
- Flask reste responsable des routes, de la logique métier et des contrôles d'autorisation.
- React communique avec Flask par API JSON et WebSocket.
- Le frontend et le backend sont servis sous le même domaine en production.
- PostgreSQL reste la source de vérité pour les utilisateurs, messages et notifications.
- Un message ou une notification est enregistré en base avant sa diffusion en temps réel.
- Les sessions sont conservées côté serveur ; aucun jeton d'authentification ne sera stocké dans `localStorage`.
- Valkey contient seulement des données éphémères avec TTL ; PostgreSQL reste l'unique source de vérité durable de l'application.
- Flask-Session utilise Valkey comme stockage partagé et le cookie navigateur contient uniquement un identifiant de session opaque.
- Pour la soutenance, Gunicorn exécute un seul worker compatible WebSocket derrière Nginx.
- Il est interdit de lancer Socket.IO avec `gunicorn -w N`. Une évolution multi-instance exige plusieurs serveurs mono-worker, une affinité Nginx et Valkey comme bus partagé.
- Nginx sert le build React et route `/api` et `/socket.io` sous le même domaine.
- Le service public Nominatim n'est jamais utilisé pour l'autocomplétion, le seed ou le géocodage en masse ; les réponses à la demande sont mises en cache et le fournisseur est configurable.
- Les coordonnées GPS sont réduites à une précision de quartier avant stockage métier et ne sont jamais affichées telles quelles à un autre utilisateur.
- Les images entrantes acceptées sont JPEG, PNG et WebP, au maximum 5 Mio et 4096 × 4096 pixels ; SVG et GIF animé sont refusés, les métadonnées EXIF sont supprimées et l'image est réencodée.
- Les genres proposés sont homme, femme et non-binaire ; les préférences sont stockées comme un ensemble de genres recherchés.
- Une compatibilité existe uniquement si chaque utilisateur accepte le genre de l'autre ; une préférence absente est interprétée comme tous les genres, donc bisexuelle au minimum au sens du sujet.
- La popularité publique est un entier de 0 à 100 calculé à partir des likes actifs, matchs actifs et visiteurs uniques récents selon la formule documentée ci-dessous.
- Les suggestions donnent une priorité absolue à la même zone, puis combinent 50 % de proximité, 30 % de tags communs et 20 % de popularité.
- Mailpit est utilisé localement et pendant la soutenance ; Brevo SMTP est un backend de production optionnel piloté uniquement par `.env`.
- PostGIS n'est pas nécessaire pour la première version : les distances seront calculées à partir de latitude/longitude avec une requête SQL adaptée.
- Le fichier d'orchestration reste indépendant de Docker et sera nommé `compose.yml`.
- La commande principale documentée sera `podman compose`; la compatibilité avec `podman-compose` sera vérifiée selon l'environnement d'évaluation.
- Les secrets sont injectés depuis un fichier `.env` local exclu de Git, jamais écrits directement dans `compose.yml`.
- Les volumes persistants, droits rootless, réseaux internes et WebSockets doivent être testés avec Podman avant la soutenance.
- MinIO est le stockage d'objets par défaut en développement et pendant la soutenance ; Cloudflare R2 est un backend optionnel de production.
- Les buckets restent privés. Le navigateur ne reçoit jamais les identifiants S3 et n'accède à un objet qu'après un contrôle d'autorisation.
- PostgreSQL stocke les métadonnées et clés des objets, pas le contenu binaire des images.
- Le choix du backend S3 est piloté par la configuration et ne doit pas modifier la logique métier des photos.
- Le `Makefile` est le point d'entrée principal du projet et appelle explicitement Podman Compose, les migrations, le seed et les outils de test.
- Les commandes du `Makefile` doivent être non interactives, reproductibles, documentées et échouer immédiatement lorsqu'une étape échoue.
- Les cibles destructrices, notamment la suppression des volumes ou la remise à zéro de la base, doivent être séparées des commandes normales et clairement nommées.

### Architecture cible

```text
Navigateur
        │
        ▼
      Nginx
      ├── fichiers React + TypeScript + Tailwind
      ├── /api ──────────────────┐
      └── /socket.io ────────────┤
                                 ▼
                    Flask + Gunicorn + gevent
                         ├── logique métier
                         ├── Flask-Session et CSRF
                         ├── Flask-SocketIO
                         ├── Pillow
                         ├── psycopg 3 ───── PostgreSQL
                         ├── client Valkey ── Valkey
                         └── client S3 ────── MinIO
                                               │
                                               └── R2 optionnel

Entrée HTTP : Nginx sert React et proxifie Flask/Socket.IO
Services : Podman Compose + PostgreSQL + Valkey + MinIO + Mailpit
```

### Arborescence cible

```text
Matcha/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── realtime/
│   │   ├── security/
│   │   └── validators/
│   ├── tests/
│   ├── pyproject.toml
│   └── wsgi.py
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── features/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── realtime/
│   │   └── types/
│   ├── tests/
│   └── package.json
├── database/
│   ├── migrations/
│   ├── seeds/
│   └── scripts/
├── e2e/
├── compose.yml
├── Makefile
├── .env.example
├── README.md
└── TASKS.md
```

## Définition de « terminé »

Toutes les implémentations et revues doivent respecter la charte
[CODE_RULES.md](CODE_RULES.md), conçue pour garder le code simple, testable et explicable
pendant l'évaluation.
Le contrat initial des routes, événements temps réel, requêtes SQL et transactions est
centralisé dans [API_AND_QUERIES.md](API_AND_QUERIES.md).
Le schéma logique de PostgreSQL, ainsi que la séparation avec Valkey et MinIO, est défini
dans [DATA_MODEL.md](DATA_MODEL.md).
Les formats JSON, uploads, cookies, événements Socket.IO et modèles de transport à utiliser
sont définis dans [TRANSFER_MODELS.md](TRANSFER_MODELS.md).

Une tâche est terminée lorsque :

- le comportement fonctionne côté interface et côté serveur ;
- les droits d'accès sont vérifiés côté serveur ;
- les entrées invalides sont refusées proprement ;
- le cas nominal et les principaux cas d'erreur sont testés ;
- aucune erreur, aucun warning et aucune notice n'apparaît dans le serveur ou le navigateur ;
- aucune donnée sensible n'est exposée dans les réponses, les logs ou Git.

## Audit de conformité et décisions encore requises

### Résultat de l'audit

- [x] Flask respecte la définition du micro-framework donnée par le sujet.
- [x] PostgreSQL et psycopg respectent l'obligation de base gratuite et de SQL manuel sans ORM.
- [x] React et Tailwind sont des bibliothèques d'interface autorisées par le sujet.
- [x] Podman, MinIO, Mailpit et le `Makefile` n'enfreignent aucune contrainte du sujet.
- [x] La mandatory peut fonctionner entièrement hors ligne et sans service cloud payant.
- [x] Les cinq bonus du PDF ont chacun une checklist et une barrière de non-régression.
- [x] La limite obligatoire de cinq photos de profil reste séparée de la galerie bonus.
- [x] Google OAuth/OIDC reste un bonus et ne remplace pas l'authentification obligatoire.
- [x] Le document couvre les 500 profils minimum, Firefox, Chrome, mobile, sécurité et délai maximal de 10 secondes.

> Les cases cochées dans cet audit signifient que l'exigence est couverte par le plan,
> pas que son implémentation est déjà terminée.

### Matrice de traçabilité du PDF

| Exigence du sujet | Couverture dans ce document | Statut du plan |
| --- | --- | --- |
| Zéro erreur, warning ou notice client/serveur | Définition de terminé, phases 9 à 11 | Couvert |
| Micro-framework sans ORM, validateur intégré ou comptes intégrés | Stack Flask, contraintes techniques, phases 0 et 2 | Couvert |
| Base gratuite relationnelle/graphe et requêtes manuelles | PostgreSQL + psycopg, migrations SQL maison | Couvert |
| Au moins 500 profils distincts | Seed Faker reproductible de 600 profils et contrôles post-seed | Couvert |
| Firefox et Chrome récents | Playwright et validation manuelle sur les vrais navigateurs | Couvert |
| En-tête, contenu principal, pied de page et mobile | Phase 9 | Couvert |
| Validation de tous les formulaires et sécurité globale | Phases 2, 3, 9 et 10 | Couvert |
| Aucun mot de passe en clair | Argon2id, phase 3 et tests de sécurité | Couvert |
| Protection HTML/JavaScript, upload et injection SQL | Échappement React, Pillow/MinIO, SQL paramétré, phase 10 | Couvert |
| Inscription avec les cinq champs minimaux | Phase 3.1 | Couvert |
| Refus des mots anglais courants | Liste locale versionnée et tests dédiés | Couvert |
| E-mail de vérification avec lien unique | Phase 3.1 et 3.2 | Couvert |
| Connexion username/mot de passe | Phase 3.2 | Couvert |
| Mot de passe oublié par e-mail | Phase 3.3 | Couvert |
| Déconnexion en un clic depuis toute page | Phases 3.2 et 9 | Couvert |
| Profil : genre, préférence, bio, tags réutilisables et cinq photos maximum | Phases 1 et 4 | Couvert |
| Une photo désignée comme photo principale | Contraintes SQL et phase 4.2 | Couvert |
| Modification permanente du profil, nom, prénom et e-mail | Phase 4.1 | Couvert |
| Voir les visiteurs et les likes reçus | Phase 4.4 | Couvert |
| Popularité publique pour chaque utilisateur | Phases 0.3 et 4.4 | Couvert, formule à décider |
| GPS jusqu'au quartier avec consentement explicite | Phase 4.3 et stratégie catalogue/Nominatim | Couvert |
| Localisation manuelle obligatoire en cas de refus GPS | Phase 4.3 | Couvert |
| Modification de la localisation à tout moment | Phase 4.3 | Couvert |
| Suggestions compatibles, bisexualité et défaut bisexuel | Phase 5.1 | Couvert, matrice à décider |
| Suggestions par distance, tags et popularité avec priorité locale | Phase 5.2 | Couvert, score à décider |
| Tri et filtre des suggestions selon les quatre critères | Phase 5.3 | Couvert |
| Recherche avancée multi-critères, tri et filtre | Phase 5.4 | Couvert |
| Afficher toutes les informations sauf e-mail et mot de passe | Phase 6.1 | Couvert |
| Enregistrer chaque consultation dans l'historique | Phase 6.2 | Couvert |
| Like interdit sans photo, match mutuel et connexion | Phase 6.3 | Couvert |
| Unlike, fin du chat et fin des notifications futures | Phase 6.3 | Couvert |
| Statut en ligne ou date/heure de dernière connexion | Phases 1.1, 6.1 et temps réel | Couvert |
| Signaler un faux compte | Phase 6.4 | Couvert |
| Bloquer : retrait recherche, notifications et chat | Phase 6.4 | Couvert |
| Afficher like reçu, match et actions unlike/déconnexion | Phases 6.1 et 6.3 | Couvert |
| Chat réservé aux matchs et délai maximal de 10 secondes | Phase 7 | Couvert |
| Nouveau message visible depuis toute page | Phases 7, 8 et 9 | Couvert |
| Les cinq notifications temps réel obligatoires | Phase 8 | Couvert |
| Notifications non lues visibles depuis toute page | Phases 8 et 9 | Couvert |
| Secrets exclusivement dans `.env` exclu de Git | Phases 0, 2, 10 et 11 | Couvert |
| Seul le contenu du dépôt est évalué | Phase 11 et installation depuis clone propre | Couvert |
| Bonus évalués uniquement si mandatory parfaite | Porte de validation des bonus | Couvert |

### Choix bloquants à fermer avant l'implémentation

Ces points ne contredisent pas le sujet, mais une décision explicite est nécessaire avant
de construire les composants concernés :

- [x] Utiliser Flask-Session avec Valkey pour les sessions partagées et leur invalidation ; ne jamais utiliser la mémoire locale d'un worker.
- [x] Utiliser Gunicorn avec un worker gevent compatible WebSocket et Flask-SocketIO.
- [x] Utiliser un seul worker temps réel pour la première version et la soutenance ; conserver Valkey comme bus Pub/Sub et préparer l'évolution multi-instance sans utiliser `gunicorn -w N`.
- [x] Utiliser Nginx pour servir le build React, le fallback SPA et router `/api` et `/socket.io` sous un même domaine.
- [x] Utiliser un catalogue local ville/quartier pour la saisie et la démonstration hors ligne ; utiliser Nominatim uniquement comme enrichissement à la demande, interchangeable, limité et mis en cache.
- [x] Utiliser une liste locale versionnée de mots anglais courants, avec licence et provenance documentées, sans appel réseau au moment de l'inscription.
- [x] Utiliser les genres homme, femme et non-binaire, avec préférences représentées comme un ensemble de genres recherchés et compatibilité obligatoirement mutuelle.
- [x] Utiliser la formule de popularité et le score multi-critères définis dans la section « Règles métier validées ».
- [x] Utiliser les durées de sécurité définies dans la section « Durées validées » et les rendre configurables avec des valeurs sûres par défaut.
- [x] Accepter JPEG, PNG et WebP, limiter chaque entrée à 5 Mio et 4096 × 4096 pixels, refuser SVG/GIF animé, supprimer EXIF et réencoder avec Pillow avant MinIO.
- [x] Générer localement les avatars de seed avec Pillow et utiliser seulement quelques portraits IA entièrement synthétiques pour les comptes principaux de démonstration.
- [x] Utiliser Mailpit localement et Brevo SMTP comme fournisseur de production optionnel, sans dépendance obligatoire à un service externe.

### Règles métier validées

#### Genres et préférences

- Genres proposés : `man`, `woman`, `non_binary`.
- Une préférence explicitement renseignée est un ensemble non vide de genres recherchés.
- La valeur peut rester absente ; sa valeur métier effective est alors l'ensemble de tous les genres.
- Une personne est éligible uniquement si son genre appartient aux préférences de l'autre dans les deux sens.
- Les libellés hétérosexuel, homosexuel et bisexuel peuvent être dérivés pour l'interface, mais l'ensemble de préférences reste la source de vérité.
- Toute modification de genre ou de préférences recalcule immédiatement l'éligibilité des suggestions et recherches sans supprimer l'historique existant.
- Un match existant reste défini uniquement par les likes mutuels et ne se termine que par unlike ou blocage, conformément au sujet.
- Le traitement des préférences sexuelles exige un consentement explicite, spécifique, informé, horodaté et versionné, non coché par défaut.
- Un utilisateur consentant qui laisse sa préférence vide est traité comme intéressé par tous les genres, conformément au sujet.
- Le retrait du consentement efface la préférence stockée et suspend suggestions, recherche et matching jusqu'à un nouveau consentement ; il ne détruit pas automatiquement les matchs existants.

#### Âge et complétude du profil

- L'application est réservée aux personnes âgées d'au moins 18 ans.
- La date de naissance est validée côté serveur et l'inscription d'un mineur est refusée avant création du compte.
- Seul l'âge calculé est affiché publiquement ; le frontend ne fournit jamais un âge faisant autorité.
- Un profil complet possède : date de naissance valide, genre, biographie non vide, au moins un tag, et localisation GPS consentie ou localisation manuelle.
- La préférence peut être absente et vaut alors tous les genres si le consentement sensible est actif.
- Les photos sont facultatives pour la complétude, puisque le sujet autorise jusqu'à cinq photos.
- Sans photo principale, l'utilisateur peut consulter et rechercher mais ne peut pas liker.
- Un profil incomplet, inactif ou non vérifié est exclu des suggestions et recherches et n'est pas consultable directement par un autre membre.

#### Unlike, blocage et suppression

- Un unlike désactive le like sortant, termine le match éventuel, désactive immédiatement tout nouvel envoi de message et notifie obligatoirement l'ancien match.
- Après unlike de A envers B, les nouvelles notifications provenant de B vers A sont supprimées jusqu'à un nouveau match mutuel.
- La conversation passée reste disponible en lecture seule aux deux utilisateurs, avec possibilité de la masquer localement.
- Un nouveau match exige toujours deux nouveaux likes actifs.
- Un blocage supprime les likes actifs entre les deux utilisateurs, termine le match et interdit recherche, suggestion, visite, like, chat et notification dans les deux sens.
- La conversation devient inaccessible dans les deux sens après blocage.
- Un déblocage ne restaure ni likes, ni match, ni conversation active.
- La suppression de compte exige le mot de passe ou une réauthentification récente.
- La suppression révoque sessions et sockets, masque immédiatement le profil, puis supprime compte, profil, consentements, préférences, localisation, photos/objets, tags associés, likes, matchs, visites, notifications, messages et identités externes.
- Un signalement peut être conservé temporairement uniquement sous forme anonymisée si sa finalité de sécurité le justifie ; sinon il est supprimé.
- Aucune donnée ou empreinte ne doit permettre de reconstruire le profil supprimé.

#### Visites et comptes inactifs

- Chaque consultation humaine réelle est enregistrée ; les rafraîchissements techniques et appels automatiques ne créent pas de visite.
- Une seule notification de visite par paire visiteur/profil est envoyée sur une fenêtre glissante de 24 heures.
- La popularité compte un visiteur unique sur sa fenêtre de 30 jours.
- Les événements détaillés de visite sont supprimés automatiquement après 90 jours.
- Après deux ans sans connexion, le compte est averti puis supprimé après un délai de grâce de 30 jours en l'absence de reconnexion.
- Les durées de rétention sont documentées, configurables et appliquées par une tâche planifiée.

#### Popularité publique

La note est un entier arrondi et borné entre 0 et 100 :

```text
popularite =
    50 × L / (L + 10)
  + 30 × M / (M + 5)
  + 20 × V / (V + 25)
```

- `L` est le nombre de likes actifs reçus d'utilisateurs uniques.
- `M` est le nombre de matchs actifs.
- `V` est le nombre de visiteurs uniques des 30 derniers jours.
- Les visites répétées d'un même utilisateur ne comptent qu'une fois dans la fenêtre.
- Les interactions supprimées, bloquées ou invalides sont exclues.
- Un unlike retire naturellement le like actif et éventuellement le match actif du calcul.
- Un signalement non vérifié ne pénalise jamais automatiquement la popularité.
- Le score est calculé côté serveur depuis les données métier, jamais accepté depuis le frontend.

#### Suggestions

Après compatibilité, blocages et complétude, le tri par défaut utilise :

```text
proximite  = max(0, 1 - distance_km / 100)
tags       = min(nombre_tags_communs / 5, 1)
popularite = note_popularite / 100

score = 0.50 × proximite + 0.30 × tags + 0.20 × popularite
```

- Les profils de la même ville ou du même quartier passent toujours avant ceux des autres zones.
- Dans chaque groupe géographique, le score décroissant détermine l'ordre.
- En cas d'égalité : distance croissante, puis identifiant stable croissant.
- Un tri explicitement choisi par l'utilisateur remplace l'ordre par défaut, mais jamais les règles de compatibilité et de blocage.

### Durées validées

| Élément | Valeur par défaut |
| --- | ---: |
| Jeton d'activation du compte | 24 heures |
| Jeton de réinitialisation du mot de passe | 30 minutes |
| Jeton de validation d'une nouvelle adresse e-mail | 1 heure |
| Expiration de session après inactivité | 30 minutes |
| Durée absolue d'une session | 8 heures |
| Renouvellement de l'identifiant de session | 30 minutes |
| Fenêtre du statut « en ligne » | 2 minutes |
| URL MinIO/R2 signée | 5 minutes |
| Objet temporaire de téléversement | 1 heure |
| Clé d'idempotence d'un événement Socket.IO | 24 heures |
| Notification répétée d'une même visite | 24 heures |
| Historique détaillé des visites | 90 jours |
| Inactivité avant avertissement du compte | 2 ans |
| Grâce après avertissement d'inactivité | 30 jours |

- Toutes les expirations sont appliquées côté serveur.
- Les durées sont configurables par `.env`, avec validation et refus des valeurs non sûres en production.
- Tous les jetons sont aléatoires, stockés sous forme de hash, à usage unique et invalidés après utilisation.
- L'expiration d'une session ferme aussi la connexion Socket.IO correspondante.
- Le client peut prévenir l'utilisateur avant expiration, mais ne décide jamais de prolonger lui-même une session.

### Règles d'arbitrage en cas d'ambiguïté

- La conformité au PDF prime sur un choix d'architecture ou un bonus.
- Une fonctionnalité obligatoire ne doit jamais dépendre de Google, Cloudflare R2 ou d'un autre service externe.
- Une validation frontend ne remplace jamais une validation backend.
- Une règle visible dans React doit être vérifiée à nouveau par Flask.
- Les états like, match, unlike et blocage sont décidés transactionnellement côté serveur.
- La préférence explicite peut être absente, mais sa valeur métier effective est alors l'ensemble de tous les genres si le consentement sensible est actif, conformément au sujet.
- Un profil incomplet peut accéder à son compte et le compléter, mais ne peut pas utiliser les fonctions nécessitant les données manquantes.
- Toute donnée de profil disponible est publique sauf l'e-mail, le mot de passe, les secrets, les coordonnées GPS précises et les données explicitement protégées pour des raisons de sécurité.

---

## Phase 0 — Décisions techniques et organisation (Obligatoire)

### 0.1 Choisir l'architecture

- [x] Choisir Python et Flask comme langage et micro-framework backend autorisé par le sujet.
- [x] Choisir React, TypeScript et Vite pour le frontend.
- [x] Choisir PostgreSQL comme base de données relationnelle gratuite.
- [x] Choisir psycopg 3 et imposer des requêtes SQL manuelles sans ORM.
- [x] Choisir Flask-SocketIO et les WebSockets pour le temps réel.
- [x] Choisir Valkey pour les sessions partagées, la présence, le rate limiting et le bus Socket.IO.
- [x] Choisir Flask-Session avec Valkey pour les sessions serveur.
- [x] Choisir Nginx pour servir React et proxifier Flask et Socket.IO sous un même domaine.
- [x] Choisir un worker Gunicorn WebSocket unique pour la soutenance.
- [x] Choisir SMTP et Mailpit pour tester les e-mails en développement.
- [x] Choisir Brevo SMTP comme fournisseur de production optionnel.
- [x] Choisir Tailwind CSS pour construire l'interface responsive.
- [x] Choisir les sessions serveur et les cookies sécurisés pour l'authentification.
- [x] Choisir Podman et Podman Compose pour l'environnement de développement rootless.
- [x] Choisir GNU Make comme interface unique d'automatisation du projet.
- [x] Définir l'arborescence cible du backend, du frontend, des scripts SQL et des tests.
- [x] Documenter ces décisions dans le README.

### 0.2 Préparer le dépôt

- [x] Créer un `.gitignore` adapté à la stack.
- [x] Créer un `.env.example` sans secret avec toutes les variables attendues.
- [x] Exclure `.env`, les clés, les fichiers temporaires et les médias locaux de Git.
- [x] Ajouter les commandes d'installation, de migration, de seed, de test et de lancement.
- [x] Fixer les versions des dépendances.
- [x] Choisir au scaffold des versions majeures stables et compatibles, puis verrouiller toutes les versions exactes dans les lockfiles.
- [x] Épingler les images Podman par version et digest pour la soutenance ; interdire le tag `latest`.
- [ ] Tester explicitement toute mise à jour avant de modifier une version verrouillée.
- [x] Initialiser le backend Flask avec un `pyproject.toml` et ses dépendances.
- [x] Initialiser le frontend React/TypeScript avec Vite et Tailwind CSS.
- [x] Configurer Ruff côté Python.
- [x] Configurer ESLint et Prettier côté React/TypeScript.
- [ ] Configurer pytest, Vitest, Testing Library et Playwright.
- [x] Créer `compose.yml` avec Nginx, Flask, PostgreSQL, Valkey, MinIO et Mailpit.
- [x] Ajouter Valkey à `compose.yml`, sans exposition publique de son port.
- [x] Configurer Valkey avec authentification locale, limites mémoire, politique d'éviction adaptée et healthcheck.
- [x] Ajouter Nginx à `compose.yml` comme seul point d'entrée HTTP exposé.
- [x] Configurer Nginx pour servir le build React et le fallback des routes SPA.
- [x] Configurer les proxys `/api` et `/socket.io`, y compris les en-têtes d'upgrade WebSocket et les timeouts.
- [x] Ajouter MinIO à `compose.yml` avec un volume persistant compatible rootless.
- [x] Ajouter une vérification de santé MinIO et garantir que l'application attend sa disponibilité.
- [x] Créer automatiquement les buckets privés requis sans rendre les objets publics.
- [x] Ajouter au `Makefile` des cibles sûres pour initialiser et vérifier le stockage d'objets.
- [x] Configurer les volumes PostgreSQL persistants avec des droits compatibles avec Podman rootless.
- [x] Configurer le réseau Compose et utiliser les noms des services pour les communications internes.
- [x] Exposer uniquement les ports nécessaires à l'hôte.
- [ ] Vérifier le fonctionnement de Flask-SocketIO et des WebSockets à travers le réseau Podman.
- [x] Configurer le choix validé Gunicorn/gevent avec exactement un worker WebSocket pour la première version.
- [ ] Configurer Flask-SocketIO avec Valkey comme bus Pub/Sub même en mono-worker, puis tester la diffusion.
- [ ] Documenter que le multi-instance exige plusieurs serveurs mono-worker derrière Nginx avec affinité, jamais `gunicorn -w N`.
- [ ] Ajouter des healthchecks distincts pour Nginx/HTTP, PostgreSQL, Valkey, MinIO et la disponibilité du canal temps réel.
- [ ] Tester et documenter `podman compose`, puis vérifier si `podman-compose` doit aussi être supporté.
- [x] Créer un `Makefile` auto-documenté avec une cible `help` utilisée par défaut.
- [x] Ajouter `make setup` pour vérifier les prérequis et préparer `.env` sans écraser un fichier existant.
- [ ] Ajouter `make config-check` pour refuser le démarrage si une variable obligatoire manque ou conserve une valeur non sûre.
- [x] Ajouter `make build` pour construire toutes les images avec les configurations requises.
- [ ] Ajouter `make up` pour démarrer l'application et ses dépendances.
- [ ] Ajouter `make start` comme parcours complet de construction, migration puis démarrage.
- [ ] Ajouter `make down` et `make restart` pour gérer proprement les services.
- [ ] Ajouter `make logs` et des variantes ciblées pour diagnostiquer les services.
- [x] Ajouter `make ps` et `make health` pour vérifier l'état de l'environnement.
- [x] Ajouter `make migrate` pour appliquer les fichiers SQL dans l'ordre.
- [x] Ajouter `make seed` pour générer les 500 profils de démonstration.
- [ ] Ajouter `make test`, `make test-backend`, `make test-frontend` et `make test-e2e`.
- [ ] Ajouter `make lint`, `make format` et `make check` pour les contrôles avant rendu.
- [ ] Ajouter `make shell-backend` et `make db-shell` pour le diagnostic local.
- [ ] Ajouter une cible destructive explicite `make reset-db` qui demande confirmation avant de supprimer les données locales.
- [ ] Ajouter `make clean` uniquement pour les artefacts régénérables ; ne pas supprimer les volumes ou `.env` implicitement.
- [ ] Permettre de surcharger les variables utiles sans coder de secret dans le `Makefile`.
- [ ] Vérifier toutes les cibles depuis un clone propre et documenter leur usage dans le README.
- [ ] Préparer les environnements développement et test.
- [x] Créer une configuration SMTP générique avec `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `SMTP_FROM_EMAIL` et `SMTP_FROM_NAME`.
- [x] Pointer la configuration locale vers Mailpit et permettre l'activation optionnelle de Brevo sans modifier le code.
- [ ] Refuser le démarrage en mode production si les paramètres SMTP obligatoires ou TLS sont invalides.
- [ ] Ajouter une gestion centralisée des erreurs et des logs sans données sensibles.

### 0.3 Définir les règles métier avant de coder

- [x] Définir les genres et préférences supportés sans coder les règles en dur dans l'interface.
- [x] Définir la compatibilité mutuelle entre genres et préférences sexuelles.
- [x] Confirmer qu'une préférence absente est traitée comme tous les genres, donc bisexuelle au minimum.
- [x] Définir la formule publique et cohérente de la note de popularité.
- [x] Définir le score de suggestion combinant distance, tags communs et popularité.
- [x] Définir précisément les effets d'un unlike, d'un blocage et d'une suppression de compte.
- [x] Définir la durée de vie des jetons d'activation et de réinitialisation.
- [x] Définir les formats, tailles et dimensions autorisés pour les photos.
- [x] Fixer l'âge minimum à 18 ans et garantir que l'âge affiché est dérivé côté serveur de la date de naissance.
- [x] Définir à deux minutes la fenêtre d'activité du statut « en ligne » et mettre à jour la dernière connexion côté serveur.
- [x] Définir les critères exacts d'un profil complet et les fonctions interdites tant qu'il est incomplet.
- [x] Définir le comportement transactionnel et directionnel des notifications après unlike et blocage.

---

## Phase 1 — Base de données (Obligatoire)

### 1.1 Concevoir le schéma

- [ ] Créer la table des utilisateurs : identifiant, username, e-mail, prénom, nom, hash du mot de passe, activation et dates.
- [ ] Ajouter les données de profil : date de naissance, genre et biographie ; stocker les genres recherchés dans une table de préférences séparée et calculer la complétude.
- [ ] Créer les tables de localisation et de consentement GPS.
- [ ] Créer une table de consentements générique contenant utilisateur, finalité, version du texte, état et horodatages de consentement/retrait.
- [ ] Stocker séparément les consentements explicites pour préférences sexuelles et géolocalisation GPS.
- [ ] Créer la table des photos avec ordre et indicateur de photo principale.
- [ ] Créer les tables des tags et de l'association utilisateur-tag.
- [ ] Créer la table des likes avec contrainte d'unicité par paire dirigée.
- [ ] Créer une table `matches` dédiée avec paire canonique unique, statut, dates et auteur de fin.
- [ ] Autoriser un match actif uniquement lorsque les deux likes dirigés sont actifs.
- [ ] Créer la table de visites de profil avec visiteur, profil visité et date.
- [ ] Créer les tables de conversations et messages.
- [ ] Créer la table des notifications avec type, contenu, date et statut lu/non lu.
- [ ] Créer la table des blocages.
- [ ] Créer la table des signalements de faux comptes.
- [ ] Créer les tables de jetons d'activation et de réinitialisation.
- [ ] Stocker la dernière activité ou dernière connexion nécessaire au statut en ligne.

### 1.2 Contraintes et performances

- [ ] Ajouter les clés étrangères et appliquer la stratégie `CASCADE`, `RESTRICT` et transaction métier validée.
- [ ] Utiliser `CASCADE` seulement pour les données exclusivement possédées : profil, associations de tags, photos et jetons.
- [ ] Utiliser `RESTRICT` pour les données de référence partagées telles que les tags globaux.
- [ ] Traiter explicitement dans une transaction métier likes, matchs, messages, visites, notifications, blocages et suppression de compte.
- [ ] Créer une table outbox pour synchroniser après commit les suppressions d'objets MinIO et autres effets externes.
- [ ] Ajouter les contraintes d'unicité sur username et e-mail normalisés.
- [ ] Ajouter les contraintes empêchant de se liker, se visiter ou se bloquer soi-même lorsque pertinent.
- [ ] Ajouter des index pour recherche, tags, localisation, likes, messages et notifications.
- [ ] Garantir qu'un utilisateur possède au maximum cinq photos et exactement une photo principale dès qu'au moins une photo existe.
- [ ] Garantir l'intégrité des paires de blocage et de connexion.
- [ ] Écrire des migrations reproductibles et une commande de remise à zéro pour l'environnement local.

### 1.3 Données de démonstration

- [ ] Ajouter Faker aux dépendances de développement Python uniquement.
- [ ] Écrire un script Python de seed utilisant psycopg et des requêtes SQL manuelles, sans ORM.
- [ ] Attribuer un `seed_batch_id` stable à toutes les données et objets générés.
- [ ] Générer au minimum 500 profils fictifs distincts ; viser 600 profils pour garder une marge de sécurité.
- [ ] Utiliser une graine aléatoire configurable avec une valeur stable par défaut afin de reproduire exactement une démonstration.
- [ ] Garantir l'unicité des usernames et des adresses e-mail fictives.
- [ ] Utiliser uniquement des domaines d'e-mail réservés à l'exemple, comme `example.test`, sans envoyer d'e-mail aux profils fictifs.
- [ ] Générer des dates de naissance produisant uniquement des utilisateurs majeurs et des âges variés.
- [ ] Répartir les genres et ensembles de genres recherchés afin de tester compatibilités hétérosexuelles, homosexuelles, bisexuelles et préférence absente.
- [ ] Créer des profils répartis dans plusieurs villes et quartiers, avec des coordonnées cohérentes, afin de démontrer proximité, distance, tri et filtrage.
- [ ] Concentrer une partie des profils dans une même zone pour démontrer la priorité géographique.
- [ ] Créer un catalogue de tags réutilisables et attribuer plusieurs tags à chaque profil.
- [ ] Préparer des profils avec beaucoup, peu et aucun tag commun pour tester le classement.
- [ ] Générer des biographies fictives non offensantes et compatibles avec les limites de taille.
- [ ] Générer différents niveaux de complétude uniquement si les profils incomplets sont volontairement nécessaires aux tests.
- [ ] Utiliser un mot de passe de démonstration conforme, haché avec Argon2id ; ne jamais insérer un mot de passe en clair en base.
- [ ] Marquer les profils de seed comme activés, sauf un petit ensemble réservé aux tests d'activation.
- [ ] Générer entre une et cinq photos valides par profil et désigner exactement une photo principale lorsque le profil possède des photos.
- [ ] Générer avec Pillow des avatars locaux déterministes à partir de la graine, sans photo réelle ni appel réseau.
- [ ] Exporter les avatars en JPEG ou WebP et les faire passer par le même pipeline MinIO que les photos utilisateur.
- [ ] Générer un petit ensemble de portraits IA entièrement synthétiques pour les comptes principaux de démonstration.
- [ ] Conserver les portraits synthétiques dans `database/seeds/assets/` avec une note décrivant leur méthode et leur date de génération.
- [ ] Ne jamais télécharger ou utiliser une photo de personne réelle sans autorisation explicite et traçable.
- [ ] Produire éventuellement des variantes autorisées par recadrage ou arrière-plan sans prétendre qu'elles représentent des personnes distinctes.
- [ ] Préparer quelques profils sans photo principale afin de démontrer l'interdiction de liker.
- [ ] Générer des likes unilatéraux, des likes réciproques et des profils sans like.
- [ ] Générer des matchs cohérents sans créer de doublon ni de connexion sans like réciproque.
- [ ] Générer des visites de profils datées et cohérentes.
- [ ] Générer des conversations uniquement entre utilisateurs réellement matchés.
- [ ] Générer des messages lus et non lus dans certaines conversations.
- [ ] Générer les différents types de notifications requis avec des états lus et non lus.
- [ ] Générer quelques blocages et vérifier qu'ils neutralisent recherche, notification et chat selon les règles métier.
- [ ] Générer quelques signalements de faux comptes pour tester leur enregistrement.
- [ ] Générer plusieurs scores de popularité à partir de la formule métier, sans injecter de valeurs incohérentes.
- [ ] Prévoir au moins cinq comptes de démonstration connus couvrant : nouveau profil, profil complet, like reçu, match avec conversation et utilisateur bloqué.
- [ ] Stocker les identifiants de démonstration dans la documentation locale prévue à cet effet, sans secret réel.
- [ ] Afficher à la fin du seed le nombre de profils, photos, tags, likes, matchs, messages et notifications créés.
- [ ] Ajouter des contrôles automatiques après le seed : au moins 500 profils, aucune relation orpheline et respect des contraintes d'unicité.
- [ ] Rendre le seed idempotent avec des upserts déterministes fondés sur la graine et le `seed_batch_id`.
- [ ] Ajouter `make seed-reset` pour supprimer uniquement le batch de démonstration et ses objets MinIO, jamais un compte réel.
- [ ] Exécuter les insertions de seed dans une transaction lorsque les dépendances le permettent et contrôler les effets MinIO via l'outbox.
- [ ] Vérifier qu'une seconde exécution ne crée ni doublons ni état incohérent.
- [ ] Ajouter `make seed` pour le jeu de données standard reproductible.
- [ ] Ajouter `make seed-demo` pour préparer les comptes et scénarios utilisés pendant la soutenance.
- [ ] Ajouter une option documentée pour choisir le nombre de profils et la graine sans modifier le code.

---

## Phase 2 — Socle backend et sécurité (Obligatoire)

### 2.1 API et validation

- [ ] Préfixer toutes les routes HTTP métier par `/api/v1`.
- [ ] Utiliser uniquement JSON pour l'API, sauf transfert contrôlé de fichiers.
- [ ] Utiliser `{ "data": ..., "meta": ... }` pour les succès.
- [ ] Utiliser `{ "error": { "code": ..., "message": ..., "fields": ... } }` pour les erreurs.
- [ ] Représenter toutes les dates en UTC au format ISO 8601.
- [ ] Utiliser des UUID comme identifiants publics et ne jamais exposer les clés internes inutiles.
- [ ] Paginer les listes à 20 éléments par défaut et 100 maximum avec un ordre stable.
- [ ] Définir et documenter les routes, codes HTTP, paramètres, formats et autorisations avant leur implémentation.
- [ ] Valider chaque donnée côté serveur, même si elle est déjà validée côté client.
- [ ] Normaliser username, e-mail, tags et textes avant stockage.
- [ ] Utiliser exclusivement des requêtes paramétrées contre les injections SQL.
- [ ] Échapper correctement les données lors de leur affichage contre les XSS.
- [ ] Limiter la taille de tous les champs et corps de requête.
- [ ] Retourner des erreurs compréhensibles sans stack trace ni information interne.

### 2.2 Sessions et autorisations

- [ ] Configurer Flask-Session avec Valkey comme stockage partagé des sessions serveur.
- [ ] Isoler par préfixes les clés de session, présence, rate limiting et Pub/Sub.
- [ ] Définir un TTL explicite sur toutes les clés Valkey persistables et un nettoyage automatique.
- [ ] Ne jamais traiter Valkey comme source de vérité des comptes, likes, matchs, messages ou notifications.
- [ ] Mettre en place l'authentification et la rotation de session après connexion.
- [ ] Stocker seulement un identifiant de session opaque dans le cookie, jamais les données d'authentification complètes.
- [ ] Configurer les cookies `HttpOnly`, `Secure` en production et `SameSite` correctement.
- [ ] Ajouter obligatoirement une protection CSRF à toutes les requêtes d'écriture authentifiées par cookie.
- [ ] Vérifier l'authentification sur toutes les routes privées.
- [ ] Vérifier l'identité et les autorisations sur chaque ressource modifiée.
- [ ] Invalider correctement la session à la déconnexion.
- [ ] Invalider toutes les sessions concernées après changement de mot de passe ou compromission.
- [ ] Nettoyer les sessions expirées et empêcher leur rejeu.
- [ ] Implémenter avec Valkey un contrôle de débit atomique sur connexion, inscription, e-mails, likes, messages et signalements.

### 2.3 Téléversement sécurisé

- [ ] Autoriser uniquement les formats d'image explicitement choisis.
- [ ] Vérifier le type réel du fichier, pas seulement son extension ou son MIME déclaré.
- [ ] Limiter la taille et les dimensions des images.
- [ ] Réencoder les images côté serveur pour neutraliser les contenus inattendus.
- [ ] Générer les noms de fichiers côté serveur.
- [ ] Stocker les fichiers hors d'un emplacement exécutable.
- [ ] Empêcher les traversées de chemin et les écrasements de fichiers.
- [ ] Supprimer proprement un média devenu inutilisé.

### 2.4 Stockage d'objets S3 compatible

- [ ] Créer une interface de stockage indépendante du fournisseur : déposer, lire, vérifier et supprimer un objet.
- [ ] Implémenter MinIO comme backend par défaut via une bibliothèque cliente S3 compatible.
- [ ] Prévoir Cloudflare R2 comme backend optionnel sans dépendance obligatoire au cloud.
- [ ] Configurer endpoint, région, bucket, access key et secret key uniquement avec `.env`.
- [ ] Ajouter toutes les variables attendues dans `.env.example` sans secret réel.
- [ ] Utiliser des identifiants MinIO de développement non triviaux et refuser les valeurs par défaut non sûres en production.
- [ ] Créer exactement trois buckets privés : `profile-photos`, `gallery` et `temporary`.
- [ ] Ne jamais exposer les clés MinIO ou R2 au frontend, aux URLs, aux logs ou à Git.
- [ ] Faire transiter chaque téléversement par Flask pour appliquer authentification, quotas et validation Pillow.
- [ ] Générer des clés d'objet aléatoires non prédictibles, sans reprendre le nom fourni par l'utilisateur.
- [ ] Stocker dans PostgreSQL la clé, le bucket, le propriétaire, le type, le format, les dimensions, la taille et les dates.
- [ ] Ne jamais stocker directement les binaires des images dans PostgreSQL.
- [ ] Faire vérifier par Flask l'authentification, le blocage, la visibilité et la propriété avant tout accès à un objet.
- [ ] Après autorisation, retourner une URL MinIO/R2 signée valable cinq minutes.
- [ ] Ne jamais créer d'URL signée avant d'avoir vérifié blocage, visibilité et droit d'accès.
- [ ] Fixer les URLs signées à cinq minutes et empêcher leur mise en cache publique lorsque nécessaire.
- [ ] Utiliser des règles CORS minimales si un accès direct signé est retenu.
- [ ] Garantir la cohérence entre PostgreSQL et le bucket lors d'un ajout, remplacement ou échec de téléversement.
- [ ] Supprimer l'ancien objet après remplacement réussi d'une photo.
- [ ] Supprimer les objets lors de la suppression d'une photo, galerie ou compte.
- [ ] Ajouter un processus contrôlé de nettoyage des objets temporaires et orphelins.
- [ ] Supprimer automatiquement les objets du bucket `temporary` après une heure.
- [ ] Consommer l'outbox PostgreSQL pour rendre les suppressions MinIO réessayables et idempotentes.
- [ ] Ne jamais supprimer un objet encore référencé par une ligne valide en base.
- [ ] Sauvegarder et restaurer ensemble les métadonnées PostgreSQL et les données MinIO.
- [ ] Vérifier que les images persistent après `make down`, `make up` et redémarrage de la machine.
- [ ] Vérifier que `make clean` ne supprime ni bucket, ni volume MinIO, ni photo utilisateur.
- [ ] Réserver la suppression des données MinIO à une cible destructive explicite avec confirmation.
- [ ] Tester fichier invalide, objet absent, stockage indisponible, quota dépassé et suppression partielle.
- [ ] Tester qu'un utilisateur ne peut ni lire, remplacer, ni supprimer l'objet d'un autre utilisateur.
- [ ] Tester le seed avec MinIO et vérifier que toutes les photos générées sont accessibles.
- [ ] Vérifier que toute la mandatory fonctionne hors ligne avec MinIO, sans Cloudflare R2.
- [ ] Documenter la configuration MinIO locale et la bascule optionnelle vers R2.

---

## Phase 3 — Inscription et authentification (Obligatoire)

### 3.1 Inscription

- [ ] Créer le formulaire avec les cinq champs minimaux du sujet — e-mail, username, nom, prénom et mot de passe — plus la date de naissance nécessaire à la règle 18+.
- [x] Refuser côté serveur toute date de naissance indiquant moins de 18 ans avant insertion du compte.
- [x] Valider le format et l'unicité de l'e-mail et du username.
- [x] Imposer une politique de mot de passe sécurisé.
- [x] Refuser les mots anglais courants comme mot de passe.
- [x] Ajouter le fichier local de mots anglais courants avec sa source, sa version, sa licence et son checksum documentés.
- [x] Comparer de manière insensible à la casse et après normalisation Unicode.
- [x] Tester des mots anglais courants, variantes de casse et entrées Unicode sans journaliser le mot de passe.
- [x] Hacher tous les mots de passe avec le choix validé Argon2id via `argon2-cffi`.
- [x] Ne jamais stocker ni journaliser le mot de passe en clair.
- [x] Créer le compte inactif et un jeton d'activation aléatoire, expirant et à usage unique.
- [x] Envoyer l'e-mail contenant le lien unique d'activation.
- [x] Envoyer les e-mails via l'interface SMTP générique, avec timeout, gestion d'erreur et sans journaliser les identifiants.
- [ ] Ne jamais envoyer d'e-mail réel aux adresses fictives sous `example.test`.
- [ ] Afficher un résultat neutre qui ne facilite pas l'énumération des comptes.

### 3.2 Activation et connexion

- [ ] Créer la route d'activation et vérifier validité, expiration et usage du jeton.
- [ ] Activer le compte puis invalider le jeton.
- [ ] Empêcher un compte non activé de se connecter.
- [ ] Permettre la connexion avec username et mot de passe.
- [ ] Limiter les tentatives et éviter de révéler quel champ est incorrect.
- [ ] Mettre à jour le statut et la dernière activité.
- [ ] Rendre la déconnexion accessible en un clic depuis chaque page authentifiée.

### 3.3 Mot de passe oublié

- [ ] Créer le formulaire de demande de réinitialisation.
- [ ] Retourner le même message que l'e-mail existe ou non.
- [ ] Générer un jeton aléatoire, expirant et à usage unique.
- [ ] Envoyer le lien par e-mail.
- [ ] Vérifier le jeton puis appliquer la même politique au nouveau mot de passe.
- [ ] Invalider le jeton et les anciennes sessions après modification.

---

## Phase 4 — Profil et localisation (Obligatoire)

### 4.1 Compléter et modifier le profil

- [ ] Créer le parcours de complétion après la première connexion.
- [ ] Refuser l'inscription avant création du compte lorsque la date de naissance indique moins de 18 ans.
- [ ] Calculer l'âge côté serveur et ne jamais accepter un âge fourni comme valeur faisant autorité.
- [ ] Permettre de définir genre, préférences sexuelles, date de naissance et biographie.
- [ ] Recueillir avant les préférences sexuelles un consentement explicite distinct, non précoché, informé, horodaté et versionné.
- [ ] Recueillir séparément le consentement GPS ; ne jamais fusionner les deux consentements.
- [ ] Permettre de consulter et retirer chaque consentement aussi facilement qu'il a été donné.
- [ ] Après retrait du consentement aux préférences, effacer la valeur et suspendre suggestions, recherche et matching jusqu'à nouveau consentement.
- [ ] Permettre d'ajouter et retirer des tags réutilisables.
- [ ] Permettre de modifier prénom, nom et adresse e-mail.
- [ ] Lors d'une modification d'e-mail, conserver l'ancienne adresse active jusqu'à validation du lien unique envoyé à la nouvelle adresse.
- [ ] Vérifier à nouveau l'unicité de la nouvelle adresse avant de finaliser la modification.
- [ ] Permettre toutes ces modifications à tout moment.
- [ ] Afficher clairement les informations manquantes qui bloquent le matching.
- [ ] Considérer le profil complet uniquement avec majorité, genre, biographie non vide, au moins un tag et une localisation valide.
- [ ] Exclure des découvertes les comptes incomplets, inactifs et non vérifiés et rendre leur profil direct indisponible aux autres membres.
- [ ] Ajouter une suppression de compte protégée par mot de passe ou réauthentification récente.
- [ ] À la suppression, révoquer immédiatement sessions et sockets puis lancer la suppression transactionnelle et l'outbox MinIO.
- [ ] Ajouter une tâche planifiée avertissant les comptes inactifs depuis deux ans puis les supprimant après 30 jours sans reconnexion.

### 4.2 Photos

- [ ] Permettre l'ajout, l'affichage et la suppression de photos.
- [ ] Refuser une sixième photo.
- [ ] Permettre de désigner une photo comme photo de profil.
- [ ] Gérer la suppression de la photo principale sans état incohérent.
- [ ] Appliquer toutes les validations de téléversement.
- [ ] Accepter uniquement JPEG, PNG et WebP après décodage réel par Pillow.
- [ ] Refuser tout fichier supérieur à 5 Mio ou toute image dépassant 4096 × 4096 pixels.
- [ ] Refuser SVG, GIF animé et formats non retenus.
- [ ] Corriger l'orientation, supprimer les métadonnées EXIF et réencoder l'image avant stockage.
- [ ] Empêcher un utilisateur sans photo principale de liker un profil.

### 4.3 Localisation respectueuse du consentement

- [ ] Demander explicitement l'autorisation avant d'appeler la géolocalisation du navigateur.
- [ ] Enregistrer le choix de consentement.
- [ ] Convertir les coordonnées en ville/quartier sans exposer inutilement leur précision.
- [ ] Réduire les coordonnées GPS à la précision de quartier avant leur stockage métier et ne jamais exposer les coordonnées brutes.
- [ ] Créer un catalogue local de villes/quartiers et coordonnées approximatives pour la saisie manuelle et le seed.
- [ ] Permettre une recherche locale dans ce catalogue sans appeler un service externe à chaque frappe.
- [ ] Intégrer Nominatim uniquement pour une recherche ou un géocodage inverse explicitement déclenché par l'utilisateur.
- [ ] Respecter pour Nominatim : au maximum une requête par seconde pour toute l'application, User-Agent identifiable, attribution visible et cache des résultats.
- [ ] Interdire l'autocomplétion directe, le bulk geocoding et l'utilisation de Nominatim par le seed.
- [ ] Rendre l'endpoint de géocodage configurable afin de pouvoir changer ou désactiver le fournisseur sans mise à jour du frontend.
- [ ] Basculer proprement sur le catalogue et la saisie manuelle lorsque Nominatim ou Internet est indisponible.
- [ ] Si le GPS est refusé ou indisponible, demander obligatoirement une ville ou un quartier.
- [ ] Empêcher le matching tant qu'aucune localisation n'est disponible.
- [ ] Permettre de modifier ou remplacer la localisation à tout moment.
- [ ] Calculer une distance exploitable pour suggestions, tris et filtres.

### 4.4 Popularité et historique personnel

- [ ] Implémenter la formule de popularité définie en phase 0.
- [ ] Recalculer ou dériver le score de façon cohérente.
- [ ] Rendre le score public et compréhensible.
- [ ] Créer la page « Qui a consulté mon profil » avec dates.
- [ ] Créer la page « Qui m'a liké ».
- [ ] Respecter les blocages dans ces listes.

---

## Phase 5 — Navigation, suggestions et recherche (Obligatoire)

### 5.1 Compatibilité des profils

- [ ] Implémenter les règles de compatibilité dans les deux sens.
- [ ] Gérer correctement hétérosexualité, homosexualité et bisexualité.
- [ ] Traiter une préférence non renseignée comme l'ensemble de tous les genres lorsque le consentement sensible est actif.
- [ ] Exclure l'utilisateur courant.
- [ ] Exclure les comptes bloqués dans les deux sens.
- [ ] Exclure systématiquement les profils incomplets, inactifs et non vérifiés des suggestions, recherches et consultations directes.

### 5.2 Suggestions intelligentes

- [ ] Calculer le nombre de tags communs.
- [ ] Calculer la distance géographique.
- [ ] Intégrer la note de popularité.
- [ ] Combiner plusieurs critères dans le classement.
- [ ] Donner la priorité aux profils de la même zone géographique.
- [ ] Vérifier avec des tests que le classement respecte réellement ces règles.
- [ ] Afficher les informations utiles expliquant la suggestion : distance, tags communs et popularité.

### 5.3 Tri et filtrage des suggestions

- [ ] Ajouter le tri par âge.
- [ ] Ajouter le tri par localisation/distance.
- [ ] Ajouter le tri par popularité.
- [ ] Ajouter le tri par nombre de tags communs.
- [ ] Ajouter les filtres par tranche d'âge.
- [ ] Ajouter les filtres par localisation/distance.
- [ ] Ajouter les filtres par plage de popularité.
- [ ] Ajouter les filtres par tags communs.
- [ ] Conserver une pagination et des performances acceptables avec 500 profils.

### 5.4 Recherche avancée

- [ ] Permettre de combiner une tranche d'âge, une localisation, une plage de popularité et plusieurs tags.
- [ ] Appliquer les mêmes règles de compatibilité et de blocage que les suggestions.
- [ ] Permettre le tri par âge, distance, popularité et tags.
- [ ] Permettre d'affiner les résultats sans perdre les critères saisis.
- [ ] Gérer proprement l'absence de résultat et les critères invalides.
- [ ] Paramétrer toutes les requêtes de recherche.

---

## Phase 6 — Consultation et interactions (Obligatoire)

### 6.1 Page publique d'un profil

- [ ] Afficher toutes les informations disponibles autorisées par le sujet : username, prénom, nom, âge, genre, préférences sexuelles, biographie, tags, localisation approximative et photos.
- [ ] Afficher la note de popularité.
- [ ] Ne jamais afficher l'e-mail, le mot de passe/hash, les jetons, les secrets, les coordonnées GPS précises ou une donnée privée de sécurité.
- [ ] Afficher le statut en ligne ou la date et l'heure de dernière connexion.
- [ ] Afficher si ce profil a déjà liké l'utilisateur courant.
- [ ] Afficher si les deux utilisateurs sont connectés.
- [ ] Proposer les actions adaptées à l'état : liker la photo de profil, unliker/se déconnecter, bloquer et signaler.

### 6.2 Visites

- [ ] Enregistrer la consultation d'un autre profil avec sa date.
- [ ] Enregistrer chaque consultation humaine réelle mais ignorer les rafraîchissements et appels automatiques techniques.
- [ ] Limiter à une notification de visite par paire visiteur/profil sur 24 heures.
- [ ] Supprimer automatiquement l'historique détaillé des visites après 90 jours.
- [ ] Créer la notification de visite en moins de 10 secondes.
- [ ] Ne pas enregistrer une consultation de son propre profil.
- [ ] Ne pas laisser les utilisateurs bloqués interagir via ce mécanisme.

### 6.3 Likes et matchs

- [ ] Permettre explicitement de liker la photo de profil d'un autre utilisateur, uniquement si l'utilisateur courant possède lui-même une photo de profil.
- [ ] Empêcher les doublons et le like de soi-même.
- [ ] Notifier le destinataire d'un nouveau like en moins de 10 secondes.
- [ ] Détecter le like réciproque de manière atomique.
- [ ] Créer ou reconnaître la connexion et notifier le match.
- [ ] Afficher immédiatement le nouvel état aux deux utilisateurs.
- [ ] Permettre l'unlike.
- [ ] Afficher clairement l'action « se déconnecter » lorsqu'un match existe ; cette action effectue l'unlike et applique toutes ses conséquences.
- [ ] Après unlike, désactiver le chat entre les deux utilisateurs.
- [ ] Après unlike, notifier l'ancien match.
- [ ] Après unlike, empêcher les notifications ultérieures provenant de cet utilisateur conformément au sujet.
- [ ] Conserver la conversation passée en lecture seule après unlike et permettre à chaque utilisateur de la masquer localement.
- [ ] Exiger deux nouveaux likes actifs pour recréer un match après unlike.
- [ ] Tester les actions simultanées et éviter les états dupliqués.

### 6.4 Blocage et signalement

- [ ] Permettre de signaler un profil comme faux compte.
- [ ] Stocker auteur, cible, motif éventuel et date sans doublon abusif.
- [ ] Permettre de bloquer un utilisateur.
- [ ] Lors du blocage, supprimer les likes actifs, terminer le match et rendre la conversation inaccessible dans les deux sens.
- [ ] Retirer les utilisateurs bloqués des suggestions et recherches.
- [ ] Empêcher likes, visites notifiantes, messages et notifications entre utilisateurs bloqués.
- [ ] Désactiver une conversation existante après blocage.
- [ ] Lors du déblocage, ne restaurer automatiquement ni likes, ni match, ni conversation active.
- [ ] Vérifier le blocage côté serveur sur chaque action, pas seulement dans l'interface.

---

## Phase 7 — Chat temps réel (Obligatoire)

- [ ] Authentifier la connexion Socket.IO à partir de la session serveur existante.
- [ ] Refuser l'ouverture ou les événements Socket.IO d'un utilisateur non authentifié.
- [ ] Revalider côté serveur l'appartenance à la conversation pour chaque message envoyé.
- [ ] Exiger un UUID v4 généré côté client pour chaque événement Socket.IO d'écriture.
- [ ] Valider l'UUID côté serveur et conserver sa clé d'idempotence dans Valkey pendant 24 heures.
- [ ] Persister d'abord le message ou la notification dans PostgreSQL avant acquittement et diffusion.
- [ ] Créer ou retrouver une conversation pour chaque connexion mutuelle.
- [ ] Autoriser l'accès uniquement aux deux participants encore connectés et non bloqués.
- [ ] Créer l'interface de liste des conversations.
- [ ] Créer l'interface d'une conversation et son historique paginé.
- [ ] Envoyer, persister puis transmettre les messages en moins de 10 secondes.
- [ ] Valider longueur, encodage et contenu des messages.
- [ ] Protéger l'affichage contre les XSS.
- [ ] Ajouter date, auteur et ordre fiable des messages.
- [ ] Gérer l'état lu/non lu.
- [ ] Afficher depuis toute page l'arrivée d'un nouveau message.
- [ ] Gérer reconnexion, messages en double et perte temporaire de connexion.
- [ ] Refuser immédiatement les messages après unlike ou blocage.

---

## Phase 8 — Notifications temps réel (Obligatoire)

- [ ] Créer une notification lors d'un like reçu.
- [ ] Créer une notification lors d'une visite de profil.
- [ ] Créer une notification lors d'un nouveau message.
- [ ] Créer une notification lors d'un like réciproque/match.
- [ ] Créer une notification lorsqu'une connexion effectue un unlike.
- [ ] Livrer chaque notification en moins de 10 secondes.
- [ ] Afficher sur toutes les pages un indicateur de notifications non lues.
- [ ] Créer une liste de notifications avec type, auteur, date et lien utile.
- [ ] Permettre de marquer une notification comme lue, individuellement ou globalement.
- [ ] Éviter les notifications dupliquées.
- [ ] Respecter blocages et règles post-unlike avant création et livraison.
- [ ] Recharger les notifications manquées après une reconnexion.

---

## Phase 9 — Interface et expérience utilisateur (Obligatoire)

- [ ] Construire un en-tête, une section principale et un pied de page.
- [ ] Rendre déconnexion, messages et notifications accessibles depuis toute page.
- [ ] Concevoir les états chargement, vide, erreur et succès.
- [ ] Ajouter une validation de formulaire claire côté client sans remplacer celle du serveur.
- [ ] Rendre l'interface utilisable sur petit écran.
- [ ] Vérifier clavier, focus, labels, contraste et textes alternatifs des images.
- [ ] Ne pas exposer de données sensibles dans le HTML, les URLs ou le stockage navigateur.
- [ ] Tester les dernières versions de Firefox et Chrome.
- [ ] Exécuter les tests finaux avec le navigateur Google Chrome réel et Firefox, pas seulement Chromium.
- [ ] Vérifier qu'aucune erreur ou aucun warning n'apparaît dans la console.

### 9.1 Protection des données et droits RGPD

- [ ] Publier une notice de confidentialité accessible avant inscription et depuis toutes les pages authentifiées.
- [ ] Expliquer pour chaque donnée la finalité, la base légale, les destinataires, la durée de conservation et les droits de l'utilisateur.
- [ ] Identifier explicitement les préférences sexuelles comme données sensibles et documenter leur consentement explicite.
- [ ] Présenter séparément les consentements préférences sexuelles, GPS et tout futur traitement optionnel.
- [ ] Ne précocher aucun consentement et conserver version, finalité, date, preuve et retrait.
- [ ] Permettre le retrait aussi facilement que l'accord et appliquer immédiatement ses conséquences métier.
- [ ] Ne collecter le GPS qu'à la demande, jamais en arrière-plan, et ne conserver aucun historique de déplacement.
- [ ] Permettre à l'utilisateur de consulter et rectifier ses données.
- [ ] Ajouter un export JSON des données personnelles : compte, profil, consentements, localisation approximative, photos référencées, likes, matchs, visites, messages et notifications.
- [ ] Ajouter la suppression de compte et vérifier la disparition des données dans PostgreSQL, Valkey, MinIO et les index/caches.
- [ ] Documenter et automatiser les durées validées de rétention et l'effacement des données expirées.
- [ ] Documenter la liste des sous-traitants et services externes optionnels : Brevo, Google, Cloudflare R2 et Nominatim.
- [ ] Garantir que la mandatory locale n'envoie aucune donnée personnelle à ces services lorsqu'ils sont désactivés.
- [ ] Tenir un registre minimal des traitements et réaliser une analyse d'impact adaptée avant un déploiement réel traitant orientation et géolocalisation à grande échelle.
- [ ] Prévoir une procédure documentée de demande d'accès, rectification, effacement et retrait de consentement.
- [ ] Tester que les données supprimées ne restent ni dans les logs, ni dans les objets temporaires, ni dans les seeds ou sauvegardes de démonstration.

---

## Phase 10 — Tests et contrôle qualité (Obligatoire)

### 10.1 Tests automatisés

- [ ] Tester les fonctions métier : compatibilité, score, distance, popularité et mots de passe.
- [ ] Tester les requêtes SQL et contraintes de base.
- [ ] Tester inscription, activation, connexion, déconnexion et réinitialisation.
- [ ] Tester toutes les modifications du profil et des photos.
- [ ] Tester les suggestions, tris, filtres et recherches combinées.
- [ ] Tester visites, likes, matchs, unlikes, blocages et signalements.
- [ ] Tester l'autorisation du chat avant et après unlike/blocage.
- [ ] Tester création, lecture et temps de livraison des notifications.
- [ ] Tester les réponses d'erreur et accès non autorisés.

### 10.2 Tests de sécurité

- [ ] Tester les injections SQL sur tous les champs et paramètres.
- [ ] Tester les XSS stockées et réfléchies dans profils, tags, recherches et messages.
- [ ] Tester CSRF, fixation de session et accès horizontal aux ressources d'autrui.
- [ ] Tester brute force et limitation de débit.
- [ ] Tester les jetons expirés, réutilisés ou modifiés.
- [ ] Tester les faux fichiers image, doubles extensions et fichiers trop volumineux.
- [ ] Vérifier que les mots de passe sont bien hachés dans la base.
- [ ] Rechercher les secrets et fichiers `.env` dans l'historique Git avant rendu.
- [ ] Vérifier que les logs ne contiennent ni mot de passe, ni jeton, ni secret.

### 10.3 Tests manuels complets

- [ ] Exécuter un parcours visiteur : inscription, activation et connexion.
- [ ] Exécuter un parcours nouveau membre : profil, tags, photos et localisation.
- [ ] Tester le refus du GPS puis la localisation manuelle obligatoire.
- [ ] Tester plusieurs combinaisons de genres et d'ensembles de genres recherchés.
- [ ] Tester deux utilisateurs dans deux navigateurs distincts.
- [ ] Vérifier visite, like, match, chat, unlike et blocage de bout en bout.
- [ ] Mesurer que messages et notifications arrivent au maximum en 10 secondes.
- [ ] Tester avec la base de 500 profils et vérifier les performances.
- [ ] Tester les vues mobile, tablette et ordinateur.
- [ ] Vérifier les consoles frontend et backend pendant tous les parcours.

---

## Phase 11 — Documentation et préparation du rendu (Obligatoire)

- [ ] Documenter les prérequis et l'installation depuis un clone propre.
- [ ] Documenter les variables de `.env.example`.
- [ ] Documenter création, migration et seed de la base.
- [ ] Documenter les commandes de développement, production, test et lint.
- [ ] Expliquer brièvement l'architecture et le schéma de données.
- [ ] Documenter l'algorithme de suggestions et la formule de popularité.
- [ ] Documenter les choix de sécurité et de temps réel.
- [ ] Fournir les comptes de démonstration sans publier de vrai secret.
- [ ] Vérifier les noms et emplacements des fichiers demandés.
- [ ] Refaire l'installation dans un environnement propre.
- [ ] Vérifier que tout le travail nécessaire est commité dans le dépôt.
- [ ] Confirmer une dernière fois : zéro erreur, warning ou notice côté client et serveur.

---

## Ordre conseillé des jalons

- [ ] **Jalon 1 — Socle :** environnement, schéma SQL, migrations, sessions et sécurité de base.
- [ ] **Jalon 2 — Compte :** inscription, e-mails, activation, connexion et mot de passe oublié.
- [ ] **Jalon 3 — Profil :** informations, photos, tags, localisation et popularité.
- [ ] **Jalon 4 — Découverte :** compatibilité, suggestions, recherche, filtres et tris.
- [ ] **Jalon 5 — Interactions :** visites, likes, matchs, unlike, blocage et signalement.
- [ ] **Jalon 6 — Temps réel :** chat, messages non lus et toutes les notifications.
- [ ] **Jalon 7 — Stabilisation :** 500 profils, responsive, navigateurs, sécurité et tests complets.
- [ ] **Jalon 8 — Rendu :** documentation, installation propre et répétition de la soutenance.

---

## Bonus — seulement si tout l'obligatoire est parfait

Le sujet précise que les bonus ne sont pas évalués si une seule exigence obligatoire
manque ou dysfonctionne. La priorité reste donc sur les phases 0 à 11.

### Porte de validation avant tout bonus

- [ ] Toutes les tâches obligatoires sont terminées et testées.
- [ ] Le seed contient au moins 500 profils valides.
- [ ] L'installation fonctionne depuis un clone propre avec Podman et le `Makefile`.
- [ ] Les parcours obligatoires passent sur Firefox et Chrome, desktop et mobile.
- [ ] Le chat et les notifications respectent le délai maximal de 10 secondes.
- [ ] Aucune erreur, aucun warning et aucune notice n'apparaît côté client ou serveur.
- [ ] Les tests de sécurité obligatoires sont passés.
- [ ] Créer une branche ou un jalon Git stable de la mandatory avant d'intégrer un bonus.
- [ ] Choisir un bonus à la fois et refaire toute la non-régression obligatoire après chaque intégration.

### B1 — Authentification externe OAuth/OIDC

Le sujet emploie le terme OmniAuth. OmniAuth étant une bibliothèque Ruby, l'équivalent
cohérent avec notre backend Python est une intégration OAuth 2.0/OIDC explicite avec un
ou plusieurs fournisseurs. Ce choix devra être expliqué pendant la soutenance.

- [x] Choisir Google comme fournisseur OAuth 2.0/OpenID Connect pour ce bonus.
- [x] Confirmer que Google OAuth/OIDC est compatible avec le sujet en tant qu'équivalent Python d'une stratégie OmniAuth.
- [ ] Créer un projet Google Cloud distinct réservé au développement et à la démonstration Matcha.
- [ ] Configurer l'écran de consentement Google OAuth en mode `Testing`.
- [ ] Ajouter explicitement les comptes Google utilisés pendant la soutenance à la liste des utilisateurs de test.
- [ ] Tenir compte de la limite Google du mode test et de l'expiration périodique des autorisations des testeurs.
- [ ] Configurer un client OAuth Google de type application web.
- [ ] Déclarer précisément les URI de redirection locales et de production ; interdire les URI génériques ou jokers.
- [ ] Limiter les scopes Google à `openid`, `email` et `profile`.
- [ ] Ne demander aucun accès à Gmail, Drive, Calendar ou autre donnée inutile à la connexion.
- [ ] Vérifier avant la soutenance que Google n'exige pas de configuration, vérification ou information supplémentaire pour le mode de publication retenu.
- [ ] Prévoir une page d'accueil et une politique de confidentialité si le bonus est publié au-delà du mode de test.
- [ ] Utiliser Authlib pour OAuth 2.0/OIDC, sans remplacer Flask ni ajouter d'ORM.
- [ ] Enregistrer `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` et les URLs uniquement dans `.env`.
- [ ] Ajouter les variables correspondantes dans `.env.example` sans valeur secrète.
- [ ] Implémenter le départ OAuth avec un paramètre `state` aléatoire contre les attaques CSRF.
- [ ] Utiliser PKCE lorsque le fournisseur et le flux choisi le permettent.
- [ ] Valider côté serveur `state`, issuer, audience, signature, expiration et nonce selon le protocole.
- [ ] Créer une table d'identités externes contenant l'identifiant Google stable `sub`, l'utilisateur Matcha, le fournisseur et les dates utiles.
- [ ] Utiliser le claim Google `sub` comme identifiant externe stable, jamais l'adresse e-mail seule.
- [ ] Ne jamais fusionner automatiquement deux comptes uniquement parce que leurs e-mails se ressemblent.
- [ ] Exiger une authentification ou une confirmation sûre avant de lier Google à un compte Matcha existant.
- [ ] Refuser la création OAuth si Google ne fournit pas un e-mail vérifié et proposer l'inscription classique.
- [ ] Exiger mot de passe ou réauthentification récente pour lier/délier Google et empêcher de supprimer le dernier moyen de connexion.
- [ ] Empêcher qu'un utilisateur se retrouve sans aucun moyen de connexion après déliaison.
- [ ] Maintenir les exigences obligatoires : compte actif, profil à compléter, localisation et photo avant like.
- [ ] Maintenir la connexion classique username/mot de passe et le mot de passe oublié.
- [ ] Ne pas considérer la connexion Google comme un remplacement de l'inscription et de l'activation obligatoires lors de l'évaluation de la mandatory.
- [ ] Créer pour un nouvel utilisateur Google un compte Matcha interne soumis aux mêmes règles de profil, consentement, matching et modération.
- [ ] Appliquer les mêmes sessions serveur, contrôles d'autorisation et règles de blocage.
- [ ] Tester refus du fournisseur, callback modifié, rejeu, compte déjà lié et e-mail absent.
- [ ] Ajouter des tests end-to-end sans dépendre d'un vrai compte personnel.
- [ ] Préparer au moins deux comptes Google de test dédiés à la démonstration, sans utiliser de compte personnel principal.
- [ ] Vérifier le parcours OAuth peu avant la soutenance afin de renouveler les autorisations de test si nécessaire.
- [ ] Vérifier que l'application obligatoire démarre et fonctionne lorsque les variables Google sont absentes et que le bonus est désactivé.
- [ ] Documenter la configuration et la désactivation propre de ce bonus.

### B2 — Galerie personnelle et édition d'images

- [ ] Séparer clairement les cinq photos du profil obligatoire de la galerie bonus.
- [ ] Limiter la galerie bonus à 20 images par utilisateur.
- [ ] Appliquer à chaque image de galerie les formats validés, 5 Mio maximum et 4096 × 4096 pixels maximum.
- [ ] Ajouter les tables et migrations de galerie sans modifier le comportement des photos de profil.
- [ ] Créer une zone de glisser-déposer accessible avec alternative via sélection de fichiers.
- [ ] Afficher la progression, les erreurs et l'annulation des téléversements.
- [ ] Réutiliser le pipeline obligatoire de validation et réencodage Pillow.
- [ ] Réutiliser l'interface S3 compatible et stocker la galerie dans les buckets MinIO/R2 privés prévus.
- [ ] Créer plusieurs tailles d'image et supprimer les métadonnées EXIF sensibles.
- [ ] Ajouter le recadrage avec aperçu avant validation.
- [ ] Ajouter la rotation sans perte ou en réencodant sûrement le résultat.
- [ ] Ajouter quelques filtres simples avec possibilité de revenir à l'original.
- [ ] Ne jamais permettre de modifier ou supprimer les fichiers d'un autre utilisateur.
- [ ] Protéger les opérations d'édition contre CSRF et traversée de chemin.
- [ ] Nettoyer les versions intermédiaires et fichiers orphelins.
- [ ] Vérifier que la suppression d'une image de galerie ne casse pas les cinq photos de profil.
- [ ] Tester fichiers invalides, quotas, éditions simultanées et utilisation mobile.
- [ ] Documenter la provenance et les droits des images de démonstration.

### B3 — Carte interactive des utilisateurs

- [ ] Utiliser MapLibre GL JS avec une source de tuiles configurable et non codée en dur.
- [ ] Vérifier les conditions d'utilisation, attribution, quotas et politique de confidentialité du fournisseur de tuiles.
- [ ] Ne charger la carte et aucun service tiers avant que cela soit nécessaire et autorisé.
- [ ] Demander un consentement distinct et explicite avant d'utiliser une localisation GPS plus précise.
- [ ] Expliquer clairement la précision, la finalité, la durée de conservation et la possibilité de retrait.
- [ ] Conserver le mode obligatoire ville/quartier pour les utilisateurs qui refusent la précision supplémentaire.
- [ ] Permettre de retirer le consentement et supprimer ou réduire immédiatement les coordonnées précises.
- [ ] Ne jamais exposer les coordonnées exactes d'un autre utilisateur dans l'API ou le navigateur.
- [ ] Afficher des positions approximatives, zones ou marqueurs décalés pour protéger les utilisateurs.
- [ ] Appliquer compatibilité, filtres, blocages et invisibilité des comptes exclus sur la carte.
- [ ] Grouper les marqueurs pour conserver de bonnes performances avec plus de 500 profils.
- [ ] Synchroniser la carte avec la recherche et les filtres existants sans les remplacer.
- [ ] Prévoir un état sans carte si le service tiers ou la géolocalisation échoue.
- [ ] Tester consentement accepté, refusé, retiré, GPS indisponible et utilisateur bloqué.
- [ ] Vérifier la conformité mobile et l'accessibilité d'une alternative sous forme de liste.

### B4 — Chat audio ou vidéo

- [ ] Utiliser WebRTC pour les médias et Flask-SocketIO uniquement pour la signalisation.
- [ ] Auto-héberger coturn avec Podman pour STUN/TURN et tester les réseaux où le pair-à-pair échoue.
- [ ] Conserver les identifiants TURN dans `.env` et limiter leur durée ou leur portée.
- [ ] Autoriser un appel uniquement entre utilisateurs actuellement matchés et non bloqués.
- [ ] Vérifier à nouveau cette autorisation côté serveur au début et pendant l'appel.
- [ ] Créer les états appel entrant, accepté, refusé, occupé, terminé et échoué.
- [ ] Demander explicitement les permissions caméra et microphone.
- [ ] Fournir couper/réactiver micro, activer/désactiver caméra et raccrocher.
- [ ] Ne jamais démarrer la caméra ou le microphone automatiquement.
- [ ] Ne pas enregistrer le flux audio/vidéo sans une fonctionnalité et un consentement séparés.
- [ ] Terminer immédiatement l'appel après unlike, blocage ou perte d'autorisation.
- [ ] Empêcher une personne bloquée de lancer ou signaler un appel.
- [ ] Ajouter une notification d'appel sans perturber les notifications obligatoires.
- [ ] Gérer reconnexion, timeout, perte réseau et refus de permissions.
- [ ] Tester entre deux navigateurs et, si possible, deux réseaux distincts.
- [ ] Vérifier Firefox, Chrome, desktop et mobile.

### B5 — Rendez-vous et événements entre utilisateurs matchés

- [ ] Autoriser la création d'une proposition uniquement entre utilisateurs matchés et non bloqués.
- [ ] Concevoir les tables pour proposition, participants, lieu, horaires, statut et historique minimal.
- [ ] Utiliser les statuts `proposed`, `accepted`, `declined`, `cancelled` et `rescheduled`.
- [ ] Gérer correctement fuseaux horaires, heure d'été et stockage des dates en UTC.
- [ ] Permettre de proposer date, heure, durée, lieu approximatif et message facultatif.
- [ ] Ne pas révéler publiquement une adresse privée ou une localisation précise.
- [ ] Permettre au destinataire d'accepter, refuser ou proposer une autre date.
- [ ] Empêcher une personne non participante de consulter ou modifier le rendez-vous.
- [ ] Ajouter des notifications dédiées sans casser les cinq types obligatoires.
- [ ] Après unlike, annuler les rendez-vous futurs non réalisés et notifier l'ancien match ; après blocage, les annuler sans notification entre utilisateurs et les rendre inaccessibles.
- [ ] Permettre l'annulation et conserver un historique minimal utile aux participants.
- [ ] Ajouter des rappels configurables sans envoyer de notification à un utilisateur bloqué.
- [ ] Éviter les doublons lors de doubles clics ou requêtes simultanées.
- [ ] Tester conflits horaires, dates passées, fuseaux différents, unlike et blocage.
- [ ] Rendre le parcours utilisable sur mobile.

### Validation de cohérence bonus/mandatory

| Bonus | Dépendances obligatoires | Risque principal | Condition de cohérence |
| --- | --- | --- | --- |
| OAuth/OIDC | Comptes, activation, sessions, profil | Contourner les règles d'inscription ou créer des doublons | Le fournisseur crée ou lie une identité, mais toutes les règles Matcha restent appliquées. |
| Galerie/édition | Photos et téléversement sécurisé | Confondre galerie et limite obligatoire de cinq photos | Les cinq photos de profil restent une collection séparée avec exactement les mêmes règles obligatoires. |
| Carte | Localisation, consentement, recherche, blocage | Exposer une position précise ou rendre le GPS obligatoire | La carte est facultative, n'affiche jamais les coordonnées exactes et conserve le mode ville/quartier. |
| Audio/vidéo | Match, chat, présence, blocage | Autoriser un appel après unlike/blocage | Chaque appel vérifie le match et le blocage côté serveur et s'arrête si la relation change. |
| Rendez-vous | Match, notifications, blocage | Laisser accessible une invitation après rupture de connexion | Les autorisations sont recalculées à chaque action et les données privées restent limitées aux participants. |

### Non-régression après chaque bonus

- [ ] Relancer `make check` et toute la suite de tests obligatoires.
- [ ] Relancer les scénarios Playwright avec deux utilisateurs.
- [ ] Vérifier que le seed standard et `make seed-demo` fonctionnent toujours.
- [ ] Vérifier qu'un bonus désactivé par configuration ne bloque pas le lancement obligatoire.
- [ ] Vérifier qu'aucun nouveau secret n'est présent dans Git ou les logs.
- [ ] Vérifier que les migrations restent reproductibles sur une base vide.
- [ ] Vérifier les performances avec au moins 500 profils.
- [ ] Vérifier Firefox, Chrome et les petits écrans.
- [ ] Vérifier à nouveau zéro erreur, warning ou notice.
- [ ] Documenter le bonus, ses variables, ses limites et sa démonstration dans le README.
