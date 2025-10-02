"""
Fonctions de dépendance FastAPI pour l'injection de dépendances.

Ce module contient les fonctions de dépendance réutilisables qui utilisent
le système DI (Dependency Injection) de FastAPI pour injecter les services
nécessaires dans les endpoints de l'API.

Conformité aux principes SOLID :
- DIP : Les endpoints dépendent d'abstractions, pas d'implémentations concrètes
- SRP : Chaque fonction de dépendance a une responsabilité unique
- OCP : Extensible pour de nouveaux types de dépendances

Architecture :
- Les fonctions de dépendance utilisent LLMServiceFactory
- Retournent toujours l'abstraction LLMService
- Gèrent les erreurs de configuration appropriément
"""

from typing import Annotated, Optional
from fastapi import Depends, HTTPException, Header, Body

# Import conditionnel pour éviter les erreurs d'import relatif
try:
    from ..domain.llm_service_factory import LLMServiceFactory
    from ..domain.llm_service_interface import LLMService
    from ..models.data_contracts import AgentConfig
except ImportError:
    # Fallback pour les tests et imports directs
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent
    sys.path.insert(0, str(src_path))
    from domain.llm_service_factory import LLMServiceFactory
    from domain.llm_service_interface import LLMService
    from models.data_contracts import AgentConfig


def get_llm_service_from_config(config: AgentConfig) -> LLMService:
    """
    Fonction de dépendance pour obtenir un service LLM depuis une configuration.
    
    Cette fonction est utilisée par FastAPI pour injecter automatiquement
    le service LLM approprié dans les endpoints qui en ont besoin.
    
    Args:
        config: Configuration de l'agent (injectée depuis le body de la requête)
        
    Returns:
        LLMService: Instance du service LLM configuré
        
    Raises:
        HTTPException: Si le fournisseur n'est pas supporté ou en cas d'erreur
    """
    try:
        service = LLMServiceFactory.get_service_from_config(config)
        return service
    except ValueError as e:
        # Erreur de configuration (fournisseur non supporté)
        raise HTTPException(
            status_code=400,
            detail=f"Erreur de configuration : {str(e)}"
        )
    except Exception as e:
        # Autres erreurs (clé API manquante, etc.)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'initialisation du service LLM : {str(e)}"
        )


def get_llm_service_by_provider(
    provider: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None
) -> LLMService:
    """
    Fonction de dépendance pour obtenir un service LLM par fournisseur.
    
    Utile pour les endpoints qui spécifient directement le fournisseur
    plutôt que de passer par une configuration complète.
    
    Args:
        provider: Nom du fournisseur LLM
        model: Modèle spécifique (optionnel)
        api_key: Clé API (optionnel, récupérée de l'environnement sinon)
        
    Returns:
        LLMService: Instance du service LLM
        
    Raises:
        HTTPException: Si le fournisseur n'est pas supporté ou en cas d'erreur
    """
    try:
        service = LLMServiceFactory.get_service(
            provider=provider,
            model=model,
            api_key=api_key
        )
        return service
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Fournisseur non supporté : {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'initialisation du service : {str(e)}"
        )


def get_llm_service_from_headers(
    x_llm_provider: Annotated[str, Header(description="Fournisseur LLM (openai, anthropic, gemini)")],
    x_llm_model: Annotated[Optional[str], Header(description="Modèle LLM spécifique")] = None,
    x_api_key: Annotated[Optional[str], Header(description="Clé API du fournisseur")] = None
) -> LLMService:
    """
    Fonction de dépendance pour obtenir un service LLM depuis les headers HTTP.
    
    Cette approche permet de spécifier le fournisseur LLM via les headers
    plutôt que dans le corps de la requête. Utile pour des endpoints génériques.
    
    Args:
        x_llm_provider: Nom du fournisseur (header X-LLM-Provider)
        x_llm_model: Modèle spécifique (header X-LLM-Model, optionnel)
        x_api_key: Clé API (header X-API-Key, optionnel)
        
    Returns:
        LLMService: Instance du service LLM configuré
        
    Raises:
        HTTPException: Si les headers sont invalides ou en cas d'erreur
    """
    try:
        service = LLMServiceFactory.get_service(
            provider=x_llm_provider,
            model=x_llm_model,
            api_key=x_api_key
        )
        return service
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Header X-LLM-Provider invalide : {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'initialisation depuis les headers : {str(e)}"
        )


def get_cached_llm_service_from_config(config: AgentConfig) -> LLMService:
    """
    Fonction de dépendance pour obtenir un service LLM avec cache.
    
    Version optimisée qui réutilise les instances déjà créées
    pour améliorer les performances.
    
    Args:
        config: Configuration de l'agent
        
    Returns:
        LLMService: Instance du service LLM (possiblement en cache)
        
    Raises:
        HTTPException: Si la configuration est invalide ou en cas d'erreur
    """
    try:
        service = LLMServiceFactory.get_service_from_config(
            config=config,
            use_cache=True
        )
        return service
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Configuration invalide : {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'initialisation (avec cache) : {str(e)}"
        )


def get_factory_info() -> dict:
    """
    Fonction de dépendance pour obtenir des informations sur la factory.
    
    Retourne des métadonnées sur les fournisseurs supportés et l'état du cache.
    Utile pour les endpoints de diagnostic et de monitoring.
    
    Returns:
        dict: Informations sur la factory et les fournisseurs supportés
    """
    return {
        "supported_providers": LLMServiceFactory.get_supported_providers(),
        "cache_info": LLMServiceFactory.get_cache_info()
    }


# Alias pour les types FastAPI (pour améliorer la lisibilité)
LLMServiceDependency = Annotated[LLMService, Depends(get_llm_service_from_config)]
CachedLLMServiceDependency = Annotated[LLMService, Depends(get_cached_llm_service_from_config)]
FactoryInfoDependency = Annotated[dict, Depends(get_factory_info)]