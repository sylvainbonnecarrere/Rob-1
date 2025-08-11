#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils - OS Utilities Module
===========================
Module centralisant les utilitaires spécifiques au système d'exploitation
Responsabilités : création lanceurs, vérifications système, gestion fichiers temporaires
"""

import os
import sys
import stat
import platform
import subprocess
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from contextlib import contextmanager


class OSUtils:
    """
    Gestionnaire des utilitaires système multi-OS
    
    Responsabilités (Single Responsibility Principle) :
    - Création et gestion des lanceurs OS-spécifiques
    - Vérifications de l'environnement système
    - Gestion des fichiers et dossiers temporaires
    - Utilitaires de compatibilité multi-plateforme
    """
    
    # Configuration des lanceurs par OS
    LAUNCHER_CONFIGS = {
        "windows": {
            "filename": "RUN.bat",
            "extension": ".bat",
            "executable_permission": False
        },
        "linux": {
            "filename": "run.sh", 
            "extension": ".sh",
            "executable_permission": True
        },
        "darwin": {  # macOS
            "filename": "run.sh",
            "extension": ".sh", 
            "executable_permission": True
        }
    }
    
    def __init__(self, workspace_root: str = "."):
        """
        Initialise les utilitaires OS
        
        Args:
            workspace_root: Répertoire racine de l'application
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.logger = logging.getLogger(__name__)
        self.current_os = self._detect_os()
        self._temp_files: List[Path] = []
        self._temp_dirs: List[Path] = []
    
    def _detect_os(self) -> str:
        """
        Détecte le système d'exploitation actuel
        
        Returns:
            str: 'windows', 'linux', ou 'darwin' (macOS)
        """
        system = platform.system().lower()
        
        # Normalisation pour Windows
        if system == 'windows' or sys.platform.startswith('win'):
            return 'windows'
        elif system == 'darwin':
            return 'darwin'  # macOS
        else:
            return 'linux'  # Par défaut pour Unix-like
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Retourne les informations détaillées du système
        
        Returns:
            Dict: Informations système complètes
        """
        return {
            "os": self.current_os,
            "platform": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
            "workspace_root": str(self.workspace_root)
        }
    
    def check_and_create_launcher(self) -> bool:
        """
        Vérifie et crée un lanceur OS-spécifique si nécessaire
        
        Returns:
            bool: True si un lanceur existe ou a été créé avec succès
        """
        try:
            print("🚀 Vérification du lanceur système...")
            
            # Obtenir la configuration pour l'OS actuel
            config = self.LAUNCHER_CONFIGS.get(self.current_os)
            if not config:
                self.logger.warning(f"OS non supporté pour lanceur: {self.current_os}")
                return False
            
            launcher_path = self.workspace_root / config["filename"]
            
            # Vérifier si le lanceur existe déjà
            if launcher_path.exists():
                print(f"✅ Lanceur existant: {config['filename']}")
                self.logger.info(f"Lanceur OS déjà présent: {config['filename']}")
                return True
            
            # Créer le lanceur
            print(f"🔧 Création du lanceur pour {platform.system()}...")
            
            launcher_content = self._generate_launcher_content()
            if not launcher_content:
                return False
            
            # Écrire le fichier lanceur
            with open(launcher_path, 'w', encoding='utf-8', newline='\\n' if self.current_os != 'windows' else '\\r\\n') as f:
                f.write(launcher_content)
            
            # Appliquer les permissions si nécessaire
            if config["executable_permission"]:
                os.chmod(launcher_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)  # 755
            
            os_display_name = {
                'windows': 'Windows',
                'linux': 'Linux', 
                'darwin': 'macOS'
            }.get(self.current_os, self.current_os)
            
            print(f"✅ Lanceur {os_display_name} créé: {config['filename']}")
            self.logger.info(f"Lanceur {os_display_name} créé avec succès")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur création lanceur: {e}")
            self.logger.error(f"Erreur création lanceur: {e}")
            return False
    
    def _generate_launcher_content(self) -> Optional[str]:
        """
        Génère le contenu du lanceur selon l'OS
        
        Returns:
            str: Contenu du lanceur ou None en cas d'erreur
        """
        try:
            if self.current_os == 'windows':
                return self._generate_windows_launcher()
            else:
                return self._generate_unix_launcher()
        except Exception as e:
            self.logger.error(f"Erreur génération contenu lanceur: {e}")
            return None
    
    def _generate_windows_launcher(self) -> str:
        """Génère le contenu du lanceur Windows (.bat)"""
        return '''@echo off
REM Lanceur automatique Rob-1 pour Windows
REM Généré automatiquement - Ne pas modifier

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
    echo.
    pause
    exit /b 1
)

REM Vérifier que main.py existe
if not exist "main.py" (
    echo ❌ Fichier main.py introuvable
    echo 📁 Répertoire actuel: %CD%
    echo.
    pause
    exit /b 1
)

REM Afficher les informations de lancement
echo ✅ Python détecté
echo 📄 Fichier main.py trouvé
echo ⏳ Lancement de l'application...
echo.

REM Lancer l'application (mode graphique silencieux)
start "Rob-1" /MIN pythonw "main.py"

REM Message de confirmation et fermeture automatique
echo ✅ Application lancée en arrière-plan
echo 🔄 Cette fenêtre va se fermer automatiquement...
timeout /t 2 /nobreak >nul
exit
'''
    
    def _generate_unix_launcher(self) -> str:
        """Génère le contenu du lanceur Unix (Linux/macOS)"""
        os_name = "macOS" if self.current_os == "darwin" else "Linux"
        
        return f'''#!/bin/bash
# Lanceur automatique Rob-1 pour {os_name}
# Généré automatiquement - Ne pas modifier

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
    echo ""
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
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
    exit 1
fi

# Afficher les informations de lancement
echo "✅ Python détecté: $PYTHON_CMD"
echo "📄 Fichier main.py trouvé"
echo "⏳ Lancement de l'application..."
echo ""

# Lancer l'application
$PYTHON_CMD "main.py"

# Récupérer le code de retour
EXIT_CODE=$?

# Gestion de fermeture
echo ""
if [ $EXIT_CODE -ne 0 ]; then
    echo "❌ Erreur lors de l'exécution (code: $EXIT_CODE)"
    echo "📋 Vérifiez les logs dans system/logs/application.log"
    read -p "Appuyez sur Entrée pour continuer..."
else
    echo "✅ Application fermée normalement"
    sleep 1
fi

exit $EXIT_CODE
'''
    
    def verifier_installation_curl(self) -> bool:
        """
        Vérifie si curl est installé et accessible dans le système
        
        Returns:
            bool: True si curl est disponible
        """
        try:
            print("🔍 Vérification de curl...")
            
            result = subprocess.run(
                ['curl', '--version'], 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=10
            )
            
            # Extraire la version de curl
            version_line = result.stdout.split('\\n')[0] if result.stdout else "Version inconnue"
            print(f"✅ Curl disponible: {version_line}")
            self.logger.info(f"Curl disponible: {version_line}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Curl installé mais erreur d'exécution: {e}")
            self.logger.warning(f"Curl erreur d'exécution: {e}")
            return False
        except FileNotFoundError:
            print("⚠️ Curl non trouvé - Installation recommandée pour compatibilité maximale")
            self.logger.warning("Curl non disponible dans le PATH")
            return False
        except subprocess.TimeoutExpired:
            print("⚠️ Timeout lors de la vérification curl")
            self.logger.warning("Timeout vérification curl")
            return False
        except Exception as e:
            print(f"⚠️ Erreur vérification curl: {e}")
            self.logger.warning(f"Erreur vérification curl: {e}")
            return False
    
    @contextmanager
    def create_temp_file(self, suffix: str = "", prefix: str = "rob1_", content: str = ""):
        """
        Gestionnaire de contexte pour fichiers temporaires auto-nettoyés
        
        Args:
            suffix: Extension du fichier
            prefix: Préfixe du nom de fichier
            content: Contenu initial du fichier
            
        Yields:
            Path: Chemin vers le fichier temporaire
        """
        temp_file = None
        try:
            # Créer le fichier temporaire
            fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, text=True)
            temp_file = Path(temp_path)
            
            # Écrire le contenu initial si fourni
            if content:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                os.close(fd)
            
            # Enregistrer pour nettoyage
            self._temp_files.append(temp_file)
            
            print(f"📁 Fichier temporaire créé: {temp_file.name}")
            self.logger.debug(f"Fichier temporaire créé: {temp_path}")
            
            yield temp_file
            
        finally:
            # Nettoyage automatique
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                    if temp_file in self._temp_files:
                        self._temp_files.remove(temp_file)
                    self.logger.debug(f"Fichier temporaire nettoyé: {temp_file}")
                except Exception as e:
                    self.logger.warning(f"Erreur nettoyage fichier temporaire: {e}")
    
    @contextmanager
    def create_temp_directory(self, prefix: str = "rob1_"):
        """
        Gestionnaire de contexte pour répertoires temporaires auto-nettoyés
        
        Args:
            prefix: Préfixe du nom de répertoire
            
        Yields:
            Path: Chemin vers le répertoire temporaire
        """
        temp_dir = None
        try:
            # Créer le répertoire temporaire
            temp_path = tempfile.mkdtemp(prefix=prefix)
            temp_dir = Path(temp_path)
            
            # Enregistrer pour nettoyage
            self._temp_dirs.append(temp_dir)
            
            print(f"📁 Répertoire temporaire créé: {temp_dir.name}")
            self.logger.debug(f"Répertoire temporaire créé: {temp_path}")
            
            yield temp_dir
            
        finally:
            # Nettoyage automatique
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                    if temp_dir in self._temp_dirs:
                        self._temp_dirs.remove(temp_dir)
                    self.logger.debug(f"Répertoire temporaire nettoyé: {temp_dir}")
                except Exception as e:
                    self.logger.warning(f"Erreur nettoyage répertoire temporaire: {e}")
    
    def cleanup_temp_files(self) -> int:
        """
        Nettoie manuellement tous les fichiers temporaires en attente
        
        Returns:
            int: Nombre de fichiers/dossiers nettoyés
        """
        cleaned_count = 0
        
        # Nettoyer les fichiers
        for temp_file in self._temp_files.copy():
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    cleaned_count += 1
                self._temp_files.remove(temp_file)
            except Exception as e:
                self.logger.warning(f"Erreur nettoyage fichier {temp_file}: {e}")
        
        # Nettoyer les répertoires
        for temp_dir in self._temp_dirs.copy():
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    cleaned_count += 1
                self._temp_dirs.remove(temp_dir)
            except Exception as e:
                self.logger.warning(f"Erreur nettoyage répertoire {temp_dir}: {e}")
        
        if cleaned_count > 0:
            print(f"🗑️ {cleaned_count} fichier(s)/dossier(s) temporaire(s) nettoyé(s)")
            self.logger.info(f"{cleaned_count} éléments temporaires nettoyés")
        
        return cleaned_count
    
    def get_executable_path(self, executable_name: str) -> Optional[Path]:
        """
        Trouve le chemin complet d'un exécutable dans le PATH
        
        Args:
            executable_name: Nom de l'exécutable à rechercher
            
        Returns:
            Path: Chemin vers l'exécutable ou None si non trouvé
        """
        try:
            if self.current_os == 'windows' and not executable_name.endswith('.exe'):
                executable_name += '.exe'
            
            result = subprocess.run(
                ['where' if self.current_os == 'windows' else 'which', executable_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout.strip():
                exe_path = Path(result.stdout.strip().split('\\n')[0])
                self.logger.debug(f"Exécutable trouvé: {executable_name} -> {exe_path}")
                return exe_path
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        self.logger.debug(f"Exécutable non trouvé: {executable_name}")
        return None


def main():
    """Point d'entrée pour tests standalone"""
    print("🔬 Test standalone OSUtils")
    print("=" * 35)
    
    # Initialiser OSUtils
    os_utils = OSUtils()
    
    # Afficher les informations système
    print("📊 Informations système:")
    system_info = os_utils.get_system_info()
    for key, value in system_info.items():
        print(f"   {key}: {value}")
    
    print()
    
    # Test création lanceur
    launcher_created = os_utils.check_and_create_launcher()
    print(f"🚀 Création lanceur: {'✅ OK' if launcher_created else '❌ Échec'}")
    
    # Test vérification curl
    curl_available = os_utils.verifier_installation_curl()
    print(f"🔍 Curl disponible: {'✅ OK' if curl_available else '⚠️  Non trouvé'}")
    
    # Test fichier temporaire
    print("\\n📁 Test fichier temporaire:")
    try:
        with os_utils.create_temp_file(suffix=".json", content='{"test": "data"}') as temp_file:
            print(f"   ✅ Fichier temporaire: {temp_file}")
            print(f"   📄 Contenu: {temp_file.read_text(encoding='utf-8')}")
        print("   🗑️ Fichier temporaire auto-nettoyé")
    except Exception as e:
        print(f"   ❌ Erreur test temporaire: {e}")
    
    # Nettoyage final
    cleaned = os_utils.cleanup_temp_files()
    
    print(f"\\n✅ Test OSUtils terminé - {cleaned} éléments nettoyés")


if __name__ == "__main__":
    main()
