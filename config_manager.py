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
                "intelligent_management": {"type": "boolean"},
                "summary_thresholds": {
                    "type": "object",
                    "properties": {
                        "words": {
                            "type": "object",
                            "properties": {
                                "enabled": {"type": "boolean"},
                                "value": {"type": "integer"}
                            }
                        },
                        "sentences": {
                            "type": "object",
                            "properties": {
                                "enabled": {"type": "boolean"},
                                "value": {"type": "integer"}
                            }
                        },
                        "tokens": {
                            "type": "object",
                            "properties": {
                                "enabled": {"type": "boolean"},
                                "value": {"type": "integer"}
                            }
                        }
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
        """Sauvegarde un template de commande API - Version V2 compatible avec nouvelle architecture"""
        try:
            # 1. Sauvegarder dans la nouvelle structure V2 (templates/chat/{provider}/curl.txt)
            if '_chat' in template_id:
                provider = template_id.replace('_chat', '')
                v2_path = os.path.join(self.templates_dir, "chat", provider, "curl.txt")
                os.makedirs(os.path.dirname(v2_path), exist_ok=True)
                
                with open(v2_path, 'w', encoding='utf-8') as f:
                    f.write(template_content)
                
                self.logger.info(f"Template V2 sauvegardé: {v2_path}")
            
            # PHASE 3.1.2: SUPPRESSION de la compatibilité api_commands (obsolète)
            # Plus de sauvegarde legacy - Architecture V2 uniquement
            self.logger.info(f"Template sauvegardé uniquement en V2 (api_commands supprimé)")
            return True
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde template {template_id} : {e}")
            return False
    
    def load_template(self, template_id: str) -> Optional[str]:
        """Charge un template de commande API - Version V2 compatible avec nouvelle architecture"""
        try:
            # 1. Essayer d'abord la nouvelle structure V2 (templates/chat/{provider}/curl.txt)
            if '_chat' in template_id:
                provider = template_id.replace('_chat', '')
                v2_path = os.path.join(self.templates_dir, "chat", provider, "curl.txt")
                if os.path.exists(v2_path):
                    with open(v2_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.logger.info(f"Template V2 chargé: {v2_path}")
                    return content
            
            # PHASE 3.1.2: SUPPRESSION du fallback api_commands (obsolète)
            # Plus de fallback legacy - Architecture V2 uniquement
            self.logger.warning(f"Template {template_id} non trouvé dans V2 (api_commands supprimé)")
            return None
        except Exception as e:
            self.logger.error(f"Erreur chargement template {template_id} : {e}")
            return None
    
    def save_typed_template(self, provider: str, template_type: str, method: str, template_content: str) -> bool:
        """Sauvegarde un template dans la nouvelle structure typée (V2)"""
        try:
            file_path = os.path.join(self.templates_dir, template_type, provider, f"{method}_basic.txt")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            self.logger.info(f"Template typé {provider}/{template_type}/{method} sauvegardé")
            return True
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde template typé {provider}/{template_type}/{method} : {e}")
            return False
    
    def load_typed_template(self, provider: str, template_type: str, method: str) -> Optional[str]:
        """Charge un template dans la nouvelle structure typée (V2)"""
        try:
            # Essayer d'abord la nouvelle structure
            file_path = os.path.join(self.templates_dir, template_type, provider, f"{method}_basic.txt")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            # PHASE 3.1.2: SUPPRESSION du fallback api_commands (obsolète)
            # Plus de fallback legacy - Architecture V2 uniquement
            
            return None
        except Exception as e:
            self.logger.error(f"Erreur chargement template typé {provider}/{template_type}/{method} : {e}")
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
    
    def validate_template_placeholders(self, template_content: str, provider: str = "") -> Dict[str, List[str]]:
        """
        Valide et analyse les placeholders dans un template selon l'architecture V2
        
        Args:
            template_content (str): Contenu du template
            provider (str): Nom du provider (gemini, claude, etc.)
            
        Returns:
            Dict contenant les placeholders trouvés par type
        """
        import re
        
        if not template_content:
            return {"user_placeholders": [], "system_placeholders": [], "errors": []}
        
        result = {
            "user_placeholders": [],
            "system_placeholders": [],
            "errors": []
        }
        
        try:
            # 1. Détecter les placeholders utilisateur (ex: GEMINI_API_KEY)
            user_placeholder_patterns = [
                r'\b([A-Z_]+_API_KEY)\b',  # GEMINI_API_KEY, CLAUDE_API_KEY, etc.
                r'\b(API_KEY)\b',          # API_KEY générique
                r'\b([A-Z_]+_TOKEN)\b'     # TOKENS divers
            ]
            
            for pattern in user_placeholder_patterns:
                matches = re.findall(pattern, template_content)
                for match in matches:
                    if match not in result["user_placeholders"]:
                        result["user_placeholders"].append(match)
            
            # 2. Détecter les placeholders système (ex: {{model_id}})
            system_placeholders = re.findall(r'\{\{([^}]+)\}\}', template_content)
            result["system_placeholders"] = list(set(system_placeholders))
            
            # 3. Validation spécifique par provider
            expected_user_placeholders = {
                "gemini": ["GEMINI_API_KEY"],
                "claude": ["CLAUDE_API_KEY"],
                "openai": ["OPENAI_API_KEY"],
                "kimi": ["KIMI_API_KEY"]
            }
            
            expected_system_placeholders = ["model_id", "prompt_content"]
            
            if provider.lower() in expected_user_placeholders:
                expected_user = expected_user_placeholders[provider.lower()]
                found_expected = [p for p in result["user_placeholders"] if p in expected_user]
                if not found_expected:
                    result["errors"].append(f"Placeholder utilisateur attendu manquant: {expected_user}")
            
            # Vérifier les placeholders système essentiels
            missing_system = [p for p in expected_system_placeholders if p not in result["system_placeholders"]]
            if missing_system:
                result["errors"].append(f"Placeholders système manquants: {missing_system}")
            
            self.logger.info(f"Validation template - User: {result['user_placeholders']}, System: {result['system_placeholders']}")
            
        except Exception as e:
            result["errors"].append(f"Erreur validation placeholders: {e}")
            self.logger.error(f"Erreur validation placeholders: {e}")
        
        return result
    
    def create_default_profiles(self) -> bool:
        """
        Crée les profils par défaut à partir des templates sécurisés si ils n'existent pas
        SÉCURITÉ: Les templates ne contiennent jamais de clés API
        AUTO-DÉTECTION: Parcourt tous les fichiers *.json.template
        """
        success = True
        
        # AUTO-DÉTECTION: Parcourir tous les templates disponibles
        templates = []
        try:
            for filename in os.listdir(self.profiles_dir):
                if filename.endswith('.json.template'):
                    template_name = filename.replace('.json.template', '')
                    templates.append(template_name)
            
            if not templates:
                self.logger.warning("⚠️ Aucun template trouvé dans profiles/")
                return False
                
            self.logger.info(f"📋 Templates détectés: {templates}")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la détection des templates: {e}")
            return False
        
        for template_name in templates:
            profile_path = os.path.join(self.profiles_dir, f"{template_name}.json")
            template_path = os.path.join(self.profiles_dir, f"{template_name}.json.template")
            
            # Si le profil n'existe pas, le créer à partir du template
            if not os.path.exists(profile_path):
                try:
                    if os.path.exists(template_path):
                        # Charger le template
                        with open(template_path, 'r', encoding='utf-8') as f:
                            template_data = json.load(f)
                        
                        # Ajouter la section conversation_management si elle n'existe pas
                        if "conversation_management" not in template_data:
                            template_data["conversation_management"] = {
                                "words_enabled": True,
                                "sentences_enabled": True,
                                "tokens_enabled": False,
                                "word_threshold": 300,
                                "sentence_threshold": 15,
                                "token_threshold": 1000,
                                "summary_template": f"Template {template_name}",
                                "custom_instructions": "Résume la conversation précédente en conservant les points clés et le contexte important.",
                                "auto_save": True
                            }
                            self.logger.info(f"✅ Section conversation_management ajoutée au profil {template_name}")
                        
                        # Sauvegarder comme profil (les clés API restent vides)
                        success = self.save_profile(template_name, template_data) and success
                        self.logger.info(f"✅ Profil {template_name} créé à partir du template sécurisé")
                    else:
                        self.logger.warning(f"⚠️ Template {template_path} introuvable")
                        success = False
                        
                except Exception as e:
                    self.logger.error(f"❌ Erreur création profil {template_name} : {e}")
                    success = False
            else:
                # Le profil existe déjà, vérifier s'il a conversation_management
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                    
                    if "conversation_management" not in existing_data:
                        # Ajouter la section conversation_management
                        existing_data["conversation_management"] = {
                            "words_enabled": True,
                            "sentences_enabled": True,
                            "tokens_enabled": False,
                            "word_threshold": 300,
                            "sentence_threshold": 15,
                            "token_threshold": 1000,
                            "summary_template": f"Template {template_name}",
                            "custom_instructions": "Résume la conversation précédente en conservant les points clés et le contexte important.",
                            "auto_save": True
                        }
                        
                        # Sauvegarder le profil mis à jour
                        success = self.save_profile(template_name, existing_data) and success
                        self.logger.info(f"✅ Section conversation_management ajoutée au profil existant {template_name}")
                    else:
                        self.logger.debug(f"Profil {template_name} a déjà conversation_management")
                        
                except Exception as e:
                    self.logger.error(f"❌ Erreur mise à jour profil {template_name} : {e}")
                    success = False
        
        return success

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
                # Nouvelle structure de configuration
                profile['conversation'] = {
                    "intelligent_management": True,
                    "summary_thresholds": {
                        "words": {"enabled": True, "value": 300},
                        "sentences": {"enabled": True, "value": 6},
                        "tokens": {"enabled": False, "value": 1200}
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

    def update_conversation_config(self, profile_name: str, conversation_config: Dict[str, Any]) -> bool:
        """
        Met à jour la configuration de conversation d'un profil
        """
        try:
            profile = self.load_profile(profile_name)
            if not profile:
                self.logger.error(f"Profil {profile_name} non trouvé")
                return False
            
            # Valider la configuration conversation
            if not self._validate_conversation_config(conversation_config):
                self.logger.error("Configuration conversation invalide")
                return False
            
            # Mettre à jour la configuration
            profile['conversation'] = conversation_config
            
            # Sauvegarder
            success = self.save_profile(profile_name, profile)
            if success:
                self.logger.info(f"Configuration conversation mise à jour pour {profile_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour conversation config: {e}")
            return False

    def get_conversation_config(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère la configuration de conversation d'un profil
        """
        try:
            profile = self.load_profile(profile_name)
            if not profile:
                return None
            
            return profile.get('conversation')
            
        except Exception as e:
            self.logger.error(f"Erreur récupération conversation config: {e}")
            return None

    def list_summary_templates(self) -> List[str]:
        """
        Liste tous les templates de résumé disponibles
        """
        try:
            templates_dir = os.path.join(self.base_path, "templates", "conversation")
            if not os.path.exists(templates_dir):
                return ["default_summary"]
            
            templates = []
            for file in os.listdir(templates_dir):
                if file.endswith('.txt'):
                    template_id = file[:-4]  # Retirer l'extension .txt
                    templates.append(template_id)
            
            return templates if templates else ["default_summary"]
            
        except Exception as e:
            self.logger.error(f"Erreur listage templates: {e}")
            return ["default_summary"]

    def load_summary_template(self, template_id: str) -> Optional[str]:
        """
        Charge le contenu d'un template de résumé
        """
        try:
            template_path = os.path.join(self.base_path, "templates", "conversation", f"{template_id}.txt")
            if not os.path.exists(template_path):
                self.logger.warning(f"Template {template_id} non trouvé")
                return None
            
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        except Exception as e:
            self.logger.error(f"Erreur chargement template {template_id}: {e}")
            return None

    def save_summary_template(self, template_id: str, content: str) -> bool:
        """
        Sauvegarde un template de résumé
        """
        try:
            templates_dir = os.path.join(self.base_path, "templates", "conversation")
            os.makedirs(templates_dir, exist_ok=True)
            
            template_path = os.path.join(templates_dir, f"{template_id}.txt")
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Template {template_id} sauvegardé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde template {template_id}: {e}")
            return False

    def _validate_conversation_config(self, config: Dict[str, Any]) -> bool:
        """
        Valide une configuration de conversation
        """
        try:
            required_keys = ['intelligent_management', 'summary_thresholds', 'summary_template_id', 'show_indicators']
            
            # Vérifier les clés obligatoires
            for key in required_keys:
                if key not in config:
                    return False
            
            # Vérifier la structure des seuils
            thresholds = config.get('summary_thresholds', {})
            for threshold_type in ['words', 'sentences', 'tokens']:
                if threshold_type in thresholds:
                    threshold_config = thresholds[threshold_type]
                    if not isinstance(threshold_config, dict):
                        return False
                    if 'enabled' not in threshold_config or 'value' not in threshold_config:
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur validation conversation config: {e}")
            return False
