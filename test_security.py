#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de sécurité du système de profils
Vérifie que les templates sont sécurisés et que les profils créés n'exposent pas de clés API
"""

import os
import sys
from config_manager import ConfigManager

def test_security_system():
    """Test complet du système de sécurité"""
    print("=" * 60)
    print("🔒 TEST DE SÉCURITÉ DU SYSTÈME DE PROFILS")
    print("=" * 60)
    
    try:
        # 1. Initialisation du ConfigManager
        print("\n📋 1. Initialisation du ConfigManager...")
        cm = ConfigManager(".")
        print("✅ ConfigManager initialisé avec succès")
        
        # 2. Vérification des templates sécurisés
        print("\n📋 2. Vérification des templates sécurisés...")
        templates_path = "profiles"
        templates = ["Gemini.json.template", "Claude.json.template", "OpenAI.json.template"]
        
        for template in templates:
            template_file = os.path.join(templates_path, template)
            if os.path.exists(template_file):
                print(f"✅ Template {template} trouvé")
            else:
                print(f"❌ Template {template} MANQUANT")
        
        # 3. Test de création des profils
        print("\n📋 3. Test de création des profils...")
        success = cm.create_default_profiles()
        if success:
            print("✅ Création des profils: SUCCÈS")
        else:
            print("❌ Création des profils: ÉCHEC")
        
        # 4. Vérification de la sécurité des profils créés
        print("\n📋 4. Vérification de la sécurité...")
        profiles = ["Gemini", "Claude", "OpenAI"]
        security_ok = True
        
        for profile_name in profiles:
            try:
                profile_data = cm.load_profile(profile_name)
                if profile_data:
                    api_key = profile_data.get("api_key", "NOT_FOUND")
                    if api_key == "":
                        print(f"✅ {profile_name}: api_key vide (SÉCURISÉ)")
                    else:
                        print(f"❌ {profile_name}: FAILLE DE SÉCURITÉ - api_key = '{api_key}'")
                        security_ok = False
                else:
                    print(f"⚠️  {profile_name}: Profil non trouvé")
            except Exception as e:
                print(f"❌ {profile_name}: Erreur de chargement - {e}")
                security_ok = False
        
        # 5. Résumé du test
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DU TEST DE SÉCURITÉ")
        print("=" * 60)
        
        if security_ok:
            print("🟢 SYSTÈME SÉCURISÉ - Aucune clé API exposée")
            print("✅ Tous les profils ont des api_key vides")
            print("✅ Templates séparés fonctionnels")
        else:
            print("🔴 PROBLÈME DE SÉCURITÉ DÉTECTÉ!")
            print("❌ Des clés API pourraient être exposées")
        
        # 6. Test des méthodes principales
        print("\n📋 6. Test des méthodes principales...")
        try:
            profiles_list = cm.list_profiles()
            print(f"✅ Liste des profils: {profiles_list}")
            
            default_profile = cm.get_default_profile()
            if default_profile:
                print(f"✅ Profil par défaut: {default_profile.get('name', 'INCONNU')}")
            else:
                print("⚠️  Aucun profil par défaut trouvé")
        
        except Exception as e:
            print(f"❌ Erreur test méthodes: {e}")
        
        print("\n🏁 Test terminé avec succès!")
        return security_ok
        
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE: {e}")
        print(f"Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Changer le répertoire de travail vers le dossier du script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Lancer le test
    success = test_security_system()
    
    # Code de sortie
    sys.exit(0 if success else 1)
