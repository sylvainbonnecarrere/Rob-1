#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST DEBUG PAS À PAS - API GEMINI
Analyser pourquoi la première requête ne fonctionne pas
"""

import os
import sys
import platform
import subprocess
import re

# Ajouter le répertoire parent pour imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.api_manager import ProfileManagerFactory
    from config_manager import ConfigManager
    print("✅ Imports réussis")
except ImportError as e:
    print(f"❌ Erreur import: {e}")
    sys.exit(1)

def test_curl_step_by_step():
    """Test chaque étape de génération de la commande curl"""
    print("\n🔍 TEST DEBUG PAS À PAS - REQUÊTE CURL")
    print("=" * 60)
    
    # 1. Initialiser APIManager
    print("1. Initialisation APIManager...")
    api_manager = ProfileManagerFactory.create_api_manager_with_validation()
    if not api_manager:
        print("❌ Échec initialisation APIManager")
        return
    print("✅ APIManager initialisé")
    
    # 2. Charger profil par défaut
    print("\n2. Chargement profil par défaut...")
    profil = api_manager.get_default_profile()
    if not profil:
        print("❌ Aucun profil par défaut")
        return
    print(f"✅ Profil chargé: {profil.get('name')}")
    print(f"   Template ID: {profil.get('template_id')}")
    print(f"   API Key: {profil.get('api_key', '')[:20]}...")
    
    # 3. Test question simple
    print("\n3. Question de test...")
    test_question = "Salut, comment ça va ?"
    print(f"✅ Question: {test_question}")
    
    # 4. Générer template avec APIManager
    print("\n4. Génération template via APIManager...")
    template_id = profil.get('template_id', 'gemini_chat')
    curl_raw = api_manager.get_processed_template(template_id, profil, test_question)
    if not curl_raw:
        print("❌ Échec génération template")
        return
    print(f"✅ Template généré ({len(curl_raw)} chars)")
    print("TEMPLATE BRUT:")
    print("-" * 40)
    print(curl_raw)
    print("-" * 40)
    
    # 5. Analyser la structure
    print("\n5. Analyse structure curl...")
    lines = curl_raw.split('\n')
    print(f"✅ Nombre de lignes: {len(lines)}")
    for i, line in enumerate(lines[:5]):  # Premières lignes
        print(f"   Ligne {i+1}: {line[:80]}...")
    
    # 6. Test conversion Windows
    print("\n6. Conversion Windows PowerShell...")
    if platform.system().lower() == 'windows':
        curl_windows = curl_raw.replace('\\\n', ' ').replace('\n', ' ')
        curl_windows = re.sub(r'\s+', ' ', curl_windows).strip()
        print(f"✅ Après conversion: {len(curl_windows)} chars")
        print("CURL WINDOWS:")
        print("-" * 40)
        print(curl_windows[:200] + "..." if len(curl_windows) > 200 else curl_windows)
        print("-" * 40)
    else:
        curl_windows = curl_raw
        print("ℹ️ Pas de conversion nécessaire (non-Windows)")
    
    # 7. Validation structure curl
    print("\n7. Validation structure curl...")
    essential_parts = [
        'curl "https://',
        '-H "x-goog-api-key:',
        '-H \'Content-Type: application/json\'',
        '-d "{'
    ]
    
    for part in essential_parts:
        if part in curl_windows:
            print(f"✅ Trouvé: {part}")
        else:
            print(f"❌ MANQUE: {part}")
    
    # 8. Test d'exécution simulé (sans vraie requête)
    print("\n8. Test structure commande...")
    try:
        # Juste valider que la commande peut être parsée
        if curl_windows.startswith('curl '):
            print("✅ Commande commence par 'curl'")
        else:
            print("❌ Commande ne commence pas par 'curl'")
            
        if '"https://generativelanguage.googleapis.com' in curl_windows:
            print("✅ URL Gemini correcte")
        else:
            print("❌ URL Gemini manquante ou incorrecte")
            
        # Compter les guillemets
        quote_count = curl_windows.count('"')
        if quote_count % 2 == 0:
            print(f"✅ Guillemets équilibrés ({quote_count} total)")
        else:
            print(f"❌ Guillemets déséquilibrés ({quote_count} total)")
            
    except Exception as e:
        print(f"❌ Erreur validation: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 RÉSUMÉ DU TEST")
    print("=" * 60)
    
    return curl_windows

if __name__ == "__main__":
    try:
        curl_final = test_curl_step_by_step()
        if curl_final:
            print("✅ Test terminé - Commande curl générée")
        else:
            print("❌ Test échoué - Pas de commande curl")
    except Exception as e:
        print(f"💥 ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
