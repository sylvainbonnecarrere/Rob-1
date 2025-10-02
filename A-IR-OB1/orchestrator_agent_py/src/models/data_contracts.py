"""
Modèles de données (Data Contracts) pour l'Orchestrator Agent.

Ce module définit les structures de données fondamentales utilisant Pydantic V2
pour assurer un typage strict et une validation robuste. Ces modèles constituent
le contrat d'interface entre tous les composants de l'application.

Conformité aux principes SOLID :
- SRP : Chaque classe a une responsabilité unique
- OCP : Extensible sans modification (héritage, composition)
- ISP : Interfaces spécifiques et cohérentes
- DIP : Abstraction via des contrats de données clairs
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class ToolCall(BaseModel):
    """
    Représente une demande d'exécution d'outil par un LLM.
    
    Cette structure capture l'intention du LLM d'utiliser un outil spécifique
    avec des arguments définis. Elle sert d'interface standardisée entre
    le moteur d'orchestration et le système d'exécution d'outils.
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    
    tool_name: str = Field(
        ...,
        description="Nom de l'outil à exécuter",
        min_length=1,
        max_length=100
    )
    
    args: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments à passer à l'outil sous forme de dictionnaire"
    )
    
    call_id: Optional[str] = Field(
        default=None,
        description="Identifiant unique de l'appel d'outil (généré par le LLM)"
    )


class ChatMessage(BaseModel):
    """
    Représente un message dans l'historique de conversation.
    
    Structure unifiée pour tous les types de messages : utilisateur, assistant,
    système, et réponses d'outils. Permet de maintenir un historique cohérent
    et de gérer les différents acteurs de la conversation.
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    
    role: Literal["user", "assistant", "system", "tool"] = Field(
        ...,
        description="Rôle de l'expéditeur du message"
    )
    
    content: str = Field(
        ...,
        description="Contenu textuel du message",
        min_length=1
    )
    
    tool_calls: Optional[List[ToolCall]] = Field(
        default=None,
        description="Liste des appels d'outils demandés par l'assistant"
    )
    
    tool_call_id: Optional[str] = Field(
        default=None,
        description="ID de l'appel d'outil (pour les messages de type 'tool')"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Métadonnées additionnelles (timestamps, token counts, etc.)"
    )


class AgentConfig(BaseModel):
    """
    Configuration d'un prototype d'agent IA.
    
    Définit les paramètres de comportement d'un agent : le fournisseur LLM,
    le modèle à utiliser, le prompt système, et les outils disponibles.
    Cette configuration permet de créer des agents spécialisés réutilisables.
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    
    agent_id: str = Field(
        ...,
        description="Identifiant unique de l'agent",
        min_length=1,
        max_length=50
    )
    
    provider: Literal["openai", "anthropic", "gemini"] = Field(
        ...,
        description="Fournisseur de service LLM"
    )
    
    model: str = Field(
        ...,
        description="Nom/ID du modèle spécifique à utiliser",
        min_length=1,
        max_length=100
    )
    
    system_prompt: str = Field(
        ...,
        description="Prompt système définissant le comportement de l'agent",
        min_length=10,
        max_length=10000
    )
    
    tools: List[str] = Field(
        default_factory=list,
        description="Liste des noms d'outils disponibles pour cet agent"
    )
    
    temperature: Optional[float] = Field(
        default=0.7,
        description="Paramètre de créativité (0.0 = déterministe, 1.0 = créatif)",
        ge=0.0,
        le=2.0
    )
    
    max_tokens: Optional[int] = Field(
        default=1000,
        description="Nombre maximum de tokens dans la réponse",
        gt=0,
        le=32000
    )
    
    supports_multimodal: bool = Field(
        default=False,
        description="Indique si l'agent supporte les entrées multimodales (images)"
    )


class OrchestrationRequest(BaseModel):
    """
    Modèle d'entrée pour le service d'orchestration.
    
    Encapsule une demande complète d'orchestration incluant la configuration
    de l'agent à utiliser et l'historique de conversation existant.
    Point d'entrée standardisé pour l'API d'orchestration.
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    
    agent_config: AgentConfig = Field(
        ...,
        description="Configuration de l'agent à utiliser pour cette requête"
    )
    
    history: List[ChatMessage] = Field(
        default_factory=list,
        description="Historique de conversation existant"
    )
    
    new_message: str = Field(
        ...,
        description="Nouveau message de l'utilisateur à traiter",
        min_length=1,
        max_length=50000
    )
    
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Contexte additionnel pour l'orchestration"
    )


class OrchestrationResponse(BaseModel):
    """
    Modèle de sortie du service d'orchestration.
    
    Contient la réponse de l'agent ainsi que l'historique mis à jour
    et les métadonnées de l'exécution.
    """
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
    
    response_message: ChatMessage = Field(
        ...,
        description="Message de réponse généré par l'agent"
    )
    
    updated_history: List[ChatMessage] = Field(
        ...,
        description="Historique complet mis à jour avec les nouveaux messages"
    )
    
    execution_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Métadonnées de l'exécution (durée, tokens utilisés, etc.)"
    )
    
    tools_executed: List[str] = Field(
        default_factory=list,
        description="Liste des outils qui ont été exécutés pendant cette orchestration"
    )