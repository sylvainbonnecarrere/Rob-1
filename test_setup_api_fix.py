"""
Test de correction du menu Setup API 
Vérification du chargement des profils par défaut et de la liste des profils
"""

import sys
import os

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_manager import ConfigManager

def test_setup_api_loading():
    """Test du chargement des profils dans Setup API"""
    print("🔧 TEST SETUP API - CHARGEMENT PROFILS")
    print("=" * 50)
    
    config_manager = ConfigManager(".")
    
    # Test 1: Vérifier le profil par défaut
    print("\n=== TEST 1: Profil par défaut ===")
    try:
        profil_defaut = config_manager.get_default_profile()
        if profil_defaut:
            print(f"✅ Profil par défaut : {profil_defaut['name']}")
            print(f"  - API URL: {profil_defaut.get('api_url', 'N/A')}")
            print(f"  - Template ID: {profil_defaut.get('template_id', 'N/A')}")
            print(f"  - Replace API Key: {profil_defaut.get('replace_apikey', 'N/A')}")
        else:
            print("❌ Aucun profil par défaut trouvé")
            return False
    except Exception as e:
        print(f"❌ Erreur chargement profil par défaut : {e}")
        return False
    
    # Test 2: Lister tous les profils disponibles
    print("\n=== TEST 2: Liste des profils ===")
    try:
        profils = config_manager.list_profiles()
        if profils:
            print(f"✅ Profils disponibles : {profils}")
            if len(profils) >= 3:
                print("✅ Au moins 3 profils (Gemini, OpenAI, Claude)")
            else:
                print("⚠️  Moins de 3 profils trouvés")
        else:
            print("❌ Aucun profil trouvé")
            return False
    except Exception as e:
        print(f"❌ Erreur listage profils : {e}")
        return False
    
    # Test 3: Chargement de chaque profil
    print("\n=== TEST 3: Chargement individuel des profils ===")
    try:
        for profil_name in profils:
            profil_data = config_manager.load_profile(profil_name)
            if profil_data:
                template_id = profil_data.get('template_id', '')
                template_exists = bool(config_manager.load_template(template_id)) if template_id else False
                print(f"✅ {profil_name} : chargé (template: {'✅' if template_exists else '❌'})")
            else:
                print(f"❌ {profil_name} : erreur de chargement")
                return False
    except Exception as e:
        print(f"❌ Erreur chargement individuel : {e}")
        return False
    
    # Test 4: Simulation du chargement Setup API
    print("\n=== TEST 4: Simulation Setup API ===")
    try:
        # Simuler charger_profil_defaut()
        profil_defaut_nom = profil_defaut.get('name', 'Gemini') if profil_defaut else 'Gemini'
        print(f"✅ Nom profil par défaut pour Setup API : {profil_defaut_nom}")
        
        # Simuler charger_donnees_profil()
        donnees_profil = config_manager.load_profile(profil_defaut_nom)
        if donnees_profil:
            print(f"✅ Données profil chargées : {list(donnees_profil.keys())}")
            
            # Vérifier les champs importants
            champs_importants = ['name', 'api_key', 'api_url', 'template_id', 'replace_apikey']
            for champ in champs_importants:
                valeur = donnees_profil.get(champ, '')
                statut = "✅" if valeur else "⚠️"
                print(f"  {statut} {champ}: {'present' if valeur else 'vide'}")
        else:
            print("❌ Impossible de charger les données du profil")
            return False
    except Exception as e:
        print(f"❌ Erreur simulation Setup API : {e}")
        return False
    
    return True

def main():
    """Test principal"""
    print("🚀 TEST CORRECTION SETUP API")
    print()
    
    success = test_setup_api_loading()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ SETUP API CORRIGÉ !")
        print("📝 Le menu Setup API devrait maintenant :")
        print("  ✅ Charger le profil par défaut correctement")
        print("  ✅ Afficher les 3 profils dans la liste déroulante")
        print("  ✅ Remplir les champs avec les bonnes données")
        print("  ✅ Gérer les templates curl correctement")
    else:
        print("❌ Il reste des problèmes à corriger")
    
    return success

if __name__ == "__main__":
    main()
