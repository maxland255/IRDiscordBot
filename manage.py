#!.venv/bin/python
# manage.py
import sys
import os
import shutil
import pathlib
import subprocess

# --- Configuration du script ---
MIN_PYTHON_VERSION = (3, 12)
VENV_DIR = ".venv"
REQUIREMENTS_FILE = "requirements.txt"
ENV_EXAMPLE_FILE = ".env.example"
ENV_FILE = ".env"
DEV_ENV_FILE = ".env.dev"


# --- Fonctions utilitaires ---

def _get_python_executable():
    """Retourne le chemin vers l'exécutable Python de l'environnement virtuel."""
    if sys.platform == "win32":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python")


def _print_help():
    """Affiche l'aide du script."""
    print("Gestionnaire de projet pour le Bot Discord.")
    print("Usage: python manage.py [commande]\n")
    print("Commandes disponibles:")
    print("  setup          : Configure l'environnement de développement initial.")
    print("  run            : Lance le bot localement (requiert 'setup' au préalable).")
    print("  docker-build   : Construit l'image Docker de production sans la lancer.")
    print("  docker-dev     : Lance le bot en mode développement avec Docker (rechargement auto).")
    print("  docker-prod    : Déploie le bot en production avec Docker.")
    print("  docker-down    : Arrête les conteneurs Docker lancés par ce script.")
    print("  db-migrate     : Gère les migrations de la base de données (Alembic).")
    print("  db-upgrade     : Applique les migrations de la base de données.")


def _run_command(command, shell=False):
    """Exécute une commande système et arrête le script en cas d'erreur."""
    try:
        subprocess.run(command, check=True, shell=shell)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de la commande: {' '.join(command)}")
        print(f"Erreur: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Erreur: La commande '{command[0]}' n'a pas été trouvée.")
        print("Assurez-vous que le programme (ex: Docker) est installé et dans le PATH.")
        sys.exit(1)


# --- Commandes principales ---

def check_python_version():
    """Vérifie si la version de Python est compatible."""
    if sys.version_info < MIN_PYTHON_VERSION:
        print(f"Erreur: Version de Python trop ancienne.")
        print(f"Ce projet requiert Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} ou supérieur.")
        print(f"Votre version est {sys.version_info.major}.{sys.version_info.minor}.")
        sys.exit(1)
    print("✅ Version de Python compatible.")


def command_setup():
    """Configure l'environnement de développement."""
    print("--- Configuration de l'environnement ---")

    # 1. Créer le fichier .env s'il n'existe pas
    if not os.path.exists(ENV_FILE):
        print(f"Copie de '{ENV_EXAMPLE_FILE}' vers '{ENV_FILE}'...")
        shutil.copy(ENV_EXAMPLE_FILE, ENV_FILE)
        print(f"✅ Fichier '{ENV_FILE}' créé. Pensez à le remplir !")
    else:
        print(f"ℹ️  Le fichier '{ENV_FILE}' existe déjà.")

    # 2. Créer l'environnement virtuel s'il n'existe pas
    if not os.path.exists(VENV_DIR):
        print(f"Création de l'environnement virtuel dans '{VENV_DIR}'...")
        _run_command([sys.executable, "-m", "venv", VENV_DIR])
        print("✅ Environnement virtuel créé.")
    else:
        print(f"ℹ️  L'environnement virtuel '{VENV_DIR}' existe déjà.")

    # 3. Installer les dépendances
    print("Installation des dépendances depuis 'requirements.txt'...")
    python_venv = _get_python_executable()
    _run_command([python_venv, "-m", "pip", "install", "-r", REQUIREMENTS_FILE])
    print("✅ Dépendances installées.")
    print("\n--- Environnement prêt ! ---")


def command_run_local():
    """Lance le bot directement en local."""
    if not pathlib.Path(DEV_ENV_FILE).exists():
        print(f"⚠️ {DEV_ENV_FILE} n'existe pas dans le fichier.")
        raise FileNotFoundError(DEV_ENV_FILE)
    print("🚀 Lancement du bot en local...")
    os.environ["APP_ENV"] = "dev"
    python_venv = _get_python_executable()
    _run_command([python_venv, "-m", "bot.main"])


def command_docker_build():
    """Construit l'image Docker de production."""
    print("🏗️  Construction de l'image Docker de production...")
    _run_command(["docker-compose", "build", "bot-prod"])
    pathlib.Path("./build").mkdir(exist_ok=True)
    _run_command(["docker", "save", "-o", "./build/ir-discord-bot.tar", "ir-discord-bot:latest"])
    print("✅ Image 'ir-discord-bot:latest' construite avec succès.")


def command_docker_dev():
    """Lance l'environnement de développement Docker."""
    print("🐳 Lancement de l'environnement de développement Docker...")
    _run_command(["docker-compose", "up", "bot-dev", "--watch"])


def command_docker_prod():
    """Déploie l'application en production avec Docker."""
    print("🚢 Déploiement en production avec Docker...")
    _run_command(["docker-compose", "up", "bot-prod", "--build", "-d"])


def command_docker_down():
    """Arrête les conteneurs Docker."""
    print("🛑 Arrêt des conteneurs Docker...")
    _run_command(["docker-compose", "down"])


def command_db_migrate(message: str):
    """Gère les migrations de la base de données avec Alembic."""
    print("🔄 Lancement d'Alembic pour gérer les migrations de la base de données...")
    _run_command([_get_python_executable(), "-m", "alembic", "revision", "--autogenerate", "-m", message])
    print("✅ Migration créée.")


def command_db_upgrade():
    """Applique les migrations de la base de données avec Alembic."""
    print("⬆️  Application des migrations de la base de données avec Alembic...")
    _run_command([_get_python_executable(), "-m", "alembic", "upgrade", "head"])
    print("✅ Migrations appliquées.")


if __name__ == "__main__":
    check_python_version()

    if len(sys.argv) < 2:
        _print_help()
        sys.exit(1)

    command = sys.argv[1]

    if command == "setup":
        command_setup()
    elif command == "run":
        command_run_local()
    elif command == "docker-build":
        command_docker_build()
    elif command == "docker-dev":
        command_docker_dev()
    elif command == "docker-prod":
        command_docker_prod()
    elif command == "docker-down":
        command_docker_down()
    elif command == "db-migrate":
        if len(sys.argv) < 3:
            print("Erreur: Veuillez fournir un message pour la migration.")
            sys.exit(1)
        message = sys.argv[2]

        command_db_migrate(message)
    elif command == "db-upgrade":
        command_db_upgrade()
    elif command == "help":
        _print_help()
    else:
        print(f"Erreur: Commande '{command}' inconnue.")
        _print_help()
        sys.exit(1)
