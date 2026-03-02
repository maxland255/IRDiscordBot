# 🎓 Academic-Gate Bot

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org)
[![Framework](https://img.shields.io/badge/pycord-2.7%2B-blue.svg)](https://pycord.dev)
[![Database](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red.svg)](https://www.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Academic-Gate** est une solution de gestion de communauté Discord "Enterprise-grade" conçue spécifiquement pour les
Hautes Écoles et Universités. Plus qu'un simple bot, c'est un framework modulaire permettant d'automatiser la
vérification des étudiants, la gestion des tickets et la modération avec une architecture robuste et scalable.

---

## ✨ Fonctionnalités Clés

### 🔐 Système de Vérification Avancé

* **Vérification SMTP :** Envoi de codes à usage unique par email.
* **Gestion des Domaines :** Restriction automatique aux domaines académiques configurés.
* **Cycle de vie des membres :** * **Étudiants :** Validité d'un an avec processus de re-vérification automatique.
    * **Profs / Alumni / Externes :** Vérification permanente et manuelle.
* **Sécurité :** Prévention du spam et des tentatives de brute-force sur les codes.

### 🎫 Gestion des Tickets & Rapports

* **Tickets Modulaires :** Création de catégories de tickets via commandes.
* **Transcripts HTML :** Archivage propre de chaque ticket via des templates Jinja2.
* **Système de Signalement :** Signalement de messages avec interface de modération dédiée.

### ⚙️ Administration & Personnalisation

* **Zéro Hard-coding :** Presque toute la configuration (domaines, rôles, délais) est stockée en SQL et modifiable via
  des commandes Slash.
* **Éditeur d'Embeds :** Créez et modifiez des embeds complexes directement depuis Discord.

---

## 🏗️ Architecture du Code

Le projet a été conçu avec une séparation stricte des responsabilités (SOC) pour garantir la maintenance de celui-ci.

* **Layer Data :** Utilisation de **SQLAlchemy** (Asynchrone) avec le **Pattern Repository**. L'utilisation de
  `typing.Protocol` permet d'abstraire la source de données.
* **Layer Validation :** **Pydantic** assure l'intégrité des données entre la DB et la logique métier.
* **Layer UI :** Les interactions (Modals, Views) sont isolées dans `bot/view` pour ne pas encombrer la logique des
  Cogs.
* **Layer Migration :** Gestion fluide du schéma de base de données avec **Alembic**.

---

## 🚀 Installation

### Pré-requis

* Python 3.12+
* Un serveur SMTP (Gmail, Outlook, ou serveur académique)
* Une base de données (SQLite, PostgreSQL ou MySQL)

### Installation rapide (Docker)

1. Clonez le dépôt : `git clone https://github.com/votre-username/academic-gate.git`
2. Configurez le fichier `.env` (voir section suivante).
3. Lancez :

```bash
   docker-compose up bot-prod
```

### Installation manuelle

1. Installez les dépendances : `pip install -r requirements.txt`
2. Appliquez les migrations : `alembic upgrade head`
3. Lancez le bot : `python bot/main.py`

---

## ⚙️ Configuration (.env)

Le bot utilise un fichier d'environnement pour les paramètres critiques :

```env
# Bot
DISCORD_BOT_TOKEN="votre_token"
GUILD_ID=1234567890  # Optionnel (Test)
APP_ENV="prod"       # dev / prod

# Database
DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db"

# Email (SMTP)
SMTP_HOST="smtp.votre-ecole.com"
SMTP_PORT=587
SMTP_USER="bot@comite.com"
SMTP_PASS="password"
SMTP_SENDER_EMAIL="bot-no-reply@comite.com"
SMTP_USE_TLS="true"

```

---

## 🛠️ Développement & Contribution

### Ajouter une fonctionnalité (Cog)

Toutes les Cogs héritent de `CogsBase`, permettant une initialisation asynchrone sécurisée avant le démarrage du bot :

```python
class MyFeature(Cog, CogsBase):
    async def initialize(self) -> None:
        # Logique d'initialisation (ex: check DB)
        pass

```

### Pattern Repository

Pour modifier la gestion des données, créez une nouvelle implémentation de l'interface dans `repositories/` :

```python
class MyRepository(Protocol):
    @abstractmethod
    async def get_data(self) -> MySchema: ...

```

---

## ⚖️ Licence

Distribué sous la licence MIT. Voir `LICENSE` pour plus d'informations.
