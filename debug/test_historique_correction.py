#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de correction de l'historique Gemini
Valide que l'échappement JSON fonctionne correctement
"""

import json
import sys
import os

# Ajouter le dossier parent au PATH pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conversation_manager import ConversationManager

def test_echappement_json():
    """
    Test l'échappement JSON avec des caractères problématiques
    """
    print("🔧 TEST ÉCHAPPEMENT JSON")
    print("=" * 50)
    
    # Créer un ConversationManager
    manager = ConversationManager()
    
    # Messages avec caractères problématiques
    messages_test = [
        ('user', 'Bonjour, comment ça va ?'),
        ('model', 'Ça va bien ! Je suis là pour vous aider avec vos "questions".'),
        ('user', 'Peux-tu expliquer la différence entre\nles listes et les tuples en Python ?'),
        ('model', 'Les listes sont mutables: [1, 2, 3]\nLes tuples sont immutables: (1, 2, 3)\n\nC\'est la différence principale.'),
        ('user', 'Merci ! Et les dictionnaires ?'),
        ('model', 'Les dictionnaires utilisent des clés: {"nom": "valeur", "age": 25}')
    ]
    
    # Ajouter les messages
    for role, content in messages_test:
        manager.add_message(role, content)
        print(f"✅ Ajouté: {role} - {len(content)} chars")
    
    # Obtenir les messages pour l'API
    api_messages = manager.get_messages_for_api()
    
    # Construire le prompt complet (comme dans soumettreQuestionAPI)
    prompt_complet = ""
    for msg in api_messages:
        role_label = "Utilisateur" if msg['role'] == 'user' else "Assistant"
        prompt_complet += f"{role_label}: {msg['parts'][0]['text']}\n"
    
    prompt_final = prompt_complet.strip()
    
    print(f"\n📝 PROMPT CONCATÉNÉ BRUT ({len(prompt_final)} chars):")
    print("-" * 30)
    print(prompt_final[:200] + "..." if len(prompt_final) > 200 else prompt_final)
    
    # DEBUG : Inspecter les caractères du prompt
    print(f"\n🔍 ANALYSE CARACTÈRES BRUTS:")
    for i, char in enumerate(prompt_final[:100]):  # Analyser les 100 premiers chars
        if ord(char) < 32 or ord(char) > 126:  # Caractères non imprimables
            print(f"   Position {i}: '{char}' (ord={ord(char)}) - {'PROBLÉMATIQUE' if ord(char) < 32 else 'OK'}")
    
    # NOUVELLE ÉTAPE : Échapper pour JSON
    prompt_escaped = manager.escape_for_json_template(prompt_final)
    print(f"\n📝 PROMPT ÉCHAPPÉ POUR JSON ({len(prompt_escaped)} chars):")
    print("-" * 30)
    print(prompt_escaped[:200] + "..." if len(prompt_escaped) > 200 else prompt_escaped)
    
    # Test de validation JSON avec le prompt échappé
    is_valid, error_msg = manager.validate_json_for_template(prompt_escaped)
    
    print(f"\n🔍 VALIDATION JSON:")
    print(f"   Valide: {'✅ OUI' if is_valid else '❌ NON'}")
    if not is_valid:
        print(f"   Erreur: {error_msg}")
    
    # Test de construction JSON complète avec le prompt échappé
    try:
        test_payload = f'{{"contents":[{{"parts":[{{"text":"{prompt_escaped}"}}]}}]}}'
        parsed = json.loads(test_payload)
        print("✅ JSON CURL VALIDE")
        
        # Vérifier la structure
        if 'contents' in parsed and len(parsed['contents']) > 0:
            text_content = parsed['contents'][0]['parts'][0]['text']
            print(f"📊 Contenu extrait: {len(text_content)} chars")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON CURL INVALIDE: {e}")
        return False
    except Exception as e:
        print(f"❌ ERREUR CONSTRUCTION: {e}")
        return False
    
    return True

def test_template_gemini_simulation():
    """
    Simule l'injection dans le template Gemini complet
    """
    print("\n🎯 TEST TEMPLATE GEMINI COMPLET")
    print("=" * 50)
    
    manager = ConversationManager()
    
    # Conversation test avec historique
    manager.add_message('user', 'Salut ! Comment ça va ?')
    manager.add_message('model', 'Salut ! Ça va très bien, merci !')
    manager.add_message('user', 'Peux-tu m\'expliquer les "APIs REST" ?')
    
    # Obtenir le prompt historique
    api_messages = manager.get_messages_for_api()
    prompt_complet = ""
    for msg in api_messages:
        role_label = "Utilisateur" if msg['role'] == 'user' else "Assistant"
        prompt_complet += f"{role_label}: {msg['parts'][0]['text']}\n"
    
    # Simuler l'injection dans le template Gemini
    gemini_payload = {
        "system_instruction": {
            "parts": [{"text": "assistant expert et précis"}]
        },
        "contents": [
            {
                "parts": [{"text": prompt_complet.strip()}]
            }
        ]
    }
    
    try:
        # Convertir en JSON string (comme le ferait curl)
        json_string = json.dumps(gemini_payload, ensure_ascii=False, indent=2)
        print("✅ TEMPLATE GEMINI VALIDE")
        print(f"📊 Taille payload: {len(json_string)} chars")
        
        # Vérifier qu'on peut le re-parser
        reparsed = json.loads(json_string)
        user_text = reparsed['contents'][0]['parts'][0]['text']
        print(f"📝 Texte utilisateur extrait: {len(user_text)} chars")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR TEMPLATE GEMINI: {e}")
        return False

def main():
    """
    Lance tous les tests de validation
    """
    print("🚀 TESTS DE CORRECTION HISTORIQUE GEMINI")
    print("=" * 60)
    
    # Test 1: Échappement JSON
    test1_ok = test_echappement_json()
    
    # Test 2: Template Gemini complet
    test2_ok = test_template_gemini_simulation()
    
    # Résultats
    print("\n📊 RÉSULTATS DES TESTS")
    print("=" * 30)
    print(f"   Échappement JSON: {'✅ RÉUSSI' if test1_ok else '❌ ÉCHOUÉ'}")
    print(f"   Template Gemini:  {'✅ RÉUSSI' if test2_ok else '❌ ÉCHOUÉ'}")
    
    if test1_ok and test2_ok:
        print("\n🎉 TOUS LES TESTS RÉUSSIS - Correction validée !")
        return 0
    else:
        print("\n⚠️  ÉCHECS DÉTECTÉS - Correction à revoir")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
