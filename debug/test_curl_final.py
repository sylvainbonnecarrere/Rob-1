#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST FINAL - COMMANDE CURL WINDOWS OPTIMISÉE
"""

import os
import sys
import platform
import re

# Ajouter le répertoire parent pour imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.api_manager import ProfileManagerFactory
    print("✅ Imports réussis")
except ImportError as e:
    print(f"❌ Erreur import: {e}")
    sys.exit(1)

def test_curl_final():
    """Test final avec conversion Windows complète"""
    print("\n🚀 TEST FINAL CURL WINDOWS")
    print("=" * 60)
    
    # Initialiser et générer template
    api_manager = ProfileManagerFactory.create_api_manager_with_validation()
    profil = api_manager.get_default_profile()
    
    test_question = "Salut, comment ça va ?"
    template_id = profil.get('template_id', 'gemini_chat')
    requete_curl = api_manager.get_processed_template(template_id, profil, test_question)
    
    print("AVANT CONVERSION:")
    print(requete_curl[:200] + "...")
    
    # CONVERSION WINDOWS COMPLÈTE (même logique que gui.py)
    if platform.system().lower() == 'windows':
        # 1. Convertir continuations de ligne
        requete_curl = requete_curl.replace('\\\n', ' ').replace('\n', ' ')
        requete_curl = re.sub(r'\s+', ' ', requete_curl).strip()
        
        # 2. Corriger guillemets headers  
        requete_curl = requete_curl.replace("-H 'Content-Type: application/json'", '-H "Content-Type: application/json"')
        
        # 3. Corriger guillemets JSON
        if " -d '{" in requete_curl and requete_curl.endswith("}'"):
            start_json = requete_curl.find(" -d '{") + 5
            json_part = requete_curl[start_json:-2]
            json_escaped = json_part.replace('"', '\\"')
            prefix = requete_curl[:requete_curl.find(" -d '{")]
            requete_curl = f'{prefix} -d "{{{json_escaped}}}"'
    
    print("\nAPRÈS CONVERSION WINDOWS:")
    print(requete_curl)
    
    # VALIDATION FINALE
    print("\n" + "=" * 60)
    print("🔍 VALIDATION FINALE")
    print("=" * 60)
    
    tests_validation = [
        ('curl "https://generativelanguage.googleapis.com', 'URL Gemini'),
        ('-H "x-goog-api-key:', 'Header API Key'),
        ('-H "Content-Type: application/json"', 'Header Content-Type (doubles)'),
        ('-d "{', 'Option -d avec guillemets doubles'),
        ('\\"system_instruction\\":', 'JSON avec échappement'),
        ('\\"contents\\":', 'Contents JSON'),
        ('Salut, comment ça va', 'Question intégrée'),
    ]
    
    all_good = True
    for pattern, description in tests_validation:
        if pattern in requete_curl:
            print(f"✅ {description}")
        else:
            print(f"❌ {description} - MANQUE: {pattern}")
            all_good = False
    
    # Test structure générale
    if requete_curl.count('"') % 2 == 0:
        print("✅ Guillemets équilibrés")
    else:
        print("❌ Guillemets déséquilibrés")
        all_good = False
    
    print(f"\n📏 Longueur finale: {len(requete_curl)} caractères")
    
    if all_good:
        print("\n🎉 SUCCÈS COMPLET - Commande curl prête pour Windows PowerShell!")
        return True
    else:
        print("\n❌ ÉCHEC - Problèmes détectés")
        return False

if __name__ == "__main__":
    success = test_curl_final()
    exit(0 if success else 1)
