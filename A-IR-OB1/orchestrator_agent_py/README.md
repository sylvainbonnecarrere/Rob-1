# Orchestrator Agent Python

🤖 **Système d'orchestration d'agents IA avec architecture microservices asynchrone**

## 🎯 Description

Application Python moderne pour l'orchestration d'agents d'intelligence artificielle générative, conçue avec FastAPI et une architecture hexagonale. Le système permet d'utiliser différents fournisseurs LLM (OpenAI, Anthropic, Gemini) de manière interchangeable avec exécution d'outils et logique ReAct.

## 🏗️ Architecture

- **Framework** : FastAPI (microservices asynchrones)
- **Validation** : Pydantic V2 avec typage strict
- **Architecture** : Hexagonale (Ports & Adapters)
- **Patterns** : SOLID, Factory, Strategy, Adapter
- **LLMs** : Support multi-fournisseurs (OpenAI, Anthropic, Gemini)

## 📁 Structure du Projet

```
orchestrator_agent_py/
├── main.py                    # Point d'entrée FastAPI
├── requirements.txt           # Dépendances Python
├── .gitignore                # Configuration Git
├── README.md                 # Documentation
└── src/
    ├── models/               # Modèles Pydantic (Data Contracts)
    │   └── data_contracts.py
    ├── domain/               # Logique métier & interfaces
    │   └── llm_service_interface.py
    ├── api/                  # Endpoints FastAPI
    └── infrastructure/       # Adapters & services externes
```

## 🚀 Installation

```bash
# Cloner le repository
git clone <repository-url>
cd orchestrator_agent_py

# Créer un environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# Installer les dépendances
pip install -r requirements.txt
```

## 📋 Fonctionnalités Actuelles

### ✅ Phase 1 - Fondations COMPLÉTÉE
### ✅ Phase 2 - Services et Adaptateurs (EN COURS)

#### Jalon 1.x - Fondations ✅
- **Modèles de données Pydantic** : AgentConfig, ChatMessage, ToolCall, OrchestrationRequest/Response
- **Interface LLM abstraite** : Port hexagonal pour l'interchangeabilité des fournisseurs
- **Architecture SOLID** : Respect des principes de conception logicielle
- **Typage strict** : Validation complète avec Pydantic V2
- **🎉 Microservice FastAPI** : API fonctionnelle avec endpoints et documentation

#### Jalon 2.1 - Premier Adaptateur LLM ✅
- **🤖 OpenAI Adapter** : Implémentation complète pour GPT-3.5/GPT-4
- **🔄 Conversion de formats** : AgentConfig/ChatMessage ↔ Format OpenAI
- **⚡ Appels asynchrones** : Client OpenAI async pour les performances
- **🛡️ Gestion des erreurs** : Validation des clés API et paramètres
- **🧪 Tests complets** : Validation offline et avec API réelle
- **🏗️ Architecture SOLID** : OCP validé - extension sans modification

#### Jalon 2.2 - Façade et Injection de Dépendances ✅
- **🏭 LLMServiceFactory** : Factory pattern pour création centralisée des services
- **🔌 Injection de Dépendances** : FastAPI DI pour découplage complet
- **📋 Registre extensible** : Ajout facile de nouveaux fournisseurs LLM
- **⚡ Cache intelligent** : Optimisation des performances optionnelle
- **🌐 Nouveaux endpoints** : /test-service, /providers avec DI
- **🎯 Principe DIP** : Endpoints dépendent de l'abstraction, pas du concret

## 🚀 Démarrage de l'Application

### Méthode 1 : Script de démarrage recommandé
```bash
cd orchestrator_agent_py
python debug/start_and_validate.py
```

### Méthode 2 : Uvicorn direct
```bash
# Windows PowerShell
cd orchestrator_agent_py
$env:PYTHONPATH = "$(pwd)"; uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Linux/Mac
cd orchestrator_agent_py
PYTHONPATH=$(pwd) uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Méthode 3 : Python direct
```bash
cd orchestrator_agent_py
python main.py
```

## 🌐 Endpoints Disponibles

Une fois l'application démarrée sur `http://localhost:8000` :

- **Health Check** : `GET /api/health`
  ```json
  {"status": "ok", "service": "orchestrator"}
  ```

- **📘 API Info** : `GET /api/`
  - Informations sur l'API et liens utiles

- **🏭 Fournisseurs LLM** : `GET /api/providers`
  - Liste des fournisseurs supportés et informations de cache

- **🧪 Test Service LLM** : `POST /api/test-service`
  - Test de l'injection de dépendances avec AgentConfig
  - Validation de la factory et du service LLM

- **📚 Documentation Interactive** : `GET /docs`
  - Interface Swagger UI pour tester l'API

- **📖 Documentation Alternative** : `GET /redoc`
  - Interface ReDoc pour la documentation

## ✅ Validation du Jalon 1.3

Pour valider que l'application fonctionne :

1. **Démarrer l'application** avec une des méthodes ci-dessus
2. **Ouvrir** `http://localhost:8000/api/health` dans un navigateur
3. **Vérifier la réponse** : `{"status": "ok", "service": "orchestrator"}`
4. **Tester la documentation** : `http://localhost:8000/docs`

**🎯 Résultat attendu** : Tous les endpoints répondent correctement

### 🚧 Prochaines Phases

- **Jalon 2.2** : Façade et injection de dépendances
- **Jalon 2.3** : Gestion des tools (Function Calling)
- **Phase 3** : Moteur d'orchestration et logique ReAct
- **Phase 4** : Fonctionnalités avancées (multimodalité, CRUD agents)

## 🛠️ Développement

Le projet suit un plan de développement incrémental avec des jalons testables :

1. **Jalon 1.1** ✅ : Structure projet & modèles Pydantic
2. **Jalon 1.2** ✅ : Interface abstraite LLMService
3. **Jalon 1.3** ✅ : Microservice FastAPI minimal
4. **Jalon 2.1** ✅ : Premier adaptateur OpenAI fonctionnel
5. **Jalon 2.2** 🚧 : Façade et injection de dépendances
6. **Jalon 2.3** : Gestion des tools (Function Calling)
7. **Jalon 3.x** : Orchestration et ReAct

## 📝 Licence

Projet de développement pour l'apprentissage de l'architecture moderne Python.

---

**Développé avec les bonnes pratiques d'architecture logicielle moderne**