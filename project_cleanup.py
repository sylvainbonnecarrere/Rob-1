"""
Script de nettoyage du projet
- Supprime tous les fichiers de test et debug
- Crée un modèle anonyme pour les profils système  
- Nettoie les logs
- Met à jour .gitignore pour protéger les données
"""

import os
import json
import shutil
from datetime import datetime

def cleanup_test_files():
    """Supprime tous les fichiers de test et debug"""
    print("🧹 NETTOYAGE DES FICHIERS DE TEST ET DEBUG")
    print("=" * 50)
    
    # Fichiers de test à supprimer
    test_files = [
        "test_agents.py",
        "test_echappement_final.py", 
        "test_file_generation.py",
        "test_gui_functions.py",
        "test_migration.py",
        "test_setup_api_fix.py",
        "test_setup_file_improvements.py",
        "test_setup_improvements.py",
        "test_solution_finale.py"
    ]
    
    # Fichiers debug à supprimer
    debug_files = [
        "debug_cas_echec.py",
        "debug_echappement.py"
    ]
    
    # Fichiers de migration et cleanup obsolètes
    obsolete_files = [
        "cleanup_migration.py",
        "final_cleanup.py",
        "migration_tool.py"
    ]
    
    # Logs à supprimer
    log_files = [
        "application.log",
        "debug_api.log", 
        "debug_curl.log"
    ]
    
    all_files = test_files + debug_files + obsolete_files + log_files
    removed_count = 0
    
    for filename in all_files:
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"✅ Supprimé: {filename}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Erreur suppression {filename}: {e}")
        else:
            print(f"⚠️  Déjà absent: {filename}")
    
    print(f"\n📊 {removed_count} fichiers supprimés")
    return removed_count > 0

def create_system_profile_template():
    """Crée un modèle anonyme pour les profils système"""
    print("\n🏗️  CRÉATION MODÈLE PROFIL SYSTÈME")
    print("=" * 50)
    
    # Modèle anonyme
    template = {
        "generated_at": "YYYY-MM-DDTHH:MM:SS.ssssss",
        "os_info": {
            "name": "Windows|Linux|Darwin",
            "version": "version_number",
            "architecture": "AMD64|x86_64|ARM64"
        },
        "python_info": {
            "version": "X.Y.Z",
            "executable": "/path/to/python/executable"
        },
        "hardware_info": {
            "cpu_cores": 0,
            "total_memory_gb": 0.0,
            "disk_free_gb": 0.0
        },
        "app_info": {
            "directory": "/path/to/app/directory",
            "script_path": "/path/to/main.py",
            "key_files": [
                "main.py",
                "gui.py",
                "config_manager.py",
                "api_client.py",
                "system_profile_generator.py",
                "utils.py"
            ]
        }
    }
    
    # Sauvegarder le modèle
    template_path = "system/hardware/profile_template.json"
    os.makedirs(os.path.dirname(template_path), exist_ok=True)
    
    try:
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        print(f"✅ Modèle créé: {template_path}")
        
        # Créer un README pour expliquer
        readme_content = """# Profils Système

Ce dossier contient les profils matériels générés automatiquement par l'application.

## Fichiers

- `profile_template.json` : Modèle de structure pour les profils
- `*_profile_*.json` : Profils générés automatiquement (ignorés par git)

## Confidentialité

Les profils générés contiennent des informations système sensibles et sont 
automatiquement exclus du contrôle de version via .gitignore.

## Structure du profil

```json
{
  "generated_at": "timestamp",
  "os_info": { "name", "version", "architecture" },
  "python_info": { "version", "executable" },
  "hardware_info": { "cpu_cores", "total_memory_gb", "disk_free_gb" },
  "app_info": { "directory", "script_path", "key_files" }
}
```
"""
        
        readme_path = "system/hardware/README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"✅ Documentation créée: {readme_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur création modèle: {e}")
        return False

def cleanup_personal_profiles():
    """Supprime les profils système contenant des données personnelles"""
    print("\n🔒 SUPPRESSION PROFILS PERSONNELS")
    print("=" * 50)
    
    hardware_dir = "system/hardware"
    if not os.path.exists(hardware_dir):
        print("⚠️  Dossier hardware non trouvé")
        return True
    
    files = os.listdir(hardware_dir)
    profile_files = [f for f in files if f.endswith('_profile_*.json') or 'profile_' in f]
    
    # Exclure le template
    profile_files = [f for f in profile_files if f != 'profile_template.json']
    
    removed_count = 0
    for filename in profile_files:
        filepath = os.path.join(hardware_dir, filename)
        try:
            os.remove(filepath)
            print(f"✅ Supprimé: {filename}")
            removed_count += 1
        except Exception as e:
            print(f"❌ Erreur suppression {filename}: {e}")
    
    print(f"📊 {removed_count} profils personnels supprimés")
    return True

def update_gitignore():
    """Met à jour .gitignore pour protéger les données sensibles"""
    print("\n🛡️  MISE À JOUR .GITIGNORE")
    print("=" * 50)
    
    gitignore_additions = """
# === DONNÉES SENSIBLES ===
# Profils système générés (contiennent infos matériel)
system/hardware/*_profile_*.json
system/hardware/windows_profile_*.json
system/hardware/linux_profile_*.json
system/hardware/macos_profile_*.json

# Logs applicatifs
*.log
debug_*.log
application.log

# Clés API et configuration sensible
api_key.txt
.env

# Cache Python
__pycache__/
*.pyc
*.pyo
*.pyd

# Fichiers temporaires
*.tmp
*.temp
.DS_Store
Thumbs.db

# Dossiers de développement/test
development/
conversations/

# Configuration locale
config_local.yaml
"""
    
    try:
        # Lire le .gitignore existant
        gitignore_path = ".gitignore"
        existing_content = ""
        
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        
        # Vérifier si les protections sont déjà présentes
        if "DONNÉES SENSIBLES" in existing_content:
            print("✅ .gitignore déjà protégé")
            return True
        
        # Ajouter les protections
        with open(gitignore_path, 'a', encoding='utf-8') as f:
            f.write(gitignore_additions)
        
        print("✅ .gitignore mis à jour avec protections")
        print("📋 Nouvelles protections ajoutées:")
        print("   - Profils système personnels")
        print("   - Logs et fichiers temporaires") 
        print("   - Dossiers de développement")
        print("   - Configuration sensible")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur mise à jour .gitignore: {e}")
        return False

def cleanup_cache():
    """Nettoie les caches et fichiers temporaires"""
    print("\n🗑️  NETTOYAGE CACHES")
    print("=" * 50)
    
    # Supprimer __pycache__
    if os.path.exists("__pycache__"):
        try:
            shutil.rmtree("__pycache__")
            print("✅ Cache Python supprimé")
        except Exception as e:
            print(f"❌ Erreur suppression cache: {e}")
    
    # Nettoyer les logs système s'ils existent
    system_logs_dir = "system/logs"
    if os.path.exists(system_logs_dir):
        try:
            log_files = [f for f in os.listdir(system_logs_dir) if f.endswith('.log')]
            for log_file in log_files:
                os.remove(os.path.join(system_logs_dir, log_file))
                print(f"✅ Log système supprimé: {log_file}")
        except Exception as e:
            print(f"❌ Erreur nettoyage logs système: {e}")
    
    print("✅ Nettoyage caches terminé")
    return True

def verify_application_integrity():
    """Vérifie que les fichiers essentiels de l'application sont présents"""
    print("\n🔍 VÉRIFICATION INTÉGRITÉ APPLICATION")
    print("=" * 50)
    
    essential_files = [
        "main.py",
        "gui.py", 
        "config_manager.py",
        "api_client.py",
        "system_profile_generator.py",
        "utils.py",
        "requirements.txt",
        "README.md"
    ]
    
    missing_files = []
    for filename in essential_files:
        if not os.path.exists(filename):
            missing_files.append(filename)
            print(f"❌ MANQUANT: {filename}")
        else:
            print(f"✅ OK: {filename}")
    
    if missing_files:
        print(f"\n⚠️  ATTENTION: {len(missing_files)} fichiers essentiels manquants!")
        return False
    else:
        print("\n✅ Tous les fichiers essentiels sont présents")
        return True

def main():
    """Nettoyage principal du projet"""
    print("🚀 NETTOYAGE COMPLET DU PROJET")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success_steps = 0
    total_steps = 6
    
    # Étape 1: Vérification intégrité AVANT nettoyage
    if verify_application_integrity():
        success_steps += 1
        print("✅ Étape 1/6: Intégrité vérifiée")
    else:
        print("❌ Étape 1/6: Problème d'intégrité détecté")
        print("🛑 ARRÊT - Vérifiez les fichiers manquants avant de continuer")
        return False
    
    # Étape 2: Nettoyage fichiers test/debug
    if cleanup_test_files():
        success_steps += 1
        print("✅ Étape 2/6: Fichiers test/debug nettoyés")
    
    # Étape 3: Suppression profils personnels
    if cleanup_personal_profiles():
        success_steps += 1
        print("✅ Étape 3/6: Profils personnels supprimés")
    
    # Étape 4: Création modèle système
    if create_system_profile_template():
        success_steps += 1
        print("✅ Étape 4/6: Modèle système créé")
    
    # Étape 5: Protection .gitignore
    if update_gitignore():
        success_steps += 1
        print("✅ Étape 5/6: .gitignore protégé")
    
    # Étape 6: Nettoyage caches
    if cleanup_cache():
        success_steps += 1
        print("✅ Étape 6/6: Caches nettoyés")
    
    # Résultat final
    print("\n" + "=" * 60)
    if success_steps == total_steps:
        print("🎉 NETTOYAGE COMPLET RÉUSSI!")
        print("📋 Résumé des actions:")
        print("   ✅ Fichiers de test/debug supprimés")
        print("   ✅ Données personnelles protégées")
        print("   ✅ Modèle système anonyme créé")
        print("   ✅ .gitignore sécurisé")
        print("   ✅ Caches nettoyés")
        print("   ✅ Intégrité application préservée")
        print("\n💡 Votre projet est maintenant prêt pour le commit!")
        print("🔒 Vos données personnelles sont protégées")
    else:
        print(f"⚠️  NETTOYAGE PARTIEL: {success_steps}/{total_steps} étapes réussies")
        print("🔍 Vérifiez les erreurs ci-dessus")
    
    return success_steps == total_steps

if __name__ == "__main__":
    main()
