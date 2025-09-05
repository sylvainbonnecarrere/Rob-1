#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Template Python natif pour GEMINI
# Provider: gemini

import os
import sys
from google import genai
from google.genai import types

# Force UTF-8 pour Windows
sys.stdout.reconfigure(encoding='utf-8')

# Configuration
api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    print("ERROR: GEMINI_API_KEY not found in environment")
    exit(1)

# Initialiser le client
client = genai.Client(api_key=api_key)

# Variables du template
model = "{{LLM_MODEL}}"
user_prompt = "{{USER_PROMPT}}"
system_role = "{{SYSTEM_PROMPT_ROLE}}"
system_behavior = "{{SYSTEM_PROMPT_BEHAVIOR}}"

# Configuration de la requête
config = types.GenerateContentConfig(
    system_instruction=f"{system_role}. {system_behavior}"
)

try:
    # Exécuter la requête
    response = client.models.generate_content(
        model=model,
        config=config,
        contents=user_prompt
    )
    
    # Formater la réponse en JSON compatible avec l'interface
    import json
    
    # Créer une structure JSON similaire à l'API REST de Gemini
    response_data = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": response.text
                        }
                    ]
                }
            }
        ]
    }
    
    # Afficher la réponse en JSON pour l'interface
    print(json.dumps(response_data, ensure_ascii=False))
    
except Exception as e:
    # Formater l'erreur en JSON également
    import json
    error_data = {
        "error": {
            "message": str(e),
            "code": "NATIVE_API_ERROR"
        }
    }
    print(json.dumps(error_data, ensure_ascii=False))
    exit(1)