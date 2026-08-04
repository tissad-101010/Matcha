# Matcha — scénarios UX et écrans

Ce document décrit l'expérience utilisateur complète de Matcha. Il traduit la mandatory
en écrans, transitions, états et cas limites vérifiables. Les bonus sont isolés à la fin et
ne doivent pas perturber ces parcours.

## Références visuelles

La fiche [UX_BUILD_SPEC.md](UX_BUILD_SPEC.md) constitue le contrat d'interface utilisé
pendant le build. Les planches ci-dessous l'illustrent.

| Parcours | Planche |
| --- | --- |
| Authentification et onboarding | [ux-01-auth-onboarding-v2.png](docs/mockups/ux-01-auth-onboarding-v2.png) |
| Découverte, recherche, profil et matching | [ux-02-discovery-matching-v2.png](docs/mockups/ux-02-discovery-matching-v2.png) |
| Messages et notifications | [ux-03-messaging-notifications-v2.png](docs/mockups/ux-03-messaging-notifications-v2.png) |
| Profil, confidentialité et états système | [ux-04-profile-privacy-system-v2.png](docs/mockups/ux-04-profile-privacy-system-v2.png) |
| Direction visuelle principale | [matcha-discovery-dashboard.png](docs/mockups/matcha-discovery-dashboard.png) |

Les images sont des références d'intention. En cas de divergence, l'ordre d'autorité est :
sujet PDF, `TASKS.md`, le présent document, `UX_BUILD_SPEC.md`, puis texte généré dans
une image.

## Principes UX globaux

- L'en-tête donne toujours accès à Découvrir, Recherche, Messages, Activité, Profil et Déconnexion.
- Messages et notifications non lus sont visibles depuis toute page authentifiée.
- Chaque écran possède les états chargement, succès, vide, erreur et indisponible pertinents.
- Toute action destructive demande confirmation et explique ses conséquences.
- Les validations frontend assistent l'utilisateur ; le backend reste l'autorité.
- Aucun écran public n'affiche e-mail, mot de passe, secret ou coordonnées GPS précises.
- Le statut et les actions affichés doivent correspondre à l'état réel du backend.
- Une action réussie fournit un retour immédiat sans masquer les changements importants.
- La navigation au clavier, le focus visible, les labels et le contraste sont obligatoires.
- Sur mobile, la navigation principale devient une barre basse ; les filtres utilisent un panneau.
- Aucun paiement, abonnement ou paywall ne bloque une fonctionnalité mandatory.
- Aucun champ de religion, origine ethnique, santé ou statut parental n'est demandé.
- La recherche ne propose pas de filtre public d'orientation : la compatibilité mutuelle
  est appliquée automatiquement côté serveur.
- Aucun réglage ne permet de masquer le statut en ligne ou la dernière connexion exigés.
- Un profil est visible uniquement par les membres authentifiés autorisés, jamais présenté
  comme public à « tout le monde ».
- L'interface ne revendique pas de chiffrement de bout en bout s'il n'est pas implémenté.

## États utilisateur structurants

| État | Accès autorisé |
| --- | --- |
| Visiteur | Inscription, connexion, mot de passe oublié, informations légales |
| Compte non vérifié | Écran de vérification, renvoi de l'e-mail, déconnexion |
| Compte vérifié, profil incomplet | Onboarding et paramètres nécessaires à la complétion |
| Profil complet sans photo | Découverte, recherche et consultation ; like interdit |
| Profil complet avec photo principale | Toutes les fonctions hors chat sans match |
| Match actif | Chat et interactions normales avec ce match |
| Après unlike | Conversation passée en lecture seule, aucun nouvel envoi |
| Utilisateur bloqué | Aucun profil, message, résultat ou notification entre les deux comptes |
| Session expirée | Écran de reconnexion ; socket fermée et action courante interrompue sûrement |

---

## Parcours A — inscription, vérification et connexion

### A1 — Arrivée d'un visiteur

1. Le visiteur arrive sur la connexion.
2. Il voit la promesse du service, la restriction 18+ et les liens légaux.
3. Il peut se connecter, créer un compte ou demander un nouveau mot de passe.

Écrans : connexion desktop/mobile, footer légal.

Cas limites : session déjà active redirigée vers Découvrir ; URL privée mémorisée puis
restaurée après connexion si elle reste autorisée.

### A2 — Inscription valide

1. L'utilisateur saisit prénom, nom, username, e-mail, date de naissance et mot de passe.
2. Les règles sont affichées avant soumission.
3. Après validation serveur, un compte non vérifié est créé.
4. L'écran « Vérifiez votre e-mail » confirme l'envoi sans exposer de secret.

Résultat : seul l'écran de vérification reste accessible jusqu'à activation.

### A3 — Erreurs d'inscription

- Moins de 18 ans : inscription refusée, aucun compte créé.
- E-mail ou username existant : erreur sur le champ, formulation qui limite l'énumération.
- Mot anglais courant : explication courte et proposition de choisir une phrase plus forte.
- Mot de passe faible : indicateur et critères non satisfaits.
- Champs invalides : focus placé sur la première erreur avec résumé accessible.
- Serveur indisponible : saisie conservée sauf mots de passe, bouton Réessayer.

### A4 — Vérification de l'e-mail

- Lien valide : compte activé, succès, bouton « Compléter mon profil ».
- Lien expiré : explication et renvoi d'un nouveau lien.
- Lien déjà utilisé : succès idempotent si le compte est activé.
- Lien invalide : erreur neutre, aucun détail sur le jeton.
- Renvoi répété : limitation de débit avec délai lisible.

### A5 — Connexion

- Identifiants valides et compte vérifié : rotation de session puis Découvrir ou onboarding.
- Compte non vérifié : écran de vérification et option de renvoi.
- Identifiants invalides : message générique, sans préciser username ou mot de passe.
- Trop de tentatives : attente temporaire expliquée sans bloquer définitivement le compte.
- Session expirée : connexion puis retour vers la destination autorisée.

### A6 — Mot de passe oublié

1. L'utilisateur saisit son e-mail.
2. Le même résultat est affiché que le compte existe ou non.
3. Le lien est valide 30 minutes et une seule fois.
4. Le nouveau mot de passe respecte les règles normales.
5. Les anciennes sessions sont révoquées et l'utilisateur se reconnecte normalement.

Cas limites : jeton expiré, déjà utilisé, modifié, demande trop fréquente et mots de passe
de confirmation différents.

---

## Parcours B — onboarding et profil complet

### B1 — Progression

Étapes : Identité → Préférences → À propos → Centres d'intérêt → Photos → Localisation.

- La progression est sauvegardée après chaque étape.
- Retour et reprise ultérieure sont possibles.
- Un résumé indique ce qui manque encore.
- Les étapes obligatoires ne peuvent pas être contournées par une URL directe.

### B2 — Identité et âge

- Genre requis : homme, femme ou non-binaire.
- Date de naissance non publique ; seul l'âge calculé est visible.
- Toute modification est validée côté serveur.

### B3 — Préférences sensibles

1. Une information concise explique la finalité de matching.
2. Le consentement explicite est séparé, non précoché, daté et versionné.
3. Une préférence explicite contient un ou plusieurs genres recherchés.
4. Si l'utilisateur consent mais ne précise rien, la valeur effective est tous les genres.
5. Sans consentement actif, recherche, suggestions et matching restent suspendus.

### B4 — Biographie et tags

- Biographie non vide avec compteur de caractères.
- Tags réutilisables proposés et recherchables localement.
- Au moins un tag est requis pour le profil complet.
- Création contrôlée d'un nouveau tag, normalisation et prévention des doublons.
- HTML/script affiché comme texte, jamais exécuté.

### B5 — Photos

- Zéro à cinq photos sont autorisées.
- Dès qu'une photo existe, exactement une est principale.
- Ajout JPEG, PNG ou WebP ; progression et erreurs par fichier.
- Réorganisation et changement de photo principale.
- Sixième photo refusée avant upload.
- Format, poids, dimensions ou contenu invalide : erreur sans conserver l'objet.
- Sans photo principale, un message explique que le like restera indisponible.

### B6 — Localisation GPS acceptée

1. L'écran explique finalité et précision avant la permission navigateur.
2. L'utilisateur donne un consentement explicite séparé.
3. Les coordonnées sont réduites à une précision de quartier.
4. Seuls ville/quartier approximatifs sont montrés.
5. En cas d'échec de géocodage, le matching par distance reste possible et une saisie
   manuelle complète le libellé.

### B7 — GPS refusé, indisponible ou retiré

- Ville ou quartier manuel devient obligatoire pour le matching.
- Le catalogue local fonctionne sans Internet.
- Le refus n'empêche pas la complétion si une localisation manuelle est fournie.
- Le retrait supprime les coordonnées GPS et réaffiche immédiatement le formulaire manuel.

### B8 — Fin de l'onboarding

- Profil complet : accès à Découvrir.
- Profil incomplet : résumé actionnable des champs manquants.
- Profil sans photo : accès autorisé, bannière discrète expliquant la limite du like.

---

## Parcours C — découverte et suggestions

### C1 — Liste normale

- Profils compatibles uniquement dans les deux sens.
- Même ville/quartier prioritaire.
- Chaque carte affiche photo principale, prénom, âge, ville/distance approximative,
  tags communs, popularité et statut/dernière connexion.
- L'ordre par défaut combine proximité, tags et popularité.

### C2 — Tri

L'utilisateur peut trier par âge, localisation/distance, popularité ou tags communs.
Le tri ne réintroduit jamais un profil incompatible, incomplet ou bloqué.

### C3 — Filtres

- Tranche d'âge.
- Localisation/distance.
- Plage de popularité.
- Nombre ou sélection de tags communs.
- Résultat actualisé, nombre de profils annoncé et filtres réinitialisables.

### C4 — États de la découverte

- Chargement : skeleton sans faux contenu interactif.
- Aucun résultat : expliquer les filtres trop restrictifs et proposer de les élargir.
- Erreur : conserver les filtres et permettre Réessayer.
- Hors ligne : conserver les dernières données non sensibles mises en cache, actions d'écriture désactivées.
- Fin de liste : message clair, aucune boucle trompeuse.

---

## Parcours D — recherche avancée

### D1 — Recherche combinée

L'utilisateur sélectionne un ou plusieurs critères : âge, popularité, localisation et tags.
Les critères peuvent être combinés, retirés et réinitialisés.

### D2 — Résultats

- Même présentation essentielle que les suggestions.
- Tri et filtres disponibles selon les quatre critères obligatoires.
- Pagination stable et retour conservant la recherche.

### D3 — Cas limites

- Aucun critère : recherche large mais compatible et paginée.
- Valeurs incohérentes : erreur inline avant requête.
- Aucun résultat : modifier ou réinitialiser les filtres.
- Profil bloqué entre requête et affichage : retiré sans erreur visible.

---

## Parcours E — consultation d'un profil

### E1 — Profil disponible

Afficher toutes les données disponibles autorisées : username, prénom, nom, âge, genre,
préférences, bio, tags, localisation approximative, photos, popularité et présence.
Ne jamais afficher e-mail, mot de passe, jetons ou coordonnées exactes.

Chaque consultation humaine crée une visite. La notification au propriétaire est limitée
à une par paire sur 24 heures, mais l'historique enregistre les consultations réelles.

### E2 — États relationnels affichés

- Aucun like.
- L'utilisateur courant a liké ce profil.
- Ce profil a liké l'utilisateur courant : « Vous plaît aussi ».
- Match actif : « Connexion établie » et accès au chat.
- Après unlike : connexion terminée.
- Bloqué/inaccessible : profil indisponible.

### E3 — Like normal

1. L'utilisateur possède une photo principale.
2. Le like est enregistré une seule fois.
3. Le destinataire reçoit une notification en moins de 10 secondes.
4. Si le like est mutuel, l'écran de match propose Envoyer un message ou Voir le profil.

### E4 — Like sans photo

- Bouton désactivé ou interception explicative.
- Message « Ajoutez une photo principale pour liker ».
- Lien direct vers Mes photos.
- Aucun like ni notification créé côté serveur.

### E5 — Unlike/déconnexion

1. Confirmation avec conséquences.
2. Like sortant désactivé et match terminé.
3. Ancien match notifié.
4. Chat passe en lecture seule.
5. Notifications futures de l'autre profil vers l'auteur supprimées jusqu'à nouveau match.

### E6 — Blocage

1. Confirmation indiquant recherche, chat et notifications supprimés.
2. Likes supprimés, match terminé, conversation inaccessible.
3. Les deux profils disparaissent de leurs résultats respectifs.
4. Le déblocage ultérieur ne restaure aucune relation.

### E7 — Signalement de faux compte

- Action distincte du blocage.
- Confirmation et motif facultatif limité.
- Succès neutre, sans révéler le traitement de modération.
- Proposition séparée de bloquer le compte.
- Doubles soumissions empêchées.

---

## Parcours F — chat

### F1 — Boîte de réception

- Uniquement les conversations issues de matchs.
- Photo, prénom, aperçu, date, statut et compteur non lu.
- Recherche locale dans les conversations.
- Boîte vide : lien vers Découvrir.

### F2 — Conversation active

- Historique paginé, séparateurs de date et ordre stable.
- Composer texte, compteur/limite et bouton Envoyer.
- États : envoi, envoyé, livré, lu, échec avec Réessayer.
- Présence en ligne ou dernière connexion.
- Nouveau message en moins de 10 secondes.
- UUID d'idempotence empêchant les doubles messages.

### F3 — Nouveau message depuis une autre page

- Toast non intrusif avec auteur, aperçu sûr et lien Voir le message.
- Badge global actualisé.
- Aucun contenu sensible affiché sur un écran de connexion ou après expiration de session.

### F4 — Reconnexion

- Bannière « Reconnexion… » sans effacer le brouillon.
- Messages manqués rechargés depuis PostgreSQL.
- Événements déjà traités non dupliqués.
- Échec durable : statut hors ligne et action Réessayer.

### F5 — Après unlike

- Historique en lecture seule.
- Composer désactivé avec explication.
- Possibilité de masquer localement la conversation.
- Aucun événement d'envoi accepté par le backend.

### F6 — Après blocage ou session expirée

- Blocage : conversation inaccessible et identité non navigable.
- Session expirée : socket fermée, écran Se reconnecter.
- Un message en cours n'est jamais marqué envoyé sans persistance confirmée.

---

## Parcours G — notifications

### G1 — Types obligatoires

- Nouveau like.
- Profil consulté.
- Nouveau message.
- Nouveau match.
- Like retiré par une connexion.

### G2 — Centre de notifications

- Non lues visuellement distinctes.
- Badge visible depuis toute page.
- Clic vers le profil ou chat si encore autorisé.
- Marquer une notification ou toutes comme lues.
- Pagination et état vide.

### G3 — Cas limites

- Notification vers profil désormais bloqué : non créée ou non livrée.
- Cible supprimée : item neutre sans lien cassé.
- Reconnexion : récupération des notifications persistées manquées.
- Double événement : une seule notification métier.
- Livraison supérieure à 10 secondes : test en échec et métrique journalisée.

---

## Parcours H — mon profil et paramètres

### H1 — Aperçu privé/public

- Vue privée avec actions Modifier et aperçu public.
- Popularité publique, statut et dernière activité tels qu'ils apparaissent aux autres.
- Indication claire des champs masqués publiquement.

### H2 — Modification

- Prénom, nom, genre, préférence, bio, tags et date de naissance selon autorisations.
- Sauvegarde réussie : toast et données rafraîchies.
- Erreurs inline sans perdre les autres modifications.
- Nouvelle adresse e-mail : ancienne conservée jusqu'à vérification de la nouvelle.

### H3 — Photos

- Grille de cinq emplacements maximum.
- Ajout, suppression, réorganisation et photo principale.
- Suppression de la principale : choix obligatoire d'une remplaçante si d'autres existent.
- Stockage indisponible : état réessayable sans ligne PostgreSQL orpheline.

### H4 — Localisation et consentements

- Ville/quartier approximatifs visibles.
- Modifier GPS ou saisie manuelle.
- Consentements distincts avec date/version et action Retirer.
- Retrait GPS : coordonnées supprimées et localisation manuelle requise pour le matching.
- Retrait préférence sensible : découverte/matching suspendus jusqu'à nouveau consentement.

### H5 — Visiteurs

- Historique daté des personnes ayant consulté le profil.
- État vide explicatif.
- Profil devenu bloqué ou supprimé rendu indisponible.
- Données au-delà de 90 jours automatiquement absentes.

### H6 — Likes reçus

- Liste complète et gratuite des personnes ayant liké le profil.
- État relationnel et accès au profil si autorisé.
- Aucun paywall ou contenu flouté.

### H7 — Déconnexion

- Accessible en un clic depuis toute page.
- Session serveur invalidée, cookie supprimé, socket fermée.
- Retour à la connexion sans données privées en cache visible.

---

## Parcours I — confidentialité et compte

### I1 — Télécharger mes données

- Demande authentifiée.
- Export JSON des données personnelles prévues dans `TASKS.md`.
- Génération en cours, succès ou erreur réessayable.
- Lien temporaire privé ou téléchargement direct contrôlé.

### I2 — Retirer un consentement

- Conséquences montrées avant confirmation.
- Retrait horodaté et effet immédiat.
- Aucun consentement regroupé ou précoché.

### I3 — Supprimer mon compte

1. Écran distinct, non caché derrière un abonnement.
2. Liste claire des conséquences irréversibles.
3. Mot de passe ou réauthentification récente.
4. Révocation immédiate des sessions et retrait public du profil.
5. Suppression PostgreSQL, Valkey et MinIO via transaction/outbox.
6. Écran final sans possibilité d'accéder à l'ancien compte.

Cas limites : mauvais mot de passe, suppression déjà lancée, MinIO temporairement
indisponible, reconnexion impossible pendant le nettoyage et demande idempotente.

### I4 — Compte inactif

- Après deux ans : e-mail d'avertissement.
- Reconnexion dans les 30 jours : annule la suppression.
- Sans reconnexion : même processus sûr que la suppression de compte.

---

## Parcours J — états système et accessibilité

### J1 — États génériques

- Skeleton de chargement.
- Liste vide contextualisée.
- Erreur de validation.
- Erreur serveur avec identifiant de support non sensible.
- Hors ligne/reconnexion.
- Session expirée/401.
- Accès interdit/403 sans révéler l'existence d'une ressource.
- Page introuvable/404 avec retour vers Découvrir.

### J2 — Responsive

- Desktop : navigation haute ou latérale et contenu multi-colonnes.
- Mobile : barre basse, cartes empilées et panneaux plein écran.
- Tablette : grille adaptée sans masquer filtres ou actions.
- Les modales destructives restent lisibles sans scroll horizontal.
- Le composer de chat reste visible avec le clavier mobile.

### J3 — Accessibilité

- Ordre de tabulation logique et focus restauré après fermeture de modal.
- Modales avec focus piégé et fermeture clavier sûre.
- Icônes accompagnées d'un libellé accessible.
- Photos avec texte alternatif adapté.
- Statut jamais communiqué uniquement par une couleur.
- Erreurs annoncées aux technologies d'assistance.
- Réduction des animations respectant `prefers-reduced-motion`.

---

## Bonus — scénarios isolés après validation de la mandatory

### K1 — Google OAuth/OIDC

- Connexion Google réussie, refusée, expirée ou e-mail non vérifié.
- Liaison/déliaison avec réauthentification.
- Impossible de supprimer le dernier moyen de connexion.
- Profil et consentements Matcha toujours requis.

### K2 — Galerie et édition

- Jusqu'à 20 images, glisser-déposer et alternative clavier.
- Recadrage, rotation, filtre, annulation et original conservé.
- Quota, format invalide, upload interrompu et nettoyage temporaire.
- Galerie séparée des cinq photos du profil obligatoire.

### K3 — Carte

- Consentement GPS précis séparé, retrait et mode liste alternatif.
- Marqueurs approximatifs, jamais de coordonnées exactes d'autrui.
- Carte indisponible sans bloquer recherche et matching mandatory.

### K4 — Audio/vidéo

- Appel entrant, accepté, refusé, occupé, échoué et terminé.
- Permissions caméra/micro refusées.
- Unlike ou blocage termine immédiatement l'appel.

### K5 — Rendez-vous

- Proposition, acceptation, refus, annulation et replanification.
- Dates passées, fuseaux, doublons et blocage.
- Données visibles uniquement des participants encore autorisés.

---

## Parcours E2E prioritaires

- [ ] Inscription → vérification → onboarding GPS accepté → découverte.
- [ ] Inscription → GPS refusé → localisation manuelle → découverte.
- [ ] Mot de passe oublié → réinitialisation → anciennes sessions invalidées.
- [ ] Profil sans photo → like refusé → ajout photo → like accepté.
- [ ] Visite → notification → like → like réciproque → match → chat.
- [ ] Match → nouveau message reçu depuis une autre page en moins de 10 secondes.
- [ ] Match → unlike → notification → conversation en lecture seule.
- [ ] Match → blocage → disparition recherche → chat et notifications interdits.
- [ ] Recherche combinée → tri → filtre → profil → retour avec état conservé.
- [ ] Modification e-mail → vérification → nouvelle adresse active.
- [ ] Retrait GPS → suppression coordonnées → localisation manuelle requise.
- [ ] Retrait consentement sensible → matching suspendu → nouveau consentement.
- [ ] Export des données → suppression du compte → objets et sessions supprimés.
- [ ] Session expirée pendant chat → socket fermée → reconnexion sûre.
- [ ] Firefox et Chrome, desktop et mobile, sans erreur ni warning.

## Critère de validation d'un écran

Un écran est validé lorsque son cas nominal, chargement, vide, erreur, accès interdit et
responsive pertinents sont traités, que les autorisations sont confirmées côté serveur,
que le clavier et les technologies d'assistance peuvent l'utiliser, et qu'aucune donnée
sensible non nécessaire n'est exposée.
