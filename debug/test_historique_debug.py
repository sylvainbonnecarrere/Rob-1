#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test débogage historique Gemini - Analyse pas à pas
Reproduit le problème avec des logs détaillés
"""

import sys
import os
import tkinter as tk

# Ajouter le dossier parent au PATH pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_historique_gemini_debug():
    """
    Test simple pour déclencher le débogage de l'historique
    Simule une conversation avec historique pour voir les logs
    """
    print("🚀 TEST DÉBOGAGE HISTORIQUE GEMINI")
    print("=" * 50)
    
    # Import du système principal
    import gui
    from conversation_manager import ConversationManager
    from config_manager import ConfigManager
    
    # Créer une fenêtre test minimale
    root = tk.Tk()
    root.withdraw()  # Cacher la fenêtre
    
    # Créer les composants nécessaires
    champ_q = tk.Text(root)
    champ_r = tk.Text(root)
    champ_history = tk.Text(root)
    
    # Initialiser le ConversationManager avec profil Gemini
    config_manager = ConfigManager()
    
    # Charger le profil Gemini
    profil_gemini = config_manager.load_profile("Gemini")
    if not profil_gemini:
        print("❌ Erreur: Impossible de charger le profil Gemini")
        return False
    
    print(f"✅ Profil Gemini chargé: {profil_gemini.get('name', 'Unknown')}")
    print(f"   History activé: {profil_gemini.get('history', False)}")
    
    # Mettre à jour le profil global
    gui.profilAPIActuel = profil_gemini
    
    # Créer le ConversationManager
    conversation_manager = ConversationManager(
        config_manager=config_manager,
        profile_config=profil_gemini.get('conversation', {}),
        api_type="gemini"
    )
    
    # Simuler une conversation avec historique
    print("\n📝 SIMULATION CONVERSATION:")
    conversation_manager.add_message('user', 'Bonjour, mon nom est toto')
    conversation_manager.add_message('model', 'Bonjour toto ! Je suis ravi de faire votre connaissance.')
    
    # Ajouter la question test dans le champ
    question_test = "Comment je m'appelle ?"
    champ_q.insert('1.0', question_test)
    
    print(f"   Question 1: Bonjour, mon nom est toto")
    print(f"   Réponse 1: Bonjour toto ! Je suis ravi...")
    print(f"   Question 2: {question_test}")
    
    print("\n🔍 LANCEMENT DU DÉBOGAGE...")
    print("=" * 50)
    
    # Appeler soumettreQuestionAPI avec les logs
    try:
        gui.soumettreQuestionAPI(champ_q, champ_r, champ_history, conversation_manager, None)
        
        # Récupérer la réponse
        reponse = champ_r.get('1.0', tk.END).strip()
        print(f"\n📋 RÉPONSE FINALE:")
        print(f"   {reponse[:200]}{'...' if len(reponse) > 200 else ''}")
        
        # Analyser si l'historique a été pris en compte
        if "toto" in reponse.lower():
            print("✅ HISTORIQUE PRIS EN COMPTE - Le nom 'toto' apparaît dans la réponse")
            return True
        else:
            print("❌ HISTORIQUE IGNORÉ - Le nom 'toto' n'apparaît pas dans la réponse")
            return False
            
    except Exception as e:
        print(f"❌ ERREUR PENDANT LE TEST: {e}")
        return False
    finally:
        root.destroy()

def main():
    """
    Lance le test de débogage
    """
    success = test_historique_gemini_debug()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 TEST RÉUSSI - Historique fonctionnel")
    else:
        print("⚠️  TEST ÉCHOUÉ - Historique non fonctionnel")
    print("=" * 50)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
