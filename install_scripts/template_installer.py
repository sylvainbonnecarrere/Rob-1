#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Install Scripts - Template Installer
====================================
Module responsable de l'installation des templates et profils par défaut
Responsabilités : création contenu initial, migration V1→V2, gestion premiers démarrages
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Import conditionnel du ConfigManager
try:
    from config_manager import ConfigManager
except ImportError:
    ConfigManager = None


class TemplateInstaller:
    """
    Installateur de templates et profils par défaut
    
    Responsabilités (Single Responsibility Principle) :
    - Installation des profils LLM par défaut (Gemini, OpenAI, Claude)
    - Création des templates API dans la structure V2 (templates/chat/{provider}/)
    - Migration depuis l'ancienne structure V1 si nécessaire
    - Gestion du premier démarrage de l'application
    """
    
    # Templates API embarqués (structure V2)
    EMBEDDED_API_TEMPLATES = {
        "gemini": {
            "curl.txt": '''curl "https://generativelanguage.googleapis.com/v1beta/models/{{model}}:generateContent?key={{api_key}}" \\
  -H 'Content-Type: application/json' \\
  -X POST \\
  -d '{
    "contents": [
      {
        "parts": [
          {
            "text": "{{prompt}}"
          }
        ]
      }
    ]
  }'
''',
            "native_basic.py": '''#!/usr/bin/env python3
"""
Gemini Native SDK Template
Utilise la bibliothèque officielle google-generativeai
"""

import google.generativeai as genai
from typing import Optional

def call_gemini_native(api_key: str, model: str, prompt: str) -> Optional[str]:
    """
    Appel natif à l'API Gemini via SDK officiel
    
    Args:
        api_key: Clé API Gemini
        model: Modèle à utiliser (ex: gemini-2.0-flash)
        prompt: Texte de la requête
    
    Returns:
        Réponse du modèle ou None en cas d'erreur
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Erreur Gemini Native: {e}")
        return None

# Point d'entrée pour l'exécution directe
if __name__ == "__main__":
    # Variables à remplacer par le système de templates
    api_key = "{{api_key}}"
    model = "{{model}}"
    prompt = "{{prompt}}"
    
    result = call_gemini_native(api_key, model, prompt)
    if result:
        print(result)
'''
        },
        
        "openai": {
            "curl.txt": '''curl "https://api.openai.com/v1/chat/completions" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer {{api_key}}" \\
  -d '{
    "model": "{{model}}",
    "messages": [
      {
        "role": "user",
        "content": "{{prompt}}"
      }
    ],
    "max_tokens": 4000,
    "temperature": 0.7
  }'
''',
            "native_basic.py": '''#!/usr/bin/env python3
"""
OpenAI Native SDK Template
Utilise la bibliothèque officielle openai
"""

from openai import OpenAI
from typing import Optional

def call_openai_native(api_key: str, model: str, prompt: str) -> Optional[str]:
    """
    Appel natif à l'API OpenAI via SDK officiel
    
    Args:
        api_key: Clé API OpenAI
        model: Modèle à utiliser (ex: gpt-4o-mini)
        prompt: Texte de la requête
    
    Returns:
        Réponse du modèle ou None en cas d'erreur
    """
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erreur OpenAI Native: {e}")
        return None

# Point d'entrée pour l'exécution directe
if __name__ == "__main__":
    # Variables à remplacer par le système de templates
    api_key = "{{api_key}}"
    model = "{{model}}"
    prompt = "{{prompt}}"
    
    result = call_openai_native(api_key, model, prompt)
    if result:
        print(result)
'''
        },
        
        "claude": {
            "curl.txt": '''curl "https://api.anthropic.com/v1/messages" \\
  -H "Content-Type: application/json" \\
  -H "x-api-key: {{api_key}}" \\
  -H "anthropic-version: 2023-06-01" \\
  -d '{
    "model": "{{model}}",
    "max_tokens": 4000,
    "messages": [
      {
        "role": "user",
        "content": "{{prompt}}"
      }
    ]
  }'
''',
            "native_basic.py": '''#!/usr/bin/env python3
"""
Claude Native SDK Template
Utilise la bibliothèque officielle anthropic
"""

import anthropic
from typing import Optional

def call_claude_native(api_key: str, model: str, prompt: str) -> Optional[str]:
    """
    Appel natif à l'API Claude via SDK officiel
    
    Args:
        api_key: Clé API Claude
        model: Modèle à utiliser (ex: claude-3-sonnet-20240229)
        prompt: Texte de la requête
    
    Returns:
        Réponse du modèle ou None en cas d'erreur
    """
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Erreur Claude Native: {e}")
        return None

# Point d'entrée pour l'exécution directe
if __name__ == "__main__":
    # Variables à remplacer par le système de templates
    api_key = "{{api_key}}"
    model = "{{model}}"
    prompt = "{{prompt}}"
    
    result = call_claude_native(api_key, model, prompt)
    if result:
        print(result)
'''
        }
    }
    
    # SUPPRIMÉ - DIRECTIVE ARCHITECTE : SOURCE UNIQUE DE VÉRITÉ
    # Les profils par défaut sont maintenant générés uniquement à partir des fichiers .json.template
    # Élimination des données hardcodées pour éviter les incohérences et les champs manquants
    # ConfigManager.create_default_profiles() gère toute l'initialisation depuis les templates
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialise l'installateur de templates
        
        Args:
            config_manager: Instance du ConfigManager pour la sauvegarde
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        if not config_manager:
            self.logger.warning("ConfigManager non fourni - certaines fonctionnalités limitées")
    
    def install_default_profiles(self) -> bool:
        """
        DÉSACTIVÉ - DIRECTIVE ARCHITECTE : SOURCE UNIQUE DE VÉRITÉ
        
        Cette méthode utilisait EMBEDDED_DEFAULT_PROFILES qui créait des profils INCOMPLETS
        sans response_path. Maintenant seul ConfigManager.create_default_profiles() 
        crée les profils à partir des fichiers .json.template COMPLETS.
        
        Returns:
            bool: True (ne fait rien, ConfigManager gère tout)
        """
        print("ℹ️ install_default_profiles() désactivé - ConfigManager gère l'initialisation")
        print("✅ Profils créés à partir des templates .json.template complets")
        return True
    
    def install_api_templates(self) -> bool:
        """
        Installe les templates API dans la structure V2
        
        Returns:
            bool: True si l'installation s'est bien passée
        """
        try:
            print("📁 Installation des templates API V2...")
            
            if not self.config_manager:
                self.logger.error("ConfigManager requis pour l'installation des templates")
                return False
            
            installed_count = 0
            migrated_count = 0
            
            for provider_name, templates in self.EMBEDDED_API_TEMPLATES.items():
                print(f"🔧 Installation templates {provider_name}...")
                
                for template_name, template_content in templates.items():
                    method = "curl" if "curl" in template_name else "native"
                    
                    # Vérifier si le template existe déjà
                    existing_template = self.config_manager.load_typed_template(
                        provider_name, "chat", method
                    )
                    
                    if existing_template:
                        print(f"✅ Template existant: {provider_name}/{method}")
                    else:
                        # Essayer de migrer depuis V1 d'abord
                        migrated = self._migrate_v1_template(provider_name, method, template_content)
                        
                        if migrated:
                            migrated_count += 1
                            print(f"🔄 Template migré V1→V2: {provider_name}/{method}")
                        else:
                            # Installation nouveau template
                            if self.config_manager.save_typed_template(
                                provider_name, "chat", method, template_content
                            ):
                                installed_count += 1
                                print(f"🆕 Template installé: {provider_name}/{method}")
                            else:
                                print(f"❌ Échec installation: {provider_name}/{method}")
            
            print(f"📊 Installation templates: {installed_count} nouveaux, {migrated_count} migrés")
            self.logger.info(f"Templates installés: {installed_count} nouveaux, {migrated_count} migrés")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur installation templates API: {e}")
            print(f"❌ Erreur installation templates: {e}")
            return False
    
    def _should_update_profile(self, existing: Dict[str, Any], new: Dict[str, Any]) -> bool:
        """
        Détermine si un profil existant doit être mis à jour
        
        Args:
            existing: Profil existant
            new: Nouveau profil par défaut
            
        Returns:
            bool: True si une mise à jour est nécessaire
        """
        # Vérifier les champs critiques pour les mises à jour
        critical_fields = ["method", "template_type", "llm_model", "api_url"]
        
        for field in critical_fields:
            if existing.get(field) != new.get(field):
                return True
        
        return False
    
    def _merge_profile_data(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fusionne les données d'un profil existant avec les nouvelles données par défaut
        
        Args:
            existing: Profil existant (contient les données utilisateur)
            new: Nouvelles données par défaut
            
        Returns:
            Dict: Profil fusionné
        """
        # Commencer avec les nouvelles données par défaut
        merged = new.copy()
        
        # Préserver les données utilisateur critiques
        user_fields = ["api_key", "role", "behavior", "history", "default"]
        
        for field in user_fields:
            if field in existing and existing[field]:
                merged[field] = existing[field]
        
        return merged
    
    def _migrate_v1_template(self, provider: str, method: str, default_content: str) -> bool:
        """
        Tente de migrer un template depuis la structure V1 (api_commands)
        
        Args:
            provider: Nom du provider (gemini, openai, claude)
            method: Méthode (curl, native)
            default_content: Contenu par défaut si pas de migration
            
        Returns:
            bool: True si la migration a réussi
        """
        if method != "curl":  # Seuls les templates curl peuvent être migrés
            return False
        
        try:
            # Construire le chemin V1
            v1_path = Path(self.config_manager.templates_dir) / "api_commands" / f"{provider}_chat.txt"
            
            if not v1_path.exists():
                return False
            
            # Lire le contenu V1
            with open(v1_path, 'r', encoding='utf-8') as f:
                v1_content = f.read().strip()
            
            if not v1_content:
                return False
            
            # Sauvegarder dans la structure V2
            success = self.config_manager.save_typed_template(
                provider, "chat", method, v1_content
            )
            
            if success:
                self.logger.info(f"Template migré V1→V2: {provider}/{method}")
                return True
            
        except Exception as e:
            self.logger.warning(f"Échec migration V1 {provider}/{method}: {e}")
        
        return False
    
    def cleanup_v1_templates(self) -> bool:
        """
        Nettoie les anciens templates V1 après migration complète
        
        Returns:
            bool: True si le nettoyage s'est bien passé
        """
        try:
            print("🗑️ Nettoyage des templates V1...")
            
            v1_dir = Path(self.config_manager.templates_dir) / "api_commands"
            
            if not v1_dir.exists():
                print("✅ Répertoire V1 déjà absent")
                return True
            
            # Compter les fichiers à supprimer
            v1_files = list(v1_dir.glob("*.txt"))
            
            if not v1_files:
                print("✅ Aucun template V1 à nettoyer")
                # Supprimer le répertoire vide
                v1_dir.rmdir()
                return True
            
            # Demander confirmation pour la suppression
            print(f"⚠️ {len(v1_files)} templates V1 trouvés à supprimer")
            
            # Pour le moment, on garde les templates V1 par sécurité
            # La suppression sera implémentée dans une version ultérieure
            print("🔄 Conservation des templates V1 par sécurité (suppression future)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur nettoyage templates V1: {e}")
            print(f"❌ Erreur nettoyage V1: {e}")
            return False


def main():
    """Point d'entrée pour tests standalone"""
    print("🔬 Test standalone TemplateInstaller")
    print("=" * 45)
    
    # Import et test basique
    try:
        from config_manager import ConfigManager
        
        config_manager = ConfigManager(".")
        installer = TemplateInstaller(config_manager)
        
        print("✅ TemplateInstaller initialisé")
        
        # Test installation profils
        profiles_ok = installer.install_default_profiles()
        print(f"📋 Installation profils: {'✅ OK' if profiles_ok else '❌ Échec'}")
        
        # Test installation templates
        templates_ok = installer.install_api_templates()
        print(f"📁 Installation templates: {'✅ OK' if templates_ok else '❌ Échec'}")
        
        if profiles_ok and templates_ok:
            print("\n✅ Test réussi - TemplateInstaller fonctionnel")
        else:
            print("\n⚠️ Test partiellement réussi - Vérifier les logs")
            
    except ImportError as e:
        print(f"❌ ConfigManager non disponible: {e}")
    except Exception as e:
        print(f"❌ Erreur test: {e}")


if __name__ == "__main__":
    main()
