import logging
import os
import yaml
import subprocess
from gui import creer_interface

# Importation pour la création du lanceur OS-spécifique
import sys
import platform
import stat

# Modification de la configuration des logs pour inclure la console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("application.log"),
        logging.StreamHandler()  # Ajout d'un gestionnaire pour afficher les logs dans la console
    ]
)

PROFILES_DIR = "profiles"
CONVERSATIONS_DIR = "conversations"
os.makedirs(PROFILES_DIR, exist_ok=True)
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)

def creer_fichiers_configuration():
    """Crée les fichiers de configuration pour Gemini, OpenAI et Claude."""
    configurations = {
        "Gemini": {
            "profil": "Gemini",
            "nom": "Gemini",
            "api_key": "",
            "api_url": "",
            "behavior": "",
            "curl_exe": "",
            "default": False,
            "history": False,
            "role": "",
            "file_generation": {
                "enabled": False,
                "mode": "simple",
                "simple_config": {
                    "include_question": True,
                    "include_response": True,
                    "base_filename": "conversation",
                    "same_file": True
                },
                "dev_config": {
                    "extension": ".py"
                }
            }
        },
        "OpenAI": {
            "profil": "OpenAI",
            "nom": "OpenAI",
            "api_key": "",
            "api_url": "",
            "behavior": "",
            "curl_exe": "",
            "default": False,
            "history": False,
            "role": "",
            "file_generation": {
                "enabled": False,
                "mode": "simple",
                "simple_config": {
                    "include_question": True,
                    "include_response": True,
                    "base_filename": "conversation",
                    "same_file": True
                },
                "dev_config": {
                    "extension": ".py"
                }
            }
        },
        "Claude": {
            "profil": "Claude",
            "nom": "Claude",
            "api_key": "",
            "api_url": "",
            "behavior": "",
            "curl_exe": "",
            "default": False,
            "history": False,
            "role": "",
            "file_generation": {
                "enabled": False,
                "mode": "simple",
                "simple_config": {
                    "include_question": True,
                    "include_response": True,
                    "base_filename": "conversation",
                    "same_file": True
                },
                "dev_config": {
                    "extension": ".py"
                }
            }
        }
    }

    for nom, config in configurations.items():
        chemin_fichier = os.path.join(PROFILES_DIR, f"{nom}.yaml")
        if not os.path.exists(chemin_fichier):
            try:
                with open(chemin_fichier, 'w') as fichier:
                    yaml.dump(config, fichier)
                print(f"Fichier de configuration créé : {chemin_fichier}")
            except Exception as e:
                print(f"Erreur lors de la création du fichier {chemin_fichier} : {e}")

def verifier_profil_gemini():
    """Vérifie si le profil Gemini existe, sinon le crée avec des valeurs par défaut."""
    gemini_profile_path = os.path.join(PROFILES_DIR, "Gemini.yaml")

    if not os.path.exists(gemini_profile_path):
        gemini_default_config = {
            "model": "Gemini",
            "api_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            "api_key": "VOTRE_CLE_API_GEMINI_ICI",
            "behavior": "comportement initial",
            "history": False
        }

        try:
            with open(gemini_profile_path, 'w') as f:
                yaml.dump(gemini_default_config, f)
            print(f"Profil Gemini créé avec succès : {gemini_profile_path}")
        except Exception as e:
            print(f"Erreur lors de la création du profil Gemini : {e}")

def verifier_et_mettre_a_jour_profils():
    """Vérifie et met à jour les profils pour inclure la clé 'default'."""
    configurations = {
        "Gemini": {
            "default": True
        },
        "OpenAI": {
            "default": False
        },
        "Claude": {
            "default": False
        }
    }

    for nom, config_update in configurations.items():
        chemin_fichier = os.path.join(PROFILES_DIR, f"{nom}.yaml")
        if os.path.exists(chemin_fichier):
            try:
                with open(chemin_fichier, 'r') as fichier:
                    config = yaml.safe_load(fichier)

                # Mettre à jour la clé 'default'
                config.update(config_update)

                with open(chemin_fichier, 'w') as fichier:
                    yaml.dump(config, fichier)
                print(f"Profil {nom} mis à jour avec la clé 'default'.")
            except Exception as e:
                print(f"Erreur lors de la mise à jour du profil {nom} : {e}")

def verifier_ou_demander_cle_api():
    """Supprimé : La clé API sera configurée via le formulaire SETUP."""
    pass

def execute_curl():
    curl_command = [
        "curl",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=AIzaSyAI56WaXrkK1iFHNxp3_akHMFTN5-kabBk",
        "-H", "Content-Type: application/json",
        "-X", "POST",
        "-d", '{"contents": [{"parts":[{"text": "En tant qu\'expert vendeur. Ton comportement est défini ainsi : excité. J\'aimerais te poser la question suivante : "}]}]}'
    ]

    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        print("Réponse de l'API :")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Erreur lors de l'exécution de la requête CURL :")
        print(e.stderr)

def check_and_create_launcher():
    """
    Vérifie et crée un lanceur OS-spécifique si nécessaire
    
    Returns:
        bool: True si un lanceur existe ou a été créé, False sinon
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        current_os = platform.system().lower()
        
        # Déterminer le nom du lanceur selon l'OS
        if current_os == 'windows' or sys.platform.startswith('win'):
            launcher_name = 'RUN.bat'
        else:
            launcher_name = 'run.sh'
        
        launcher_path = os.path.join(script_dir, launcher_name)
        
        # Si le lanceur existe déjà, pas besoin de le recréer
        if os.path.exists(launcher_path):
            logging.info(f"Lanceur OS déjà présent: {launcher_name}")
            return True
        
        # Créer le lanceur
        logging.info(f"Création du lanceur pour {platform.system()}...")
        
        if current_os == 'windows' or sys.platform.startswith('win'):
            # Contenu du fichier batch Windows
            batch_content = """@echo off
REM Lanceur automatique Rob-1 pour Windows

echo ================================================
echo 🚀 Lancement de Rob-1
echo ================================================

REM Changer vers le répertoire du script
cd /d "%~dp0"

REM Vérifier que Python est disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé ou pas dans le PATH
    echo 💡 Veuillez installer Python depuis https://python.org
    pause
    exit /b 1
)

REM Vérifier que main.py existe
if not exist "main.py" (
    echo ❌ Fichier main.py introuvable
    echo 📁 Répertoire actuel: %CD%
    pause
    exit /b 1
)

REM Lancer l'application et fermer cette fenêtre
echo ✅ Lancement de main.py...
start "" pythonw "main.py"
exit
"""
            
            with open(launcher_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            logging.info(f"✅ Lanceur Windows créé: {launcher_name}")
            
        else:  # Linux ou macOS
            # Contenu du script shell Unix
            shell_content = """#!/bin/bash
# Lanceur automatique Rob-1 pour Linux/macOS

echo "================================================"
echo "🚀 Lancement de Rob-1"
echo "================================================"

# Obtenir le répertoire du script
SCRIPT_DIR="$(dirname "$0")"
cd "$SCRIPT_DIR"

# Vérifier que Python est disponible
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python n'est pas installé ou pas dans le PATH"
    echo "💡 Veuillez installer Python depuis votre gestionnaire de paquets"
    read -p "Appuyez sur Entrée pour continuer..."
    exit 1
fi

# Déterminer la commande Python à utiliser
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

# Vérifier que main.py existe
if [ ! -f "main.py" ]; then
    echo "❌ Fichier main.py introuvable"
    echo "📁 Répertoire actuel: $(pwd)"
    read -p "Appuyez sur Entrée pour continuer..."
    exit 1
fi

# Lancer l'application
echo "✅ Lancement de main.py avec $PYTHON_CMD..."
$PYTHON_CMD "main.py"

# Récupérer le code de retour
EXIT_CODE=$?

# Gestion de fermeture
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ Erreur lors de l'exécution (code: $EXIT_CODE)"
    read -p "Appuyez sur Entrée pour continuer..."
else
    echo "✅ Application fermée normalement"
    sleep 1
fi

exit $EXIT_CODE
"""
            
            with open(launcher_path, 'w', encoding='utf-8') as f:
                f.write(shell_content)
            
            # Rendre le script exécutable
            os.chmod(launcher_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)  # 755
            
            os_name = "macOS" if current_os == 'darwin' else "Linux"
            logging.info(f"✅ Lanceur {os_name} créé: {launcher_name}")
        
        return True
        
    except Exception as e:
        logging.error(f"Erreur lors de la création du lanceur: {e}")
        return False

def main():
    """Point d'entrée principal de l'application."""
    logging.info("Application démarrée.")
    # Ajout d'un log pour indiquer le lancement initial de l'application
    logging.info("Lancement initial de l'application.")
    
    # Créer le lanceur OS-spécifique au premier lancement
    check_and_create_launcher()
    
    try:
        creer_interface()
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution de l'interface : {e}")
        raise
    finally:
        logging.info("Application terminée.")

if __name__ == "__main__":
    logging.info("Initialisation de l'application... (Première instance)")
    try:
        main()
    except Exception as e:
        logging.critical(f"Erreur critique : {e}")
        print("Une erreur critique est survenue. Consultez les logs pour plus de détails.")