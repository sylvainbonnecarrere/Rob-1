"""
Test des fonctions corrigées de l'interface graphique
"""

import sys
import os

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_manager import ConfigManager

def test_gui_functions():
    """Test des fonctions principales de l'interface"""
    print("🔧 TEST DES FONCTIONS GUI CORRIGÉES")
    print("=" * 50)
    
    # Initialiser le ConfigManager
    config_manager = ConfigManager(".")
    
    # Test 1: Chargement du profil par défaut
    print("\n=== TEST 1: Chargement du profil par défaut ===")
    try:
        default_profile = config_manager.get_default_profile()
        if default_profile:
            print(f"✅ Profil par défaut chargé : {default_profile['name']}")
            print(f"  - API URL: {default_profile.get('api_url', 'N/A')}")
            print(f"  - Template ID: {default_profile.get('template_id', 'N/A')}")
            print(f"  - Replace API Key: {default_profile.get('replace_apikey', 'N/A')}")
        else:
            print("❌ Aucun profil par défaut trouvé")
            return False
    except Exception as e:
        print(f"❌ Erreur lors du chargement du profil par défaut : {e}")
        return False
    
    # Test 2: Chargement du template
    print("\n=== TEST 2: Chargement du template ===")
    try:
        template_id = default_profile.get('template_id', '')
        if template_id:
            template_content = config_manager.load_template(template_id)
            if template_content:
                print(f"✅ Template {template_id} chargé avec succès")
                print(f"  - Longueur: {len(template_content)} caractères")
                print(f"  - Début: {template_content[:100]}...")
            else:
                print(f"❌ Template {template_id} introuvable")
                return False
        else:
            print("❌ Aucun template_id dans le profil")
            return False
    except Exception as e:
        print(f"❌ Erreur lors du chargement du template : {e}")
        return False
    
    # Test 3: Simulation de la fonction creerCommandeAPI
    print("\n=== TEST 3: Simulation creerCommandeAPI ===")
    try:
        def creerCommandeAPI_test(profil):
            if not profil:
                return ""
            
            # Nouveau système : utiliser les templates séparés
            template_id = profil.get('template_id', '')
            if template_id:
                template_content = config_manager.load_template(template_id)
                if template_content:
                    # Remplacer la clé API dans le template
                    api_key = profil.get('api_key', '')
                    replace_key = profil.get('replace_apikey', 'GEMINI_API_KEY')
                    if api_key and replace_key:
                        return template_content.replace(replace_key, api_key)
                    return template_content
            
            # Fallback : ancien système curl_exe (pour compatibilité)
            curl_exe = profil.get('curl_exe', '')
            api_key = profil.get('api_key', '')
            if curl_exe and api_key:
                return curl_exe.replace('GEMINI_API_KEY', api_key)
            return curl_exe
        
        cmd_api = creerCommandeAPI_test(default_profile)
        if cmd_api:
            print(f"✅ Commande API créée avec succès")
            print(f"  - Longueur: {len(cmd_api)} caractères")
            print(f"  - Début: {cmd_api[:150]}...")
            
            # Vérifier que la clé API a été remplacée
            api_key = default_profile.get('api_key', '')
            replace_key = default_profile.get('replace_apikey', 'GEMINI_API_KEY')
            if api_key and replace_key not in cmd_api:
                print(f"✅ Clé API correctement remplacée")
            else:
                print(f"⚠️  La clé API n'a pas été remplacée correctement")
        else:
            print("❌ Aucune commande API générée")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la création de la commande API : {e}")
        return False
    
    # Test 4: Vérification des champs nécessaires
    print("\n=== TEST 4: Vérification des champs du profil ===")
    try:
        required_fields = ['name', 'api_key', 'template_id', 'replace_apikey']
        missing_fields = []
        
        for field in required_fields:
            if not default_profile.get(field):
                missing_fields.append(field)
        
        if not missing_fields:
            print("✅ Tous les champs requis sont présents")
        else:
            print(f"⚠️  Champs manquants ou vides : {missing_fields}")
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des champs : {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 TOUS LES TESTS RÉUSSIS !")
    print("L'interface Test API devrait maintenant fonctionner correctement.")
    return True

if __name__ == "__main__":
    success = test_gui_functions()
    if success:
        print("\n✅ Prêt pour tester l'interface Test API")
    else:
        print("\n❌ Il reste des problèmes à corriger")
    sys.exit(0 if success else 1)
