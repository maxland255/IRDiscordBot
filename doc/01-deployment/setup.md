# 🚀 Guide d'installation (Setup)

Ce guide vous explique comment déployer **Academic-Gate** sur un serveur Linux. Le bot est optimisé pour tourner sous *
*Docker**, mais peut aussi être lancé nativement.

## 📋 Pré-requis

* **Git** installé.
* **Docker** et **Docker Compose** (recommandé).
* **Python 3.13** (si installation native).
* Un serveur SMTP (pour l'envoi des mails de vérification).

---

## 1. Clonage du projet

Commencez par récupérer les sources dans un dossier dédié :

```bash
mkdir ir-discord-bot
cd ir-discord-bot
git clone https://github.com/maxland255/IRDiscordBot.git .

```

---

## 2. Configuration (.env)

Le bot utilise des fichiers d'environnement distincts selon le mode. Pour une mise en production, vous devez créer un
fichier `.env.prod`.

```bash
cp .env.example .env.prod

```

### 🔑 Variables obligatoires

Ouvrez `.env.prod` et remplissez les champs suivants :

| Variable            | Description                                                                |
|---------------------|----------------------------------------------------------------------------|
| `DISCORD_BOT_TOKEN` | Le token secret de votre application Discord.                              |
| `DATABASE_URL`      | L'URL de votre base (ex: `postgresql+asyncpg://user:pass@db:5432/dbname`). |
| `SMTP_HOST`         | L'adresse de votre serveur mail.                                           |
| `SMTP_PORT`         | Le port (généralement `587` pour TLS).                                     |
| `SMTP_USER`         | L'identifiant de connexion SMTP.                                           |
| `SMTP_PASS`         | Le mot de passe SMTP.                                                      |
| `SMTP_SENDER_EMAIL` | L'adresse qui apparaîtra comme expéditeur.                                 |

### ⚙️ Variables optionnelles (Valeurs par défaut)

* `GUILD_ID`: `None` (Laissez vide pour un déploiement global des commandes).
* `LOG_LEVEL`: `INFO` (Passez en `DEBUG` en cas de problème).
* `SMTP_USE_TLS`: `True`.
* `SMTP_START_TLS`: `False`.

---

## 3. Initialisation de la Base de Données

Avant de lancer le bot, vous devez injecter le schéma de données. On utilise **Alembic** pour gérer ces migrations.

**Via le manager (recommandé) :**

```bash
python3 manager.py db-upgrade

```

**Ou via Alembic directement :**

```bash
alembic upgrade head

```

---

## 4. Lancement du bot

Trois méthodes s'offrent à vous selon votre infrastructure.

### Méthode A : Docker Compose (Vivement recommandé) 🐳

C'est la méthode la plus stable. Elle gère le redémarrage automatique et l'isolation.

* **Production :** (Logs épurés, utilisateur non-root)

```bash
docker compose up bot-prod -d

```

* **Développement :** (Logs complets, rechargement à chaud)

```bash
docker compose up bot-dev

```

> **Astuce :** Lancez une première fois en `bot-dev` ou avec `LOG_LEVEL="DEBUG"` pour vérifier que l'initialisation des
> Cogs se déroule sans erreur.

### Méthode B : Docker simple

Le Dockerfile est multi-stage. Vous pouvez build l'image selon votre besoin :

```bash
# Build pour la prod
docker build --target production -t ir-bot:latest .
# Lancement
docker run --env-file .env.prod ir-bot:latest

```

### Méthode C : Installation native (Python)

Si vous ne souhaitez pas utiliser Docker :

1. **Initialisation :**

```bash
python3 manager.py setup

```

*(Crée le venv, installe les dépendances et prépare le .env.dev)*

2. **Lancement :**

```bash
python3 manager.py run

```

---

## 🔍 Vérification des logs

Une fois lancé, vous pouvez suivre l'activité du bot dans le dossier `/logs` ou via Docker :

```bash
docker compose logs -f bot-prod

```
