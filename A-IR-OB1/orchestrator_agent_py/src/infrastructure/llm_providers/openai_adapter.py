"""
Adaptateur OpenAI pour l'interface LLMService.

Ce module implémente l'adaptateur concret pour l'API OpenAI, respectant
le contrat défini par LLMService. Il gère la conversion des modèles de données
internes vers le format attendu par l'API OpenAI et vice versa.

Architecture Hexagonale :
- Ceci est un 'Adapter' (côté infrastructure) qui implémente le 'Port' LLMService
- Isole la logique métier des spécificités de l'API OpenAI

Conformité SOLID :
- SRP : Responsabilité unique = adaptateur OpenAI
- OCP : Extension sans modification de l'interface
- DIP : Dépendance vers l'abstraction LLMService
"""

import os
from typing import List, Any, Dict
from openai import AsyncOpenAI

# Import conditionnel pour éviter les erreurs d'import relatif
try:
    from ...domain.llm_service_interface import LLMService
    from ...models.data_contracts import AgentConfig, ChatMessage, OrchestrationResponse, ToolCall
except ImportError:
    # Fallback pour les tests et imports directs
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(src_path))
    from domain.llm_service_interface import LLMService
    from models.data_contracts import AgentConfig, ChatMessage, OrchestrationResponse, ToolCall


class OpenAIAdapter(LLMService):
    """
    Adaptateur pour les services OpenAI (GPT-3.5, GPT-4, etc.).
    
    Cette classe implémente l'interface LLMService pour permettre l'utilisation
    des modèles OpenAI dans l'écosystème d'orchestration d'agents.
    
    Attributes:
        client: Client asynchrone OpenAI pour les appels API
        model: Nom du modèle OpenAI à utiliser
        api_key: Clé API OpenAI (récupérée depuis les variables d'environnement)
    """
    
    def __init__(self, model: str = "gpt-3.5-turbo", api_key: str = None):
        """
        Initialise l'adaptateur OpenAI.
        
        Args:
            model: Nom du modèle OpenAI à utiliser (par défaut: gpt-3.5-turbo)
            api_key: Clé API OpenAI. Si None, sera récupérée depuis OPENAI_API_KEY
            
        Raises:
            ValueError: Si la clé API n'est pas fournie et n'existe pas dans l'environnement
        """
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Clé API OpenAI manquante. "
                "Fournissez-la via le paramètre api_key ou la variable d'environnement OPENAI_API_KEY"
            )
        
        # Initialisation du client asynchrone OpenAI
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def get_model_name(self) -> str:
        """
        Retourne le nom du modèle OpenAI configuré.
        
        Returns:
            str: Nom du modèle (ex: "gpt-3.5-turbo", "gpt-4-turbo-preview")
        """
        return self.model
    
    async def get_supported_tools(self) -> List[str]:
        """
        Retourne la liste des outils supportés par ce fournisseur OpenAI.
        
        Pour ce jalon, retourne une liste d'outils de démonstration.
        L'implémentation complète sera faite dans les jalons suivants.
        
        Returns:
            List[str]: Liste des noms d'outils supportés
        """
        # Pour le Jalon 2.1, on retourne des outils factices
        # L'implémentation complète viendra au Jalon 2.3
        return ["get_time", "web_search", "calculate"]
    
    async def format_tools_for_llm(self, tool_names: List[str]) -> Any:
        """
        Formate les outils dans le format requis par l'API OpenAI.
        
        Pour ce jalon, retourne None car la gestion complète des outils
        sera implémentée au Jalon 2.3.
        
        Args:
            tool_names: Liste des noms d'outils à formater
            
        Returns:
            None: Implémentation placeholder pour ce jalon
        """
        # Implémentation placeholder pour le Jalon 2.1
        # L'implémentation complète viendra au Jalon 2.3
        return None
    
    async def chat_completion(
        self, 
        config: AgentConfig, 
        history: List[ChatMessage]
    ) -> OrchestrationResponse:
        """
        Effectue un appel de completion de chat avec l'API OpenAI.
        
        Cette méthode convertit notre format interne vers le format OpenAI,
        effectue l'appel API, puis convertit la réponse vers notre format.
        
        Args:
            config: Configuration de l'agent (prompt système, modèle, etc.)
            history: Historique de conversation existant
            
        Returns:
            OrchestrationResponse: Réponse structurée avec le message généré
            
        Raises:
            Exception: En cas d'erreur avec l'API OpenAI
        """
        try:
            # Conversion de l'historique vers le format OpenAI
            messages = self._convert_history_to_openai_format(config, history)
            
            # Appel asynchrone à l'API OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=config.temperature or 0.7,
                max_tokens=config.max_tokens or 1000
            )
            
            # Extraction de la réponse
            choice = response.choices[0]
            message = choice.message
            
            # Conversion vers notre format interne
            response_message = self._convert_openai_response_to_chat_message(message)
            
            # Mise à jour de l'historique
            updated_history = history.copy()
            updated_history.append(response_message)
            
            # Métadonnées d'exécution
            execution_metadata = {
                "model_used": self.model,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "finish_reason": choice.finish_reason
            }
            
            # Construction de la réponse d'orchestration
            return OrchestrationResponse(
                response_message=response_message,
                updated_history=updated_history,
                execution_metadata=execution_metadata,
                tools_executed=[]  # Pas d'outils exécutés dans ce jalon
            )
            
        except Exception as e:
            # Gestion d'erreur simplifiée pour ce jalon
            raise Exception(f"Erreur lors de l'appel à l'API OpenAI: {str(e)}")
    
    def _convert_history_to_openai_format(
        self, 
        config: AgentConfig, 
        history: List[ChatMessage]
    ) -> List[Dict[str, str]]:
        """
        Convertit l'historique interne vers le format de messages OpenAI.
        
        Args:
            config: Configuration de l'agent (pour le prompt système)
            history: Historique de conversation interne
            
        Returns:
            List[Dict[str, str]]: Messages formatés pour l'API OpenAI
        """
        messages = []
        
        # Ajout du prompt système en premier
        if config.system_prompt:
            messages.append({
                "role": "system",
                "content": config.system_prompt
            })
        
        # Conversion des messages de l'historique
        for msg in history:
            # Mapping des rôles (notre format -> OpenAI)
            openai_role = msg.role
            if msg.role == "tool":
                # Les réponses d'outils sont traitées différemment
                # Pour ce jalon, on les convertit en messages utilisateur
                openai_role = "user"
            
            openai_message = {
                "role": openai_role,
                "content": msg.content
            }
            
            # Gestion des tool_calls (sera complétée au Jalon 2.3)
            if msg.tool_calls and msg.role == "assistant":
                # Pour ce jalon, on ignore les tool_calls
                # L'implémentation complète viendra au Jalon 2.3
                pass
            
            messages.append(openai_message)
        
        return messages
    
    def _convert_openai_response_to_chat_message(self, openai_message) -> ChatMessage:
        """
        Convertit une réponse OpenAI vers notre format ChatMessage.
        
        Args:
            openai_message: Message de réponse de l'API OpenAI
            
        Returns:
            ChatMessage: Message converti vers notre format interne
        """
        # Gestion des tool calls (sera complétée au Jalon 2.3)
        tool_calls = None
        if hasattr(openai_message, 'tool_calls') and openai_message.tool_calls:
            # Pour ce jalon, on va créer des ToolCall basiques
            tool_calls = []
            for tool_call in openai_message.tool_calls:
                tool_calls.append(ToolCall(
                    tool_name=tool_call.function.name,
                    args=eval(tool_call.function.arguments) if tool_call.function.arguments else {},
                    call_id=tool_call.id
                ))
        
        return ChatMessage(
            role="assistant",
            content=openai_message.content or "",
            tool_calls=tool_calls,
            metadata={
                "source": "openai",
                "model": self.model
            }
        )