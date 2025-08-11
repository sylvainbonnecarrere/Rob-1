import logging
import os
import subprocess
from gui import creer_interface

# Importation pour la création du lanceur OS-spécifique  
import sys
import platform
import stat

# Configuration des logs avec gestion d'erreurs
try:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("application.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
except Exception as e:
    print(f"Attention: Impossible de configurer les logs - {e}")

# Création des dossiers essentiels
PROFILES_DIR = "profiles"
CONVERSATIONS_DIR = "conversations"
TEMPLATES_DIR = "templates"

try:
    os.makedirs(PROFILES_DIR, exist_ok=True)
    os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    # Migration Phase 3 V2: Templates gérés exclusivement via APIManager
    # Architecture V2 pure - Plus de référence à api_commands (supprimé)
    os.makedirs(os.path.join(TEMPLATES_DIR, "chat"), exist_ok=True)
    print("✅ Dossiers système créés avec succès")
except Exception as e:
    print(f"⚠️ Erreur création dossiers: {e}")

def initialisation_premier_lancement():
    """Initialisation complète pour le premier lancement de l'application"""
    try:
        # Import du ConfigManager pour la gestion JSON
        from config_manager import ConfigManager
        
        # Initialiser le gestionnaire de configuration
        config_manager = ConfigManager(".")
        
        # Créer les profils par défaut via ConfigManager (JSON)
        config_manager.create_default_profiles()
        
        print("✅ Configuration par défaut initialisée (système JSON)")
        return True
        
    except ImportError as e:
        print(f"❌ Erreur import ConfigManager: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur initialisation: {e}")
        return False

def verifier_installation_curl():
    """Vérifie si curl est installé et accessible dans le système"""
    try:
        result = subprocess.run(['curl', '--version'], capture_output=True, text=True, check=True)
        print("✅ Curl installé et accessible")
        return True
    except subprocess.CalledProcessError:
        print("⚠️ Curl non trouvé - Installation recommandée pour compatibilité maximale")
        return False
    except FileNotFoundError:
        print("⚠️ Curl non trouvé - Installation recommandée pour compatibilité maximale") 
        return False
    except Exception as e:
        print(f"⚠️ Erreur vérification curl: {e}")
        return False

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
python --version >nul 2>nul
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

def ensure_templates_installed():
    """S'assure que tous les templates API sont correctement installés"""
    try:
        from install_templates import create_api_templates, create_profile_templates
        
        # Générer/vérifier les templates API
        create_api_templates()
        
        # Générer les templates de profils si nécessaire
        create_profile_templates()
        
        logging.info("✅ Templates API vérifiés et mis à jour")
        return True
        
    except Exception as e:
        logging.warning(f"⚠️ Erreur vérification templates: {e}")
        return False

def main():
    """Point d'entrée principal de l'application."""
    logging.info("🚀 Application Rob-1 V2 démarrée")
    
    # === INITIALISATION PREMIER LANCEMENT ===
    print("📋 Initialisation système...")
    
    # 1. Initialisation configuration par défaut
    if not initialisation_premier_lancement():
        print("❌ Échec initialisation - L'application va continuer avec les paramètres disponibles")
    
    # 2. Vérification curl (pour mode curl par défaut)
    verifier_installation_curl()
    
    # 3. S'assurer que les templates API sont correctement installés
    print("📁 Vérification templates...")
    ensure_templates_installed()
    
    # 4. Créer le lanceur OS-spécifique au premier lancement
    print("🔧 Configuration lanceur système...")
    check_and_create_launcher()
    
    print("✅ Initialisation terminée - Lancement interface")
    
    # === LANCEMENT INTERFACE ===
    try:
        creer_interface()
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution de l'interface : {e}")
        print(f"❌ Erreur interface: {e}")
        raise
    finally:
        logging.info("🔄 Application terminée")

if __name__ == "__main__":
    logging.info("Initialisation de l'application... (Première instance)")
    try:
        main()
    except Exception as e:
        logging.critical(f"Erreur critique : {e}")
        print("Une erreur critique est survenue. Consultez les logs pour plus de détails.")