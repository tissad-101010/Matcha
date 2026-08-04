# Matcha

Matcha est une application web de rencontre conçue pour accompagner deux partenaires
potentiels depuis leur inscription jusqu'à leur mise en relation. Un membre peut créer son
compte, compléter son profil, découvrir des personnes compatibles, rechercher selon plusieurs
critères, exprimer son intérêt et discuter en temps réel après un intérêt réciproque.

Le projet est réalisé dans le cadre du sujet **Web — Matcha, version 6.0**. Sa priorité est de
livrer une partie obligatoire complète, sûre, responsive et explicable pendant l'évaluation.
Les bonus ne seront développés qu'après validation parfaite de cette base.

> **État actuel : préparation terminée, implémentation à démarrer.** Le dépôt contient le
> contrat fonctionnel, technique, UX, API et données. Il ne contient pas encore l'application
> Flask/React exécutable.

## Objectif

Matcha doit permettre à un utilisateur de :

1. s'inscrire avec une adresse e-mail, un username, un nom, un prénom, une date de naissance
   et un mot de passe sécurisé ;
2. vérifier son compte par e-mail, se connecter, se déconnecter et réinitialiser son mot de
   passe ;
3. renseigner son genre, ses préférences de rencontre, sa biographie, ses centres d'intérêt,
   sa localisation et jusqu'à cinq photos ;
4. consulter des suggestions compatibles classées par proximité, tags communs et popularité ;
5. effectuer une recherche avancée par âge, popularité, localisation et tags ;
6. consulter un profil, enregistrer la visite, liker, unliker, bloquer ou signaler un membre ;
7. créer un match lorsque deux likes sont réciproques ;
8. échanger des messages et recevoir des notifications en temps réel en moins de dix secondes.

## Règles métier principales

- L'application est réservée aux personnes âgées d'au moins 18 ans.
- La compatibilité est mutuelle : le genre de chaque membre doit appartenir aux préférences
  de l'autre.
- Une préférence absente correspond à tous les genres lorsque le consentement sensible est actif.
- Les consentements aux préférences et à la géolocalisation GPS sont explicites, séparés et
  non précochés.
- En cas de refus du GPS, une ville ou un quartier doit être renseigné manuellement.
- Les positions exactes ne sont jamais affichées ; seule une localisation approximative est utilisée.
- Un profil peut être complet sans photo, mais un membre sans photo principale ne peut pas liker.
- Un like réciproque crée un match et autorise le chat.
- Un unlike termine le match, bloque les nouveaux messages et conserve l'historique en lecture seule.
- Un blocage rend profils, recherche, notifications et conversation inaccessibles dans les deux sens.
- La popularité est une note publique calculée côté serveur depuis les likes actifs, matchs actifs
  et visiteurs uniques récents.
- Le statut en ligne ou la date et l'heure de dernière connexion sont visibles sur les profils.

## Fonctionnalités obligatoires

### Authentification

- inscription et validation de toutes les entrées ;
- refus des mots anglais courants comme mot de passe ;
- hash Argon2id, aucun mot de passe en clair ;
- lien unique de vérification d'e-mail ;
- connexion par username et mot de passe ;
- réinitialisation du mot de passe par e-mail ;
- déconnexion accessible en un clic depuis toute page.

### Profil et localisation

- genre, préférences, biographie et tags réutilisables ;
- zéro à cinq photos, avec exactement une photo principale lorsqu'une photo existe ;
- modification du profil, du nom, du prénom et de l'e-mail ;
- liste des visiteurs et des likes reçus ;
- note de popularité publique ;
- GPS réduit au quartier après consentement ou localisation manuelle de remplacement.

### Découverte et recherche

- exclusion automatique des profils incompatibles, incomplets, bloqués ou inactifs ;
- priorité aux personnes de la même zone ;
- classement combinant distance, tags communs et popularité ;
- tri et filtres par âge, localisation, popularité et tags ;
- recherche avancée multi-critères avec les mêmes protections.

### Interactions, chat et notifications

- enregistrement de chaque consultation humaine de profil ;
- like, match réciproque, unlike, blocage et signalement de faux compte ;
- chat réservé aux matchs actifs ;
- historique en lecture seule après unlike et inaccessible après blocage ;
- notifications temps réel pour like, visite, match, message et unlike ;
- messages et notifications non lus visibles depuis toutes les pages.

## Architecture retenue

```text
Navigateur React + TypeScript + Tailwind
                    │
                    ▼
                  Nginx
            ┌───────┴────────┐
            ▼                ▼
       API Flask        Flask-SocketIO
            │                │
            ├──── psycopg ───┴── PostgreSQL
            ├─────────────────── Valkey
            ├─────────────────── MinIO
            └─────────────────── SMTP / Mailpit
```

| Domaine | Choix |
| --- | --- |
| Backend | Python, Flask, Gunicorn et gevent |
| Frontend | React, TypeScript, Vite et Tailwind CSS |
| Base de données | PostgreSQL avec SQL manuel et psycopg 3, sans ORM |
| Temps réel | Flask-SocketIO et WebSockets |
| Sessions et présence | Flask-Session et Valkey |
| Photos | Pillow et stockage S3 compatible MinIO |
| E-mails | SMTP avec Mailpit en local et Brevo optionnel en production |
| Proxy web | Nginx |
| Conteneurs | Podman et Podman Compose rootless |
| Automatisation | GNU Make |
| Tests | pytest, Vitest, Testing Library et Playwright |

Nginx est le seul point d'entrée HTTP. Il sert le build React et route `/api` et
`/socket.io` vers Flask. PostgreSQL conserve les données durables, Valkey les sessions et
états temporaires, et MinIO les fichiers privés. La partie obligatoire peut fonctionner
localement sans service cloud payant.

## Contraintes de qualité et de sécurité

- aucune erreur, aucun warning et aucune notice côté serveur ou navigateur ;
- compatibilité avec les versions récentes de Firefox et Chrome ;
- interface responsive avec en-tête, contenu principal et pied de page ;
- validation de toutes les entrées côté serveur ;
- requêtes SQL paramétrées et écrites manuellement ;
- protection contre injections SQL, HTML/JavaScript, CSRF et uploads malveillants ;
- secrets uniquement dans `.env`, toujours exclu de Git ;
- cookies de session sécurisés et sessions conservées côté serveur ;
- photos décodées, EXIF supprimé et fichiers réencodés avant stockage privé ;
- au moins 500 profils distincts dans la base pour l'évaluation ;
- code court, lisible, commenté lorsqu'une décision n'est pas évidente et compréhensible
  pendant la soutenance.

## Données de démonstration

Le seed prévu générera de manière reproductible au moins 600 profils fictifs afin de dépasser
la contrainte des 500 profils. Il couvrira différentes combinaisons de genres, préférences,
localisations, tags, popularités, photos, likes, matchs, visites et conversations.

Les avatars seront produits localement avec Pillow. Quelques comptes principaux pourront
utiliser des portraits entièrement synthétiques. Aucun profil ne devra représenter une
personne réelle sans autorisation.

## Lancement prévu

Une fois l'implémentation disponible, le parcours principal sera :

```bash
make setup
make start
make health
```

Les commandes prévues incluent également :

```bash
make migrate
make seed
make test
make lint
make check
make down
```

Ces commandes sont documentées comme **prévues** tant que le Makefile et les services ne sont
pas encore implémentés.

## Documentation du projet

| Document | Rôle |
| --- | --- |
| [Sujet original](fr.subject.pdf) | Source normative prioritaire |
| [TASKS.md](TASKS.md) | Plan complet, décisions techniques et règles métier |
| [SCENARIOS.md](SCENARIOS.md) | Parcours utilisateur, états et cas limites |
| [UX_BUILD_SPEC.md](UX_BUILD_SPEC.md) | Contrat des écrans et critères UX |
| [CODE_RULES.md](CODE_RULES.md) | Lisibilité, sécurité, tests et préparation à l'évaluation |
| [API_AND_QUERIES.md](API_AND_QUERIES.md) | Endpoints, Socket.IO, requêtes SQL et transactions |
| [DATA_MODEL.md](DATA_MODEL.md) | Tables, relations, contraintes et rétention |
| [TRANSFER_MODELS.md](TRANSFER_MODELS.md) | Formats et modèles échangés entre les services |

En cas de divergence, l'ordre d'autorité est : sujet PDF, `TASKS.md`, `SCENARIOS.md`,
spécifications détaillées, puis maquettes visuelles.

## Maquettes

Les planches de référence sont disponibles dans [`docs/mockups`](docs/mockups) :

- authentification et onboarding ;
- découverte, recherche et matching ;
- messagerie et notifications ;
- profil, consentements et états système ;
- direction visuelle desktop et mobile.

Les images décrivent l'intention visuelle. Les permissions et comportements sont toujours
décidés par les documents textuels et vérifiés côté serveur.

## Bonus envisagés

Après validation complète de la partie obligatoire :

- authentification Google OAuth/OIDC ;
- galerie personnelle et édition basique d'images ;
- carte interactive avec consentement GPS plus précis ;
- appels audio ou vidéo entre utilisateurs matchés ;
- organisation de rendez-vous ou événements entre matchs.

Chaque bonus restera isolé et ne devra ni remplacer ni fragiliser une fonctionnalité obligatoire.

## Évaluation

Seul le contenu présent dans le dépôt sera évalué. Le projet devra donc pouvoir être construit,
lancé, migré, rempli et testé depuis un clone propre. Chaque module devra être explicable :
besoin couvert, trajet des données, contrôle serveur, risques de sécurité et tests associés.
