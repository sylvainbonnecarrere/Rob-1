#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Manager - Rob-1 Phase 1 Refactorisation
Module centralisant la gestion des profils API
Extrait de gui.py pour respecter le principe de responsabilité unique (SRP)

ARCHITECTURE:
- Interface IProfileManager pour extensibilité
- Classe APIManager utilisant la composition avec ConfigManager  
- Façade simplifiée pour les opérations sur les profils
- Support pour profils par défaut et personnalisés

CONFORMITÉ DESIGN PATTERNS:
- Facade Pattern: Interface simplifiée pour ConfigManager
- Composition over Inheritance: APIManager compose avec ConfigManager
- Interface Segregation: IProfileManager pour les contrats clairs
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import os
import json
from pathlib import Path

# Import du ConfigManager existant
from config_manager import ConfigManager


class IProfileManager(ABC):
    """
    Interface pour la gestion des profils API
    Principe: Interface Segregation (ISP)
    """
    
    @abstractmethod
    def load_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Charge un profil par son nom"""
        pass
    
    @abstractmethod
    def get_default_profile(self) -> Optional[Dict[str, Any]]:
        """Récupère le profil par défaut"""
        pass
    
    @abstractmethod
    def list_available_profiles(self) -> List[str]:
        """Liste tous les profils disponibles"""
        pass
    
    @abstractmethod
    def validate_profile(self, profile_data: Dict[str, Any]) -> bool:
        """Valide la structure d'un profil"""
        pass
    
    @abstractmethod
    def get_profile_summary(self, profile_name: str) -> Optional[Dict[str, str]]:
        """Récupère un résumé d'un profil (provider, method, model)"""
        pass
    
    @abstractmethod
    def load_template(self, template_id: str) -> Optional[str]:
        """Charge un template par son ID"""
        pass
    
    @abstractmethod
    def list_available_templates(self) -> List[str]:
        """Liste tous les templates disponibles"""
        pass
    
    @abstractmethod
    def validate_template(self, template_content: str, provider: str = "") -> Dict[str, List[str]]:
        """Valide un template et analyse ses placeholders"""
        pass


class APIManager(IProfileManager):
    """
    Gestionnaire centralisé des profils API
    
    RESPONSABILITÉS:
    - Gestion des profils API via ConfigManager
    - Interface simplifiée pour l'accès aux profils
    - Validation et résumés des profils
    - Gestion des profils par défaut
    
    COMPOSITION:
    - Utilise ConfigManager pour les opérations de base
    - Ajoute une couche d'abstraction métier
    """
    
    def __init__(self):
        """Initialise le gestionnaire API avec ConfigManager"""
        self._config_manager = ConfigManager()
        self._profiles_cache = {}
        self._last_used_profile = None
        
    def load_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Charge un profil par son nom
        
        Args:
            profile_name: Nom du profil à charger
            
        Returns:
            Dict contenant les données du profil ou None si introuvable
        """
        try:
            # Utiliser le ConfigManager pour charger le profil
            profile_data = self._config_manager.load_profile(profile_name)
            
            if profile_data:
                # Mettre en cache pour optimisation
                self._profiles_cache[profile_name] = profile_data
                self._last_used_profile = profile_name
                return profile_data
            
            return None
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement du profil {profile_name}: {e}")
            return None
    
    def get_default_profile(self) -> Optional[Dict[str, Any]]:
        """
        Récupère le profil par défaut
        
        Returns:
            Dict du profil par défaut ou None
        """
        try:
            # Chercher le profil marqué comme défaut
            available = self.list_available_profiles()
            
            for profile_name in available:
                profile_data = self.load_profile(profile_name)
                if profile_data and profile_data.get('default', False):
                    return profile_data
            
            # Si aucun profil par défaut, prendre le premier disponible
            if available:
                return self.load_profile(available[0])
                
            return None
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération du profil par défaut: {e}")
            return None
    
    def list_available_profiles(self) -> List[str]:
        """
        Liste tous les profils disponibles
        
        Returns:
            Liste des noms de profils disponibles
        """
        try:
            # Utiliser la méthode du ConfigManager
            return self._config_manager.list_profiles()
            
        except Exception as e:
            print(f"❌ Erreur lors de la liste des profils: {e}")
            return []
    
    def validate_profile(self, profile_data: Dict[str, Any]) -> bool:
        """
        Valide la structure d'un profil
        
        Args:
            profile_data: Données du profil à valider
            
        Returns:
            True si le profil est valide, False sinon
        """
        try:
            # Utiliser la validation du ConfigManager
            return self._config_manager.validate_profile_data(profile_data)
            
        except Exception as e:
            print(f"❌ Erreur lors de la validation du profil: {e}")
            return False
    
    def get_profile_summary(self, profile_name: str) -> Optional[Dict[str, str]]:
        """
        Récupère un résumé d'un profil (informations clés)
        
        Args:
            profile_name: Nom du profil
            
        Returns:
            Dict avec provider, method, model ou None
        """
        try:
            profile_data = self.load_profile(profile_name)
            if not profile_data:
                return None
            
            # Extraire les informations clés
            summary = {
                'name': profile_name,
                'provider': profile_data.get('model', 'Unknown'),
                'method': profile_data.get('method', 'Unknown'),
                'llm_model': profile_data.get('llm_model', 'Unknown'),
                'has_api_key': bool(profile_data.get('api_key', '')),
                'default': profile_data.get('default', False)
            }
            
            return summary
            
        except Exception as e:
            print(f"❌ Erreur lors de la création du résumé pour {profile_name}: {e}")
            return None
    
    def get_all_profiles_summary(self) -> List[Dict[str, str]]:
        """
        Récupère un résumé de tous les profils disponibles
        
        Returns:
            Liste des résumés de tous les profils
        """
        summaries = []
        
        for profile_name in self.list_available_profiles():
            summary = self.get_profile_summary(profile_name)
            if summary:
                summaries.append(summary)
        
        return summaries
    
    def get_profiles_by_provider(self, provider: str) -> List[str]:
        """
        Récupère tous les profils d'un provider donné
        
        Args:
            provider: Nom du provider (gemini, openai, claude, etc.)
            
        Returns:
            Liste des noms de profils pour ce provider
        """
        matching_profiles = []
        
        for profile_name in self.list_available_profiles():
            summary = self.get_profile_summary(profile_name)
            if summary and summary.get('provider', '').lower() == provider.lower():
                matching_profiles.append(profile_name)
        
        return matching_profiles
    
    def get_profiles_by_method(self, method: str) -> List[str]:
        """
        Récupère tous les profils d'une méthode donnée (curl/native)
        
        Args:
            method: Méthode (curl ou native)
            
        Returns:
            Liste des noms de profils pour cette méthode
        """
        matching_profiles = []
        
        for profile_name in self.list_available_profiles():
            summary = self.get_profile_summary(profile_name)
            if summary and summary.get('method', '').lower() == method.lower():
                matching_profiles.append(profile_name)
        
        return matching_profiles
    
    def get_last_used_profile(self) -> Optional[str]:
        """
        Returns:
            Nom du dernier profil utilisé ou None
        """
        return self._last_used_profile
    
    def clear_cache(self):
        """Vide le cache des profils"""
        self._profiles_cache.clear()
        
    def get_cache_info(self) -> Dict[str, int]:
        """
        Returns:
            Informations sur le cache (nb profils en cache)
        """
        return {
            'cached_profiles': len(self._profiles_cache),
            'available_profiles': len(self.list_available_profiles())
        }
    
    def load_template(self, template_id: str) -> Optional[str]:
        """
        Charge un template API via ConfigManager avec APIManager comme façade
        
        Args:
            template_id: ID du template à charger (ex: 'openai_chat')
            
        Returns:
            Contenu du template ou None si non trouvé
        """
        try:
            return self._config_manager.load_template(template_id)
        except Exception as e:
            print(f"[ERREUR] Erreur chargement template {template_id}: {e}")
            return None
    
    def save_template(self, template_id: str, template_content: str) -> bool:
        """
        Sauvegarde un template API via ConfigManager avec APIManager comme façade
        
        Args:
            template_id: ID du template à sauvegarder
            template_content: Contenu du template
            
        Returns:
            True si sauvegarde réussie, False sinon
        """
        try:
            return self._config_manager.save_template(template_id, template_content)
        except Exception as e:
            print(f"[ERREUR] Erreur sauvegarde template {template_id}: {e}")
            return False
    
    def list_available_templates(self) -> List[str]:
        """
        Liste tous les templates disponibles depuis templates/chat (V2)
        PLUS D'API_COMMANDS - Migration vers architecture V2
        
        Returns:
            Liste des IDs de templates disponibles
        """
        try:
            templates = []
            base_dir = Path.cwd()
            chat_dir = base_dir / "templates" / "chat"
            
            if chat_dir.exists() and chat_dir.is_dir():
                # Scanner les providers dans templates/chat
                for provider_dir in chat_dir.iterdir():
                    if provider_dir.is_dir():
                        curl_file = provider_dir / "curl.txt"
                        if curl_file.exists():
                            template_id = f"{provider_dir.name}_chat"
                            templates.append(template_id)
                            print(f"[DEBUG] Template V2 trouvé: {template_id} -> {curl_file}")
            else:
                print(f"[WARNING] Dossier templates/chat non trouvé: {chat_dir}")
            
            return sorted(templates)
        except Exception as e:
            print(f"[ERREUR] Erreur listage templates V2: {e}")
            return []
    
    def validate_template(self, template_content: str, provider: str = "") -> Dict[str, List[str]]:
        """
        Valide un template et analyse ses placeholders
        
        Args:
            template_content: Contenu du template à valider
            provider: Provider associé au template (optionnel)
            
        Returns:
            Dictionnaire avec les placeholders trouvés et erreurs
        """
        try:
            return self._config_manager.validate_template_placeholders(template_content, provider)
        except Exception as e:
            print(f"[ERREUR] Erreur validation template: {e}")
            return {"user_placeholders": [], "system_placeholders": [], "errors": [str(e)]}
    
    def ensure_templates_structure(self) -> bool:
        """
        S'assure que la structure V2 des templates est correcte
        PLUS D'API_COMMANDS - Architecture V2 uniquement
        
        Returns:
            True si structure correcte ou corrigée, False sinon
        """
        try:
            base_dir = Path.cwd()
            
            # Structure V2 SANS api_commands
            templates_dirs = [
                base_dir / "templates" / "chat" / "openai",
                base_dir / "templates" / "chat" / "gemini", 
                base_dir / "templates" / "chat" / "claude",
                base_dir / "templates" / "chat" / "kimi",
                base_dir / "templates" / "conversation"
            ]
            
            for dir_path in templates_dirs:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"[DEBUG] Dossier V2 créé/vérifié: {dir_path}")
            
            print("[OK] Structure templates V2 vérifiée (SANS api_commands)")
            return True
        except Exception as e:
            print(f"[ERREUR] Erreur création structure V2: {e}")
            return False
    
    def get_template_content(self, template_id: str) -> Optional[str]:
        """
        Méthode principale pour charger le contenu d'un template
        ARCHITECTURE V3.1.2: Responsabilité centralisée dans APIManager
        
        Args:
            template_id: ID du template à charger (ex: 'openai_chat', 'gemini_chat')
            
        Returns:
            Contenu du template ou None si non trouvé
        """
        try:
            print(f"[APIManager] Chargement template: {template_id}")
            
            # Utiliser la logique existante de load_template
            content = self.load_template(template_id)
            
            if content:
                print(f"[APIManager] Template {template_id} chargé avec succès ({len(content)} caractères)")
                return content
            else:
                print(f"[APIManager] Template {template_id} non trouvé")
                return None
                
        except Exception as e:
            print(f"[ERREUR APIManager] Erreur chargement template {template_id}: {e}")
            return None

    def get_processed_template(self, template_id: str, profile_data: Dict[str, Any], user_prompt: str = "") -> Optional[str]:
        """
        Charge un template et remplace tous les placeholders par les vraies valeurs
        NOUVEAU: Phase 1 - Correction logique placeholders
        
        Args:
            template_id: ID du template (ex: 'gemini_chat')
            profile_data: Données du profil contenant api_key, model, etc.
            user_prompt: Prompt utilisateur à injecter
            
        Returns:
            Template avec placeholders remplacés ou None
        """
        try:
            print(f"[APIManager] Traitement template avec placeholders: {template_id}")
            
            # 1. Charger le template brut (curl_basic.txt)
            if '_chat' in template_id:
                provider = template_id.replace('_chat', '')
                template_path = os.path.join(self._config_manager.templates_dir, "chat", provider, "curl_basic.txt")
                
                if not os.path.exists(template_path):
                    print(f"[APIManager] Template curl_basic.txt non trouvé: {template_path}")
                    return None
                
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
            else:
                print(f"[APIManager] Format de template_id non supporté: {template_id}")
                return None
            
            # 2. Remplacer les placeholders
            processed_content = self._replace_placeholders(template_content, profile_data, user_prompt)
            
            print(f"[APIManager] Template traité avec succès ({len(processed_content)} caractères)")
            return processed_content
            
        except Exception as e:
            print(f"[ERREUR APIManager] Erreur traitement template {template_id}: {e}")
            return None

    def _replace_placeholders(self, template_content: str, profile_data: Dict[str, Any], user_prompt: str = "") -> str:
        """
        Remplace tous les placeholders d'un template par les vraies valeurs
        NOUVEAU: Phase 1 - Logique robuste de remplacement avec échappement JSON
        
        Args:
            template_content: Contenu du template avec placeholders
            profile_data: Données du profil
            user_prompt: Prompt utilisateur
            
        Returns:
            Template avec placeholders remplacés
        """
        try:
            content = template_content
            
            # Fonction d'échappement JSON pour les valeurs contenant des caractères spéciaux
            def escape_json_value(value):
                """Échappe les caractères spéciaux pour JSON"""
                if not isinstance(value, str):
                    return str(value)
                
                # Échapper les caractères JSON essentiels
                escaped = value
                escaped = escaped.replace('\\', '\\\\')  # Échapper les backslashes en premier
                escaped = escaped.replace('"', '\\"')    # Échapper les guillemets doubles
                escaped = escaped.replace('\n', '\\n')   # Échapper les retours à la ligne
                escaped = escaped.replace('\r', '\\r')   # Échapper les retours chariot
                escaped = escaped.replace('\t', '\\t')   # Échapper les tabulations
                escaped = escaped.replace('\b', '\\b')   # Échapper les backspaces
                escaped = escaped.replace('\f', '\\f')   # Échapper les form feeds
                
                return escaped
            
            # Placeholders standards avec échappement pour USER_PROMPT
            replacements = {
                '{{API_KEY}}': profile_data.get('api_key', ''),
                '{{LLM_MODEL}}': profile_data.get('model', profile_data.get('llm_model', '')),
                '{{USER_PROMPT}}': escape_json_value(user_prompt),  # ← ÉCHAPPEMENT JSON
                '{{SYSTEM_PROMPT_ROLE}}': profile_data.get('role', ''),
                '{{SYSTEM_PROMPT_BEHAVIOR}}': profile_data.get('behavior', ''),
            }
            
            # Effectuer les remplacements
            for placeholder, value in replacements.items():
                if placeholder in content:
                    content = content.replace(placeholder, str(value))
                    print(f"[APIManager] Remplacé {placeholder} -> {str(value)[:50]}...")
            
            # Vérifier qu'il ne reste pas de placeholders non remplacés
            import re
            remaining_placeholders = re.findall(r'\{\{([^}]+)\}\}', content)
            if remaining_placeholders:
                print(f"[ATTENTION] Placeholders non remplacés: {remaining_placeholders}")
            
            return content
            
        except Exception as e:
            print(f"[ERREUR] Erreur remplacement placeholders: {e}")
            return template_content

    def get_template_summary(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un résumé d'un template (métadonnées et validation)
        
        Args:
            template_id: ID du template
            
        Returns:
            Dictionnaire avec les informations du template
        """
        try:
            content = self.get_template_content(template_id)
            if not content:
                return None
            
            # Analyser le template
            validation = self.validate_template(content, template_id.replace('_chat', ''))
            
            # Extraire des métadonnées basiques
            lines = content.strip().split('\n')
            
            summary = {
                'id': template_id,
                'provider': template_id.replace('_chat', '') if '_chat' in template_id else 'unknown',
                'size_bytes': len(content.encode('utf-8')),
                'lines_count': len(lines),
                'has_api_key_placeholder': any('API_KEY' in line for line in lines),
                'user_placeholders': validation.get('user_placeholders', []),
                'system_placeholders': validation.get('system_placeholders', []),
                'validation_errors': validation.get('errors', []),
                'is_valid': len(validation.get('errors', [])) == 0
            }
            
            return summary
        except Exception as e:
            print(f"[ERREUR] Erreur création résumé template {template_id}: {e}")
            return None


class ProfileManagerFactory:
    """
    Factory pour créer des instances d'APIManager
    Pattern: Factory Method
    """
    
    @staticmethod
    def create_api_manager() -> APIManager:
        """
        Crée une nouvelle instance d'APIManager
        
        Returns:
            Instance configurée d'APIManager
        """
        return APIManager()
    
    @staticmethod
    def create_api_manager_with_validation() -> Optional[APIManager]:
        """
        Crée une instance d'APIManager avec validation préalable
        
        Returns:
            Instance d'APIManager si la validation passe, None sinon
        """
        try:
            # Vérifier que ConfigManager peut être importé et fonctionne
            manager = APIManager()
            
            # Test basique : lister les profils
            profiles = manager.list_available_profiles()
            
            print(f"✅ APIManager créé avec succès ({len(profiles)} profils détectés)")
            return manager
            
        except Exception as e:
            print(f"❌ Erreur lors de la création d'APIManager: {e}")
            return None


# Export des classes principales
__all__ = ['IProfileManager', 'APIManager', 'ProfileManagerFactory']


if __name__ == "__main__":
    # Test basique du module
    print("🧪 TEST MODULE API_MANAGER")
    print("=" * 40)
    
    # Créer une instance
    api_manager = ProfileManagerFactory.create_api_manager_with_validation()
    
    if api_manager:
        print("\n📋 PROFILS DISPONIBLES:")
        profiles = api_manager.list_available_profiles()
        for profile in profiles:
            summary = api_manager.get_profile_summary(profile)
            if summary:
                print(f"   • {profile}: {summary['provider']} ({summary['method']})")
        
        print(f"\n📊 STATISTIQUES:")
        cache_info = api_manager.get_cache_info()
        print(f"   Profils disponibles: {cache_info['available_profiles']}")
        print(f"   Profils en cache: {cache_info['cached_profiles']}")
        
        print(f"\n✅ MODULE API_MANAGER FONCTIONNEL")
    else:
        print(f"\n❌ ÉCHEC DU TEST MODULE")
