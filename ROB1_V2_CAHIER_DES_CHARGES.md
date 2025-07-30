# 📋 **CAHIER DES CHARGES ROB-1 V2.0**
## *Spécifications Techniques et Fonctionnelles Détaillées*

---

## 🎯 **CONTEXTE ET OBJECTIFS**

### **Projet**
**Rob-1 V2.0** - Évolution de l'application desktop de gestion multi-LLM vers une solution enterprise-grade avec architecture plugin-based, support international et robustesse renforcée.

### **Base Existante (V1.0)**
- ✅ **POC Production validé** - OpenAI et Gemini fonctionnels
- ✅ **Architecture modulaire** - Design patterns émergents
- ✅ **Fonctionnalités core** - Test API, Setup History, gestion conversations
- ✅ **Templates curl** - Système basique mais fonctionnel

### **Vision V2.0**
Transformer le POC en **application production robuste** avec :
- 🌍 **Support international** (FR/EN extensible)
- 🔌 **Architecture plugins** pour nouveaux LLM
- 🔒 **Robustesse encodage** universelle
- 🧪 **Stratégie test** complète (dev + utilisateur)

---

## 🏗️ **ARCHITECTURE CIBLE V2.0**

### **Structure Modulaire Évolutive**
```
📁 Rob-1-V2/
├── 🎯 Core/
│   ├── Domain/                   # Logique métier pure
│   │   ├── models/              # Entités (Profile, Conversation, Template)
│   │   ├── services/            # Services métier (LLMService, ConversationService)
│   │   └── interfaces/          # Contrats d'interface
│   ├── Application/             # Use cases et orchestration
│   │   ├── usecases/           # TestAPI, SetupHistory, ExportFiles
│   │   ├── handlers/           # Event handlers
│   │   └── validators/         # Validation données entrantes
│   ├── Infrastructure/          # Implémentations techniques
│   │   ├── repositories/       # Accès données (JSON, fichiers)
│   │   ├── providers/          # Providers LLM (OpenAI, Gemini, Claude...)
│   │   ├── i18n/              # Système internationalisation
│   │   └── encoding/           # Gestion robuste encodage
│   └── Presentation/            # Interfaces utilisateur
│       ├── gui/                # Interface Tkinter
│       ├── cli/                # Interface ligne de commande (futur)
│       └── api/                # API REST (futur)
├── 🔌 Plugins/
│   ├── LLMProviders/           # Plugins providers LLM
│   │   ├── OpenAIProvider/     # Plugin OpenAI (native + curl)
│   │   ├── GeminiProvider/     # Plugin Gemini (native + curl)
│   │   ├── ClaudeProvider/     # Plugin Claude (native + curl)
│   │   └── [NewLLM]Provider/   # Templates nouveaux LLM
│   ├── ExportFormats/          # Plugins export
│   │   ├── MarkdownExporter/   # Export MD
│   │   ├── PDFExporter/        # Export PDF (futur)
│   │   └── JSONExporter/       # Export JSON structuré
│   └── Extensions/             # Plugins fonctionnalités
│       ├── RAGExtension/       # Retrieval Augmented Generation (futur)
│       ├── MultiModalExt/      # Support images/documents (futur)
│       └── WorkflowExt/        # Workflows automatisés (futur)
├── 🌍 Resources/
│   ├── i18n/                   # Fichiers langues
│   │   ├── fr.json            # Français
│   │   ├── en.json            # Anglais
│   │   └── template.json      # Template nouvelle langue
│   ├── templates/             # Templates par provider et méthode
│   │   ├── openai/
│   │   │   ├── native/        # Templates SDK natif
│   │   │   ├── curl/          # Templates curl (legacy)
│   │   │   └── rest/          # Templates HTTP direct
│   │   ├── gemini/
│   │   └── claude/
│   └── configs/               # Configurations par défaut
└── 🧪 Tests/
    ├── unit/                  # Tests unitaires
    ├── integration/           # Tests intégration
    ├── encoding/             # Tests spécifiques encodage
    └── user/                 # Tests utilisateur automatisés
```

### **Design Patterns Formalisés**

#### **A. Repository Pattern**
```python
# Interface abstraction données
class ProfileRepository(ABC):
    @abstractmethod
    def get_all_profiles(self) -> List[Profile]: pass
    
    @abstractmethod  
    def save_profile(self, profile: Profile) -> bool: pass
    
    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Profile]: pass

# Implémentation JSON
class JSONProfileRepository(ProfileRepository):
    def __init__(self, encoding_service: EncodingService):
        self.encoding = encoding_service
```

#### **B. Factory Pattern + Strategy**
```python
# Factory providers LLM
class LLMProviderFactory:
    @staticmethod
    def create_provider(provider_type: str, method: str) -> LLMProvider:
        # Retourne CurlProvider, NativeProvider, RestProvider
        
# Strategy per method
class LLMProvider(ABC):
    @abstractmethod
    def send_request(self, prompt: str, config: Dict) -> LLMResponse: pass
```

#### **C. Plugin System**
```python
# Interface plugin
class LLMPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: pass
    
    @property  
    @abstractmethod
    def supported_methods(self) -> List[str]: pass  # ['native', 'curl', 'rest']
    
    @abstractmethod
    def get_template(self, method: str, template_type: str) -> Template: pass
```

---

## 🎯 **AXE 1 : SYSTÈME TEMPLATES ET TEST API AVANCÉ**

### **1.A. Architecture Templates Multi-Méthodes**

#### **Structure Templates par Provider**
```
📁 templates/
├── openai/
│   ├── native/
│   │   ├── chat_basic.py        # Template SDK basique
│   │   ├── chat_advanced.py     # Template avec paramètres fins
│   │   ├── chat_streaming.py    # Template streaming
│   │   └── chat_multimodal.py   # Template images (futur)
│   ├── curl/
│   │   ├── chat_basic.txt       # Template curl simple
│   │   ├── chat_advanced.txt    # Template curl paramètres fins
│   │   └── chat_batch.txt       # Template batch requests
│   └── rest/
│       ├── chat_requests.py     # Template requests HTTP
│       └── chat_async.py        # Template async HTTP
├── gemini/
├── claude/
└── [newllm]/                    # Template extensibilité
```

#### **Spécification Template Native (Exemple OpenAI)**
```python
# Template: templates/openai/native/chat_advanced.py
class OpenAIChatAdvancedTemplate:
    def __init__(self, config: OpenAIConfig):
        self.client = openai.OpenAI(api_key=config.api_key)
        self.config = config
    
    def execute(self, prompt: str, **kwargs) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=kwargs.get('model', 'gpt-4o-mini'),
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 1000),
            top_p=kwargs.get('top_p', 1.0),
            frequency_penalty=kwargs.get('frequency_penalty', 0),
            presence_penalty=kwargs.get('presence_penalty', 0),
            stream=kwargs.get('stream', False)
        )
        return self._parse_response(response)
```

#### **Configuration Template Versionnée**
```json
{
  "provider": "openai",
  "template_id": "chat_advanced",
  "method": "native",
  "version": "2.0",
  "model_versions": [
    "gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"
  ],
  "parameters": {
    "temperature": {
      "type": "float",
      "min": 0.0,
      "max": 2.0,
      "default": 0.7,
      "description_fr": "Créativité des réponses",
      "description_en": "Response creativity"
    },
    "max_tokens": {
      "type": "int", 
      "min": 1,
      "max": 4096,
      "default": 1000,
      "description_fr": "Longueur maximale réponse",
      "description_en": "Maximum response length"
    },
    "top_p": {
      "type": "float",
      "min": 0.0, 
      "max": 1.0,
      "default": 1.0,
      "description_fr": "Diversité vocabulaire",
      "description_en": "Vocabulary diversity"
    }
  },
  "capabilities": ["text", "json_mode"],
  "encoding": "utf-8",
  "validation_rules": {
    "prompt_max_length": 10000,
    "allowed_chars": "unicode_all"
  }
}
```

### **1.B. Interface Test API Enrichie**

#### **Formulaire Dynamique Setup API**
**Fonctionnalités cibles :**
- ✅ **Sélection Provider** : Dropdown avec providers disponibles
- ✅ **Sélection Méthode** : Native/Curl/Rest selon provider
- ✅ **Sélection Template** : Templates disponibles pour provider/méthode
- ✅ **Configuration Modèle** : Dropdown modèles supportés
- ✅ **Paramètres Avancés** : Formulaire dynamique selon template
- ✅ **Validation Temps Réel** : Validation paramètres + encodage
- ✅ **Prévisualisation** : Aperçu requête générée

#### **Interface Test API Avancée**
**Améliorations cibles :**
- ✅ **Zone Prompt Enrichie** : Support multi-ligne + compteur caractères
- ✅ **Validation Encodage** : Détection caractères problématiques
- ✅ **Historique Prompts** : Sauvegarde prompts récents
- ✅ **Réponse Formatée** : Syntax highlighting + export direct
- ✅ **Métriques Temps Réel** : Temps réponse, tokens utilisés, coût estimé
- ✅ **Mode Debug** : Affichage requête brute + headers

#### **Spécification Technique Interface**
```python
# Interface Setup API enrichie
class SetupAPIView:
    def __init__(self, i18n_service: I18nService, encoding_service: EncodingService):
        self.i18n = i18n_service
        self.encoding = encoding_service
        
    def create_dynamic_form(self, provider: str, template: str) -> tkinter.Frame:
        # Génération formulaire basé sur template config
        # Validation temps réel paramètres
        # Support caractères internationaux
        pass
        
    def validate_input(self, input_text: str) -> ValidationResult:
        # Validation encodage UTF-8
        # Détection caractères problématiques
        # Suggestions corrections
        pass
```

---

## 🌍 **AXE 2 : INTERNATIONALISATION ET UX ROBUSTE**

### **2.A. Système i18n Complet**

#### **Architecture Fichiers Langues**
```json
// Resources/i18n/fr.json
{
  "menus": {
    "setup_api": "Configuration API",
    "test_api": "Test API", 
    "setup_history": "Historique Configuration",
    "file_generation": "Génération Fichiers",
    "preferences": "Préférences"
  },
  "labels": {
    "provider": "Fournisseur LLM",
    "method": "Méthode de connexion",
    "template": "Template",
    "model": "Modèle",
    "prompt": "Prompt",
    "response": "Réponse"
  },
  "messages": {
    "api_success": "Requête API réussie",
    "api_error": "Erreur API : {error}",
    "encoding_warning": "Caractères spéciaux détectés : {chars}",
    "validation_error": "Erreur validation : {field}"
  },
  "tooltips": {
    "temperature": "Contrôle la créativité des réponses (0.0 = déterministe, 2.0 = très créatif)",
    "max_tokens": "Nombre maximum de tokens dans la réponse"
  }
}
```

#### **Service i18n Dynamique**
```python
class I18nService:
    def __init__(self):
        self.current_language = "fr"
        self.translations = {}
        self.observers = []  # Observer pattern pour changement langue
        
    def get_text(self, key: str, **kwargs) -> str:
        # Récupération texte avec interpolation variables
        # Fallback vers anglais si clé manquante
        # Log clés manquantes pour traduction
        pass
        
    def change_language(self, lang: str):
        # Changement langue + notification observers
        # Rechargement interface sans redémarrage
        pass
```

### **2.B. Robustesse Encodage Universelle**

#### **Service Encodage Centralisé**
```python
class EncodingService:
    def __init__(self):
        self.charset_normalizer = charset_normalizer
        
    def validate_and_normalize(self, text: str) -> EncodingResult:
        """Validation et normalisation texte utilisateur"""
        result = EncodingResult()
        
        # 1. Détection encodage automatique
        detected = self.charset_normalizer.from_bytes(text.encode())
        
        # 2. Normalisation Unicode
        normalized = unicodedata.normalize('NFC', text)
        
        # 3. Validation caractères problématiques
        problematic_chars = self._detect_problematic_chars(normalized)
        
        # 4. Suggestions corrections
        if problematic_chars:
            result.warnings = self._generate_warnings(problematic_chars)
            
        result.normalized_text = normalized
        result.is_valid = len(problematic_chars) == 0
        return result
        
    def _detect_problematic_chars(self, text: str) -> List[str]:
        # Détection émojis potentiellement problématiques
        # Caractères de contrôle
        # Caractères non-printables
        pass
```

#### **Tests Encodage Automatisés**
```python
# Tests/encoding/test_international_chars.py
class TestInternationalChars:
    TEST_CASES = [
        "Texte français avec accents àáâäçéèêë",
        "English text with special chars @#$%", 
        "中文测试文本",
        "العربية النص",
        "Русский текст",
        "Emoji test 🚀🎉💻🌍",
        "Mixed: Café 中文 🎯 @test#123",
        "Control chars: \t\n\r",
        "Unicode symbols: ©®™€£¥"
    ]
    
    def test_gui_input_handling(self):
        # Test saisie formulaires
        # Test affichage GUI
        # Test sauvegarde/chargement
        pass
```

---

## 🏗️ **AXE 3 : ARCHITECTURE PATTERNS ENTERPRISE**

### **3.A. Repository Pattern Implementation**

#### **Interface Repository Générique**
```python
from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic

T = TypeVar('T')

class Repository(Generic[T], ABC):
    @abstractmethod
    def get_all(self) -> List[T]: pass
    
    @abstractmethod
    def get_by_id(self, id: str) -> Optional[T]: pass
    
    @abstractmethod
    def save(self, entity: T) -> bool: pass
    
    @abstractmethod
    def delete(self, id: str) -> bool: pass
    
    @abstractmethod
    def exists(self, id: str) -> bool: pass
```

#### **Implémentations Concrètes**
```python
# Profils
class ProfileRepository(Repository[Profile]):
    def __init__(self, encoding_service: EncodingService):
        self.encoding = encoding_service
        self.profiles_dir = Path("profiles")
        
# Conversations
class ConversationRepository(Repository[Conversation]):
    def __init__(self, encoding_service: EncodingService):
        self.encoding = encoding_service
        self.conversations_dir = Path("conversations")
        
# Templates
class TemplateRepository(Repository[Template]):
    def __init__(self, encoding_service: EncodingService):
        self.encoding = encoding_service
        self.templates_dir = Path("templates")
```

### **3.B. Service Layer Architecture**

#### **Services Métier**
```python
# Service LLM unifié
class LLMService:
    def __init__(self, 
                 provider_factory: LLMProviderFactory,
                 template_repo: TemplateRepository,
                 encoding_service: EncodingService):
        self.factory = provider_factory
        self.templates = template_repo
        self.encoding = encoding_service
        
    def send_request(self, profile_name: str, prompt: str, **kwargs) -> LLMResponse:
        # 1. Validation encodage prompt
        # 2. Chargement profil + template
        # 3. Création provider approprié
        # 4. Exécution requête
        # 5. Parsing réponse unifiée
        pass

# Service Conversation
class ConversationService:
    def __init__(self, 
                 conversation_repo: ConversationRepository,
                 encoding_service: EncodingService):
        self.repo = conversation_repo
        self.encoding = encoding_service
        
    def add_exchange(self, conversation_id: str, prompt: str, response: str):
        # Ajout échange avec validation encodage
        # Déclenchement résumé si seuil atteint
        # Notification observers
        pass
```

### **3.C. Event-Driven Architecture**

#### **Système Événements**
```python
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class Event:
    type: str
    data: Dict[str, Any]
    timestamp: datetime

class EventBus:
    def __init__(self):
        self.handlers = defaultdict(list)
        
    def subscribe(self, event_type: str, handler: Callable):
        self.handlers[event_type].append(handler)
        
    def publish(self, event: Event):
        for handler in self.handlers[event.type]:
            handler(event)

# Événements spécifiques
@dataclass
class APIRequestEvent(Event):
    provider: str
    prompt: str
    response_time: float

@dataclass  
class EncodingWarningEvent(Event):
    text: str
    problematic_chars: List[str]
```

---

## 🧪 **AXE 4 : STRATÉGIE TESTS COMPLÈTE**

### **4.A. Tests Développeur Automatisés**

#### **Structure Tests**
```
📁 Tests/
├── unit/
│   ├── test_encoding_service.py      # Tests robustesse encodage
│   ├── test_llm_providers.py         # Tests providers individuels  
│   ├── test_template_parsing.py      # Tests parsing templates
│   ├── test_i18n_service.py          # Tests internationalisation
│   └── test_repositories.py          # Tests accès données
├── integration/
│   ├── test_api_workflows.py         # Tests workflows complets
│   ├── test_conversation_flows.py    # Tests gestion conversations
│   └── test_plugin_loading.py        # Tests système plugins
├── encoding/
│   ├── test_international_chars.py   # Tests caractères internationaux
│   ├── test_emoji_support.py         # Tests émojis et symboles
│   └── test_charset_detection.py     # Tests détection encodage
└── user/
    ├── test_gui_interactions.py      # Tests interface utilisateur
    ├── test_form_validation.py       # Tests validation formulaires
    └── test_error_handling.py        # Tests gestion erreurs
```

#### **Datasets Tests Internationaux**
```python
# Tests/encoding/datasets.py
INTERNATIONAL_TEST_CASES = {
    "french": [
        "Bonjour, comment allez-vous ?",
        "Café, crème, cœur, naïf",
        "L'hôtel coûte 50€ par nuit"
    ],
    "chinese": [
        "你好世界",
        "这是一个测试",
        "中文字符测试"
    ],
    "arabic": [
        "مرحبا بالعالم",
        "هذا اختبار",
        "النص العربي"
    ],
    "emoji": [
        "Hello 👋 World 🌍",
        "Test 🧪 Success ✅",
        "AI 🤖 Chat 💬 App 📱"
    ],
    "mixed": [
        "Café 中文 🎯 @test",
        "Hello العالم 🌍 €50",
        "Test àéç 测试 🚀 #hashtag"
    ]
}
```

### **4.B. Tests Utilisateurs Intégrés**

#### **Framework Feedback Utilisateur**
```python
class UserFeedbackCollector:
    def __init__(self, encoding_service: EncodingService):
        self.encoding = encoding_service
        
    def collect_encoding_issues(self, user_input: str, context: str):
        # Collecte problèmes encodage rapportés utilisateur
        # Analyse patterns erreurs fréquentes
        # Suggestions améliorations
        pass
        
    def collect_ui_feedback(self, screen: str, action: str, success: bool):
        # Collecte retours interface utilisateur
        # Analyse workflows problématiques
        # Métriques UX
        pass
```

#### **Tests A/B Interface**
```python
class ABTestingFramework:
    def __init__(self):
        self.variants = {}
        self.metrics = {}
        
    def test_form_layout(self, variant: str) -> Dict:
        # Test différentes organisations formulaires
        # Mesure taux completion
        # Mesure temps saisie
        # Détection erreurs utilisateur
        pass
```

---

## 🔌 **SYSTÈME PLUGINS ET EXTENSIBILITÉ**

### **Plugin Architecture LLM**

#### **Interface Plugin Standard**
```python
class LLMPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: pass
    
    @property
    @abstractmethod 
    def version(self) -> str: pass
    
    @property
    @abstractmethod
    def supported_methods(self) -> List[str]: pass  # ['native', 'curl', 'rest']
    
    @property
    @abstractmethod
    def supported_models(self) -> List[str]: pass
    
    @abstractmethod
    def get_template(self, method: str, template_type: str) -> Template: pass
    
    @abstractmethod
    def create_provider(self, method: str, config: Dict) -> LLMProvider: pass
    
    @abstractmethod
    def validate_config(self, config: Dict) -> ValidationResult: pass
```

#### **Plugin Discovery et Loading**
```python
class PluginManager:
    def __init__(self):
        self.plugins = {}
        self.plugin_dirs = ["Plugins/LLMProviders/"]
        
    def discover_plugins(self) -> List[LLMPlugin]:
        # Scan dossiers plugins
        # Chargement dynamique modules
        # Validation interfaces
        # Gestion dépendances
        pass
        
    def load_plugin(self, plugin_name: str) -> LLMPlugin:
        # Chargement plugin spécifique
        # Validation compatibilité
        # Initialisation configuration
        pass
```

### **Template Plugin Structure**

#### **Structure Plugin Type**
```
📁 Plugins/LLMProviders/NewLLMProvider/
├── __init__.py                  # Plugin entry point
├── plugin.py                    # Plugin implementation
├── config.json                  # Plugin configuration
├── templates/
│   ├── native/
│   │   ├── chat_basic.py       # Template SDK natif
│   │   └── chat_advanced.py
│   ├── curl/
│   │   ├── chat_basic.txt      # Template curl
│   │   └── chat_advanced.txt
│   └── rest/
│       └── chat_requests.py    # Template HTTP
├── tests/
│   ├── test_plugin.py          # Tests plugin
│   └── test_templates.py       # Tests templates
└── README.md                   # Documentation plugin
```

#### **Configuration Plugin**
```json
{
  "plugin": {
    "name": "NewLLMProvider",
    "version": "1.0.0",
    "description": "Support for NewLLM API",
    "author": "Developer Name",
    "compatible_versions": ["2.0.0+"]
  },
  "provider": {
    "base_url": "https://api.newllm.com",
    "auth_type": "bearer",
    "models": [
      "newllm-base",
      "newllm-advanced", 
      "newllm-pro"
    ],
    "methods": ["native", "curl", "rest"],
    "capabilities": ["text", "streaming"],
    "rate_limits": {
      "requests_per_minute": 60,
      "tokens_per_minute": 10000
    }
  },
  "dependencies": {
    "python": ">=3.8",
    "packages": ["newllm-sdk>=1.0.0"]
  }
}
```

---

## 📊 **SPÉCIFICATIONS TECHNIQUES DÉTAILLÉES**

### **Configuration Globale Application**

#### **Structure Configuration V2**
```json
{
  "application": {
    "version": "2.0.0",
    "language": "fr",
    "encoding": "utf-8", 
    "theme": "default",
    "log_level": "INFO"
  },
  "plugins": {
    "enabled": true,
    "auto_discovery": true,
    "plugin_dirs": ["Plugins/"],
    "trusted_sources": ["official", "verified"]
  },
  "api": {
    "timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 1.0,
    "max_prompt_length": 10000,
    "encoding_validation": true
  },
  "ui": {
    "auto_save": true,
    "auto_save_interval": 300,
    "max_history_entries": 100,
    "form_validation": "realtime"
  },
  "encoding": {
    "strict_validation": false,
    "normalize_unicode": true,
    "warn_problematic_chars": true,
    "charset_fallback": "utf-8"
  }
}
```

### **Base de Données / Persistence**

#### **Schema Profils V2**
```json
{
  "profile": {
    "id": "unique_id",
    "name": "Profile Name",
    "provider": "openai",
    "method": "native",
    "template": "chat_advanced",
    "created_at": "2025-07-30T10:00:00Z",
    "updated_at": "2025-07-30T10:00:00Z",
    "version": "2.0"
  },
  "config": {
    "model": "gpt-4o-mini",
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 1000,
      "top_p": 1.0
    },
    "api_key": "encrypted_key",
    "custom_headers": {}
  },
  "preferences": {
    "default_profile": false,
    "auto_summary": true,
    "export_format": "markdown",
    "language": "fr"
  },
  "metadata": {
    "usage_count": 0,
    "last_used": "2025-07-30T10:00:00Z",
    "success_rate": 1.0,
    "avg_response_time": 2.5
  }
}
```

### **Sécurité et Validation**

#### **Validation Règles**
```python
VALIDATION_RULES = {
    "prompt": {
        "max_length": 10000,
        "min_length": 1,
        "allowed_chars": "unicode_printable",
        "forbidden_patterns": [
            r"<script.*?>.*?</script>",  # XSS basique
            r"javascript:",              # JavaScript URLs
            r"data:.*base64"            # Data URLs suspectes
        ]
    },
    "api_key": {
        "min_length": 10,
        "pattern": r"^[a-zA-Z0-9\-_\.]+$",
        "encryption": "required"
    },
    "config_values": {
        "temperature": {"min": 0.0, "max": 2.0},
        "max_tokens": {"min": 1, "max": 100000},
        "top_p": {"min": 0.0, "max": 1.0}
    }
}
```

---

## 🚀 **ROADMAP ET PRIORISATION**

### **Phase 1 : Fondations Robustes (6-8 semaines)**
**Priorité : CRITIQUE**

#### **Sprint 1-2 : Architecture Core**
- ✅ Refactoring architecture Repository Pattern
- ✅ Implémentation Service Layer
- ✅ Système Event-Driven basique
- ✅ Service Encodage centralisé

#### **Sprint 3-4 : Templates Multi-Méthodes**
- ✅ Migration templates curl vers structure plugin
- ✅ Implémentation templates native OpenAI/Gemini
- ✅ Factory Pattern pour providers LLM
- ✅ Validation templates + tests

#### **Sprint 5-6 : Interface Enrichie**
- ✅ Formulaires dynamiques Setup API
- ✅ Interface Test API avancée
- ✅ Validation temps réel + encodage
- ✅ Métriques et debugging

### **Phase 2 : Internationalisation (4-6 semaines)**
**Priorité : ÉLEVÉE**

#### **Sprint 7-8 : i18n Infrastructure**
- ✅ Service i18n + fichiers langues
- ✅ Traduction complète FR/EN
- ✅ Observer Pattern changement langue
- ✅ Tests encodage international

#### **Sprint 9-10 : UX Consolidée**
- ✅ Révision nomenclature + cohérence
- ✅ Validation formulaires robuste
- ✅ Gestion erreurs internationalisée
- ✅ Tests utilisateur A/B

### **Phase 3 : Extensions et Plugins (4-8 semaines)**
**Priorité : MOYENNE**

#### **Sprint 11-12 : Plugin System**
- ✅ Plugin Manager + discovery
- ✅ Interface plugin standardisée
- ✅ Migration providers existants
- ✅ Documentation développeur plugins

#### **Sprint 13-14 : Nouveaux LLM (selon besoins)**
- ✅ Intégration nouveaux providers
- ✅ Templates spécifiques
- ✅ Tests + validation
- ✅ Documentation utilisateur

### **Phase 4 : Tests et Qualité (2-4 semaines)**
**Priorité : ÉLEVÉE**

#### **Sprint 15-16 : Tests Complets**
- ✅ Tests unitaires + intégration
- ✅ Tests encodage automatisés
- ✅ Framework feedback utilisateur
- ✅ Métriques qualité + performance

---

## 📋 **CRITÈRES D'ACCEPTATION**

### **Fonctionnels**
- ✅ **Compatibilité V1** : Toutes fonctionnalités V1 préservées
- ✅ **Multi-méthodes** : Native + Curl + Rest fonctionnels
- ✅ **i18n complète** : FR/EN sans redémarrage
- ✅ **Robustesse encodage** : Support caractères internationaux
- ✅ **Interface enrichie** : Formulaires dynamiques + validation
- ✅ **Plugin system** : Nouveaux LLM intégrables facilement

### **Techniques** 
- ✅ **Architecture patterns** : Repository, Factory, Strategy, Observer
- ✅ **Tests coverage** : >80% code coverage
- ✅ **Performance** : Temps démarrage <3s, API calls <5s
- ✅ **Sécurité** : Validation entrées + encryption clés API
- ✅ **Documentation** : Code documenté + guides utilisateur/développeur

### **Qualité**
- ✅ **Encodage universel** : Aucune corruption caractères
- ✅ **Gestion erreurs** : Messages clairs + récupération gracieuse
- ✅ **UX cohérente** : Terminologie uniforme + navigation intuitive
- ✅ **Extensibilité** : Nouveaux LLM ajoutables sans modification core
- ✅ **Maintenance** : Code modulaire + logs détaillés

---

## 🎯 **PRÉPARATION INTÉGRATION NOUVEAUX LLM**

### **Analyse Besoins Templates**

En préparation de l'intégration de nouveaux LLM, l'architecture V2 doit supporter :

#### **A. Diversité Providers**
- **APIs REST variées** : Endpoints, authentification, formats différents
- **SDKs natifs** : Bibliothèques officielles spécifiques
- **Paramètres uniques** : Chaque LLM a ses paramètres spécifiques
- **Formats réponses** : Structures JSON variables selon provider

#### **B. Types Templates Multiples par LLM**
```
📁 NewLLMProvider/
├── templates/
│   ├── native/
│   │   ├── chat_basic.py           # Chat simple
│   │   ├── chat_advanced.py        # Paramètres fins
│   │   ├── chat_streaming.py       # Streaming responses
│   │   ├── completion_basic.py     # Text completion
│   │   ├── embedding.py            # Embeddings (si supporté)
│   │   └── multimodal.py           # Images/documents (si supporté)
│   ├── curl/
│   │   ├── chat_basic.txt
│   │   ├── chat_advanced.txt
│   │   └── batch_requests.txt      # Requêtes batch
│   └── rest/
│       ├── async_requests.py       # Requêtes asynchrones
│       └── webhook_callback.py     # Callbacks webhooks
```

#### **C. Interface Test API Adaptative**
L'interface Test API V2 devra s'adapter dynamiquement aux capacités de chaque LLM :

```python
class AdaptiveTestAPIInterface:
    def render_form_for_provider(self, provider: str, template: str):
        # Génération formulaire basé sur capabilities provider
        # Affichage paramètres spécifiques disponibles
        # Validation selon règles provider
        pass
        
    def get_available_methods(self, provider: str) -> List[str]:
        # Retourne méthodes supportées: ['native', 'curl', 'rest']
        # Selon disponibilité SDK + configuration
        pass
```

### **Questions Architecturales Clés**

1. **Standardisation Templates** : Comment unifier les templates tout en préservant spécificités ?
2. **Méthodes Privilégiées** : Native vs Curl - quelle priorité pour nouveaux LLM ?
3. **Validation Dynamique** : Comment valider paramètres variables selon provider ?
4. **Gestion Erreurs** : Comment unifier codes erreur disparates ?
5. **Performance** : Comment optimiser chargement plugins nombreux ?

Ces questions seront adressées lors de l'analyse des nouveaux LLM à intégrer.

---

**🎯 STATUT : Cahier des charges V2.0 détaillé - Prêt pour validation et développement**

**📅 Document créé :** 30 Juillet 2025  
**👨‍💻 Destinataire :** Équipe développement pour reprise projet sans connaissance préalable  
**🎪 Phase suivante :** Analyse nouveaux LLM + spécifications templates détaillées
