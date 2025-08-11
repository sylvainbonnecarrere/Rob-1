#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST FINAL VALIDATION HISTORIQUE
Test complet de l'historique Gemini avec nouvelle architecture échappement JSON
"""

import os
import sys

# Ajouter le répertoire parent pour imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from conversation_manager import ConversationManager
    from config_manager import ConfigManager  
    import json
    print("✅ Tous les imports réussis")
except ImportError as e:
    print(f"❌ Erreur import: {e}")
    sys.exit(1)

def test_validation_finale():
    """Test complet avec scénario réaliste"""
    print("\n🧪 TEST FINAL VALIDATION HISTORIQUE")
    print("=" * 50)
    
    # 1. Charger configuration
    config_manager = ConfigManager()
    print("✅ ConfigManager initialisé")
    
    # 2. Initialiser ConversationManager
    conv_manager = ConversationManager(config_manager)
    print("✅ ConversationManager initialisé")
    
    # 3. Historique simulé réaliste avec tous les caractères problématiques
    historique_test = '''Human: Bonjour, comment ça va ?
Assistant: Bonjour ! Je vais bien, merci de demander. Comment puis-je vous aider aujourd'hui ?
