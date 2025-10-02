"""
Interface abstraite pour les services LLM (Large Language Models).

Ce module définit le contrat (Port) que tous les adaptateurs LLM doivent implémenter
selon l'architecture hexagonale. Cette interface assure l'interchangeabilité des
fournisseurs LLM (OpenAI, Anthropic, Gemini) tout en maintenant un contrat unifié.

Principes SOLID appliqués :
- DIP (Dependency Inversion Principle) : Le code métier dépend de l'abstraction, 
  pas des implémentations concrètes
- ISP (Interface Segregation Principle) : Interface cohérente et spécialisée
- OCP (Open/Closed Principle) : Extensible par ajout de nouveaux adaptateurs
- SRP (Single Responsibility Principle) : Responsabilité unique = contrat LLM

Architecture Hexagonale :
- Ce fichier définit un 'Port' (interface) du côté domain
- Les implémentations concrètes seront des 'Adapters' dans infrastructure/
"""

from abc import ABC, abstractmethod
from typing import List, Any

# Import conditionnel pour éviter les erreurs d'import relatif lors des tests
try:
    from ..models.data_contracts import AgentConfig, ChatMessage, OrchestrationResponse
except ImportError:
    # Fallback pour les tests et imports directs
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent
    sys.path.insert(0, str(src_path))
    from models.data_contracts import AgentConfig, ChatMessage, OrchestrationResponse


class LLMService(ABC):
    """
    Interface abstraite définissant le contrat pour tous les services LLM.
    
    Cette interface garantit que tous les adaptateurs LLM (Gemini, OpenAI, Anthropic)
    exposent les mêmes méthodes avec la même signature, permettant l'interchangeabilité
    des fournisseurs sans modification du code métier.
    
    Toutes les méthodes sont asynchrones pour optimiser les performances des
    appels I/O vers les APIs externes.
    """

    @abstractmethod
    async def chat_completion(
        self, 
        config: AgentConfig, 
        history: List[ChatMessage]
    ) -> OrchestrationResponse:
        """
        Effectue une conversation avec le LLM configuré.
        
        Cette méthode centrale gère le flux de conversation principal en envoyant
        l'historique et la configuration à l'API LLM, puis retourne une réponse
        structurée incluant la nouvelle réponse et l'historique mis à jour.
        
        Args:
            config: Configuration de l'agent (modèle, prompt système, outils, etc.)
            history: Historique complet de la conversation jusqu'à présent
            
        Returns:
            OrchestrationResponse: Réponse structurée avec le message généré,
            l'historique mis à jour et les métadonnées d'exécution
            
        Raises:
            LLMServiceError: En cas d'erreur de communication avec l'API
            ValidationError: Si les paramètres d'entrée sont invalides
        """
        pass

    @abstractmethod
    async def get_supported_tools(self) -> List[str]:
        """
        Retourne la liste des outils supportés par ce fournisseur LLM.
        
        Chaque fournisseur peut avoir des capacités différentes en termes
        d'exécution d'outils (Function Calling). Cette méthode permet de
        connaître les limitations et d'adapter la configuration des agents.
        
        Returns:
            List[str]: Liste des noms d'outils que ce LLM peut gérer
            
        Examples:
            >>> service = GeminiAdapter()
            >>> tools = await service.get_supported_tools()
            >>> print(tools)
            ['web_search', 'code_execution', 'image_analysis']
        """
        pass

    @abstractmethod
    async def get_model_name(self) -> str:
        """
        Retourne le nom exact du modèle LLM utilisé par cet adaptateur.
        
        Utile pour le logging, le monitoring, et la traçabilité des réponses.
        Permet également de vérifier quelle version de modèle est effectivement
        utilisée par l'adaptateur.
        
        Returns:
            str: Nom complet et précis du modèle (ex: "gpt-4-turbo-preview",
            "claude-3-sonnet-20240229", "gemini-1.5-pro-latest")
            
        Examples:
            >>> service = OpenAIAdapter(model="gpt-4-turbo")
            >>> model = await service.get_model_name()
            >>> print(model)
            "gpt-4-turbo-preview"
        """
        pass

    @abstractmethod
    async def format_tools_for_llm(self, tool_names: List[str]) -> Any:
        """
        Convertit une liste d'outils internes vers le format requis par l'API LLM.
        
        Chaque fournisseur LLM a son propre format pour décrire les outils disponibles
        (OpenAI utilise 'tools', Anthropic utilise 'tools', Gemini utilise 'function_declarations').
        Cette méthode effectue la transformation appropriée.
        
        Args:
            tool_names: Liste des noms d'outils internes à convertir
            
        Returns:
            Any: Structure de données formatée selon l'API du fournisseur.
            Le type exact dépend du fournisseur :
            - OpenAI: List[Dict] avec clés 'type' et 'function'
            - Anthropic: List[Dict] avec schéma spécifique
            - Gemini: Dict avec 'function_declarations'
            
        Examples:
            >>> service = OpenAIAdapter()
            >>> formatted = await service.format_tools_for_llm(['web_search'])
            >>> print(formatted)
            [{'type': 'function', 'function': {'name': 'web_search', ...}}]
        """
        pass

    # Méthodes additionnelles pour l'évolutivité future
    
    async def health_check(self) -> bool:
        """
        Vérifie la disponibilité du service LLM.
        
        Implémentation par défaut qui peut être surchargée par les adaptateurs
        pour effectuer un test de connectivité spécifique.
        
        Returns:
            bool: True si le service est accessible, False sinon
        """
        return True
    
    async def get_usage_stats(self) -> dict:
        """
        Retourne les statistiques d'utilisation du service.
        
        Implémentation par défaut qui peut être surchargée pour fournir
        des métriques spécifiques au fournisseur (tokens consommés, coût, etc.).
        
        Returns:
            dict: Dictionnaire avec les statistiques d'usage
        """
        return {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0
        }