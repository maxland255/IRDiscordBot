# 🔐 Système de Vérification

Le système de vérification est le cœur d'**Academic-Gate**. Il garantit que chaque membre appartient réellement à
l'institution en utilisant une validation par email SMTP avec filtrage de domaines.

---

## 1. Flux Utilisateur & Statuts

Le bot gère deux types de parcours selon le profil de l'utilisateur :

| Statut         | Méthode             | Validité               | Contrainte                            |
|----------------|---------------------|------------------------|---------------------------------------|
| **Étudiant**   | Automatique (Email) | **Limitée** (ex: 1 an) | Soumis aux délais de kick/grâce.      |
| **Alumni**     | Manuelle (Ticket)   | **Infinie**            | Pas de limite de temps.               |
| **Professeur** | Manuelle (Ticket)   | **Infinie**            | Pas de limite de temps.               |
| **Externe**    | Manuelle (Ticket)   | **Infinie**            | Cas particuliers (partenaires, etc.). |

### Les commandes "Membre" :

* `/verify code` : Permet de saisir le code reçu par email.
* `/verify reverify` : Relance le processus de vérification quand le statut étudiant a expiré.

---

## 2. Configuration Administrative

L'ensemble du système se pilote via le groupe `/verification config`. La commande centrale est :
`/verification config configure`

Elle affiche un panneau interactif permettant de modifier la base de données en temps réel :

### 🛠️ Panneau de Contrôle (Boutons) :

* **Edit Roles :** Associe chaque statut (Étudiant, Alumni, etc.) à un rôle Discord spécifique.
* **Edit Ticket Type :** Définit quelle catégorie de ticket sera ouverte pour les vérifications manuelles (
  Alumni/Profs).
* **Add/Remove Domain :** Gère la "Whitelist" des domaines d'emails autorisés (ex: `@student.he-noms.be`).

### ⏳ Focus : Gestion des Délais (Edit Delays)

C'est ici que vous gérez la politique de nettoyage du serveur. **Attention : ces délais ne s'appliquent qu'aux membres
non-vérifiés ou ayant le statut Étudiant.**

1. **Kick Delay (Heures) :** Délai accordé à tout nouvel arrivant pour se vérifier. S'il ne le fait pas dans ce temps
   imparti, il est automatiquement expulsé du serveur.
2. **Grace Period (Jours) :** Une fois la vérification d'un **Étudiant** expirée, il dispose de ce nombre de jours pour
   utiliser `/verify reverify`. Passé ce délai, ses accès sont révoqués.

* *Rappel : Les Alumni, Professeurs et Externes sont exemptés de ces compte à rebours.*

---

## 3. Paramètres Techniques (.env)

La connexion au serveur mail de votre institution se configure dans le fichier d'environnement. Ces valeurs sont
chargées au démarrage via **Pydantic**.

```env
# --- Configuration SMTP ---
SMTP_HOST="smtp.votre-ecole.com"
SMTP_PORT=587
SMTP_USER="votre-email@comite.com"
SMTP_PASS="votre-mot-de-passe"
SMTP_SENDER_EMAIL="bot-no-reply@comite.com"

# --- Sécurité ---
# Activez l'un ou l'autre selon votre serveur (jamais les deux)
SMTP_USE_TLS="true"    # SSL/TLS Direct
SMTP_START_TLS="false"  # STARTTLS (Explicite)

```

---

## 4. Commandes d'Administration Avancées

Pour les cas particuliers (erreurs d'emails, invités spéciaux), utilisez le groupe `/verification admin` :

* `/verification admin get_verification [member]` : Affiche la fiche complète (Email, Date de vérification, Date
  d'expiration).
* `/verification admin set_status [member] [status]` : Force le statut d'un membre (ex: passer un étudiant en Alumni
  manuellement). Possibilité de fermer son ticket de vérification en une seule action.
* `/verification admin create_verification [member]` : Crée manuellement une entrée en base de données pour un
  utilisateur.

---

## 💡 Logique de sécurité

Le bot utilise un système de **codes à usage unique** stockés en base de données. Chaque tentative est logguée. Si un
utilisateur tente de forcer un domaine non-autorisé, le bot bloque immédiatement l'envoi de l'email pour préserver les
quotas SMTP et la réputation de l'expéditeur.
