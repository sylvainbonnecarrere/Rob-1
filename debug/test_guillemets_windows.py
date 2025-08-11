#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST SPÉCIFIQUE - PROBLÈME GUILLEMETS WINDOWS
"""

import re

# Template tel que généré par APIManager
template_original = '''curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent" \\
  -H "x-goog-api-key: AIzaSyDAUEcUAClwI5fOZayUreslNWkhWU4rehQ" \\
  -H 'Content-Type: application/json' \\
  -d '{
    "system_instruction": {
      "parts": [
        {
          "text": "alien rigolo réponses courtes et de moins de 5 phrases."
        }
      ]
    },
    "contents": [
      {
        "parts": [
          {
            "text": "Salut, comment ça va ?"
          }
        ]
      }
    ]
  }'
'''

print("🔍 ANALYSE PROBLÈME GUILLEMETS WINDOWS")
print("=" * 60)

print("TEMPLATE ORIGINAL:")
print(template_original)
print("\n" + "=" * 60)

# Conversion actuelle
converted = template_original.replace('\\\n', ' ').replace('\n', ' ')
converted = re.sub(r'\s+', ' ', converted).strip()

print("APRÈS CONVERSION ACTUELLE:")
print(converted)
print("\n" + "=" * 60)

# Conversion améliorée pour Windows PowerShell
def convert_for_windows_powershell(curl_template):
    """Conversion spécifique Windows PowerShell"""
    # 1. Convertir continuations de ligne
    result = curl_template.replace('\\\n', ' ').replace('\n', ' ')
    
    # 2. Nettoyer espaces multiples
    result = re.sub(r'\s+', ' ', result).strip()
    
    # 3. CORRECTION WINDOWS: Remplacer guillemets simples par doubles pour le JSON
    # Trouver le pattern -d '{ ... }' et le remplacer par -d "{ ... }"
    # Mais il faut échapper les guillemets internes
    if " -d '{" in result and result.endswith("}'"):
        # Extraire la partie JSON
        start_json = result.find(" -d '{") + 5  # Position après -d '{
        json_part = result[start_json:-2]  # Tout sauf le }' final
        
        # Échapper les guillemets dans le JSON
        json_escaped = json_part.replace('"', '\\"')
        
        # Reconstruire avec guillemets doubles
        prefix = result[:result.find(" -d '{")]
        result = f'{prefix} -d "{{{json_escaped}}}"'
    
    return result

print("CONVERSION AMÉLIORÉE WINDOWS:")
windows_fixed = convert_for_windows_powershell(template_original)
print(windows_fixed)
print("\n" + "=" * 60)

# Test validation
tests = [
    ('curl "https://', 'URL correcte'),
    ('-H "x-goog-api-key:', 'Header API key'),
    ('-H "Content-Type: application/json"', 'Header Content-Type avec doubles'),
    ('-d "{', 'Option -d avec guillemets doubles'),
    ('\\"system_instruction\\":', 'JSON échappé'),
]

print("VALIDATION WINDOWS:")
for test_pattern, description in tests:
    if test_pattern in windows_fixed:
        print(f"✅ {description}")
    else:
        print(f"❌ {description} - Motif: {test_pattern}")

print(f"\nLongueur finale: {len(windows_fixed)} caractères")
