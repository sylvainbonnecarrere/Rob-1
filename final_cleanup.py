"""
Script de nettoyage final - Suppression des fichiers de test de migration
Nettoie le projet en conservant uniquement les fonctionnalités opérationnelles
"""

import os
import shutil

def cleanup_test_files():
    """Supprime les fichiers de test de migration devenus obsolètes"""
    print("🧹 NETTOYAGE DES FICHIERS DE TEST")
    print("=" * 50)
    
    # Fichiers à supprimer
    files_to_remove = [
        "test_migration.py",
        "test_gui_functions.py", 
        "test_file_generation.py",
        "cleanup_migration.py"
    ]
    
    # Logs à supprimer
    logs_to_remove = [
        "migration_test.log"
    ]
    
    print("\n=== SUPPRESSION DES FICHIERS DE TEST ===")
    removed_count = 0
    
    for filename in files_to_remove:
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"🗑️  Supprimé : {filename}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Erreur suppression {filename} : {e}")
        else:
            print(f"ℹ️  Déjà absent : {filename}")
    
    print("\n=== SUPPRESSION DES LOGS DE TEST ===")
    
    for filename in logs_to_remove:
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"🗑️  Supprimé : {filename}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Erreur suppression {filename} : {e}")
        else:
            print(f"ℹ️  Déjà absent : {filename}")
    
    print("\n=== CONSERVATION DES FICHIERS ESSENTIELS ===")
    
    # Fichiers à conserver absolument
    essential_files = [
        "config_manager.py",
        "system_profile_generator.py", 
        "migration_tool.py",
        "gui.py",
        "main.py"
    ]
    
    for filename in essential_files:
        if os.path.exists(filename):
            print(f"✅ Conservé : {filename}")
        else:
            print(f"⚠️  MANQUANT : {filename}")
    
    print("\n=== VÉRIFICATION DES RÉPERTOIRES ===")
    
    # Vérifier les répertoires essentiels
    essential_dirs = [
        "profiles",
        "templates", 
        "system",
        "conversations"
    ]
    
    for dirname in essential_dirs:
        if os.path.exists(dirname):
            file_count = len([f for f in os.listdir(dirname) if os.path.isfile(os.path.join(dirname, f))])
            print(f"✅ {dirname}/ : {file_count} fichiers")
        else:
            print(f"⚠️  MANQUANT : {dirname}/")
    
    print("\n" + "=" * 50)
    print(f"🎉 NETTOYAGE TERMINÉ !")
    print(f"📊 {removed_count} fichiers supprimés")
    print("✨ Projet nettoyé et prêt pour la suite")
    
    return removed_count > 0

if __name__ == "__main__":
    print("🚀 NETTOYAGE POST-MIGRATION")
    print("Suppression des fichiers de test obsolètes...")
    print()
    
    success = cleanup_test_files()
    
    if success:
        print("\n✅ Nettoyage effectué avec succès")
        print("\n📝 Prochaines étapes :")
        print("  1. Vérifier que l'interface fonctionne toujours")
        print("  2. Tester les menus Setup et Test API")
        print("  3. S'attaquer aux problèmes d'historique")
    else:
        print("\n⚠️  Rien à nettoyer ou erreurs rencontrées")
