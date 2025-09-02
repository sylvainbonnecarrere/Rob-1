#!/usr/bin/env python3
"""
Native Manager - Gestionnaire d'exécution native pour les LLMs
==============================================================

Module parallèle à payload_manager.py pour l'exécution native des requêtes API.
Utilise un système d'extraction dynamique des variables d'environnement 
basé exclusivement sur les templates officiels.

Auteur: Assistant IA
Date: 2025-09-02
Version: 1.0
"""

import os
import re
import sys
import subprocess
import tempfile
import json
import logging
from typing import Dict, Optional, Any

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DynamicProviderManager:
    """
    Gestionnaire de providers basé exclusivement sur l'extraction 
    dynamique depuis les templates officiels.
    """
    
    def __init__(self, templates_dir="templates/chat"):
        self.templates_dir = templates_dir
        self._provider_cache = {}
        self._scan_providers()
    
    def _scan_providers(self):
        """Scanne et analyse tous les providers disponibles"""
        if not os.path.exists(self.templates_dir):
            logger.warning(f"Dossier templates non trouvé: {self.templates_dir}")
            return
        
        for provider_name in os.listdir(self.templates_dir):
            provider_dir = os.path.join(self.templates_dir, provider_name)
            if os.path.isdir(provider_dir):
                self._analyze_provider(provider_name, provider_dir)
        
        logger.info(f"[DynamicProviderManager] {len(self._provider_cache)} providers analysés")
    
    def _analyze_provider(self, provider_name, provider_dir):
        """Analyse un provider spécifique"""
        curl_txt = os.path.join(provider_dir, "curl.txt")
        curl_basic_txt = os.path.join(provider_dir, "curl_basic.txt")
        
        provider_info = {
            "name": provider_name,
            "has_curl": os.path.exists(curl_txt),
            "has_curl_basic": os.path.exists(curl_basic_txt),
            "api_key_var": None,
            "complete": False
        }
        
        # Extraction de la variable d'environnement si les fichiers existent
        if provider_info["has_curl"] and provider_info["has_curl_basic"]:
            api_var = self._extract_api_key_variable(curl_txt, curl_basic_txt)
            if api_var:
                provider_info["api_key_var"] = api_var
                provider_info["complete"] = True
                logger.debug(f"[DynamicProviderManager] {provider_name} → {api_var}")
        
        self._provider_cache[provider_name.lower()] = provider_info
    
    def _extract_api_key_variable(self, curl_txt, curl_basic_txt):
        """
        Extrait la variable d'environnement réelle depuis curl.txt
        en vérifiant que {{API_KEY}} existe dans curl_basic.txt
        """
        try:
            # 1. Vérifier que {{API_KEY}} est présent dans curl_basic.txt
            with open(curl_basic_txt, 'r', encoding='utf-8') as f:
                basic_content = f.read()
            
            if "{{API_KEY}}" not in basic_content:
                return None
            
            # 2. Extraire la vraie variable depuis curl.txt
            with open(curl_txt, 'r', encoding='utf-8') as f:
                curl_content = f.read()
            
            # 3. Patterns pour trouver les variables d'environnement
            patterns = [
                r'\$([A-Z_]+_API_KEY)',           # $GEMINI_API_KEY
                r'Bearer \$([A-Z_]+_API_KEY)',    # Bearer $OPENAI_API_KEY  
                r'Bearer \$([A-Z_]+)',            # Bearer $ANTHROPIC_API_KEY
                r'x-goog-api-key: \$([A-Z_]+)',   # x-goog-api-key: $GEMINI_API_KEY
                r'x-api-key: \$([A-Z_]+)',        # x-api-key: $CLAUDE_API_KEY
                r'Authorization: Bearer \$([A-Z_]+)', # Authorization: Bearer $XAI_API_KEY
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, curl_content)
                if matches:
                    return matches[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur extraction {curl_txt}: {e}")
            return None
    
    def get_api_key_variable(self, provider_name):
        """
        Retourne la variable d'environnement pour un provider
        UNIQUEMENT basée sur l'extraction des templates
        """
        provider_info = self._provider_cache.get(provider_name.lower())
        return provider_info["api_key_var"] if provider_info and provider_info["complete"] else None
    
    def get_api_key_from_env(self, provider_name):
        """
        Récupère la clé API depuis la variable d'environnement
        """
        api_var = self.get_api_key_variable(provider_name)
        if not api_var:
            return None
        
        return os.environ.get(api_var)
    
    def is_provider_supported(self, provider_name):
        """Vérifie si un provider est supporté"""
        provider_info = self._provider_cache.get(provider_name.lower())
        return provider_info and provider_info["complete"]


class NativeManager:
    """
    Gestionnaire principal pour l'exécution native des requêtes LLM.
    Parallèle à payload_manager.py avec architecture similaire.
    """
    
    def __init__(self):
        """Initialise le gestionnaire native avec le système dynamique"""
        logger.info("[NativeManager] Initialisation du gestionnaire natif")
        
        self.provider_manager = DynamicProviderManager()
        self.dependency_cache = set()  # Cache des modules installés
        
        # Vérification initiale
        self._check_python_environment()
        logger.info("[NativeManager] ✅ Gestionnaire natif initialisé")
    
    def _check_python_environment(self):
        """Vérifie l'environnement Python"""
        try:
            python_version = sys.version_info
            if python_version.major != 3 or python_version.minor < 8:
                raise RuntimeError(f"Python 3.8+ requis, version actuelle: {sys.version}")
            
            logger.debug(f"[NativeManager] Python {sys.version} détecté")
            
        except Exception as e:
            logger.error(f"[NativeManager] Erreur vérification environnement: {e}")
            raise
    
    def execute_native_request(self, template_string: str, variables: Dict[str, str], provider_name: str) -> Dict[str, Any]:
        """
        Fonction principale d'exécution des requêtes natives.
        
        Args:
            template_string: Code Python template avec placeholders
            variables: Dictionnaire des variables à remplacer (LLM_MODEL, USER_PROMPT, etc.)
            provider_name: Nom du provider (gemini, openai, claude, etc.)
            
        Returns:
            Dict contenant la réponse de l'API ou les erreurs
            
        Format de retour similaire à curl:
        {
            "status": "success|error",
            "output": "réponse de l'API",
            "errors": "messages d'erreur si applicable",
            "execution_time": "native",
            "variables": {...}  # Variables extraites si succès
        }
        """
        logger.info(f"[NativeManager] Début exécution native - Provider: {provider_name}")
        
        try:
            # Étape 1: Validation du provider
            if not self.provider_manager.is_provider_supported(provider_name):
                raise ValueError(f"Provider '{provider_name}' non supporté ou incomplet")
            
            # Étape 2: Préparation du template
            prepared_code = self._prepare_template(template_string, variables, provider_name)
            logger.debug(f"[NativeManager] Template préparé - {len(prepared_code)} caractères")
            
            # Étape 3: Installation des dépendances si nécessaire
            self._install_dependencies(provider_name, prepared_code)
            
            # Étape 4: Exécution sécurisée
            result = self._execute_safely(prepared_code)
            
            logger.info("[NativeManager] ✅ Exécution native réussie")
            return {
                "status": "success",
                "output": result["stdout"],
                "errors": result["stderr"] if result["stderr"] else None,
                "execution_time": "native",
                "variables": variables
            }
            
        except Exception as e:
            logger.error(f"[NativeManager] ❌ Erreur exécution: {e}")
            return {
                "status": "error",
                "output": None,
                "errors": str(e),
                "execution_time": "native",
                "variables": variables
            }
    
    def _prepare_template(self, template_string: str, variables: Dict[str, str], provider_name: str) -> str:
        """
        Prépare le template en remplaçant les placeholders et injectant la clé API.
        
        Args:
            template_string: Template Python brut
            variables: Variables à remplacer
            provider_name: Nom du provider pour extraction de la clé API
            
        Returns:
            Code Python prêt à l'exécution
        """
        logger.debug(f"[NativeManager] Préparation template pour {provider_name}")
        
        # 1. Extraction de la variable d'environnement
        api_key_var = self.provider_manager.get_api_key_variable(provider_name)
        if not api_key_var:
            raise ValueError(f"Variable API non trouvée pour provider '{provider_name}'")
        
        # 2. Vérification de la clé API
        api_key = os.environ.get(api_key_var)
        if not api_key:
            raise ValueError(f"Variable d'environnement {api_key_var} non définie")
        
        # 3. Ajout de l'en-tête UTF-8 si absent
        prepared_code = template_string
        if "# -*- coding: utf-8 -*-" not in prepared_code:
            prepared_code = "# -*- coding: utf-8 -*-\n" + prepared_code
        
        # 4. Injection de la gestion de clé API si non présente
        if f"os.environ.get('{api_key_var}')" not in prepared_code:
            api_injection = f"""
import os

# Récupération automatique de la clé API pour {provider_name}
api_key = os.environ.get('{api_key_var}')
if not api_key:
    print("ERROR: {api_key_var} not found in environment")
    exit(1)
"""
            # Insérer après les imports
            import_end = prepared_code.find('\n\n')
            if import_end > 0:
                prepared_code = prepared_code[:import_end] + api_injection + prepared_code[import_end:]
            else:
                prepared_code = api_injection + prepared_code
        
        # 5. Remplacement des placeholders (RÈGLE: ne remplace que si trouvé)
        for placeholder, value in variables.items():
            placeholder_pattern = f"{{{{{placeholder}}}}}"
            if placeholder_pattern in prepared_code:
                prepared_code = prepared_code.replace(placeholder_pattern, str(value))
                logger.debug(f"[NativeManager] Remplacé {placeholder_pattern} → {str(value)[:50]}...")
        
        # 6. Validation syntaxique
        try:
            compile(prepared_code, '<template>', 'exec')
            logger.debug("[NativeManager] ✅ Validation syntaxique réussie")
        except SyntaxError as e:
            raise SyntaxError(f"Erreur syntaxe template: {e}")
        
        return prepared_code
    
    def _install_dependencies(self, provider_name: str, code: str):
        """
        Installe automatiquement les dépendances requises selon le provider.
        
        Args:
            provider_name: Nom du provider
            code: Code à analyser pour les imports
        """
        logger.debug(f"[NativeManager] Vérification dépendances pour {provider_name}")
        
        # Mapping des dépendances par provider
        provider_dependencies = {
            "gemini": ["google-genai"],
            "openai": ["openai"],
            "claude": ["anthropic"],
            "mistral": ["mistralai"],
            # Autres providers ajoutés automatiquement
        }
        
        # Extraire les imports du code
        import_patterns = [
            r'from\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
            r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*)'
        ]
        
        required_modules = set()
        for pattern in import_patterns:
            matches = re.findall(pattern, code)
            for match in matches:
                main_module = match.split('.')[0]
                required_modules.add(main_module)
        
        # Installation des modules manquants
        for module in required_modules:
            if module not in self.dependency_cache and module not in sys.stdlib_module_names:
                try:
                    __import__(module)
                    self.dependency_cache.add(module)
                    logger.debug(f"[NativeManager] Module {module} déjà disponible")
                except ImportError:
                    self._install_module(module, provider_dependencies.get(provider_name, []))
    
    def _install_module(self, module_name: str, provider_packages: list):
        """
        Installe un module via pip.
        
        Args:
            module_name: Nom du module à installer
            provider_packages: Liste des packages recommandés pour ce provider
        """
        # Déterminer le package à installer
        package_to_install = module_name
        
        # Mappings spéciaux
        special_mappings = {
            "google": "google-genai",
            "openai": "openai", 
            "anthropic": "anthropic",
            "mistralai": "mistralai"
        }
        
        if module_name in special_mappings:
            package_to_install = special_mappings[module_name]
        elif provider_packages and module_name in str(provider_packages):
            package_to_install = provider_packages[0]  # Premier package recommandé
        
        logger.info(f"[NativeManager] 🔧 Installation automatique: {package_to_install}")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package_to_install
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, result.args, result.stderr)
            
            self.dependency_cache.add(module_name)
            logger.info(f"[NativeManager] ✅ Module {package_to_install} installé")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"[NativeManager] ❌ Erreur installation {package_to_install}: {e}")
            raise RuntimeError(f"Impossible d'installer {package_to_install}")
    
    def _execute_safely(self, code: str, timeout: int = 30) -> Dict[str, str]:
        """
        Exécute le code Python de manière sécurisée dans un subprocess.
        
        Args:
            code: Code Python à exécuter
            timeout: Timeout en secondes
            
        Returns:
            Dict avec stdout, stderr, returncode
        """
        logger.debug("[NativeManager] Début exécution sécurisée")
        
        try:
            # Création d'un fichier temporaire
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            # Exécution dans un subprocess isolé
            result = subprocess.run(
                [sys.executable, temp_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                env=os.environ.copy()  # Passe les variables d'environnement
            )
            
            # Nettoyage
            os.unlink(temp_file_path)
            
            logger.debug(f"[NativeManager] Exécution terminée - Code retour: {result.returncode}")
            
            return {
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip() if result.stderr else "",
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"[NativeManager] ❌ Timeout après {timeout}s")
            if 'temp_file_path' in locals():
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            raise RuntimeError(f"Exécution interrompue après {timeout}s")
            
        except Exception as e:
            logger.error(f"[NativeManager] ❌ Erreur exécution: {e}")
            if 'temp_file_path' in locals():
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            raise


def test_native_manager():
    """Test rapide du NativeManager"""
    print("🧪 Test NativeManager...")
    
    try:
        manager = NativeManager()
        print("✅ NativeManager initialisé")
        
        # Test avec un template simple
        template = """
from google import genai
from google.genai import types

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="{{LLM_MODEL}}",
    config=types.GenerateContentConfig(
        system_instruction="{{SYSTEM_PROMPT_ROLE}}. {{SYSTEM_PROMPT_BEHAVIOR}}"),
    contents="{{USER_PROMPT}}"
)

print(response.text)
"""
        
        variables = {
            "LLM_MODEL": "gemini-2.5-flash",
            "SYSTEM_PROMPT_ROLE": "You are a helpful assistant",
            "SYSTEM_PROMPT_BEHAVIOR": "You respond briefly",
            "USER_PROMPT": "Say hello"
        }
        
        # Test nécessite GEMINI_API_KEY dans l'environnement
        if os.environ.get('GEMINI_API_KEY'):
            result = manager.execute_native_request(template, variables, "gemini")
            print(f"✅ Test exécution: {result['status']}")
        else:
            print("⚠️  Test exécution skippé (GEMINI_API_KEY manquante)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False


if __name__ == "__main__":
    test_native_manager()
