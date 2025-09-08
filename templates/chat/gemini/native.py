#!/usr/bin/env python3
# Template Python natif pour GEMINI
# Provider: gemini

import os
from google import genai
from google.genai import types


try:
    client = genai.Client(api_key="GEMINI_API_KEY")
    # Exécuter la requête
    response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction="You are a cat. Your name is Neko."),
    contents="Hello there"
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