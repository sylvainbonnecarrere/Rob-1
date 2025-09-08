#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SynthesisManager - Gestionnaire de synthèse pour ConversationManager
Gestion de la synthèse d'historique avec support curl et native
Compatible avec la structure JSON V2
"""

import json
import subprocess
import os
import sys

def api_summary_call(prompt_text):
    """
    Fonction de synthèse compatible V2 avec support curl/native automatique
    
    Args:
        prompt_text (str): Le prompt de synthèse généré par ConversationManager
        
    Returns:
        str: Le résumé généré ou message d'erreur
    """
    try:
        # Récupérer le profil actuel
        profil = charger_profil_api()
        if not profil:
            return "❌ Aucun profil API chargé"
        
        # Lire la méthode depuis la structure V2
        chat_config = profil.get('chat', {})
        method = chat_config.get('method', 'curl')
        
        print(f"[SYNTHESIS] Méthode détectée: {method}")
        
        # Déléguer selon la méthode
        if method == 'native':
            return _synthesis_native(prompt_text, profil)
        else:
            return _synthesis_curl(prompt_text, profil)
            
    except Exception as e:
        print(f"[SYNTHESIS ERROR] {e}")
        import traceback
        traceback.print_exc()
        return f"❌ Erreur synthèse: {e}"

def _synthesis_curl(prompt_text, profil):
    """
    Synthèse via méthode curl avec mapping V2
    """
    try:
        print("[SYNTHESIS] === MODE CURL ===")
        
        # SOLUTION SIMPLE: Patcher temporairement la variable globale profilAPIActuel
        # puis utiliser les fonctions existantes qui marchent
        
        # Importer et patcher temporairement
        import gui
        original_profil = getattr(gui, 'profilAPIActuel', None)
        gui.profilAPIActuel = profil  # Patcher temporairement
        
        try:
            # Utiliser les fonctions existantes qui marchent
            from gui import preparer_requete_curl, executer_commande_curl
            
            # Préparer la requête curl avec le profil patché
            resultat_preparation = preparer_requete_curl(prompt_text)
            
            # Gérer nouveau système avec payload file
            if isinstance(resultat_preparation, tuple) and len(resultat_preparation) == 2:
                requete_curl, payload_file = resultat_preparation
                print(f"[SYNTHESIS] Fichier payload: {payload_file}")
            else:
                requete_curl = resultat_preparation
                payload_file = None
                print(f"[SYNTHESIS] Mode ancien système")
            
            # Exécuter la commande curl
            resultat = executer_commande_curl(requete_curl, payload_file)
            
        finally:
            # Restaurer le profil original
            if original_profil is not None:
                gui.profilAPIActuel = original_profil
            elif hasattr(gui, 'profilAPIActuel'):
                delattr(gui, 'profilAPIActuel')
        
        if resultat.returncode == 0:
            try:
                reponse_json = json.loads(resultat.stdout)
                
                # MAPPING V2: Utiliser chat.response_path
                chat_config = profil.get('chat', {})
                response_path = chat_config.get('response_path', [])
                
                print(f"[SYNTHESIS] Response path V2: {response_path}")
                
                # Pour l'instant, utiliser le fallback direct car les méthodes changent
                print("[SYNTHESIS] Utilisation parsing direct Gemini")
                if response_path == ["candidates", 0, "content", "parts", 0, "text"]:
                    texte_reponse = reponse_json["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"[SYNTHESIS] ✅ Résumé curl extrait: {len(texte_reponse)} chars")
                    return texte_reponse
                else:
                    return f"❌ Response path non supporté: {response_path}"
                    
            except json.JSONDecodeError as e:
                print(f"[SYNTHESIS] Erreur JSON: {e}")
                return f"❌ Erreur JSON synthèse curl: {e}"
        else:
            print(f"[SYNTHESIS] Erreur curl: {resultat.stderr}")
            return "❌ Erreur API synthèse curl"
            
    except Exception as e:
        print(f"[SYNTHESIS] Exception curl: {e}")
        return f"❌ Exception synthèse curl: {e}"

def _synthesis_native(prompt_text, profil):
    """
    Synthèse via méthode native avec mapping V2
    """
    try:
        print("[SYNTHESIS] === MODE NATIVE ===")
        
        # Utiliser native_manager existant
        from native_manager import NativeManager
        from core.api_manager import APIManager
        
        # Initialiser NativeManager
        native_manager = NativeManager()
        
        # Récupérer le template native
        api_manager = APIManager()
        provider = profil.get('name', '').lower()
        template_id = f"{provider}_chat_native"
        
        template_content = api_manager.get_template_basic_content(template_id)
        if not template_content:
            return f"❌ Template native {template_id} non trouvé"
        
        # Mapping V2 pour les variables
        chat_config = profil.get('chat', {})
        values_config = chat_config.get('values', {})
        
        # Instructions de synthèse depuis conversation_management
        conversation_mgmt = profil.get('conversation_management', {})
        custom_instructions = conversation_mgmt.get('custom_instructions', 'Résume cette conversation')
        
        print(f"[SYNTHESIS] Instructions: {custom_instructions}")
        print(f"[SYNTHESIS] Template: {template_id}")
        
        # Variables pour le template native
        variables = {
            'USER_PROMPT': prompt_text,
            'LLM_MODEL': values_config.get('llm_model', ''),
            'API_KEY': values_config.get('api_key', ''),
            'SYSTEM_PROMPT_ROLE': custom_instructions,  # Utiliser custom_instructions
            'SYSTEM_PROMPT_BEHAVIOR': 'Assistant de synthèse'
        }
        
        # Exécuter requête native
        resultat = native_manager.execute_native_request(
            template_content,
            variables,
            provider
        )
        
        print(f"[SYNTHESIS] Résultat native brut: {resultat}")
        
        # Vérifier le statut de retour
        if resultat.get('status') != 'success':
            error_msg = resultat.get('errors', 'Erreur inconnue')
            print(f"[SYNTHESIS] Erreur native: {error_msg}")
            return f"❌ Erreur native: {error_msg}"
        
        # Extraire la réponse
        output = resultat.get('output', '')
        if not output:
            print("[SYNTHESIS] Pas de réponse native obtenue")
            return "❌ Pas de réponse native obtenue"
        
        print(f"[SYNTHESIS] Output native: {output[:200]}...")
        
        # Parser avec response_parser comme pour curl
        import api_response_parser
        
        # Récupérer response_path V2
        response_path = chat_config.get('response_path', [])
        print(f"[SYNTHESIS] Response path V2: {response_path}")
        
        try:
            # Parser la réponse JSON si c'est du JSON
            import json
            if output.strip().startswith('{'):
                response_data = json.loads(output)
                
                # Utiliser l'APIResponseParser pour extraire le texte automatiquement
                success, synthesis_text = api_response_parser.extract_text_from_api_response(response_data, 'auto')
                
                if success:
                    print(f"[SYNTHESIS] ✅ Résumé native extrait: {len(synthesis_text)} chars")
                    return synthesis_text
                else:
                    print(f"[SYNTHESIS] Erreur parsing: {synthesis_text}")
                    return f"❌ Erreur parsing native: {synthesis_text}"
            else:
                # Réponse directe (texte brut)
                print(f"[SYNTHESIS] Réponse directe: {output[:100]}...")
                return output
        except Exception as e:
            print(f"[SYNTHESIS] Erreur parsing native: {e}")
            return output  # Retourner la réponse brute en cas d'erreur
            
    except Exception as e:
        print(f"[SYNTHESIS] Exception native: {e}")
        return f"❌ Exception synthèse native: {e}"

def charger_profil_api():
    """
    Charge le profil API actuel depuis gui.py
    """
    try:
        from gui import charger_profil_api as gui_charger_profil
        return gui_charger_profil()
    except ImportError:
        print("[SYNTHESIS] Erreur import charger_profil_api")
        return None
