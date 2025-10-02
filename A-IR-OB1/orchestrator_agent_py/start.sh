#!/usr/bin/env bash
# Script de démarrage pour l'application FastAPI (Linux/MacOS)

# Configuration de l'environnement
export PYTHONPATH="$(pwd)"

# Démarrage de l'application
.venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000