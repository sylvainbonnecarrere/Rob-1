"""
Router principal de l'API FastAPI.

Ce module contient tous les endpoints de l'application d'orchestration d'agents IA.
Il utilise APIRouter pour une architecture modulaire et une séparation claire des responsabilités.

Jalon 2.2 : Intégration de l'Injection de Dépendances pour les services LLM.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

# Import conditionnel pour éviter les erreurs d'import relatif
try:
    from .dependencies import (
        get_llm_service_from_config,
        get_llm_service_by_provider,
        get_factory_info,
        LLMServiceDependency,
        FactoryInfoDependency
    )
    from ..domain.llm_service_interface import LLMService
    from ..models.data_contracts import AgentConfig
except ImportError:
    # Fallback pour les tests et imports directs
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent
    sys.path.insert(0, str(src_path))
    from api.dependencies import (
        get_llm_service_from_config,
        get_llm_service_by_provider,
        get_factory_info,
        LLMServiceDependency,
        FactoryInfoDependency
    )
    from domain.llm_service_interface import LLMService
    from models.data_contracts import AgentConfig


# Création du routeur principal
router = APIRouter()


@router.get("/health", response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    """
    Endpoint de health check pour vérifier le statut de l'application.
    
    Returns:
        Dict[str, str]: Statut de l'application et nom du service
    """
    return {
        "status": "ok",
        "service": "orchestrator"
    }


@router.get("/", response_model=Dict[str, Any])
async def root() -> Dict[str, Any]:
    """
    Endpoint racine fournissant des informations sur l'API.
    
    Returns:
        Dict[str, Any]: Informations sur l'API et liens utiles
    """
    return {
        "message": "Orchestrator Agent API",
        "version": "1.0.0",
        "status": "active",
        "documentation": "/docs",
        "health_check": "/health"
    }


@router.post("/test-service", response_model=Dict[str, Any])
async def test_llm_service(
    config: AgentConfig,
    llm_service: LLMService = Depends(get_llm_service_from_config)
) -> Dict[str, Any]:
    """
    Endpoint de test pour valider l'injection de dépendances et la façade LLM.
    
    Cet endpoint démontre l'utilisation de l'injection de dépendances FastAPI
    pour obtenir automatiquement le service LLM approprié selon la configuration.
    
    Args:
        config: Configuration de l'agent (dans le body de la requête)
        llm_service: Service LLM injecté automatiquement par FastAPI
        
    Returns:
        Dict[str, Any]: Informations sur le service LLM utilisé
        
    Raises:
        HTTPException: Si le fournisseur n'est pas supporté ou en cas d'erreur
    """
    try:
        # Test des méthodes du service injecté
        model_name = await llm_service.get_model_name()
        supported_tools = await llm_service.get_supported_tools()
        
        return {
            "success": True,
            "message": "Service LLM injecté avec succès",
            "config_received": {
                "agent_id": config.agent_id,
                "provider": config.provider,
                "model": config.model
            },
            "service_info": {
                "model_name": model_name,
                "supported_tools": supported_tools,
                "service_type": type(llm_service).__name__
            },
            "dependency_injection": "validated"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du test du service LLM : {str(e)}"
        )


@router.get("/providers", response_model=Dict[str, Any])
async def get_supported_providers(
    factory_info: dict = Depends(get_factory_info)
) -> Dict[str, Any]:
    """
    Endpoint pour obtenir les fournisseurs LLM supportés.
    
    Utilise l'injection de dépendances pour obtenir les informations
    de la factory sans couplage direct.
    
    Args:
        factory_info: Informations de la factory injectées automatiquement
        
    Returns:
        Dict[str, Any]: Liste des fournisseurs supportés et informations de cache
    """
    return {
        "supported_providers": factory_info["supported_providers"],
        "cache_info": factory_info["cache_info"],
        "jalon": "2.2 - Façade et Injection de Dépendances"
    }


@router.post("/test-provider/{provider}")
async def test_specific_provider(
    provider: str,
    model: str = "default",
    llm_service: LLMService = Depends(get_llm_service_by_provider)
) -> Dict[str, Any]:
    """
    Endpoint pour tester un fournisseur spécifique par URL.
    
    Démontre l'injection de dépendances avec paramètres d'URL.
    
    Args:
        provider: Nom du fournisseur (dans l'URL)
        model: Modèle à utiliser (paramètre de requête)
        llm_service: Service LLM injecté automatiquement
        
    Returns:
        Dict[str, Any]: Informations sur le service testé
    """
    try:
        model_name = await llm_service.get_model_name()
        
        return {
            "success": True,
            "provider_requested": provider,
            "model_requested": model,
            "actual_model": model_name,
            "service_type": type(llm_service).__name__,
            "test_result": "Provider injection successful"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du test du fournisseur {provider} : {str(e)}"
        )