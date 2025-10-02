"""
Factory (Façade) pour les services LLM.

Ce module implémente le pattern Factory/Façade pour centraliser l'instanciation
des adaptateurs LLM selon le fournisseur spécifié. Cette approche respecte
les principes SOLID et facilite l'extensibilité du système.

Architecture et Patterns appliqués :
- Factory Pattern : Création d'objets selon un type/paramètre
- Façade Pattern : Point d'accès unifié aux adaptateurs LLM
- DIP (Dependency Inversion) : Retour de l'abstraction LLMService
- OCP (Open/Closed) : Extension facile pour nouveaux fournisseurs

Conformité SOLID :
- SRP : Responsabilité unique = factory des services LLM
- OCP : Ajout de nouveaux fournisseurs sans modification du code client
- DIP : Les clients dépendent de LLMService, pas des adaptateurs concrets
"""

import os
from typing import Dict, Type, Optional
from fastapi import HTTPException

# Import conditionnel pour éviter les erreurs d'import relatif
try:
    from .llm_service_interface import LLMService
    from ..infrastructure.llm_providers.openai_adapter import OpenAIAdapter
    from ..models.data_contracts import AgentConfig
except ImportError:
    # Fallback pour les tests et imports directs
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent
    sys.path.insert(0, str(src_path))
    from domain.llm_service_interface import LLMService
    from infrastructure.llm_providers.openai_adapter import OpenAIAdapter
    from models.data_contracts import AgentConfig


class LLMServiceFactory:
    """
    Factory pour l'instanciation des services LLM.
    
    Cette classe centralise la logique de création des adaptateurs LLM
    en fonction du fournisseur spécifié. Elle maintient un registre
    des fournisseurs supportés et leurs classes d'adaptateur correspondantes.
    
    Attributes:
        _registry: Mapping fournisseur -> classe d'adaptateur
        _instances: Cache des instances créées (optionnel pour optimisation)
    """
    
    # Registre des fournisseurs supportés
    _registry: Dict[str, Type[LLMService]] = {
        "openai": OpenAIAdapter,
        # Futurs fournisseurs seront ajoutés ici :
        # "anthropic": AnthropicAdapter,  # Jalon 2.x
        # "gemini": GeminiAdapter,        # Jalon 2.x
    }
    
    # Cache des instances (optionnel pour optimisation)
    _instances: Dict[str, LLMService] = {}
    
    @classmethod
    def get_service(
        cls, 
        provider: str, 
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        use_cache: bool = False
    ) -> LLMService:
        """
        Retourne une instance du service LLM pour le fournisseur spécifié.
        
        Args:
            provider: Nom du fournisseur LLM ('openai', 'anthropic', 'gemini')
            model: Nom du modèle spécifique (optionnel, utilise les défauts)
            api_key: Clé API pour le fournisseur (optionnel, utilise l'environnement)
            use_cache: Si True, réutilise les instances existantes
            
        Returns:
            LLMService: Instance de l'adaptateur correspondant au fournisseur
            
        Raises:
            ValueError: Si le fournisseur n'est pas supporté
            HTTPException: En cas d'erreur d'instanciation (pour les endpoints FastAPI)
        """
        # Validation du fournisseur
        provider_lower = provider.lower()
        
        if provider_lower not in cls._registry:
            supported = ", ".join(cls._registry.keys())
            raise ValueError(
                f"Fournisseur LLM non supporté : '{provider}'. "
                f"Fournisseurs supportés : {supported}"
            )
        
        # Vérification du cache si demandé
        cache_key = f"{provider_lower}:{model or 'default'}"
        if use_cache and cache_key in cls._instances:
            return cls._instances[cache_key]
        
        try:
            # Récupération de la classe d'adaptateur
            adapter_class = cls._registry[provider_lower]
            
            # Instanciation avec paramètres appropriés
            kwargs = {}
            
            if provider_lower == "openai":
                # Configuration spécifique OpenAI
                if model:
                    kwargs["model"] = model
                if api_key:
                    kwargs["api_key"] = api_key
            # elif provider_lower == "anthropic":
            #     # Configuration spécifique Anthropic (futur)
            #     pass
            # elif provider_lower == "gemini":
            #     # Configuration spécifique Gemini (futur)
            #     pass
            
            # Création de l'instance
            service_instance = adapter_class(**kwargs)
            
            # Mise en cache si demandé
            if use_cache:
                cls._instances[cache_key] = service_instance
            
            return service_instance
            
        except Exception as e:
            # Conversion en HTTPException pour les endpoints FastAPI
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de l'instanciation du service LLM '{provider}': {str(e)}"
            )
    
    @classmethod
    def get_service_from_config(
        cls, 
        config: AgentConfig,
        use_cache: bool = False
    ) -> LLMService:
        """
        Retourne une instance du service LLM basée sur la configuration d'agent.
        
        Cette méthode de commodité extrait les paramètres nécessaires
        depuis un objet AgentConfig pour créer le service approprié.
        
        Args:
            config: Configuration de l'agent contenant le fournisseur et le modèle
            use_cache: Si True, réutilise les instances existantes
            
        Returns:
            LLMService: Instance de l'adaptateur configuré
            
        Raises:
            ValueError: Si le fournisseur dans la config n'est pas supporté
            HTTPException: En cas d'erreur d'instanciation
        """
        return cls.get_service(
            provider=config.provider,
            model=config.model,
            use_cache=use_cache
        )
    
    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """
        Retourne la liste des fournisseurs LLM supportés.
        
        Returns:
            list[str]: Liste des noms de fournisseurs supportés
        """
        return list(cls._registry.keys())
    
    @classmethod
    def register_provider(
        cls, 
        provider: str, 
        adapter_class: Type[LLMService]
    ) -> None:
        """
        Enregistre un nouveau fournisseur LLM dans la factory.
        
        Cette méthode permet d'étendre dynamiquement les fournisseurs
        supportés sans modifier le code de la factory.
        
        Args:
            provider: Nom du fournisseur à ajouter
            adapter_class: Classe d'adaptateur implémentant LLMService
            
        Raises:
            TypeError: Si adapter_class n'hérite pas de LLMService
        """
        if not issubclass(adapter_class, LLMService):
            raise TypeError(
                f"La classe {adapter_class.__name__} doit hériter de LLMService"
            )
        
        cls._registry[provider.lower()] = adapter_class
    
    @classmethod
    def clear_cache(cls) -> None:
        """
        Vide le cache des instances de services.
        
        Utile pour les tests ou lors de changements de configuration.
        """
        cls._instances.clear()
    
    @classmethod
    def get_cache_info(cls) -> Dict[str, int]:
        """
        Retourne des informations sur le cache des instances.
        
        Returns:
            Dict[str, int]: Informations sur le cache (nombre d'instances, etc.)
        """
        return {
            "cached_instances": len(cls._instances),
            "supported_providers": len(cls._registry)
        }