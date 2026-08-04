# Matcha — spécification UX de référence pour le build

Ce document est la référence opérationnelle des écrans. Il complète `TASKS.md` et
`SCENARIOS.md` sans les remplacer.

## Ordre de priorité

En cas de divergence : sujet PDF → `TASKS.md` → `SCENARIOS.md` → ce document → maquettes PNG.
Une phrase ou un contrôle visible dans une image ne crée jamais une exigence métier.

## Règles non négociables

- Service réservé aux personnes de 18 ans ou plus.
- L'inscription demande une date de naissance ; l'âge est calculé côté serveur.
- Les seules préférences sensibles utiles au matching sont les genres recherchés.
- Le consentement aux préférences est explicite, spécifique, non précoché et séparé du GPS.
- Ne jamais demander religion, origine ethnique, santé ou statut parental.
- Sans consentement aux préférences : découverte, recherche et matching suspendus.
- Le GPS est facultatif ; une ville ou un quartier manuel reste disponible.
- La localisation affichée est approximative, jamais une coordonnée exacte.
- Un profil complet peut ne contenir aucune photo.
- De zéro à cinq photos ; si une photo existe, exactement une est principale.
- Sans photo principale, la consultation reste possible mais le like est interdit.
- La compatibilité mutuelle est calculée côté serveur ; aucun filtre public
  « orientation » n'est proposé dans la recherche.
- Le statut en ligne ou la dernière connexion est visible sur les profils, sans réglage
  permettant de masquer cette obligation.
- Un unlike termine le match et rend l'historique du chat accessible en lecture seule.
- Un blocage rend profil, conversation et notifications mutuelles inaccessibles.
- Une session expirée propose une reconnexion ; un blocage ne la propose pas.
- Ne pas annoncer de chiffrement de bout en bout. L'interface peut indiquer une protection
  ou un chiffrement en transit uniquement si la configuration correspondante existe.
- Aucun paiement, abonnement ou paywall sur les fonctions obligatoires.
- Un profil n'est jamais présenté comme public à « tout le monde » : sa visibilité est
  limitée aux membres authentifiés autorisés par les règles de blocage et de matching.

## Écrans à construire

### 1. Authentification et onboarding

- Connexion, inscription, vérification d'e-mail, mot de passe oublié et réinitialisation.
- Inscription : prénom, nom, username, e-mail, date de naissance et mot de passe.
- Onboarding sauvegardé : identité, préférences consenties, bio, tags, photos facultatives,
  puis localisation GPS consentie ou manuelle.
- États : validation, moins de 18 ans, lien expiré, compte non vérifié, chargement et panne.

### 2. Découverte, recherche et profil

- Suggestions triées selon zone, proximité, tags et popularité.
- Recherche avancée : âge, popularité, localisation et tags.
- Cartes : photo principale ou placeholder, prénom, âge, localisation approximative,
  tags, popularité et présence.
- Profil détaillé : informations autorisées, visite enregistrée, like, unlike, blocage et
  signalement selon l'état courant.
- État sans photo principale : bouton Like désactivé avec explication.

### 3. Match, messages et notifications

- Match créé seulement après like réciproque.
- Chat actif seulement entre deux utilisateurs actuellement matchés.
- Notifications : like reçu, visite, match, message et unlike.
- Après unlike : historique en lecture seule et possibilité de le masquer localement.
- Après blocage : conversation inaccessible, retour à la liste des messages.
- Session expirée : socket fermée et bouton « Se reconnecter ».

### 4. Profil, confidentialité et compte

- Édition des informations et gestion de zéro à cinq photos.
- Consentements préférences et GPS affichés séparément, jamais activés par défaut.
- Export des données et suppression définitive avec confirmation renforcée.
- Likes reçus accessibles gratuitement.
- États système dédiés : vide, chargement, erreur, hors ligne, 404 et session expirée.

## Critères d'acceptation des maquettes

- Chaque contrôle représenté correspond à une règle de `TASKS.md` ou est purement visuel.
- Aucun champ sensible non nécessaire n'est affiché.
- Les états unlike, blocage et session expirée ont des actions différentes.
- Desktop et mobile conservent les mêmes permissions métier.
- Les textes de sécurité restent factuels et vérifiables.
- Les bonus sont identifiés comme tels et ne bloquent jamais la mandatory.
