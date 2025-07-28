#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de création d'exécutable/lanceur multi-OS pour Rob-1
Génère automatiquement le lanceur approprié selon l'OS détecté
"""

import os
import sys
import platform
import stat

def create_os_specific_launcher(main_script_name='main.py'):
    """
    Crée un lanceur spécifique à l'OS pour exécuter l'application Python
    
    Args:
        main_script_name (str): Nom du script Python principal (défaut: 'main.py')
    
    Returns:
        bool: True si le lanceur a été créé avec succès, False sinon
    """
    try:
        # Détecter l'OS
        current_os = platform.system().lower()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        print(f"🔍 Détection de l'OS: {platform.system()}")
        print(f"📁 Répertoire de travail: {script_dir}")
        
        if current_os == 'windows' or sys.platform.startswith('win'):
            # === WINDOWS - Créer RUN.bat ===
            launcher_path = os.path.join(script_dir, 'RUN.bat')
            
            # Contenu du fichier batch Windows
            batch_content = f"""@echo off
REM Lanceur automatique Rob-1 pour Windows
REM Généré automatiquement le {platform.node()}

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
if not exist "{main_script_name}" (
    echo ❌ Fichier {main_script_name} introuvable
    echo 📁 Répertoire actuel: %CD%
    pause
    exit /b 1
)

REM Lancer l'application et fermer cette fenêtre
echo ✅ Lancement de {main_script_name}...
start "" pythonw "{main_script_name}"
exit
"""
            
            # Écrire le fichier batch
            with open(launcher_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            print(f"✅ Lanceur Windows créé: {launcher_path}")
            return True
            
        elif current_os in ['linux', 'darwin']:  # Linux ou macOS
            # === LINUX/MACOS - Créer run.sh ===
            launcher_path = os.path.join(script_dir, 'run.sh')
            
            # Contenu du script shell Unix
            shell_content = f"""#!/bin/bash
# Lanceur automatique Rob-1 pour Linux/macOS
# Généré automatiquement sur {platform.node()}

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
if [ ! -f "{main_script_name}" ]; then
    echo "❌ Fichier {main_script_name} introuvable"
    echo "📁 Répertoire actuel: $(pwd)"
    read -p "Appuyez sur Entrée pour continuer..."
    exit 1
fi

# Lancer l'application
echo "✅ Lancement de {main_script_name} avec $PYTHON_CMD..."
$PYTHON_CMD "{main_script_name}"

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
            
            # Écrire le fichier shell
            with open(launcher_path, 'w', encoding='utf-8') as f:
                f.write(shell_content)
            
            # Rendre le script exécutable
            os.chmod(launcher_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)  # 755
            
            os_name = "macOS" if current_os == 'darwin' else "Linux"
            print(f"✅ Lanceur {os_name} créé: {launcher_path}")
            print(f"🔧 Permissions exécutables définies (755)")
            return True
            
        else:
            print(f"❌ OS non supporté: {current_os}")
            print(f"💡 OS supportés: Windows, Linux, macOS")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la création du lanceur: {e}")
        return False

def check_launcher_exists():
    """
    Vérifie si un lanceur existe déjà pour cet OS
    
    Returns:
        tuple: (exists: bool, launcher_path: str)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    current_os = platform.system().lower()
    
    if current_os == 'windows' or sys.platform.startswith('win'):
        launcher_path = os.path.join(script_dir, 'RUN.bat')
    else:
        launcher_path = os.path.join(script_dir, 'run.sh')
    
    return os.path.exists(launcher_path), launcher_path

def main():
    """Fonction principale du script de création de lanceur"""
    print("=" * 60)
    print("🛠️  GÉNÉRATEUR DE LANCEUR ROB-1")
    print("=" * 60)
    
    # Vérifier si un lanceur existe déjà
    exists, launcher_path = check_launcher_exists()
    
    if exists:
        print(f"ℹ️  Un lanceur existe déjà: {os.path.basename(launcher_path)}")
        response = input("🔄 Voulez-vous le recréer ? (o/N): ").lower().strip()
        
        if response not in ['o', 'oui', 'y', 'yes']:
            print("✅ Génération annulée - Lanceur existant conservé")
            return
        
        # Supprimer l'ancien lanceur
        try:
            os.remove(launcher_path)
            print(f"🗑️  Ancien lanceur supprimé")
        except Exception as e:
            print(f"⚠️  Impossible de supprimer l'ancien lanceur: {e}")
    
    # Créer le nouveau lanceur
    print(f"\n🔨 Création du lanceur pour {platform.system()}...")
    
    success = create_os_specific_launcher('main.py')
    
    if success:
        _, new_launcher_path = check_launcher_exists()
        launcher_name = os.path.basename(new_launcher_path)
        
        print(f"\n" + "=" * 60)
        print("🎉 LANCEUR CRÉÉ AVEC SUCCÈS!")
        print("=" * 60)
        print(f"📁 Fichier: {launcher_name}")
        print(f"📍 Emplacement: {new_launcher_path}")
        
        current_os = platform.system().lower()
        if current_os == 'windows' or sys.platform.startswith('win'):
            print(f"\n💡 UTILISATION:")
            print(f"   • Double-cliquez sur {launcher_name}")
            print(f"   • Ou tapez dans un terminal: {launcher_name}")
        else:
            print(f"\n💡 UTILISATION:")
            print(f"   • Dans un terminal: ./{launcher_name}")
            print(f"   • Ou: bash {launcher_name}")
            
        print(f"\n🚀 Votre application Rob-1 peut maintenant être lancée facilement!")
    else:
        print(f"\n❌ ÉCHEC DE LA CRÉATION DU LANCEUR")
        print(f"💡 Vérifiez les permissions et l'espace disque disponible")

if __name__ == "__main__":
    main()
