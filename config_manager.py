"""
Configuration Manager - Gestionnaire centralisé pour les configurations JSON
Remplace la gestion YAML par du JSON avec validation et séparation des templates
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import jsonschema
from jsonschema import validate, ValidationError

# Schémas JSON pour validation
PROFILE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "api_key": {"type": ["string", "null"]},
        "api_url": {"type": "string"},
        "behavior": {"type": "string"},
        "role": {"type": "string"},
        "default": {"type": "boolean"},
        "history": {"type": "boolean"},
        "replace_apikey": {"type": "string"},
        "template_id": {"type": "string"},  # Référence vers template séparé
        "file_generation": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "mode": {"type": "string", "enum": ["simple", "development"]},
                "simple_config": {
                    "type": "object",
                    "properties": {
                        "include_question": {"type": "boolean"},
                        "include_response": {"type": "boolean"},
                        "base_filename": {"type": "string"},
                        "same_file": {"type": "boolean"}
                    }
                },
                "dev_config": {
                    "type": "object",
                    "properties": {
                        "extension": {"type": "string"}
                    }
                }
            }
        },
        "conversation": {
            "type": "object",
            "properties": {
                "summary_enabled": {"type": "boolean"},
                "summary_threshold": {
                    "type": "object",
                    "properties": {
                        "words": {"type": "integer"},
                        "sentences": {"type": "integer"}
                    }
                },
                "summary_template_id": {"type": "string"},
                "show_indicators": {"type": "boolean"}
            }
        }
    },
    "required": ["name", "api_key", "api_url", "default"]
}

SYSTEM_PROFILE_SCHEMA = {
    "type": "object",
    "properties": {
        "generated_at": {"type": "string"},
        "os_info": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "string"},
                "architecture": {"type": "string"}
            }
        },
        "python_info": {
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "executable": {"type": "string"}
            }
        },
        "hardware_info": {
            "type": "object",
            "properties": {
                "cpu_cores": {"type": "integer"},
                "total_memory_gb": {"type": "number"},
                "disk_free_gb": {"type": "number"}
            }
        },
        "app_info": {
            "type": "object",
            "properties": {
                "directory": {"type": "string"},
                "script_path": {"type": "string"},
                "key_files": {"type": "array", "items": {"type": "string"}}
            }
        }
    },
    "required": ["generated_at", "os_info", "python_info", "hardware_info", "app_info"]
}

class ConfigManager:
    """Gestionnaire centralisé des configurations JSON"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.profiles_dir = os.path.join(base_dir, "profiles")
        self.templates_dir = os.path.join(base_dir, "templates")
        self.system_dir = os.path.join(base_dir, "system")
        
        # Assurer que les répertoires existent
        os.makedirs(self.profiles_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.system_dir, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
    
    def validate_profile(self, profile_data: Dict[str, Any]) -> bool:
        """Valide un profil selon le schéma JSON"""
        try:
            validate(instance=profile_data, schema=PROFILE_SCHEMA)
            return True
        except ValidationError as e:
            self.logger.error(f"Erreur validation profil : {e.message}")
            return False
    
    def save_profile(self, profile_name: str, profile_data: Dict[str, Any]) -> bool:
        """Sauvegarde un profil en JSON avec validation"""
        try:
            if not self.validate_profile(profile_data):
                return False
            
            file_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Profil {profile_name} sauvegardé avec succès")
            return True
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde profil {profile_name} : {e}")
            return False
    
    def load_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Charge un profil JSON"""
        try:
            file_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            if self.validate_profile(profile_data):
                return profile_data
            else:
                self.logger.warning(f"Profil {profile_name} invalide")
                return None
        except Exception as e:
            self.logger.error(f"Erreur chargement profil {profile_name} : {e}")
            return None
    
    def get_default_profile(self) -> Optional[Dict[str, Any]]:
        """Récupère le profil marqué comme défaut"""
        try:
            for filename in os.listdir(self.profiles_dir):
                if filename.endswith('.json'):
                    profile_name = filename[:-5]  # Retirer .json
                    profile = self.load_profile(profile_name)
                    if profile and profile.get('default', False):
                        return profile
            
            # Fallback sur Gemini si aucun défaut trouvé
            return self.load_profile('Gemini')
        except Exception as e:
            self.logger.error(f"Erreur récupération profil défaut : {e}")
            return None
    
    def list_profiles(self) -> List[str]:
        """Liste tous les profils disponibles"""
        try:
            profiles = []
            for filename in os.listdir(self.profiles_dir):
                if filename.endswith('.json'):
                    profiles.append(filename[:-5])  # Retirer .json
            return profiles
        except Exception as e:
            self.logger.error(f"Erreur listage profils : {e}")
            return []
    
    def set_default_profile(self, profile_name: str) -> bool:
        """Définit un profil comme défaut (et retire le statut des autres)"""
        try:
            # Retirer le statut default de tous les profils
            for existing_profile in self.list_profiles():
                profile_data = self.load_profile(existing_profile)
                if profile_data:
                    profile_data['default'] = (existing_profile == profile_name)
                    self.save_profile(existing_profile, profile_data)
            
            return True
        except Exception as e:
            self.logger.error(f"Erreur définition profil défaut : {e}")
            return False
    
    def save_template(self, template_id: str, template_content: str) -> bool:
        """Sauvegarde un template de commande API"""
        try:
            file_path = os.path.join(self.templates_dir, "api_commands", f"{template_id}.txt")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            self.logger.info(f"Template {template_id} sauvegardé")
            return True
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde template {template_id} : {e}")
            return False
    
    def load_template(self, template_id: str) -> Optional[str]:
        """Charge un template de commande API"""
        try:
            file_path = os.path.join(self.templates_dir, "api_commands", f"{template_id}.txt")
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Erreur chargement template {template_id} : {e}")
            return None
    
    def save_conversation_template(self, template_id: str, template_content: str) -> bool:
        """Sauvegarde un template de conversation (résumé, etc.)"""
        try:
            file_path = os.path.join(self.templates_dir, "conversation", f"{template_id}.txt")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            self.logger.info(f"Template conversation {template_id} sauvegardé")
            return True
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde template conversation {template_id} : {e}")
            return False
    
    def load_conversation_template(self, template_id: str) -> Optional[str]:
        """Charge un template de conversation"""
        try:
            file_path = os.path.join(self.templates_dir, "conversation", f"{template_id}.txt")
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Erreur chargement template conversation {template_id} : {e}")
            return None
    
    def create_default_profiles(self) -> bool:
        """Crée les profils par défaut si ils n'existent pas"""
        default_profiles = {
            "Gemini": {
                "name": "Gemini",
                "api_key": "",
                "api_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                "behavior": "excité, ronchon, répond en une phrase ou deux",
                "role": "alien rigolo",
                "default": True,
                "history": True,
                "replace_apikey": "GEMINI_API_KEY",
                "template_id": "gemini_chat",
                "file_generation": {
                    "enabled": False,
                    "mode": "simple",
                    "simple_config": {
                        "include_question": True,
                        "include_response": True,
                        "base_filename": "conversation",
                        "same_file": True
                    },
                    "dev_config": {
                        "extension": ".py"
                    }
                },
                "conversation": {
                    "summary_enabled": True,
                    "summary_threshold": {
                        "words": 300,
                        "sentences": 6
                    },
                    "summary_template_id": "default_summary",
                    "show_indicators": True
                }
            },
            "OpenAI": {
                "name": "OpenAI",
                "api_key": "",
                "api_url": "https://api.openai.com/v1/completions",
                "behavior": "comportement initial",
                "role": "",
                "default": False,
                "history": False,
                "replace_apikey": "",
                "template_id": "openai_chat",
                "file_generation": {
                    "enabled": False,
                    "mode": "simple",
                    "simple_config": {
                        "include_question": True,
                        "include_response": True,
                        "base_filename": "conversation",
                        "same_file": True
                    },
                    "dev_config": {
                        "extension": ".py"
                    }
                }
            },
            "Claude": {
                "name": "Claude",
                "api_key": "",
                "api_url": "https://api.anthropic.com/v1/claude",
                "behavior": "comportement initial",
                "role": "",
                "default": False,
                "history": False,
                "replace_apikey": "",
                "template_id": "claude_chat",
                "file_generation": {
                    "enabled": False,
                    "mode": "simple",
                    "simple_config": {
                        "include_question": True,
                        "include_response": True,
                        "base_filename": "conversation",
                        "same_file": True
                    },
                    "dev_config": {
                        "extension": ".py"
                    }
                }
            }
        }
        
        # Templates correspondants
        templates = {
            "gemini_chat": '''curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=GEMINI_API_KEY" \\
  -H 'Content-Type: application/json' \\
  -X POST \\
  -d '{"contents": [{"parts": [{"text": "Explain how AI works"}]}]}'  ''',
            "openai_chat": "# Template OpenAI à développer",
            "claude_chat": "# Template Claude à développer"
        }
        
        # Templates de conversation pour les résumés
        conversation_templates = {
            "default_summary": """Veuillez analyser la conversation suivante et créer un résumé concis qui préserve les informations essentielles pour maintenir la continuité de la discussion.

INSTRUCTIONS DE RÉSUMÉ :
- Conservez les points clés et décisions importantes
- Maintenez le contexte nécessaire pour les prochaines questions
- Soyez concis mais informatif (maximum 150 mots)
- Organisez par thèmes si plusieurs sujets sont abordés

CONVERSATION À RÉSUMER :
{HISTORIQUE_COMPLET}

RÉSUMÉ CONTEXTUEL :"""
        }
        
        try:
            # Créer les profils
            for profile_name, profile_data in default_profiles.items():
                if not os.path.exists(os.path.join(self.profiles_dir, f"{profile_name}.json")):
                    self.save_profile(profile_name, profile_data)
            
            # Créer les templates
            for template_id, template_content in templates.items():
                self.save_template(template_id, template_content)
            
            # Créer les templates de conversation
            for template_id, template_content in conversation_templates.items():
                self.save_conversation_template(template_id, template_content)
            
            self.logger.info("Profils et templates par défaut créés")
            return True
        except Exception as e:
            self.logger.error(f"Erreur création profils défaut : {e}")
            return False
    
    def update_profile_with_conversation_config(self, profile_name: str) -> bool:
        """
        Met à jour un profil existant avec la configuration de conversation
        Utile pour migrer les profils existants
        """
        try:
            profile = self.load_profile(profile_name)
            if not profile:
                self.logger.error(f"Profil {profile_name} non trouvé")
                return False
            
            # Ajouter la configuration de conversation si elle n'existe pas
            if 'conversation' not in profile:
                profile['conversation'] = {
                    "summary_enabled": True,
                    "summary_threshold": {
                        "words": 300,
                        "sentences": 6
                    },
                    "summary_template_id": "default_summary",
                    "show_indicators": True
                }
                
                # Sauvegarder le profil mis à jour
                success = self.save_profile(profile_name, profile)
                if success:
                    self.logger.info(f"Profil {profile_name} mis à jour avec configuration conversation")
                return success
            else:
                self.logger.info(f"Profil {profile_name} a déjà une configuration conversation")
                return True
                
        except Exception as e:
            self.logger.error(f"Erreur mise à jour profil {profile_name}: {e}")
            return False
