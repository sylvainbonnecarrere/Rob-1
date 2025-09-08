#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Template Python natif pour GEMINI
# Provider: gemini

import os
from google import genai
from google.genai import types

try:
    client = genai.Client(api_key="{{API_KEY}}")
    # Exécuter la requête
    response = client.models.generate_content(
    model="{{LLM_MODEL}}",
    config=types.GenerateContentConfig(
        system_instruction="{{SYSTEM_PROMPT_ROLE}}. {{SYSTEM_PROMPT_BEHAVIOR}}"),
    contents="{{USER_PROMPT}}"
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