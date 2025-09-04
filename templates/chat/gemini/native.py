#!/usr/bin/env python3
# Template Python natif pour GEMINI
# Provider: gemini

import os
from google import genai
from google.genai import types

# Configuration
api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    print("ERROR: GEMINI_API_KEY not found in environment")
    exit(1)

# Initialiser le client
client = genai.Client(api_key=api_key)

# Variables du template
model = "gemini-2.5-flash:generateContent"
user_prompt = "Hello there"
system_role = "You are a cat. "
system_behavior = "Your name is Neko."

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
    
    # Afficher la réponse
    print(response.text)
    
except Exception as e:
    print(f"Erreur API: {e}")
    exit(1)