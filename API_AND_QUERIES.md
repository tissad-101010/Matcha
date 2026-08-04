# Matcha — endpoints, événements temps réel et requêtes SQL

Ce document définit le contrat initial du backend obligatoire. Il complète `TASKS.md`,
`SCENARIOS.md` et `CODE_RULES.md`. Les bonus sont isolés à la fin.

## 1. Conventions HTTP

- Préfixe obligatoire : `/api/v1`.
- Corps et réponses : JSON, sauf upload et téléchargement de photos.
- Authentification : session serveur Flask-Session dans un cookie `HttpOnly`.
- Toute mutation exige un jeton CSRF envoyé dans l'en-tête `X-CSRF-Token`.
- Les dates sont en UTC au format ISO 8601 ; le frontend réalise l'affichage local.
- Les listes utilisent une pagination par curseur, jamais un chargement sans limite.
- Les identifiants publics sont des UUID non séquentiels.
- Une réussite renvoie directement la ressource ou un objet `{ "data": ... }` cohérent.
- Une erreur utilise la forme suivante :

```json
{
  "error": {
    "code": "validation_error",
    "message": "Certains champs sont invalides.",
    "fields": { "email": "Adresse invalide." },
    "request_id": "..."
  }
}
```

Codes principaux : `200`, `201`, `204`, `400`, `401`, `403`, `404`, `409`, `413`,
`422`, `429` et `500`. Un objet bloqué ou inaccessible répond généralement `404` pour ne
pas confirmer son existence.

## 2. Endpoints système

| Méthode | Endpoint | Auth | Rôle |
| --- | --- | --- | --- |
| GET | `/health/live` | Non | Vérifier que le processus répond |
| GET | `/health/ready` | Non | Vérifier PostgreSQL, Valkey et MinIO |
| GET | `/api/v1/csrf` | Session | Obtenir ou renouveler le jeton CSRF |

Les endpoints de santé ne renvoient aucun secret ni détail d'infrastructure au public.

## 3. Authentification et compte

| Méthode | Endpoint | Auth | Entrée principale | Résultat |
| --- | --- | --- | --- | --- |
| POST | `/api/v1/auth/register` | Non | prénom, nom, username, e-mail, date de naissance, mot de passe | Compte non vérifié et e-mail envoyé |
| POST | `/api/v1/auth/verify-email` | Non | token | Compte vérifié |
| POST | `/api/v1/auth/resend-verification` | Non | e-mail | Réponse neutre |
| POST | `/api/v1/auth/login` | Non | username, mot de passe | Session créée et cookie renouvelé |
| POST | `/api/v1/auth/logout` | Oui | CSRF | Session et socket révoquées |
| GET | `/api/v1/auth/session` | Oui | — | Utilisateur courant et état du profil |
| POST | `/api/v1/auth/forgot-password` | Non | e-mail | Réponse neutre |
| POST | `/api/v1/auth/reset-password` | Non | token, nouveau mot de passe | Mot de passe changé, sessions révoquées |
| PATCH | `/api/v1/account/email` | Oui | nouvel e-mail, mot de passe courant | Vérification du nouvel e-mail lancée |
| POST | `/api/v1/account/email/confirm` | Oui | token | Nouvel e-mail activé |
| PATCH | `/api/v1/account/password` | Oui | ancien et nouveau mot de passe | Mot de passe changé, autres sessions révoquées |
| GET | `/api/v1/account/export` | Oui | — | Export JSON des données personnelles |
| DELETE | `/api/v1/account` | Oui | mot de passe, confirmation | Suppression définitive |

Règles : réponses neutres contre l'énumération, rotation de session à la connexion,
rate limiting et jetons à usage unique stockés sous forme de hash.

## 4. Profil, préférences et consentements

| Méthode | Endpoint | Auth | Rôle |
| --- | --- | --- | --- |
| GET | `/api/v1/me/profile` | Oui | Lire son profil privé complet |
| PATCH | `/api/v1/me/profile` | Oui | Modifier prénom, nom, date de naissance, genre et bio |
| PUT | `/api/v1/me/preferences` | Oui | Définir l'ensemble des genres recherchés |
| DELETE | `/api/v1/me/preferences` | Oui | Retirer la préférence stockée |
| GET | `/api/v1/me/consents` | Oui | Lire les consentements et leurs versions |
| PUT | `/api/v1/me/consents/preferences` | Oui | Donner le consentement sensible explicite |
| DELETE | `/api/v1/me/consents/preferences` | Oui | Retirer le consentement et suspendre le matching |
| PUT | `/api/v1/me/consents/location` | Oui | Donner le consentement GPS |
| DELETE | `/api/v1/me/consents/location` | Oui | Retirer le consentement et réduire/supprimer le GPS |
| GET | `/api/v1/tags?query=` | Oui | Rechercher les tags réutilisables |
| PUT | `/api/v1/me/tags` | Oui | Remplacer la liste de tags du profil |
| POST | `/api/v1/tags` | Oui | Créer un tag normalisé si autorisé |

`PATCH /me/profile` utilise une allowlist et ne permet jamais de changer popularité,
présence, rôle, vérification ou consentement.

## 5. Photos

| Méthode | Endpoint | Auth | Rôle |
| --- | --- | --- | --- |
| GET | `/api/v1/me/photos` | Oui | Lister ses photos et leur ordre |
| POST | `/api/v1/me/photos` | Oui | Ajouter une image multipart, maximum cinq |
| PATCH | `/api/v1/me/photos/{photo_id}` | Oui | Changer ordre ou désigner comme principale |
| DELETE | `/api/v1/me/photos/{photo_id}` | Oui | Supprimer une photo et rétablir l'invariant principal |
| GET | `/api/v1/photos/{photo_id}` | Oui | Servir une photo autorisée sans exposer MinIO |

Le serveur vérifie taille, type réel, dimensions et animation, puis réencode avec Pillow
avant stockage dans un bucket privé.

## 6. Localisation

| Méthode | Endpoint | Auth | Rôle |
| --- | --- | --- | --- |
| GET | `/api/v1/locations?query=` | Oui | Autocomplétion depuis le catalogue local |
| GET | `/api/v1/me/location` | Oui | Lire sa localisation privée |
| PUT | `/api/v1/me/location/manual` | Oui | Enregistrer ville/quartier du catalogue |
| PUT | `/api/v1/me/location/gps` | Oui | Réduire et enregistrer les coordonnées consenties |
| DELETE | `/api/v1/me/location` | Oui | Effacer la localisation avant remplacement |

Les réponses publiques ne contiennent que ville/quartier approximatif et distance arrondie.

## 7. Découverte, recherche et profils publics

| Méthode | Endpoint | Paramètres | Rôle |
| --- | --- | --- | --- |
| GET | `/api/v1/discovery/suggestions` | curseur, limite, tri, filtres | Suggestions compatibles avec priorité locale |
| GET | `/api/v1/search/profiles` | âge min/max, popularité, location, distance, tags, tri, curseur | Recherche avancée |
| GET | `/api/v1/profiles/{user_id}` | — | Profil autorisé et enregistrement de la visite |
| GET | `/api/v1/me/visitors` | période, curseur | Historique des visiteurs |
| GET | `/api/v1/me/likes-received` | curseur | Membres ayant liké le profil |

L'orientation n'est jamais un filtre HTTP public. La compatibilité mutuelle, le blocage,
la complétude et les consentements sont toujours appliqués côté serveur.

## 8. Likes, matchs, blocages et signalements

| Méthode | Endpoint | Rôle |
| --- | --- | --- |
| POST | `/api/v1/profiles/{user_id}/like` | Créer/réactiver un like et éventuellement un match |
| DELETE | `/api/v1/profiles/{user_id}/like` | Unlike transactionnel et fin du match |
| GET | `/api/v1/matches` | Lister les matchs actifs, paginés |
| GET | `/api/v1/matches/{match_id}` | Lire l'état d'un match autorisé |
| POST | `/api/v1/profiles/{user_id}/block` | Bloquer et supprimer les relations actives |
| DELETE | `/api/v1/profiles/{user_id}/block` | Débloquer sans restaurer les relations |
| GET | `/api/v1/me/blocks` | Lister ses blocages |
| POST | `/api/v1/profiles/{user_id}/reports` | Signaler avec motif et description facultative |

Le like est idempotent. L'unlike et le blocage verrouillent les relations concernées pour
éviter qu'un message ou un match soit créé simultanément.

## 9. Conversations et messages

| Méthode | Endpoint | Rôle |
| --- | --- | --- |
| GET | `/api/v1/conversations` | Lister conversations actives et historiques visibles |
| GET | `/api/v1/conversations/{conversation_id}` | Lire métadonnées et droit d'envoi |
| GET | `/api/v1/conversations/{conversation_id}/messages` | Messages paginés avant un curseur |
| POST | `/api/v1/conversations/{conversation_id}/messages` | Secours HTTP pour persister un message |
| POST | `/api/v1/conversations/{conversation_id}/read` | Mettre à jour le dernier message lu |
| POST | `/api/v1/conversations/{conversation_id}/hide` | Masquer localement l'historique |

Le serveur refuse l'envoi si le match n'est plus actif, même si l'interface affiche encore
un ancien état.

## 10. Notifications

| Méthode | Endpoint | Rôle |
| --- | --- | --- |
| GET | `/api/v1/notifications` | Lister les notifications paginées |
| GET | `/api/v1/notifications/unread-count` | Compteur global non lu |
| POST | `/api/v1/notifications/{notification_id}/read` | Marquer une notification comme lue |
| POST | `/api/v1/notifications/read-all` | Tout marquer comme lu |

Types obligatoires : `like_received`, `profile_visited`, `match_created`, `message_received`
et `match_ended` après unlike.

## 11. Événements Socket.IO

Namespace : `/realtime`. La session cookie est vérifiée à la connexion.

| Sens | Événement | Charge utile | Rôle |
| --- | --- | --- | --- |
| Client → serveur | `message:send` | conversation_id, client_message_id, body | Valider et persister un message |
| Serveur → client | `message:ack` | client_message_id, message | Confirmer la persistance |
| Serveur → client | `message:new` | message | Diffuser au destinataire |
| Client → serveur | `conversation:read` | conversation_id, message_id | Mettre à jour la lecture |
| Serveur → client | `conversation:updated` | état minimal | Match terminé, lecture seule ou masqué |
| Serveur → client | `notification:new` | notification | Afficher une notification globale |
| Serveur → client | `notification:count` | unread_count | Synchroniser le badge |
| Client → serveur | `presence:heartbeat` | aucun | Rafraîchir l'activité dans Valkey |
| Serveur → client | `presence:updated` | user_id, online, last_seen_at | Actualiser la présence autorisée |
| Serveur → client | `session:expired` | code | Fermer l'interface temps réel |

Les rooms utilisent des identifiants internes, jamais un nom choisi par le client sans
contrôle d'appartenance.

## 12. Catalogue des requêtes SQL manuelles

Chaque identifiant ci-dessous devient une fonction de repository nommée et testée.

### Comptes et sessions

- `ACCOUNT_INSERT` — créer un compte non vérifié avec hash Argon2id.
- `ACCOUNT_FIND_FOR_LOGIN` — charger uniquement les champs nécessaires à la connexion.
- `ACCOUNT_FIND_BY_EMAIL` — usage interne avec réponse HTTP toujours neutre.
- `ACCOUNT_MARK_VERIFIED` — activer le compte avec verrouillage du jeton.
- `ACCOUNT_UPDATE_EMAIL_PENDING` / `ACCOUNT_CONFIRM_EMAIL` — changement vérifié.
- `ACCOUNT_UPDATE_PASSWORD` — changer le hash et la date de rotation.
- `TOKEN_INSERT`, `TOKEN_CONSUME_IF_VALID`, `TOKEN_REVOKE_ALL` — jetons hashés à usage unique.
- Les sessions elles-mêmes résident dans Valkey ; PostgreSQL conserve seulement les données
  durables et les traces nécessaires définies par la politique de sécurité.

### Profil, préférences et consentements

- `PROFILE_GET_PRIVATE` — vue privée du propriétaire.
- `PROFILE_UPDATE_ALLOWED_FIELDS` — mise à jour explicite des champs autorisés.
- `PROFILE_COMPLETENESS_GET` — calculer les champs obligatoires manquants.
- `PREFERENCES_REPLACE` / `PREFERENCES_DELETE` — ensemble de genres recherchés.
- `CONSENT_UPSERT` — conserver finalité, version, état et horodatages.
- `CONSENT_WITHDRAW_PREFERENCES` — retirer consentement et préférence dans une transaction.
- `TAG_SEARCH`, `TAG_INSERT_NORMALIZED`, `PROFILE_TAGS_REPLACE` — tags réutilisables.

### Photos et localisation

- `PHOTO_LIST`, `PHOTO_INSERT`, `PHOTO_REORDER`, `PHOTO_SET_MAIN`, `PHOTO_DELETE`.
- `PHOTO_LOCK_FOR_UPDATE` — garantir maximum cinq et une principale si nécessaire.
- `LOCATION_CATALOG_SEARCH` — autocomplétion locale indexée.
- `LOCATION_UPSERT_MANUAL`, `LOCATION_UPSERT_REDUCED_GPS`, `LOCATION_DELETE`.
- `LOCATION_PUBLIC_VIEW` — ne sélectionner que les champs approximatifs autorisés.

### Découverte et recherche

- `SUGGESTIONS_SELECT` — exclure soi-même, bloqués, profils incomplets et incompatibles ;
  priorité absolue à la même zone puis score 50 % proximité, 30 % tags et 20 % popularité.
- `SEARCH_PROFILES_SELECT` — mêmes exclusions avec filtres âge, popularité, localisation et tags.
- `PROFILE_PUBLIC_GET_AUTHORIZED` — profil sans e-mail, date de naissance ni GPS exact.
- `POPULARITY_RECOMPUTE_ONE` — recalcul borné de 0 à 100.
- `POPULARITY_RECOMPUTE_BATCH` — maintenance contrôlée pour plusieurs profils.

La distance utilise les coordonnées réduites et une formule SQL documentée. Le score et ses
sous-scores sont sélectionnés explicitement pour pouvoir expliquer et tester le classement.

### Visites, likes et matchs

- `VISIT_INSERT` — enregistrer chaque consultation humaine autorisée.
- `VISIT_NOTIFICATION_ELIGIBLE` — maximum une notification par paire sur 24 heures.
- `VISITORS_LIST` — historique de 90 jours paginé.
- `LIKE_LOCK_PAIR` — verrouiller la paire d'utilisateurs dans un ordre stable.
- `LIKE_UPSERT_ACTIVE` — like idempotent.
- `LIKE_RECIPROCAL_EXISTS` — détecter la réciprocité active.
- `MATCH_INSERT_IF_ABSENT` — créer un seul match actif.
- `LIKE_DEACTIVATE` — unlike directionnel.
- `MATCH_END` — terminer le match et passer le chat en lecture seule.
- `LIKES_RECEIVED_LIST`, `MATCHES_LIST_ACTIVE` — listes paginées.

### Blocages et signalements

- `BLOCK_LOCK_PAIR`, `BLOCK_INSERT`, `BLOCK_DELETE`.
- `BLOCK_REMOVE_ACTIVE_LIKES_AND_MATCH` — supprimer likes et terminer le match.
- `BLOCK_EXISTS_EITHER_DIRECTION` — filtre commun à toutes les lectures/interactions.
- `BLOCKS_LIST` — liste privée du propriétaire.
- `REPORT_INSERT` — signalement immuable avec motif contrôlé.

### Conversations, messages et notifications

- `CONVERSATIONS_LIST_VISIBLE` — actives ou historiques non masqués.
- `CONVERSATION_GET_AUTHORIZED` — vérifier participant, blocage et état du match.
- `MESSAGE_INSERT_IDEMPOTENT` — unicité auteur + `client_message_id`.
- `MESSAGES_LIST_BEFORE_CURSOR` — pagination stable par date et identifiant.
- `CONVERSATION_MARK_READ` — progression monotone du dernier message lu.
- `CONVERSATION_HIDE_FOR_USER` — masque local, sans suppression chez l'autre utilisateur.
- `NOTIFICATION_INSERT`, `NOTIFICATION_LIST`, `NOTIFICATION_MARK_READ`.
- `NOTIFICATIONS_MARK_ALL_READ`, `NOTIFICATIONS_UNREAD_COUNT`.

### Suppression de compte

- `ACCOUNT_LOCK_FOR_DELETE` — empêcher les nouvelles interactions.
- `ACCOUNT_DELETE_DEPENDENCIES` — supprimer dans un ordre documenté les données non gérées
  par cascade.
- `ACCOUNT_DELETE` — suppression finale.
- La suppression des objets MinIO et la révocation Valkey sont coordonnées par un service ;
  une table d'opérations à reprendre évite de perdre la trace d'un objet si MinIO échoue.

## 13. Transactions critiques

### Like et création de match

1. Vérifier session, profil complet, photo principale, consentement et absence de blocage.
2. Verrouiller la paire dans un ordre stable.
3. Activer le like.
4. Chercher le like réciproque.
5. Créer le match si nécessaire.
6. Créer les notifications dans la même transaction.
7. Après commit seulement, diffuser les événements Socket.IO.

### Unlike

1. Verrouiller la paire et désactiver le like sortant.
2. Terminer le match actif et désactiver l'envoi dans la conversation.
3. Créer la notification de fin de match.
4. Commit, puis diffuser les changements.

### Blocage

1. Verrouiller la paire et créer le blocage.
2. Désactiver les likes, terminer le match et rendre la conversation inaccessible.
3. Supprimer les notifications futures visibles entre les deux comptes selon `TASKS.md`.
4. Commit, puis retirer les rooms Socket.IO concernées.

## 14. Index minimaux à prévoir

- Comptes : username normalisé unique, e-mail normalisé unique.
- Tokens : hash unique, type, expiration et consommation.
- Tags : nom normalisé unique ; index de recherche adapté.
- Préférences : `(user_id, desired_gender)` unique.
- Photos : `(user_id, position)` unique et index principal partiel par utilisateur.
- Likes et blocages : `(source_user_id, target_user_id)` unique et index inverse.
- Matchs : paire canonique unique et index des matchs actifs.
- Visites : profil visité + date, visiteur + date.
- Messages : conversation + date + id ; auteur + client_message_id unique.
- Notifications : destinataire + état lu + date.
- Localisation : zone/catalogue et colonnes nécessaires au calcul de distance.

Les index définitifs doivent être confirmés avec `EXPLAIN`; éviter les index sans requête
réelle correspondante.

## 15. Bonus — endpoints isolés

Ils ne sont ajoutés qu'après validation complète de la mandatory :

- Google OIDC : `/api/v1/auth/oidc/google/start` et `/callback`.
- Galerie bonus : `/api/v1/gallery/images` et opérations d'édition non destructives.
- Carte : réutilise `/search/profiles` avec une représentation approximative, sans GPS exact.
- Audio/vidéo : endpoint de création d'appel et événements de signalisation dédiés.
- Rendez-vous : CRUD limité aux utilisateurs matchés et notifications associées.

Les migrations, routes, tables et composants bonus restent séparés et ne modifient pas le
contrat obligatoire existant.

## 16. Checklist avant d'implémenter un endpoint

- [ ] Exigence du sujet et scénario associés identifiés.
- [ ] Authentification, CSRF et autorisation définis.
- [ ] Schéma d'entrée et champs autorisés définis.
- [ ] Requêtes SQL nécessaires nommées et paramétrées.
- [ ] Transaction et verrous déterminés si plusieurs écritures sont liées.
- [ ] Données publiques et privées séparées.
- [ ] Codes HTTP et erreurs attendues définis.
- [ ] Rate limit et journalisation sûre décidés.
- [ ] Tests nominal, invalide, interdit, bloqué et concurrence prévus.
- [ ] Événement temps réel diffusé uniquement après commit.
