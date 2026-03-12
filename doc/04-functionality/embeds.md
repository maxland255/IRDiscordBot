# 🖼️ Système de Création d'Embeds

Le bot **Academic-Gate** intègre un éditeur d'embeds puissant et intuitif. Contrairement à la majorité des bots, vous
n'avez pas besoin de site web tiers ou de connaissances en JSON : tout se gère via des **boutons** et des **fenêtres
modales** directement dans Discord.

---

## 1. Pourquoi utiliser ce système ?

* **Centralisation :** Tous vos messages officiels sont stockés en base de données.
* **Multi-publication :** Un même embed peut être publié (copié) dans plusieurs salons différents.
* **Édition en direct :** Modifiez un embed existant et voyez les changements s'appliquer instantanément grâce à la
  prévisualisation.

---

## 2. Le Workflow de Création

Le processus se déroule en trois étapes simples :

### Étape 1 : Initialisation

Lancez la commande :

```text
/embeds create title: "Titre de mon Embed"

```

Le bot va alors générer un message spécial de **Prévisualisation**.

### Étape 2 : Édition Interactive

Sous la prévisualisation, vous trouverez une interface composée de boutons. Chaque bouton ouvre une **fenêtre modale** (
formulaire Discord) :

* **Auteur / Footer :** Modifiez le texte et l'icône de l'en-tête et du pied de page.
* **Contenu :** Modifiez le titre, la description et la couleur.
* **Images :** Ajoutez une URL d'image principale ou une miniature (thumbnail).
* **Fields :** Gérez vos champs (Title/Value) avec l'option "Inline". Vous pouvez ajouter, modifier l'ordre ou supprimer
  des champs.

### Étape 3 : Publication

Une fois satisfait du résultat, récupérez l'ID de votre embed (via `/embeds list`) et utilisez :

```text
/embeds publish embed_id: 4

```

Le bot enverra une version "propre" (sans les boutons d'édition) dans le salon actuel.

---

## 3. Liste des Commandes

| Commande          | Description                                                           |
|-------------------|-----------------------------------------------------------------------|
| `/embeds create`  | Crée une nouvelle structure d'embed et ouvre l'éditeur.               |
| `/embeds edit`    | Ré-affiche l'interface d'édition pour un embed existant (via son ID). |
| `/embeds publish` | Envoie l'embed final dans le salon actuel.                            |
| `/embeds list`    | Affiche la liste de tous les embeds créés avec leurs IDs respectifs.  |
| `/embeds delete`  | Supprime définitivement un embed de la base de données.               |

---

## 💡 Astuce de Modérateur

L'utilisation de `/embeds list` est très utile pour cloner des messages d'information d'une année à l'autre. Vous pouvez
modifier la date dans l'embed via l'éditeur et le republier sans avoir à tout retaper.

C'est super précis ! Le fait d'utiliser un `Select` pour gérer les champs (Fields) est une excellente idée ergonomique :
ça évite d'avoir 10 boutons "Field 1", "Field 2" et ça permet de gérer la limite des 25 options de Discord proprement.

Voici le complément technique pour ta documentation `docs/04-functionality/embeds.md`. Tu peux l'insérer juste après la
section sur le workflow pour détailler ce que l'utilisateur voit réellement.

---

## 🎨 Focus : L'Interface de l'Éditeur

Une fois la commande `/embeds create` ou `/embeds edit` lancée, une interface interactive composée de deux rangées
d'actions apparaît sous la prévisualisation.

#### 🕹️ Les Boutons d'Action (Rangée 1)

Chaque bouton ouvre une fenêtre modale spécifique pour modifier une section précise de l'embed :

* **Edit Embed :** Pour modifier le **Titre**, la **Description** et la **Couleur** (format hexadécimal).
* **Edit Author :** Pour définir le nom de l'auteur, l'URL de son profil et son icône.
* **Edit Images :** Pour configurer l'**Image principale** (grand format) et la **Miniature** (thumbnail en haut à
  droite).
* **Edit Footer :** Pour modifier le texte du pied de page et son icône.
* **Delete Field :** Un bouton de sécurité (en rouge) permettant de supprimer rapidement le champ actuellement
  sélectionné.

#### 📑 Gestion Dynamique des Champs (Rangée 2)

C'est ici que réside la puissance de l'outil. Un menu déroulant (**Select**) permet de piloter les "Fields" de l'embed :

1. **Édition :** Le menu liste tous les champs existants (affiche les 100 premiers caractères du nom/valeur). En
   sélectionner un ouvre une modale pour le modifier.
2. **Création :** Si l'embed possède moins de 25 champs, une option spéciale **"Create New Field"** est automatiquement
   ajoutée à la fin de la liste.
3. **Limites :** Le système respecte nativement la limite de Discord (25 champs maximum) et tronque intelligemment les
   textes trop longs dans le menu de sélection pour garantir un affichage fluide.

> **⏰ Sécurité et Temps de session :**
> L'interface d'édition est active pendant **10 minutes** (600 secondes). Passé ce délai, les boutons deviennent
> inactifs pour libérer les ressources du bot. Si vous n'avez pas terminé, relancez simplement `/embeds edit [ID]`.
