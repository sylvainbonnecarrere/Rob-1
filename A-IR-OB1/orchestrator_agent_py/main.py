"""
Point d'entrée principal de l'application FastAPI d'orchestration d'agents IA.

Ce fichier configure et démarre l'application FastAPI avec uvicorn.
Il inclut la configuration CORS et intègre le routeur principal.
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire courant au PYTHONPATH
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.router import router


def create_app() -> FastAPI:
    """
    Créé et configure l'application FastAPI.
    
    Returns:
        FastAPI: Instance de l'application configurée
    """
    # Initialisation de l'application FastAPI
    app = FastAPI(
        title="Orchestrator Agent API",
        description="API pour l'orchestration d'agents IA avec support multi-LLM",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Configuration CORS pour le développement
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # À restreindre en production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Inclusion du routeur principal
    app.include_router(router, prefix="/api")
    
    return app


# Création de l'instance de l'application
app = create_app()


if __name__ == "__main__":
    # Démarrage de l'application avec uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Rechargement automatique en développement
        log_level="info"
    )