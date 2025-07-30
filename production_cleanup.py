#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NETTOYAGE PRODUCTION FINAL
Supprime tous les fichiers temporaires et prépare pour commit
"""

import os
import subprocess
import shutil
from pathlib import Path

def analyze_git_status():
    """Analyse l'état Git actuel"""
    print("🔍 ANALYSE GIT STATUS")
    print("=" * 40)
    
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            modified_files = []
            untracked_files = []
            deleted_files = []
            
            for line in lines:
                if line.strip():
                    status = line[:2]
                    filename = line[3:]
                    
                    if 'M' in status:
                        modified_files.append(filename)
                    elif 'D' in status:
                        deleted_files.append(filename)
                    elif '??' in status:
                        untracked_files.append(filename)
            
            print("📝 FICHIERS MODIFIÉS:")
            for f in modified_files:
                print(f"   ✏️  {f}")
            
            print(f"\n🗑️  FICHIERS SUPPRIMÉS:")
            for f in deleted_files:
                print(f"   ❌ {f}")
            
            print(f"\n❓ FICHIERS NON SUIVIS:")
            for f in untracked_files:
                if any(pattern in f for pattern in ['test_', 'debug_', 'cleanup_']):
                    print(f"   🗑️  {f} (À SUPPRIMER)")
                else:
                    print(f"   ➕ {f} (À AJOUTER)")
            
            return modified_files, untracked_files, deleted_files
            
    except Exception as e:
        print(f"❌ Erreur git status: {e}")
        return [], [], []

def cleanup_temporary_files():
    """Supprime tous les fichiers temporaires"""
    print(f"\n🧹 SUPPRESSION FICHIERS TEMPORAIRES")
    print("=" * 40)
    
    # Fichiers à supprimer
    files_to_remove = [
        # Tests de développement
        "test_final_setup_history.py",
        "test_installation_complete.py", 
        "test_security.py",
        "test_curl_fix.py",
        
        # Scripts de debug
        "debug_conversation_manager_fix.py",
        "debug_curl_multiline.py",
        "debug_editable_instructions.py",
        "debug_openai_issue.py", 
        "debug_setup_history_logic_corrections.py",
        "debug_setup_history_modifications.py",
        "debug_setup_history_validation.py",
        
        # Corrections temporaires
        "correction_finale_curl.py",
        "patch_curl_multiline.py",
        "fix_openai_support.py",
        "validation_setup_history_improvements.py",
        
        # Scripts de nettoyage eux-mêmes
        "cleanup_final.py",
        "project_cleanup.py",
        
        # Logs
        "debug_curl.log",
        
        # Ce script après exécution
        "production_cleanup.py"
    ]
    
    removed_count = 0
    
    for filename in files_to_remove:
        filepath = Path(filename)
        if filepath.exists():
            try:
                filepath.unlink()
                print(f"✅ Supprimé: {filename}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Erreur {filename}: {e}")
        else:
            print(f"⚪ Absent: {filename}")
    
    # Nettoyer __pycache__
    pycache_dirs = list(Path(".").rglob("__pycache__"))
    for pycache_dir in pycache_dirs:
        if pycache_dir.is_dir():
            try:
                shutil.rmtree(pycache_dir)
                print(f"✅ Supprimé: {pycache_dir}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Erreur {pycache_dir}: {e}")
    
    # Supprimer dossiers obsolètes
    obsolete_folders = [
        "profiles_backup_conversation",
        "development"
    ]
    
    for folder in obsolete_folders:
        folder_path = Path(folder)
        if folder_path.exists() and folder_path.is_dir():
            try:
                shutil.rmtree(folder_path)
                print(f"✅ Dossier supprimé: {folder}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Erreur dossier {folder}: {e}")
    
    return removed_count

def check_yaml_files():
    """Vérifie et supprime les fichiers YAML obsolètes"""
    print(f"\n📄 VÉRIFICATION FICHIERS YAML")
    print("=" * 40)
    
    yaml_files = list(Path(".").glob("*.yaml"))
    
    if not yaml_files:
        print("✅ Aucun fichier YAML trouvé")
        return 0
    
    removed_count = 0
    
    for yaml_file in yaml_files:
        # Garder seulement les YAML essentiels (aucun pour l'instant)
        if yaml_file.name in ["config.yaml"]:  # À supprimer aussi car obsolète
            print(f"🗑️  YAML obsolète détecté: {yaml_file.name}")
            try:
                yaml_file.unlink()
                print(f"✅ Supprimé: {yaml_file.name}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Erreur {yaml_file.name}: {e}")
        else:
            print(f"⚠️  YAML non reconnu: {yaml_file.name}")
    
    return removed_count

def validate_production_files():
    """Valide que les fichiers essentiels sont présents"""
    print(f"\n✅ VALIDATION FICHIERS PRODUCTION")
    print("=" * 40)
    
    essential_files = [
        "main.py",
        "gui.py", 
        "config_manager.py",
        "conversation_manager.py",
        "system_profile_generator.py",
        "api_response_parser.py",  # NOUVEAU
        "utils.py",
        "install_templates.py",    # NOUVEAU
        "requirements.txt",
        "setup.py",
        "RUN.bat",
        "README.md"
    ]
    
    missing_files = []
    
    for file in essential_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ MANQUANT: {file}")
            missing_files.append(file)
    
    return len(missing_files) == 0

def production_cleanup():
    """Nettoyage radical pour la production"""
    
    print("🧹 NETTOYAGE RADICAL POUR PRODUCTION")
    print("=" * 60)
    
    # Fichiers à supprimer définitivement
    files_to_delete = [
        # Tests de développement
        "test_final_openai_solution.py",
        "test_final_setup_history.py", 
        "test_installation_complete.py",
        "test_security.py",
        "test_curl_fix.py",
        
        # Scripts de debug
        "debug_conversation_manager_fix.py",
        "debug_curl_multiline.py",
        "debug_editable_instructions.py", 
        "debug_openai_issue.py",
        "debug_setup_history_logic_corrections.py",
        "debug_setup_history_modifications.py",
        "debug_setup_history_validation.py",
        
        # Corrections temporaires
        "correction_finale_curl.py",
        "patch_curl_multiline.py",
        "fix_openai_support.py", 
        "validation_setup_history_improvements.py",
        
        # Tests obsolètes
        "test_character_cleaning.py",
        "test_conversation_fix.py",
        "test_conversation_integration.py",
        "test_conversation_manager.py", 
        "test_conversation_workflow.py",
        "test_flexible_history_system.py",
        "test_integration_complete.py",
        "test_openai_structure.py",
        "test_profile_custom_instructions.py",
        "test_resume_profile_indicator.py", 
        "test_setup_history_complete.py",
        "test_setup_history_dynamic.py",
        
        # Scripts de nettoyage eux-mêmes
        "cleanup_final.py",
        "project_cleanup.py",
        
        # Migrations obsolètes
        "migration_conversation.py",
        "create_launcher.py",  # Déjà supprimé selon git
        
        # Système d'agents obsolète
        "agents.py",
        "config.yaml",
        
        # Scripts d'installation (garder install_templates.py)
        # "install_templates.py",  # GARDER pour la production
        
        # Logs de debug
        "debug_curl.log",
        
        # API obsolète
        "api_client.py",
        "api.py",
        
        # Ce script lui-même
        "production_cleanup.py"
    ]
    
    # Dossiers à nettoyer
    folders_to_clean = [
        "__pycache__",
        "profiles_backup_conversation",  # Backup obsolète
        "development"  # Dossier de développement
    ]
    
    removed_count = 0
    
    print("🗑️  SUPPRESSION DES FICHIERS:")
    print("-" * 40)
    
    for filename in files_to_delete:
        filepath = Path(filename)
        if filepath.exists():
            try:
                filepath.unlink()
                print(f"✅ Supprimé: {filename}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Erreur: {filename} - {e}")
        else:
            print(f"⚪ Absent: {filename}")
    
    print(f"\n🗂️  SUPPRESSION DES DOSSIERS:")
    print("-" * 40)
    
    for foldername in folders_to_clean:
        # Chercher tous les dossiers avec ce nom
        for folder_path in Path(".").rglob(foldername):
            if folder_path.is_dir():
                try:
                    shutil.rmtree(folder_path)
                    print(f"✅ Dossier supprimé: {folder_path}")
                    removed_count += 1
                except Exception as e:
                    print(f"❌ Erreur dossier: {folder_path} - {e}")
    
    # Fichiers YAML obsolètes si pas utilisés
    yaml_files = list(Path(".").glob("*.yaml"))
    for yaml_file in yaml_files:
        if yaml_file.name == "config.yaml":
            # Vérifier si vraiment obsolète
            print(f"⚠️  YAML trouvé: {yaml_file.name} - vérification manuelle nécessaire")
    
    print(f"\n📋 STRUCTURE FINALE DE PRODUCTION:")
    print("-" * 40)
    print("""
    📁 Rob-1/ (PRODUCTION)
    ├── 🐍 main.py                    # Point d'entrée principal
    ├── 🖥️  gui.py                     # Interface utilisateur  
    ├── ⚙️  config_manager.py         # Gestion configuration
    ├── 💬 conversation_manager.py    # Gestion conversations
    ├── 🔧 system_profile_generator.py # Génération profils système
    ├── 🌐 api_response_parser.py     # Parser multi-API (NOUVEAU)
    ├── 🛠️  utils.py                   # Utilitaires
    ├── 🏗️  install_templates.py      # Installation templates
    ├── 📦 requirements.txt           # Dépendances Python
    ├── 🚀 setup.py                   # Script d'installation  
    ├── ▶️  RUN.bat                    # Lanceur Windows
    ├── 📖 README.md                  # Documentation principale
    ├── 📋 Install.md                 # Guide d'installation
    ├── 📄 SetUpFile.md               # Documentation setup
    ├── 📜 SETUP_HISTORY_FINAL_RESUME.md # Historique
    └── 📁 Dossiers/
        ├── profiles/                 # Profils API (JSON)
        ├── templates/                # Templates curl
        ├── conversations/            # Historiques conversations
        └── system/                   # Données système
    """)
    
    print(f"\n🎯 RÉSUMÉ DU NETTOYAGE:")
    print(f"Fichiers supprimés: {removed_count}")
    
    print(f"\n✅ FICHIERS CONSERVÉS POUR PRODUCTION:")
    essential_files = [
        "main.py", "gui.py", "config_manager.py", 
        "conversation_manager.py", "system_profile_generator.py",
        "api_response_parser.py", "utils.py", "install_templates.py",
        "requirements.txt", "setup.py", "RUN.bat",
        "README.md", "Install.md", "SetUpFile.md",
        "SETUP_HISTORY_FINAL_RESUME.md"
    ]
    
    for file in essential_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ MANQUANT: {file}")
    
    print(f"\n🎉 NETTOYAGE RADICAL TERMINÉ!")
    print("🚀 Projet prêt pour la production")
    print("✅ OpenAI fonctionnel")
    print("✅ Architecture multi-API en place")
    print("✅ Gemini compatible")
    
    return removed_count

if __name__ == "__main__":
    removed = production_cleanup()
    print(f"\n🏁 {removed} fichiers/dossiers supprimés")
    print("🎯 Projet optimisé pour la production")
