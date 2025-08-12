#!/usr/bin/env python3
"""
Module d'extraction générique des réponses API - Phase 2
Gère l'extraction du contenu textuel depuis les réponses JSON des différentes APIs
"""

import json
import logging
from typing import Any, List, Union, Optional

def parse_response(json_data: Union[str, dict], response_path: List[Union[str, int]]) -> Optional[str]:
    """
    Extrait le texte de réponse depuis une structure JSON en utilisant un chemin de navigation
    
    Args:
        json_data: Données JSON (string ou dict) de la réponse API
        response_path: Liste des clés/indices pour naviguer dans la structure JSON
                      Ex: ["candidates", 0, "content", "parts", 0, "text"]
    
    Returns:
        str: Texte extrait de la réponse ou None si extraction échoue
    """
    
    try:
        # Conversion string JSON -> dict si nécessaire
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
            
        print(f"[ResponseParser] Navigation avec path: {response_path}")
        
        # Navigation dans la structure JSON
        current = data
        for i, key in enumerate(response_path):
            print(f"[ResponseParser] Étape {i+1}: accès à '{key}' dans {type(current).__name__}")
            
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list) and isinstance(key, int) and 0 <= key < len(current):
                current = current[key]
            else:
                print(f"[ResponseParser] ❌ Échec navigation à l'étape {i+1}: clé '{key}' non trouvée")
                print(f"[ResponseParser] Structure disponible: {list(current.keys()) if isinstance(current, dict) else f'Liste de {len(current)} éléments' if isinstance(current, list) else type(current).__name__}")
                return None
                
        # Vérification que le résultat final est du texte
        if isinstance(current, str):
            print(f"[ResponseParser] ✅ Texte extrait avec succès ({len(current)} chars)")
            return current
        else:
            print(f"[ResponseParser] ❌ Résultat final n'est pas du texte: {type(current).__name__}")
            return None
            
    except json.JSONDecodeError as e:
        print(f"[ResponseParser] ❌ Erreur parsing JSON: {e}")
        return None
    except Exception as e:
        print(f"[ResponseParser] ❌ Erreur extraction: {e}")
        return None

def validate_response_structure(json_data: Union[str, dict], response_path: List[Union[str, int]]) -> dict:
    """
    Valide la structure d'une réponse et retourne des informations de diagnostic
    
    Args:
        json_data: Données JSON de la réponse API
        response_path: Chemin de navigation attendu
    
    Returns:
        dict: Informations de validation (success, error, structure_info)
    """
    
    result = {
        "success": False,
        "error": None,
        "structure_info": {},
        "extracted_text": None
    }
    
    try:
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
            
        # Analyse de la structure racine
        if isinstance(data, dict):
            result["structure_info"]["root_keys"] = list(data.keys())
        elif isinstance(data, list):
            result["structure_info"]["root_type"] = f"Liste de {len(data)} éléments"
        
        # Tentative d'extraction
        extracted = parse_response(data, response_path)
        if extracted:
            result["success"] = True
            result["extracted_text"] = extracted[:100] + "..." if len(extracted) > 100 else extracted
        else:
            result["error"] = "Extraction échouée avec le response_path fourni"
            
    except Exception as e:
        result["error"] = str(e)
    
    return result

def debug_json_structure(json_data: Union[str, dict], max_depth: int = 3) -> dict:
    """
    Analyse et affiche la structure d'un JSON pour aider au debugging
    
    Args:
        json_data: Données JSON à analyser
        max_depth: Profondeur maximale d'analyse
        
    Returns:
        dict: Structure analysée
    """
    
    def analyze_structure(obj, depth=0):
        if depth > max_depth:
            return f"[Profondeur {max_depth} atteinte]"
            
        if isinstance(obj, dict):
            return {key: analyze_structure(value, depth + 1) for key, value in obj.items()}
        elif isinstance(obj, list):
            if len(obj) == 0:
                return "[]"
            elif len(obj) == 1:
                return [analyze_structure(obj[0], depth + 1)]
            else:
                return [analyze_structure(obj[0], depth + 1), f"... +{len(obj)-1} éléments"]
        else:
            return f"{type(obj).__name__}: {str(obj)[:50]}{'...' if len(str(obj)) > 50 else ''}"
    
    try:
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
            
        return analyze_structure(data)
    except Exception as e:
        return {"error": str(e)}
