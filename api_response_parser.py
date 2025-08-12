#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Architecture Évolutive - Système de parseurs de réponse multi-API
"""

import json
import logging
from typing import Dict, Any, Tuple, Optional, Callable

class APIResponseParser:
    """
    Gestionnaire centralisé pour parser les réponses de différentes APIs
    Architecture évolutive permettant d'ajouter facilement de nouvelles APIs
    """
    
    def __init__(self):
        # Registre des parseurs par type d'API
        self._parsers: Dict[str, Callable] = {
            'gemini': self._parse_gemini_response,
            'openai': self._parse_openai_response,
            'claude': self._parse_claude_response,
            'qwen': self._parse_qwen_response,
            'auto': self._auto_detect_and_parse
        }
    
    def parse_response(self, response_json: Dict[str, Any], api_type: str = 'auto') -> Tuple[bool, str, str]:
        """
        Parse une réponse API selon le type spécifié
        
        Args:
            response_json: La réponse JSON de l'API
            api_type: Type d'API ('gemini', 'openai', 'claude', 'auto')
            
        Returns:
            Tuple (success, text_content, api_detected)
        """
        try:
            if api_type in self._parsers:
                return self._parsers[api_type](response_json)
            else:
                return False, f"Type d'API non supporté: {api_type}", "unknown"
                
        except Exception as e:
            logging.error(f"Erreur lors du parsing de la réponse: {e}")
            return False, f"Erreur de parsing: {e}", "error"
    
    def _auto_detect_and_parse(self, response_json: Dict[str, Any]) -> Tuple[bool, str, str]:
        """
        Détection automatique du type d'API et parsing approprié
        """
        # D'abord vérifier les erreurs pour identifier l'API même en cas d'échec
        if "error" in response_json:
            error_obj = response_json["error"]
            
            # Identifier l'API par les caractéristiques de l'erreur
            if isinstance(error_obj, dict):
                # OpenAI: structure {"error": {"message": "...", "type": "...", "code": "..."}}
                if "type" in error_obj or "code" in error_obj:
                    success, text, _ = self._parsers['openai'](response_json)
                    return success, text, "openai"
                
                # Gemini: structure différente
                elif "status" in error_obj or "code" in str(error_obj):
                    success, text, _ = self._parsers['gemini'](response_json)
                    return success, text, "gemini"
                
                # Claude: structure {"error": {"message": "...", "type": "..."}}
                else:
                    success, text, _ = self._parsers['claude'](response_json)
                    return success, text, "claude"
        
        # Détection par présence de clés spécifiques pour les réponses de succès
        detection_rules = [
            ('candidates', 'gemini'),
            ('choices', 'openai'),
            ('content', 'claude'),
            ('output', 'qwen')
        ]
        
        for key, api_type in detection_rules:
            if key in response_json:
                success, text, _ = self._parsers[api_type](response_json)
                return success, text, api_type
        
        # Si aucune structure connue détectée
        return False, f"Structure de réponse non reconnue: {list(response_json.keys())}", "unknown"
    
    def _parse_gemini_response(self, response_json: Dict[str, Any]) -> Tuple[bool, str, str]:
        """Parse une réponse Gemini"""
        try:
            if "error" in response_json:
                error_msg = response_json["error"].get("message", "Erreur inconnue")
                return False, f"Erreur API Gemini: {error_msg}", "gemini"
            
            text = response_json["candidates"][0]["content"]["parts"][0]["text"]
            return True, text, "gemini"
            
        except (KeyError, IndexError, TypeError) as e:
            return False, f"Structure Gemini invalide: {e}", "gemini"
    
    def _parse_openai_response(self, response_json: Dict[str, Any]) -> Tuple[bool, str, str]:
        """Parse une réponse OpenAI (Chat Completion ou Completion)"""
        try:
            if "error" in response_json:
                error_obj = response_json["error"]
                if isinstance(error_obj, dict):
                    error_msg = error_obj.get("message", "Erreur inconnue")
                    error_type = error_obj.get("type", "")
                    error_code = error_obj.get("code", "")
                    full_error = f"Erreur API OpenAI: {error_msg}"
                    if error_type:
                        full_error += f" (Type: {error_type})"
                    if error_code:
                        full_error += f" (Code: {error_code})"
                    return False, full_error, "openai"
                else:
                    return False, f"Erreur API OpenAI: {error_obj}", "openai"
            
            choice = response_json["choices"][0]
            
            # Chat Completion format (gpt-4, gpt-3.5-turbo)
            if "message" in choice:
                text = choice["message"]["content"]
                return True, text, "openai"
            
            # Legacy Completion format (text-davinci-003)
            elif "text" in choice:
                text = choice["text"]
                return True, text, "openai"
            
            else:
                return False, "Format OpenAI non reconnu", "openai"
                
        except (KeyError, IndexError, TypeError) as e:
            return False, f"Structure OpenAI invalide: {e}", "openai"
    
    def _parse_claude_response(self, response_json: Dict[str, Any]) -> Tuple[bool, str, str]:
        """Parse une réponse Claude/Anthropic"""
        try:
            if "error" in response_json:
                error_msg = response_json["error"].get("message", "Erreur inconnue")
                return False, f"Erreur API Claude: {error_msg}", "claude"
            
            # Format standard Claude
            if isinstance(response_json.get("content"), list):
                text = response_json["content"][0]["text"]
                return True, text, "claude"
            
            # Format alternatif
            elif "text" in response_json:
                text = response_json["text"]
                return True, text, "claude"
            
            else:
                return False, "Format Claude non reconnu", "claude"
                
        except (KeyError, IndexError, TypeError) as e:
            return False, f"Structure Claude invalide: {e}", "claude"
    
    def _parse_qwen_response(self, response_json: Dict[str, Any]) -> Tuple[bool, str, str]:
        """Parse une réponse Qwen/Alibaba"""
        try:
            if "error" in response_json:
                error_msg = response_json["error"].get("message", "Erreur inconnue")
                return False, f"Erreur API Qwen: {error_msg}", "qwen"
            
            # Format standard Qwen
            if "output" in response_json and "text" in response_json["output"]:
                text = response_json["output"]["text"]
                return True, text, "qwen"
            
            else:
                return False, "Format Qwen non reconnu", "qwen"
                
        except (KeyError, IndexError, TypeError) as e:
            return False, f"Structure Qwen invalide: {e}", "qwen"
    
    def register_custom_parser(self, api_name: str, parser_function: Callable):
        """
        Enregistre un parseur personnalisé pour une nouvelle API
        
        Args:
            api_name: Nom de l'API
            parser_function: Fonction de parsing (response_json) -> (success, text, api_type)
        """
        self._parsers[api_name] = parser_function
        logging.info(f"Parseur personnalisé enregistré pour {api_name}")
    
    def get_supported_apis(self) -> list:
        """Retourne la liste des APIs supportées"""
        return [api for api in self._parsers.keys() if api != 'auto']


# Instance globale du parseur
response_parser = APIResponseParser()


def get_response_parser() -> APIResponseParser:
    """Retourne l'instance globale du parseur de réponses"""
    return response_parser


# Fonctions utilitaires pour compatibilité avec le code existant
def extract_text_from_api_response(response_json: Dict[str, Any], api_type: str = 'auto') -> Tuple[bool, str]:
    """
    Fonction utilitaire pour extraire le texte d'une réponse API
    Compatible avec l'interface existante
    """
    success, text, detected_api = response_parser.parse_response(response_json, api_type)
    return success, text


def get_api_type_from_response(response_json: Dict[str, Any]) -> str:
    """
    Détecte automatiquement le type d'API depuis la réponse
    """
    _, _, api_type = response_parser.parse_response(response_json, 'auto')
    return api_type


if __name__ == "__main__":
    # Tests unitaires
    print("🧪 TEST DU SYSTÈME DE PARSEURS")
    print("=" * 50)
    
    # Test Gemini
    gemini_response = {
        "candidates": [{"content": {"parts": [{"text": "Réponse Gemini test"}]}}]
    }
    success, text, api = response_parser.parse_response(gemini_response)
    print(f"✅ Gemini: {success} | '{text}' | API: {api}")
    
    # Test OpenAI Chat
    openai_chat_response = {
        "choices": [{"message": {"content": "Réponse OpenAI Chat test"}}]
    }
    success, text, api = response_parser.parse_response(openai_chat_response)
    print(f"✅ OpenAI Chat: {success} | '{text}' | API: {api}")
    
    # Test OpenAI Completion
    openai_completion_response = {
        "choices": [{"text": "Réponse OpenAI Completion test"}]
    }
    success, text, api = response_parser.parse_response(openai_completion_response)
    print(f"✅ OpenAI Completion: {success} | '{text}' | API: {api}")
    
    # Test Claude
    claude_response = {
        "content": [{"text": "Réponse Claude test"}]
    }
    success, text, api = response_parser.parse_response(claude_response)
    print(f"✅ Claude: {success} | '{text}' | API: {api}")
    
    # Test Auto-détection
    success, text, api = response_parser.parse_response(gemini_response, 'auto')
    print(f"✅ Auto-détection: {success} | API détectée: {api}")
    
    print(f"\n📋 APIs supportées: {response_parser.get_supported_apis()}")
