@echo off
REM Script de démarrage pour l'application FastAPI (Windows)

REM Configuration de l'environnement
set PYTHONPATH=%cd%

REM Démarrage de l'application
..\.venv\Scripts\uvicorn.exe main:app --reload --host 0.0.0.0 --port 8000