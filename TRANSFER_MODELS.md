# Matcha — formats et modèles des données en transit

Ce document est le contrat d'échange entre React, Flask, Socket.IO, PostgreSQL, Valkey et
MinIO. Il complète `API_AND_QUERIES.md` et `DATA_MODEL.md`.

Les modèles ci-dessous sont des contrats, pas des tables SQL. Ils doivent être implémentés :

- côté frontend avec des types TypeScript et des fonctions de décodage aux frontières ;
- côté backend avec des fonctions Python explicites de parsing, validation et sérialisation ;
- sans ORM ni framework automatique de validation qui masquerait les règles du sujet.

## 1. Formats par canal

| Canal | Format | Encodage et protection |
| --- | --- | --- |
| React ↔ Flask | JSON | UTF-8 sur HTTPS |
| Upload photo | `multipart/form-data` | fichier binaire sur HTTPS |
| Lecture photo | JPEG, PNG ou WebP réencodé | réponse binaire autorisée |
| React ↔ Socket.IO | événements avec payload JSON | WebSocket sécurisé, fallback contrôlé |
| Session | cookie opaque | `HttpOnly`, `Secure` en production, `SameSite=Lax` |
| CSRF | en-tête `X-CSRF-Token` | lié à la session |
| Export personnel | fichier JSON UTF-8 | téléchargement authentifié |
| Flask ↔ PostgreSQL | paramètres et types SQL natifs | psycopg 3, jamais de concaténation |
| Flask ↔ Valkey | chaînes/JSON minimal avec TTL | réseau interne et authentification |
| Flask ↔ MinIO | flux binaire S3 | bucket privé, clé opaque |
| Flask ↔ SMTP | message MIME | TLS en production |

Le JSON ne transporte jamais `NaN`, `Infinity`, tuple Python, objet `datetime` brut ou octets
Base64 pour une photo.

## 2. Conventions primitives

Les exemples utilisent une notation proche de TypeScript :

```text
Uuid       = string au format UUID canonique
DateOnly   = string "YYYY-MM-DD"
UtcDateTime = string ISO 8601 UTC, par exemple "2026-08-04T19:04:12Z"
Cursor     = string opaque ; le client ne l'interprète pas
```

- Tous les identifiants sont des chaînes UUID.
- Tous les timestamps sortants sont en UTC avec suffixe `Z`.
- Une date de naissance utilise `DateOnly`, jamais un timestamp.
- Un champ absent facultatif est omis ; `null` est réservé à une valeur connue comme absente.
- Les nombres sont des nombres JSON, jamais des chaînes avec unité.
- Les textes sont du texte brut ; React les échappe à l'affichage.
- Les enums sont des chaînes stables en anglais, traduites uniquement dans l'interface.
- Les propriétés JSON utilisent `snake_case` pour correspondre clairement au backend.

## 3. Enveloppes communes

### `DataResponse<T>`

```json
{ "data": {} }
```

### `ListResponse<T>`

```json
{
  "data": [],
  "pagination": {
    "next_cursor": null,
    "has_more": false
  }
}
```

### `ErrorResponse`

```json
{
  "error": {
    "code": "validation_error",
    "message": "Certains champs sont invalides.",
    "fields": { "birth_date": "Vous devez avoir au moins 18 ans." },
    "request_id": "81c7d0a6-a91c-4543-b51e-f07b116b677d"
  }
}
```

`fields` est facultatif. Aucun traceback, SQL, nom de service interne ou secret n'est renvoyé.

### `NoContentResponse`

Réponse HTTP `204` sans corps. Ne jamais envoyer un faux objet JSON vide avec un statut 204.

### `PaginationQuery`

```text
cursor?: Cursor
limit?: integer, défaut 20, minimum 1, maximum 50
```

Le curseur est signé ou opaque et encode un ordre stable sans exposer de donnée sensible.

## 4. Modèles d'identité et de session

### `RegisterRequest`

```text
first_name: string
last_name: string
username: string
email: string
birth_date: DateOnly
password: string
```

### `RegistrationResult`

```text
account_id: Uuid
status: "pending_verification"
verification_email_sent: boolean
```

### `TokenRequest`

```text
token: string
```

Le token brut n'apparaît jamais dans une réponse ou un log.

### `EmailRequest`

```text
email: string
```

La réponse reste identique que le compte existe ou non.

### `LoginRequest`

```text
username: string
password: string
```

### `SessionUser`

```text
id: Uuid
username: string
first_name: string
account_status: "pending_verification" | "active" | "deletion_pending"
profile_complete: boolean
has_main_photo: boolean
matching_enabled: boolean
```

### `SessionResponse`

```text
user: SessionUser
csrf_token: string
expires_at: UtcDateTime
```

Le cookie de session est posé séparément dans `Set-Cookie`. Il n'est jamais recopié en JSON.

### `ForgotPasswordRequest`

Alias de `EmailRequest`.

### `ResetPasswordRequest`

```text
token: string
new_password: string
```

### `ChangePasswordRequest`

```text
current_password: string
new_password: string
```

### `ChangeEmailRequest`

```text
new_email: string
current_password: string
```

### `DeleteAccountRequest`

```text
current_password?: string
confirmation: "DELETE"
```

Une réauthentification récente peut remplacer `current_password`. Le serveur décide, jamais
le client.

## 5. Modèles de profil

### `Gender`

```text
"man" | "woman" | "non_binary"
```

### `PrivateProfile`

```text
id: Uuid
username: string
email: string
pending_email: string | null
first_name: string
last_name: string
birth_date: DateOnly
gender: Gender | null
bio: string | null
desired_genders: Gender[]
tags: TagSummary[]
photos: PhotoSummary[]
location: PrivateLocation | null
consents: ConsentState[]
profile_complete: boolean
missing_profile_fields: string[]
created_at: UtcDateTime
updated_at: UtcDateTime
```

Ce modèle est privé. Il n'est jamais utilisé pour afficher le profil d'un autre membre.

### `UpdateProfileRequest`

Tous les champs sont facultatifs, mais seuls ceux de cette allowlist sont acceptés :

```text
first_name?: string
last_name?: string
birth_date?: DateOnly
gender?: Gender
bio?: string
```

### `UpdatePreferencesRequest`

```text
desired_genders: Gender[]
```

Le tableau peut être vide uniquement pour signifier « tous les genres » avec consentement
sensible actif. Les doublons sont refusés ou normalisés explicitement.

### `PublicProfile`

```text
id: Uuid
username: string
first_name: string
last_name: string
age: integer
gender: Gender
desired_genders: Gender[]
bio: string
tags: TagSummary[]
photos: PublicPhoto[]
location: PublicLocation
popularity: integer
presence: Presence
viewer_state: ViewerProfileState
```

Conformément au sujet, le profil autorisé affiche les informations disponibles, mais jamais
e-mail, date de naissance exacte, consentements, coordonnées GPS ou clés MinIO.

### `ViewerProfileState`

```text
liked_by_me: boolean
likes_me: boolean
matched: boolean
match_id: Uuid | null
can_like: boolean
can_message: boolean
```

Ces valeurs sont calculées côté serveur. Le frontend ne les déduit pas de manière autoritaire.

## 6. Tags et consentements

### `TagSummary`

```text
id: Uuid
name: string
```

### `TagSearchQuery`

```text
query: string
limit?: integer, maximum 20
```

### `CreateTagRequest`

```text
name: string
```

### `ReplaceProfileTagsRequest`

```text
tag_ids: Uuid[]
```

Au moins un tag est nécessaire à la complétude ; les doublons sont interdits.

### `ConsentPurpose`

```text
"matching_preferences" | "gps_location"
```

### `ConsentState`

```text
purpose: ConsentPurpose
granted: boolean
policy_version: string
occurred_at: UtcDateTime
```

### `GrantConsentRequest`

```text
policy_version: string
confirmed: true
```

Chaque finalité utilise son propre endpoint. Aucun modèle ne regroupe les deux cases dans une
acceptation unique et elles ne sont jamais précochées.

## 7. Photos

### `PhotoUploadRequest`

Requête `multipart/form-data` :

```text
file: flux binaire JPEG, PNG ou WebP
```

Limites : 5 Mio, 4096 × 4096, pas de SVG ni GIF animé. Le type déclaré n'est pas fiable :
Pillow décode, supprime EXIF et réencode avant MinIO.

### `PhotoSummary`

```text
id: Uuid
url: string
position: integer 1..5
is_main: boolean
width: integer
height: integer
```

`url` pointe vers l'API autorisée ou une URL signée de cinq minutes. `object_key`, bucket,
chemin local et métadonnées EXIF sont interdits dans le transfert public.

### `PublicPhoto`

```text
id: Uuid
url: string
position: integer
is_main: boolean
```

### `UpdatePhotoRequest`

```text
position?: integer 1..5
is_main?: boolean
```

Le serveur maintient exactement une principale dès qu'au moins une photo existe.

## 8. Localisation

### `LocationSuggestion`

```text
id: Uuid
city: string
district: string | null
country_code: string
label: string
```

### `ManualLocationRequest`

```text
catalog_location_id: Uuid
```

### `GpsLocationRequest`

```text
latitude: number entre -90 et 90
longitude: number entre -180 et 180
```

Les coordonnées exactes ne sont utilisées que le temps de les réduire côté serveur. Elles ne
sont ni renvoyées au frontend ni conservées telles quelles.

### `PrivateLocation`

```text
source: "manual" | "gps_reduced"
catalog_location_id: Uuid
city: string
district: string | null
updated_at: UtcDateTime
```

Même le modèle privé ne renvoie pas les coordonnées réduites si l'écran n'en a pas besoin.

### `PublicLocation`

```text
city: string
district: string | null
distance_km: number | null
same_zone: boolean
```

La distance est arrondie ; aucune latitude ou longitude n'est incluse.

## 9. Découverte et recherche

### `DiscoveryQuery`

```text
cursor?: Cursor
limit?: integer 1..50
sort?: "recommended" | "age" | "distance" | "tags" | "popularity"
age_min?: integer, minimum 18
age_max?: integer
distance_max_km?: number
popularity_min?: integer 0..100
popularity_max?: integer 0..100
tag_ids?: Uuid[]
```

### `SearchProfilesQuery`

Même modèle, avec :

```text
location_id?: Uuid
```

Aucun champ `orientation` ou `desired_genders` n'est accepté comme filtre public. La
compatibilité mutuelle est appliquée automatiquement côté serveur.

### `ProfileCard`

```text
id: Uuid
first_name: string
age: integer
main_photo: PublicPhoto | null
tags: TagSummary[]
location: PublicLocation
popularity: integer 0..100
presence: Presence
```

### `Presence`

```text
online: boolean
last_seen_at: UtcDateTime | null
```

Le statut ou la dernière connexion reste visible comme demandé par le sujet.

## 10. Visites, likes et matchs

### `VisitorItem`

```text
visitor: ProfileCard
visited_at: UtcDateTime
```

### `LikeReceivedItem`

```text
user: ProfileCard
liked_at: UtcDateTime
```

### `InteractionResult`

```text
target_user_id: Uuid
liked_by_me: boolean
matched: boolean
match: MatchSummary | null
```

### `MatchSummary`

```text
id: Uuid
other_user: ProfileCard
status: "active" | "ended_unlike" | "ended_block"
created_at: UtcDateTime
ended_at: UtcDateTime | null
conversation_id: Uuid
```

### `BlockSummary`

```text
user_id: Uuid
username: string
blocked_at: UtcDateTime
```

### `CreateReportRequest`

```text
reason: "fake_account" | "harassment" | "inappropriate_content" | "other"
description?: string
```

Le motif `fake_account` couvre explicitement l'obligation du sujet. Le texte est borné et
échappé à l'affichage.

## 11. Conversations et messages

### `ConversationSummary`

```text
id: Uuid
match_id: Uuid
other_user: ProfileCard
can_send: boolean
read_only_reason: "unlike" | null
last_message: Message | null
unread_count: integer
updated_at: UtcDateTime
```

Une conversation bloquée n'est pas sérialisée : elle devient inaccessible.

### `Message`

```text
id: Uuid
conversation_id: Uuid
author_id: Uuid
body: string
created_at: UtcDateTime
```

### `SendMessageRequest`

```text
client_message_id: Uuid
body: string
```

L'endpoint HTTP tire `conversation_id` du chemin ; l'événement Socket.IO l'inclut dans son
payload. Le serveur n'accepte jamais `author_id` envoyé par le client.

### `ReadConversationRequest`

```text
message_id: Uuid
```

### `MessagePageQuery`

```text
before?: Cursor
limit?: integer 1..50
```

## 12. Notifications

### `NotificationType`

```text
"like_received" | "profile_visited" | "match_created" |
"message_received" | "match_ended"
```

### `Notification`

```text
id: Uuid
type: NotificationType
actor: { id: Uuid, first_name: string, main_photo_url: string | null }
created_at: UtcDateTime
read_at: UtcDateTime | null
target: {
  profile_id?: Uuid
  match_id?: Uuid
  conversation_id?: Uuid
  message_id?: Uuid
}
```

`target` contient seulement les identifiants nécessaires au type. Si l'objet est devenu
inaccessible par blocage, la notification n'est pas envoyée.

### `UnreadCount`

```text
unread_count: integer
```

## 13. Événements Socket.IO

Namespace : `/realtime`.

### Client → serveur

```text
message:send       { conversation_id: Uuid, client_message_id: Uuid, body: string }
conversation:read  { conversation_id: Uuid, message_id: Uuid }
presence:heartbeat {}
```

### Serveur → client

```text
message:ack          { client_message_id: Uuid, message: Message }
message:new          { message: Message }
conversation:updated { conversation_id: Uuid, can_send: boolean, read_only_reason: "unlike" | null }
notification:new     { notification: Notification }
notification:count   { unread_count: integer }
presence:updated     { user_id: Uuid, presence: Presence }
session:expired      { code: "inactive_timeout" | "absolute_timeout" | "revoked" }
```

Chaque payload entrant est validé comme une requête HTTP. Un événement n'autorise jamais une
action que l'endpoint équivalent refuserait.

## 14. Export personnel

### `PersonalDataExport`

Fichier `application/json; charset=utf-8` :

```text
exported_at: UtcDateTime
account: informations privées du compte sans password_hash
profile: PrivateProfile
consent_history: ConsentState[]
visits: événements encore présents dans la rétention de 90 jours
likes: relations de l'utilisateur
matches: historique de matchs
messages: messages écrits ou reçus encore stockés
notifications: notifications encore stockées
reports_submitted: signalements soumis selon les droits applicables
photos: métadonnées et références de téléchargement autorisées
```

Les tokens, sessions, secrets, valeurs Valkey, clés MinIO, données internes de modération et
informations privées d'autres personnes ne sont pas exportés.

## 15. Modèles transportés vers les services internes

### Flask → PostgreSQL

- UUID Python transmis comme paramètre UUID psycopg.
- `date` et `datetime` timezone-aware transmis comme types natifs.
- Listes de genres/tags écrites par opérations paramétrées ou `executemany` contrôlé.
- Aucune requête SQL complète n'est construite depuis une chaîne utilisateur.
- Les lignes SQL sont converties explicitement en modèles de réponse allowlistés.

### Flask → Valkey

```text
session:{opaque_id}       JSON minimal de session, TTL glissant et absolu
presence:{user_id}        timestamp UTC, TTL 2 minutes
rate:{action}:{subject}   compteur entier, TTL de fenêtre
idem:{user_id}:{event_id} résultat minimal, TTL 24 heures
```

Ne jamais y mettre mot de passe, contenu de message, coordonnées GPS ou profil complet.

### Flask → MinIO

```text
object key: profiles/{user_uuid}/{photo_uuid}.{extension_reencoded}
body: flux binaire réencodé
metadata: content-type et dimensions minimales
```

Le bucket est privé. La clé n'est pas une donnée publique et n'est jamais choisie par le client.

### Flask → SMTP

Message MIME avec destinataire, sujet et HTML/texte. Les liens contiennent le token brut à
usage unique uniquement dans l'URL envoyée ; les logs et PostgreSQL n'en gardent que le hash.

## 16. Correspondance exhaustive endpoints → modèles

### Système et authentification

| Endpoint | Entrée | Sortie |
| --- | --- | --- |
| `GET /health/live`, `/health/ready` | aucune | état minimal |
| `GET /csrf` | cookie session | `csrf_token` |
| `POST /auth/register` | `RegisterRequest` | `RegistrationResult` |
| `POST /auth/verify-email` | `TokenRequest` | `SessionUser` |
| `POST /auth/resend-verification` | `EmailRequest` | message neutre |
| `POST /auth/login` | `LoginRequest` | `SessionResponse` + cookie |
| `POST /auth/logout` | CSRF | 204 |
| `GET /auth/session` | cookie | `SessionResponse` |
| `POST /auth/forgot-password` | `ForgotPasswordRequest` | message neutre |
| `POST /auth/reset-password` | `ResetPasswordRequest` | 204 |
| `PATCH /account/email` | `ChangeEmailRequest` | état pending |
| `POST /account/email/confirm` | `TokenRequest` | `SessionUser` |
| `PATCH /account/password` | `ChangePasswordRequest` | 204 |
| `GET /account/export` | aucune | `PersonalDataExport` |
| `DELETE /account` | `DeleteAccountRequest` | 204 |

Tous les chemins de cette section, sauf santé, utilisent le préfixe `/api/v1`.

### Profil, médias et localisation

| Endpoint | Entrée | Sortie |
| --- | --- | --- |
| `GET /me/profile` | aucune | `PrivateProfile` |
| `PATCH /me/profile` | `UpdateProfileRequest` | `PrivateProfile` |
| `PUT /me/preferences` | `UpdatePreferencesRequest` | `PrivateProfile` |
| `DELETE /me/preferences` | aucune | 204 |
| `GET /me/consents` | aucune | `ConsentState[]` |
| `PUT /me/consents/{purpose}` | `GrantConsentRequest` | `ConsentState` |
| `DELETE /me/consents/{purpose}` | aucune | `ConsentState` |
| `GET /tags` | `TagSearchQuery` | `TagSummary[]` |
| `POST /tags` | `CreateTagRequest` | `TagSummary` |
| `PUT /me/tags` | `ReplaceProfileTagsRequest` | `TagSummary[]` |
| `GET /me/photos` | aucune | `PhotoSummary[]` |
| `POST /me/photos` | `PhotoUploadRequest` | `PhotoSummary` |
| `PATCH /me/photos/{id}` | `UpdatePhotoRequest` | `PhotoSummary[]` |
| `DELETE /me/photos/{id}` | aucune | 204 |
| `GET /photos/{id}` | aucune | image binaire autorisée |
| `GET /locations` | query texte | `LocationSuggestion[]` |
| `GET /me/location` | aucune | `PrivateLocation | null` |
| `PUT /me/location/manual` | `ManualLocationRequest` | `PrivateLocation` |
| `PUT /me/location/gps` | `GpsLocationRequest` | `PrivateLocation` |
| `DELETE /me/location` | aucune | 204 |

`{purpose}` représente les deux endpoints distincts définis dans `API_AND_QUERIES.md`, pas
une finalité arbitraire fournie par le client.

### Découverte, interactions et modération

| Endpoint | Entrée | Sortie |
| --- | --- | --- |
| `GET /discovery/suggestions` | `DiscoveryQuery` | `ListResponse<ProfileCard>` |
| `GET /search/profiles` | `SearchProfilesQuery` | `ListResponse<ProfileCard>` |
| `GET /profiles/{id}` | aucune | `PublicProfile` |
| `GET /me/visitors` | pagination/période | `ListResponse<VisitorItem>` |
| `GET /me/likes-received` | pagination | `ListResponse<LikeReceivedItem>` |
| `POST /profiles/{id}/like` | aucune | `InteractionResult` |
| `DELETE /profiles/{id}/like` | aucune | `InteractionResult` |
| `GET /matches` | pagination | `ListResponse<MatchSummary>` |
| `GET /matches/{id}` | aucune | `MatchSummary` |
| `POST /profiles/{id}/block` | aucune | `BlockSummary` |
| `DELETE /profiles/{id}/block` | aucune | 204 |
| `GET /me/blocks` | pagination | `ListResponse<BlockSummary>` |
| `POST /profiles/{id}/reports` | `CreateReportRequest` | identifiant du signalement |

### Messages et notifications

| Endpoint | Entrée | Sortie |
| --- | --- | --- |
| `GET /conversations` | pagination | `ListResponse<ConversationSummary>` |
| `GET /conversations/{id}` | aucune | `ConversationSummary` |
| `GET /conversations/{id}/messages` | `MessagePageQuery` | `ListResponse<Message>` |
| `POST /conversations/{id}/messages` | `SendMessageRequest` | `Message` |
| `POST /conversations/{id}/read` | `ReadConversationRequest` | 204 |
| `POST /conversations/{id}/hide` | aucune | 204 |
| `GET /notifications` | pagination | `ListResponse<Notification>` |
| `GET /notifications/unread-count` | aucune | `UnreadCount` |
| `POST /notifications/{id}/read` | aucune | `Notification` |
| `POST /notifications/read-all` | aucune | `UnreadCount` |

Les chemins des trois dernières sections utilisent tous `/api/v1`.

## 17. Données interdites selon le contexte

| Contexte | Données interdites |
| --- | --- |
| Profil public | e-mail, naissance exacte, consentements, GPS, hash, tokens |
| Carte de suggestion | nom de famille si non nécessaire, préférences détaillées, GPS exact |
| Notification | contenu complet du profil ou données privées de l'acteur |
| Socket de présence | e-mail, localisation, session, adresse IP |
| Logs | mot de passe, token brut, cookie, message, GPS, photo |
| Valkey | profil complet, message durable, préférence sensible, GPS |
| URL photo | bucket, credentials, clé interne durable |

## 18. Vérifications de cohérence

- Les maquettes demandent une date de naissance, mais les profils publics reçoivent seulement
  l'âge calculé.
- Les maquettes rendent les photos facultatives ; `main_photo` est donc nullable sur les cartes.
- Le like sans photo est refusé via `viewer_state.can_like`, vérifié à nouveau par Flask.
- Les consentements GPS et préférences utilisent deux transferts séparés.
- La recherche n'accepte aucun filtre public d'orientation.
- La localisation publique ne transporte jamais de coordonnées.
- Le statut en ligne ou la dernière connexion est fourni par `Presence` sans option permettant
  de le masquer.
- L'unlike produit une conversation `can_send=false`; le blocage ne sérialise plus la conversation.
- La session expirée est un événement distinct et permet la reconnexion.
- Les cinq notifications correspondent exactement au sujet et à `API_AND_QUERIES.md`.
- Les messages persistés sont confirmés avant `message:ack` et restent disponibles dans
  l'historique autorisé.
- Les objets JSON correspondent aux colonnes de `DATA_MODEL.md`, mais n'exposent jamais une
  ligne SQL complète.
- Les bonus n'ajoutent aucun champ au contrat obligatoire avant leur activation.

## 19. Checklist d'implémentation d'un modèle

- [ ] Type TypeScript défini sans `any`.
- [ ] Décodeur frontend vérifie la réponse reçue à la frontière réseau.
- [ ] Parseur/validateur Python explicite défini pour l'entrée.
- [ ] Allowlist de sérialisation Python définie pour la sortie.
- [ ] Limites de longueur, enum et nombres vérifiées côté Flask.
- [ ] Données sensibles absentes des réponses et des logs.
- [ ] Exemple JSON et test de contrat ajoutés.
- [ ] Erreur de champ au format `ErrorResponse` testée.
- [ ] Endpoint, requêtes SQL et règles métier liés dans le nom du test.
- [ ] Événement Socket.IO testé avec les mêmes permissions que l'endpoint HTTP.
