#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST DEBUG CORRECTION CURL
Analyser pourquoi corriger_commande_curl() casse les commandes simples
"""

import re

def corriger_commande_curl(commande):
    """Fonction temporaire simplifiée"""
    if not commande:
        return commande
    print("[DEBUG] Correction curl simplifiée")
    corrected = commande.replace('\\\n', ' ').replace('\n', ' ')
    corrected = re.sub(r'\s+', ' ', corrected).strip()
    return corrected

# Template original du curl_basic.txt
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
            "text": "Test message simple"
          }
        ]
      ]
    ]
  }'
'''

print("🔍 ANALYSE CORRECTION CURL")
print("=" * 60)
print("AVANT CORRECTION:")
print(template_original)
print("\n" + "=" * 60)
print("APRÈS CORRECTION:")
commande_corrigee = corriger_commande_curl(template_original)
print(commande_corrigee)
print("\n" + "=" * 60)
print("ANALYSE DU PROBLÈME:")

# Vérifier si les headers sont intacts
if '-H "x-goog-api-key:' in commande_corrigee and "Content-Type: application/json" in commande_corrigee:
    print("✅ Headers semblent corrects")
else:
    print("❌ Headers corrompus dans la correction")
    
# Vérifier la structure JSON
if commande_corrigee.count('"') % 2 == 0:
    print("✅ Guillemets équilibrés")
else:
    print("❌ Guillemets déséquilibrés - problème de parsing")
