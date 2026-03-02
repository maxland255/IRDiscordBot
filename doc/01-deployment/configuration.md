# ⚙️ Configuration sur Discord

Une fois le bot en ligne et présent sur votre serveur, la configuration se fait exclusivement via les
**commandes Slash**.
Ce chapitre vous guide à travers l'initialisation et le paramétrage des systèmes de base.

---

## 1. Initialisation : `/config init`

C'est la première commande à exécuter. Elle prépare le terrain et définit les réglages globaux du serveur.

### Paramètres disponibles :

| Paramètre         | Type      | Par défaut | Description                                               |
|-------------------|-----------|------------|-----------------------------------------------------------|
| `warn_height`     | `float`   | `0.2`      | Poids d'un avertissement simple (voir Algorithme).        |
| `default_timeout` | `int`     | `600`      | Durée de base (en secondes) pour un timeout.              |
| `logs_moderation` | `Channel` | `None`     | Salon pour les logs de sanctions.                         |
| `logs_server`     | `Channel` | `None`     | Salon pour les logs d'activité (arrivées, départs, etc.). |
| `rules_channel`   | `Channel` | `None`     | Salon où sera affiché le règlement dynamique.             |
| `report_channel`  | `Channel` | `None`     | Salon recevant les signalements des membres.              |

---

## 2. Le Moteur de Modération "Fair-Play" 🧠

Contrairement aux autres bots, **Academic-Gate** ne permet pas aux modérateurs de choisir arbitrairement une durée de
bannissement ou de timeout. La sanction est calculée selon l'historique du membre.

### L'Algorithme de Calcul

La durée finale est déterminée par le poids cumulé des fautes passées. Voici la formule mathématique utilisée par le
bot :

* Poids Historique (

) : Somme des poids de toutes les infractions précédentes (un `warn` vaut par défaut `0.2`).

* **Seuil d'Avertissement :** Si un membre reçoit un `/warn` et que son

atteint ou dépasse **1.0**, il subit automatiquement un timeout calculé.

* Poids Actuel (

) : Défini par le **Niveau de Gravité** choisi par le modérateur lors de la commande.

---

## 3. Gestion des Niveaux de Gravité

Pour que le système de timeout fonctionne, vous devez définir des niveaux de gravité via le groupe de commandes
`/gravity-levels`.

* **Créer :** `/gravity-levels create [nom] [poids] [description]`
* *Exemple :* Nom: `Faible`, Poids: `1.0` | Nom: `Grave`, Poids: `5.0`.


* **Visualiser :** `/gravity-levels view` pour obtenir la liste et les IDs.
* **Modifier/Supprimer :** Utilisez `/gravity-levels update` ou `delete`.

---

## 4. Signalements (Reports)

Le bot intègre une fonctionnalité de signalement native via les **Context Menus** de Discord :

1. Un membre fait un clic droit sur un message abusif.
2. **Applications** -> **Report message**.
3. Le signalement est envoyé dans le `report_channel` avec le contexte (auteur, contenu, lien).

---

## 5. Maintenance de la Configuration

* **Mise à jour :** Utilisez `/config configuration` pour modifier un paramètre spécifique sans réinitialiser le reste.
* **Réinitialisation :** `/config unconfigure` permet de "nettoyer" certains réglages (passer un salon à `None`).
* *Exemple :* `/config unconfigure rules_channel: True` supprimera le lien vers le salon de règlement.


* **Vue d'ensemble :** `/config view` génère un récapitulatif complet sous forme d'Embed.

---

### Pourquoi ce système ?

En configurant un `warn_height` faible (ex: `0.1`), vous permettez aux étudiants de faire quelques erreurs mineures
avant que la sanction ne devienne lourde. À l'inverse, un récidiviste verra la durée de ses timeouts augmenter de façon
exponentielle à chaque nouvelle faute, protégeant ainsi la sérénité du serveur sans intervention manuelle complexe.

---

## 📘 Prochaines étapes

Maintenant que le coeur du bot est configuré, passons à l'organisation des fonctionnalités spécifiques :

* [Vérification SMTP & Email](https://www.google.com/search?q=./functionality/verification.md)
* [Système de Tickets & Embeds](https://www.google.com/search?q=./functionality/tickets.md)
