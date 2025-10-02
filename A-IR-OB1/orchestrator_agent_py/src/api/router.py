"""
Router principal de l'API FastAPI.

Ce module contient tous les endpoints de l'application d'orchestration d'agents IA.
Il utilise APIRouter pour une architecture modulaire et une séparation claire des responsabilités.
"""

from fastapi import APIRouter
from typing import Dict, Any


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