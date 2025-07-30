#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de templates API curl pour l'installation
Assure que tous les templates sont correctement générés
"""

import os
import json
from pathlib import Path

def create_api_templates():
    """Crée tous les templates API curl nécessaires"""
    
    print("🏗️  GÉNÉRATION DES TEMPLATES API")
    print("=" * 50)
    
    # Créer le dossier templates si nécessaire
    templates_dir = Path("templates/api_commands")
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Template OpenAI (le plus important à corriger)
    openai_template = '''curl https://api.openai.com/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer OPENAI_API_KEY" \\
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {
        "role": "user",
        "content": "Explain how AI works"
      }
    ],
    "max_tokens": 1000,
    "temperature": 0.7
  }'
'''
    
    # Template Gemini (maintenir la compatibilité)
    gemini_template = '''curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=GEMINI_API_KEY" \\
  -H 'Content-Type: application/json' \\
  -X POST \\
  -d '{"contents": [{"parts": [{"text": "Explain how AI works"}]}]}'   
'''
    
    # Template Claude (pour l'avenir)
    claude_template = '''curl https://api.anthropic.com/v1/messages \\
  -H "Content-Type: application/json" \\
  -H "x-api-key: CLAUDE_API_KEY" \\
  -H "anthropic-version: 2023-06-01" \\
  -d '{
    "model": "claude-3-sonnet-20240229",
    "max_tokens": 1000,
    "messages": [
      {
        "role": "user",
        "content": "Explain how AI works"
      }
    ]
  }'
'''
    
    templates = {
        "openai_chat.txt": openai_template,
        "gemini_chat.txt": gemini_template,
        "claude_chat.txt": claude_template
    }
    
    generated_count = 0
    updated_count = 0
    
    for filename, content in templates.items():
        filepath = templates_dir / filename
        
        if filepath.exists():
            # Vérifier si le contenu est différent
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                
                if existing_content.strip() != content.strip():
                    # Mise à jour nécessaire
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"🔄 Mis à jour: {filename}")
                    updated_count += 1
                else:
                    print(f"✅ Correct: {filename}")
                    
            except Exception as e:
                print(f"❌ Erreur lecture {filename}: {e}")
        else:
            # Nouveau template
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"🆕 Créé: {filename}")
                generated_count += 1
            except Exception as e:
                print(f"❌ Erreur création {filename}: {e}")
    
    # Vérification finale du template OpenAI
    print(f"\n🔍 VÉRIFICATION TEMPLATE OPENAI:")
    print("-" * 40)
    
    openai_path = templates_dir / "openai_chat.txt"
    if openai_path.exists():
        with open(openai_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifications critiques
        checks = [
            ("/chat/completions" in content, "Endpoint correct"),
            ('"messages"' in content, "Structure messages"),
            ('"role": "user"' in content, "Role user"),
            ('"content":' in content, "Field content"),
            ('"model":' in content, "Model spécifié"),
            ("max_tokens" in content, "Max tokens"),
            ("temperature" in content, "Temperature"),
            ("OPENAI_API_KEY" in content, "Placeholder API key")
        ]
        
        all_good = True
        for check, desc in checks:
            print(f"{'✅' if check else '❌'} {desc}")
            if not check:
                all_good = False
        
        if all_good:
            print("🎉 Template OpenAI parfaitement configuré!")
        else:
            print("⚠️ Template OpenAI nécessite des corrections")
    else:
        print("❌ Template OpenAI introuvable!")
    
    print(f"\n📊 RÉSUMÉ:")
    print(f"Templates créés: {generated_count}")
    print(f"Templates mis à jour: {updated_count}")
    
    return generated_count + updated_count > 0

def create_profile_templates():
    """Crée les templates de profils JSON pour l'installation"""
    
    print(f"\n🗂️  GÉNÉRATION DES TEMPLATES DE PROFILS")
    print("-" * 50)
    
    profiles_dir = Path("profiles")
    profiles_dir.mkdir(exist_ok=True)
    
    # Template de profil OpenAI (le plus important)
    openai_profile_template = {
        "profil": "OpenAI",
        "nom": "OpenAI",
        "api_key": "",
        "replace_apikey": "OPENAI_API_KEY",
        "template_id": "openai_chat",
        "default": False,
        "history": False,
        "role": "",
        "behavior": "",
        "conversation": {
            "enabled": True,
            "max_context_length": 4000,
            "summary_enabled": True,
            "summary_trigger_length": 8000,
            "summary_target_length": 2000,
            "summary_template_id": "openai_summary",
            "conversation_file": "conversations/conversation.txt"
        },
        "file_generation": {
            "enabled": False,
            "mode": "simple",
            "simple_config": {
                "include_question": True,
                "include_response": True,
                "base_filename": "conversation",
                "same_file": True
            },
            "dev_config": {
                "extension": ".py"
            }
        }
    }
    
    # Template de profil Gemini (compatibilité)
    gemini_profile_template = {
        "profil": "Gemini",
        "nom": "Gemini",
        "api_key": "",
        "replace_apikey": "GEMINI_API_KEY",
        "template_id": "gemini_chat",
        "default": True,
        "history": False,
        "role": "",
        "behavior": "",
        "conversation": {
            "enabled": True,
            "max_context_length": 4000,
            "summary_enabled": True,
            "summary_trigger_length": 8000,
            "summary_target_length": 2000,
            "summary_template_id": "gemini_summary",
            "conversation_file": "conversations/conversation.txt"
        },
        "file_generation": {
            "enabled": False,
            "mode": "simple",
            "simple_config": {
                "include_question": True,
                "include_response": True,
                "base_filename": "conversation",
                "same_file": True
            },
            "dev_config": {
                "extension": ".py"
            }
        }
    }
    
    # Template de profil Claude
    claude_profile_template = {
        "profil": "Claude",
        "nom": "Claude",
        "api_key": "",
        "replace_apikey": "CLAUDE_API_KEY",
        "template_id": "claude_chat",
        "default": False,
        "history": False,
        "role": "",
        "behavior": "",
        "conversation": {
            "enabled": True,
            "max_context_length": 4000,
            "summary_enabled": True,
            "summary_trigger_length": 8000,
            "summary_target_length": 2000,
            "summary_template_id": "claude_summary",
            "conversation_file": "conversations/conversation.txt"
        },
        "file_generation": {
            "enabled": False,
            "mode": "simple",
            "simple_config": {
                "include_question": True,
                "include_response": True,
                "base_filename": "conversation",
                "same_file": True
            },
            "dev_config": {
                "extension": ".py"
            }
        }
    }
    
    templates = {
        "OpenAI.json.template": openai_profile_template,
        "Gemini.json.template": gemini_profile_template,
        "Claude.json.template": claude_profile_template
    }
    
    template_count = 0
    
    for filename, template_data in templates.items():
        filepath = profiles_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Template créé: {filename}")
            template_count += 1
        except Exception as e:
            print(f"❌ Erreur création {filename}: {e}")
    
    return template_count

def validate_installation():
    """Valide que l'installation est complète"""
    
    print(f"\n🔍 VALIDATION DE L'INSTALLATION")
    print("-" * 50)
    
    errors = []
    
    # Vérifier les templates API
    api_templates = ["openai_chat.txt", "gemini_chat.txt", "claude_chat.txt"]
    for template in api_templates:
        path = Path(f"templates/api_commands/{template}")
        if path.exists():
            print(f"✅ Template API: {template}")
        else:
            print(f"❌ Manquant: {template}")
            errors.append(f"Template API manquant: {template}")
    
    # Vérifier les templates de profils
    profile_templates = ["OpenAI.json.template", "Gemini.json.template", "Claude.json.template"]
    for template in profile_templates:
        path = Path(f"profiles/{template}")
        if path.exists():
            print(f"✅ Template profil: {template}")
        else:
            print(f"❌ Manquant: {template}")
            errors.append(f"Template profil manquant: {template}")
    
    # Vérifier la structure spécifique OpenAI
    openai_path = Path("templates/api_commands/openai_chat.txt")
    if openai_path.exists():
        with open(openai_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "/chat/completions" in content and '"messages"' in content:
            print("✅ Template OpenAI structure correcte")
        else:
            print("❌ Template OpenAI structure incorrecte")
            errors.append("Template OpenAI mal formé")
    
    if errors:
        print(f"\n❌ ERREURS DÉTECTÉES:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print(f"\n🎉 INSTALLATION VALIDÉE!")
        print("✅ Tous les templates sont présents")
        print("✅ OpenAI correctement configuré")
        return True

def main():
    """Fonction principale d'installation des templates"""
    
    print("🚀 INSTALLATION COMPLÈTE DES TEMPLATES")
    print("=" * 60)
    
    # Générer les templates
    api_updated = create_api_templates()
    profile_created = create_profile_templates()
    
    # Valider l'installation
    is_valid = validate_installation()
    
    print(f"\n🏁 RÉSUMÉ DE L'INSTALLATION:")
    print(f"Templates API: {'✅ Générés/Mis à jour' if api_updated else '✅ Déjà corrects'}")
    print(f"Templates profils: {'✅ Créés' if profile_created else '✅ Existants'}")
    print(f"Validation: {'✅ Succès' if is_valid else '❌ Échec'}")
    
    if is_valid:
        print(f"\n🎉 INSTALLATION TERMINÉE!")
        print("✅ OpenAI template correctement généré")
        print("✅ Prêt à utiliser Test API avec OpenAI")
        print("✅ Architecture multi-API opérationnelle")
    else:
        print(f"\n⚠️ INSTALLATION INCOMPLÈTE")
        print("🔧 Corrections manuelles nécessaires")

if __name__ == "__main__":
    main()
