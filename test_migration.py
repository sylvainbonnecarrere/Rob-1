"""
Test et exécution de la migration YAML → JSON
Script autonome pour valider la nouvelle architecture
"""

import sys
import os
import logging

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from migration_tool import migrate_yaml_profiles_to_json
from system_profile_generator import generate_system_profile_at_startup
from config_manager import ConfigManager

def setup_logging():
    """Configure le logging pour les tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('migration_test.log')
        ]
    )

def test_config_manager():
    """Test du ConfigManager"""
    print("\n=== TEST CONFIG MANAGER ===")
    
    try:
        config_mgr = ConfigManager(".")
        
        # Test création profils par défaut
        config_mgr.create_default_profiles()
        print("✅ Profils par défaut créés")
        
        # Test liste profils
        profiles = config_mgr.list_profiles()
        print(f"✅ Profils trouvés : {profiles}")
        
        # Test chargement profil par défaut
        default_profile = config_mgr.get_default_profile()
        if default_profile:
            print(f"✅ Profil par défaut : {default_profile['name']}")
        else:
            print("❌ Aucun profil par défaut")
        
        return True
    except Exception as e:
        print(f"❌ Erreur ConfigManager : {e}")
        return False

def test_system_profile_generator():
    """Test du générateur de profil système"""
    print("\n=== TEST SYSTEM PROFILE GENERATOR ===")
    
    try:
        success = generate_system_profile_at_startup(".")
        if success:
            print("✅ Profil système généré avec succès")
        else:
            print("❌ Échec génération profil système")
        
        return success
    except Exception as e:
        print(f"❌ Erreur SystemProfileGenerator : {e}")
        return False

def test_yaml_migration():
    """Test de la migration YAML"""
    print("\n=== TEST MIGRATION YAML ===")
    
    try:
        # Vérifier s'il y a des fichiers YAML à migrer
        profiles_dir = "profiles"
        yaml_files = []
        if os.path.exists(profiles_dir):
            yaml_files = [f for f in os.listdir(profiles_dir) if f.endswith('.yaml')]
        
        if not yaml_files:
            print("ℹ️  Aucun fichier YAML à migrer")
            return True
        
        print(f"📁 Fichiers YAML trouvés : {yaml_files}")
        
        # Effectuer la migration
        success = migrate_yaml_profiles_to_json(".")
        
        if success:
            print("✅ Migration YAML → JSON réussie")
        else:
            print("❌ Échec migration YAML → JSON")
        
        return success
    except Exception as e:
        print(f"❌ Erreur migration : {e}")
        return False

def test_json_profiles_validity():
    """Vérifie la validité des profils JSON après migration"""
    print("\n=== VALIDATION PROFILS JSON ===")
    
    try:
        config_mgr = ConfigManager(".")
        
        profiles = config_mgr.list_profiles()
        if not profiles:
            print("❌ Aucun profil JSON trouvé")
            return False
        
        valid_count = 0
        for profile_name in profiles:
            profile = config_mgr.load_profile(profile_name)
            if profile:
                valid_count += 1
                print(f"✅ {profile_name} : valide")
            else:
                print(f"❌ {profile_name} : invalide")
        
        print(f"📊 Résultat : {valid_count}/{len(profiles)} profils valides")
        return valid_count == len(profiles)
    except Exception as e:
        print(f"❌ Erreur validation : {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 DÉBUT DES TESTS DE MIGRATION")
    print("=" * 50)
    
    setup_logging()
    
    tests = [
        ("ConfigManager", test_config_manager),
        ("System Profile Generator", test_system_profile_generator),
        ("Migration YAML", test_yaml_migration),
        ("Validation JSON", test_json_profiles_validity)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Erreur critique test {test_name} : {e}")
            results[test_name] = False
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    
    success_count = 0
    for test_name, success in results.items():
        status = "✅ RÉUSSI" if success else "❌ ÉCHEC"
        print(f"{test_name}: {status}")
        if success:
            success_count += 1
    
    print(f"\n🎯 TOTAL : {success_count}/{len(tests)} tests réussis")
    
    if success_count == len(tests):
        print("\n🎉 MIGRATION COMPLÈTE RÉUSSIE !")
        print("📝 Prochaines étapes :")
        print("  1. Intégrer les nouvelles fonctions dans gui.py")
        print("  2. Tester l'interface utilisateur")
        print("  3. Supprimer les anciens fichiers YAML")
        print("  4. Nettoyer le fichier [profil]system_windows.yaml")
    else:
        print("\n⚠️  MIGRATION PARTIELLE - Vérifiez les erreurs ci-dessus")
    
    return success_count == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
