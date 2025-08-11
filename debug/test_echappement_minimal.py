#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test minimal - validation de l'échappement JSON
Teste uniquement l'échappement sans passer par l'interface complète
"""

import sys
import os
import json

# Ajouter le dossier parent au PATH pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_echappement_direct():
    """
    Test direct de l'échappement JSON pour l'historique
    """
    print("🔧 TEST ÉCHAPPEMENT DIRECT")
    print("=" * 40)
    
    # Historique problématique (comme généré par la concaténation)
    historique_brut = """Utilisateur: Bonjour, mon nom est toto\\nAssistant: Bonjour toto ! Je suis ravi de faire votre connaissance.\\nUtilisateur: Comment je m'appelle ?\\n"""
    
    print(f"Historique brut: {historique_brut}")
    
    # Échappement pour JSON (simulation de escape_for_json_template)
    escaped = historique_brut
    
    # 1. Échapper les antislashes
    escaped = escaped.replace('\\', '\\\\')
    # 2. Échapper les guillemets
    escaped = escaped.replace('"', '\\"')
    # 3. Corriger les \\n en \n
    escaped = escaped.replace('\\\\n', '\\n')
    
    print(f"Historique échappé: {escaped}")
    
    # Test de construction JSON
    try:
        test_json = f'{{"text": "{escaped}"}}'
        parsed = json.loads(test_json)
        print("✅ JSON valide:")
        print(f"   Texte: {parsed['text'][:100]}...")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON invalide: {e}")
        return False

def test_template_complet():
    """
    Test avec le template Gemini complet
    """
    print("\n🎯 TEST TEMPLATE GEMINI")
    print("=" * 40)
    
    # Simuler le prompt avec historique échappé
    historique_echappe = "Utilisateur: Bonjour, mon nom est toto\\nAssistant: Bonjour toto ! Je suis ravi de faire votre connaissance.\\nUtilisateur: Comment je m'appelle ?\\n"
    
    # Template Gemini (simulation)
    payload = {
        "system_instruction": {
            "parts": [{"text": "assistant expert"}]
        },
        "contents": [
            {
                "parts": [{"text": f"Question: {historique_echappe}"}]
            }
        ]
    }
    
    try:
        json_string = json.dumps(payload, ensure_ascii=False, indent=2)
        print("✅ Template Gemini valide")
        print(f"Taille: {len(json_string)} chars")
        return True
    except Exception as e:
        print(f"❌ Template Gemini invalide: {e}")
        return False

def main():
    print("🚀 TEST MINIMAL ÉCHAPPEMENT")
    print("=" * 50)
    
    test1 = test_echappement_direct()
    test2 = test_template_complet()
    
    print("\n📊 RÉSULTATS:")
    print(f"   Échappement direct: {'✅' if test1 else '❌'}")
    print(f"   Template complet:   {'✅' if test2 else '❌'}")
    
    if test1 and test2:
        print("\n🎉 ÉCHAPPEMENT FONCTIONNEL")
        return 0
    else:
        print("\n⚠️  ÉCHAPPEMENT DÉFAILLANT")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
