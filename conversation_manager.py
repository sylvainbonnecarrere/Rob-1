"""
ConversationManager - Gestionnaire intelligent d'historique avec résumé contextuel
Version intégrée avec ConfigManager et indicateurs visuels
Remplace la concaténation simple par une gestion intelligente des conversations
Support tiktoken pour comptage précis des tokens
"""

import json
import logging
import re
import unicodedata
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logging.warning("tiktoken non disponible - comptage tokens désactivé")

class ConversationManager:
    """
    Gestionnaire de conversation avec résumé contextuel automatique
    Évite la saturation des tokens en résumant l'historique long
    """
    
    def __init__(self, config_manager=None, profile_config: Dict[str, Any] = None, api_type: str = None):
        """
        Initialise le gestionnaire de conversation
        
        Args:
            config_manager: Instance du ConfigManager pour les templates
            profile_config: Configuration du profil (section conversation)
            api_type: Type d'API (gemini, claude, openai) pour configurations spécifiques
        """
        # Configurations par défaut selon l'API
        self.api_specific_defaults = {
            "gemini": {
                "summary_enabled": True,
                "summary_threshold": {"words": 400, "sentences": 8},  # Gemini supporte plus de contexte
                "summary_template_id": "gemini_summary",
                "show_indicators": True
            },
            "claude": {
                "summary_enabled": True,
                "summary_threshold": {"words": 350, "sentences": 7},  # Claude bon équilibre
                "summary_template_id": "claude_summary",
                "show_indicators": True
            },
            "openai": {
                "summary_enabled": True,
                "summary_threshold": {"words": 250, "sentences": 5},  # OpenAI plus conservateur
                "summary_template_id": "openai_summary",
                "show_indicators": True
            },
            "default": {
                "summary_enabled": True,
                "summary_threshold": {"words": 300, "sentences": 6},
                "summary_template_id": "default_summary",
                "show_indicators": True
            }
        }
        
        # Déterminer l'API à utiliser pour les défauts
        self.api_type = api_type.lower() if api_type else "default"
        if self.api_type not in self.api_specific_defaults:
            self.api_type = "default"
        
        # Configuration par défaut selon l'API
        self.default_config = self.api_specific_defaults[self.api_type]
        
        # Utiliser la config du profil ou les valeurs par défaut spécifiques à l'API
        self.config = profile_config if profile_config else self.default_config
        self.config_manager = config_manager
        
        # Nouvelle gestion des seuils avec structure étendue
        self.intelligent_management = self._get_config_value("intelligent_management", True)
        
        # Configuration des seuils selon la nouvelle structure
        if self.intelligent_management and "summary_thresholds" in self.config:
            # Nouvelle structure avec seuils configurables
            thresholds = self.config["summary_thresholds"]
            self.words_threshold = thresholds.get("words", {}).get("value", self.default_config["summary_threshold"]["words"])
            self.sentences_threshold = thresholds.get("sentences", {}).get("value", self.default_config["summary_threshold"]["sentences"])
            self.tokens_threshold = thresholds.get("tokens", {}).get("value", 1200)
            
            # Seuils activés/désactivés
            self.words_enabled = thresholds.get("words", {}).get("enabled", True)
            self.sentences_enabled = thresholds.get("sentences", {}).get("enabled", True)
            self.tokens_enabled = thresholds.get("tokens", {}).get("enabled", False)
        else:
            # Fallback vers ancienne structure ou valeurs par défaut
            # CORRECTION: Gérer les formats de configuration multiples
            
            # 1. Vérifier directement dans le profil s'il y a summary_threshold
            old_threshold = self.config.get("summary_threshold", None) if self.config else None
            
            # 2. Si pas trouvé, essayer les clés individuelles du fichier JSON
            if old_threshold is None:
                words_val = self._get_config_value("word_threshold", self.default_config["summary_threshold"]["words"])
                sentences_val = self._get_config_value("sentence_threshold", self.default_config["summary_threshold"]["sentences"])
                tokens_val = self._get_config_value("token_threshold", 1200)
                
                self.words_threshold = words_val
                self.sentences_threshold = sentences_val
                self.tokens_threshold = tokens_val
                
                # Utiliser les clés enabled si disponibles, sinon valeurs par défaut
                self.words_enabled = self._get_config_value("words_enabled", True)
                self.sentences_enabled = self._get_config_value("sentences_enabled", True)
                self.tokens_enabled = self._get_config_value("tokens_enabled", False)
                
            else:
                # 3. Utiliser l'ancienne structure si trouvée
                self.words_threshold = old_threshold.get("words", self.default_config["summary_threshold"]["words"])
                self.sentences_threshold = old_threshold.get("sentences", self.default_config["summary_threshold"]["sentences"])
                self.tokens_threshold = 1200
                
                # Par défaut, mots et phrases activés
                self.words_enabled = True
                self.sentences_enabled = True
                self.tokens_enabled = False
        
        self.show_indicators = self._get_config_value("show_indicators", self.default_config["show_indicators"])
        self.template_id = self._get_config_value("summary_template_id", self.default_config["summary_template_id"])
        
        # Instructions personnalisées pour le résumé
        self.custom_instructions = self._get_config_value("custom_instructions", "")
        
        # Initialisation tiktoken pour comptage des tokens
        self.token_encoder = self._get_token_encoder()
        
        # État de la conversation
        self.conversation_history: List[Dict[str, str]] = []
        self.current_summary: Optional[str] = None
        self.summary_count = 0
        self.logger = logging.getLogger(__name__)
        
        tokens_info = f" / {self.tokens_threshold} tokens" if self.tokens_enabled else ""
        self.logger.info(f"ConversationManager initialisé pour API '{self.api_type}' - Seuils: {self.words_threshold} mots / {self.sentences_threshold} phrases{tokens_info}")
    
    def _get_config_value(self, key: str, default_value: Any) -> Any:
        """
        Récupère une valeur de configuration avec fallback intelligent
        1. Valeur du profil utilisateur
        2. Valeur par défaut de l'API
        3. Valeur par défaut générale
        """
        # Essayer d'abord la config du profil
        if self.config and key in self.config:
            return self.config[key]
        
        # Ensuite la config par défaut de l'API
        if key in self.default_config:
            return self.default_config[key]
        
        # Enfin la valeur par défaut fournie
        return default_value
    
    def _get_token_encoder(self):
        """
        Retourne l'encodeur tiktoken approprié selon l'API
        """
        if not TIKTOKEN_AVAILABLE:
            return None
        
        # Encodeurs selon l'API
        encoders = {
            "openai": "cl100k_base",    # GPT-4, ChatGPT
            "claude": "cl100k_base",    # Approximation pour Claude
            "gemini": "cl100k_base",    # Approximation pour Gemini
            "default": "cl100k_base"
        }
        
        try:
            encoding_name = encoders.get(self.api_type, "cl100k_base")
            return tiktoken.get_encoding(encoding_name)
        except Exception as e:
            self.logger.warning(f"Erreur initialisation tiktoken: {e}")
            return None
    
    def _count_tokens(self, text: str) -> int:
        """
        Compte les tokens dans le texte avec tiktoken
        """
        if not self.token_encoder or not text:
            return 0
        
        try:
            return len(self.token_encoder.encode(text))
        except Exception as e:
            self.logger.warning(f"Erreur comptage tokens: {e}")
            return 0
    
    def escape_for_json(self, text: str) -> str:
        """
        Échappe un texte de manière définitive pour injection JSON sécurisée.
        Cette fonction doit être appelée lors de l'enregistrement dans l'historique,
        pas au moment de la requête.
        
        Args:
            text: Texte à échapper pour JSON
            
        Returns:
            Texte complètement échappé et sécurisé pour JSON
        """
        if not text:
            return ""
        
        # ÉTAPE 1 : Échappement JSON obligatoire (ordre important !)
        escaped = text
        
        # 1. Échapper les antislashes AVANT tout le reste (pour éviter double échappement)
        escaped = escaped.replace('\\', '\\\\')
        
        # 2. Échapper les guillemets doubles pour JSON
        escaped = escaped.replace('"', '\\"')
        
        # 3. Échapper les caractères de nouvelle ligne pour JSON
        escaped = escaped.replace('\n', '\\n')
        escaped = escaped.replace('\r', '\\r')
        
        # 4. Échapper les tabulations
        escaped = escaped.replace('\t', '\\t')
        
        # 5. Échapper les caractères de contrôle problématiques
        escaped = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', escaped)
        
        # ÉTAPE 2 : Normalisation des caractères accentués (optionnel, après échappement)
        replacements = {
            'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a',
            'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
            'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
            'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
            'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
            'ý': 'y', 'ÿ': 'y',
            'ç': 'c', 'ñ': 'n',
            'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A', 'Å': 'A',
            'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
            'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I',
            'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O',
            'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U',
            'Ý': 'Y', 'Ÿ': 'Y',
            'Ç': 'C', 'Ñ': 'N'
        }
        
        # Appliquer les remplacements d'accents (optionnel)
        for original, replacement in replacements.items():
            escaped = escaped.replace(original, replacement)
        
        # ÉTAPE 3 : Nettoyage final - supprimer espaces multiples
        escaped = re.sub(r'\s+', ' ', escaped).strip()
        
        return escaped
    
    def add_message(self, role: str, content: str) -> None:
        """
        Ajoute un nouveau message à l'historique avec échappement JSON automatique.
        
        Args:
            role: 'user' ou 'model'
            content: Contenu du message (sera automatiquement échappé)
        """
        if role not in ['user', 'model']:
            raise ValueError("Le rôle doit être 'user' ou 'model'")
        
        # ÉTAPE 2 : Échapper le contenu dès l'enregistrement
        escaped_content = self.escape_for_json(content.strip())
        
        message = {
            'role': role,
            'content': escaped_content,
            'timestamp': datetime.now().isoformat(),
            'word_count': len(escaped_content.split()),
            'sentence_count': len(re.split(r'[.!?]+', escaped_content.strip()))
        }
        
        self.conversation_history.append(message)
        self.logger.debug(f"Message ajouté: {role} - {message['word_count']} mots, {message['sentence_count']} phrases")
        
        # Log d'avertissement si le contenu original contenait des caractères problématiques
        original_clean = content.strip()
        if original_clean != escaped_content:
            self.logger.info("Contenu nettoyé pour éviter les problèmes d'échappement JSON")
    
    def get_current_history_word_count(self) -> int:
        """
        Calcule le nombre total de mots dans l'historique actuel
        """
        total_words = 0
        
        # Compter les mots du résumé actuel
        if self.current_summary:
            total_words += len(self.current_summary.split())
        
        # Compter les mots de tous les messages de l'historique
        for message in self.conversation_history:
            total_words += message.get('word_count', len(message['content'].split()))
        
        return total_words
    
    def get_current_history_sentence_count(self) -> int:
        """
        Calcule le nombre total de phrases dans l'historique actuel
        """
        total_sentences = 0
        
        # Compter les phrases du résumé actuel
        if self.current_summary:
            total_sentences += len(re.split(r'[.!?]+', self.current_summary.strip()))
        
        # Compter les phrases de tous les messages de l'historique
        for message in self.conversation_history:
            total_sentences += message.get('sentence_count', len(re.split(r'[.!?]+', message['content'].strip())))
        
        return total_sentences
    
    def should_summarize(self) -> bool:
        """
        Vérifie si un résumé est nécessaire selon les seuils configurés
        Nouvelle logique : Premier seuil activé atteint = déclenchement
        """
        # Si la gestion intelligente est désactivée, utiliser la logique par défaut
        if not self.intelligent_management:
            return self._should_summarize_default()
        
        # Récupérer les statistiques actuelles
        stats = self.get_stats()
        current_words = stats["total_words"]
        current_sentences = stats["total_sentences"]
        current_tokens = stats.get("total_tokens", 0)
        
        # Vérifier chaque seuil activé (logique OU)
        reasons = []
        
        if self.words_enabled and current_words >= self.words_threshold:
            reasons.append(f"mots: {current_words}/{self.words_threshold}")
        
        if self.sentences_enabled and current_sentences >= self.sentences_threshold:
            reasons.append(f"phrases: {current_sentences}/{self.sentences_threshold}")
        
        if self.tokens_enabled and current_tokens >= self.tokens_threshold:
            reasons.append(f"tokens: {current_tokens}/{self.tokens_threshold}")
        
        should_summarize = len(reasons) > 0
        
        if should_summarize:
            self.logger.info(f"Seuil(s) atteint(s) ({', '.join(reasons)}) - Résumé nécessaire")
        
        return should_summarize
    
    def _should_summarize_default(self) -> bool:
        """
        Logique de résumé par défaut (ancienne méthode)
        Utilisée quand la gestion intelligente est désactivée
        """
        current_words = self.get_current_history_word_count()
        current_sentences = self.get_current_history_sentence_count()
        
        words_exceeded = current_words > self.words_threshold
        sentences_exceeded = current_sentences > self.sentences_threshold
        
        should_summarize = words_exceeded or sentences_exceeded
        
        if should_summarize:
            reason = []
            if words_exceeded:
                reason.append(f"mots: {current_words}/{self.words_threshold}")
            if sentences_exceeded:
                reason.append(f"phrases: {current_sentences}/{self.sentences_threshold}")
            
            self.logger.info(f"Seuil par défaut atteint ({', '.join(reason)}) - Résumé nécessaire")
        
        return should_summarize
    
    def _load_summary_template(self) -> str:
        """
        Charge le template de résumé depuis le ConfigManager
        """
        if self.config_manager:
            template = self.config_manager.load_conversation_template(self.template_id)
            if template:
                return template
        
        # Template par défaut si aucun n'est trouvé
        return """Veuillez analyser la conversation suivante et créer un résumé concis qui préserve les informations essentielles.

CONVERSATION À RÉSUMER :
{HISTORIQUE_COMPLET}

RÉSUMÉ CONTEXTUEL :"""
    
    def _build_summary_prompt(self) -> str:
        """
        Construit le prompt pour demander un résumé à l'IA
        """
        # Construire l'historique complet
        full_history = ""
        
        # Inclure le résumé précédent s'il existe
        if self.current_summary:
            cleaned_summary = self._clean_text_for_api(self.current_summary)
            full_history += f"[Contexte précédent]\n{cleaned_summary}\n\n[Conversation récente]\n"
        
        # Ajouter tous les messages de l'historique
        for message in self.conversation_history:
            role_label = "Utilisateur" if message['role'] == 'user' else "Assistant"
            # Le contenu est déjà nettoyé lors de l'ajout, mais on s'assure
            cleaned_content = self._clean_text_for_api(message['content'])
            full_history += f"{role_label}: {cleaned_content}\n"
        
        # Charger le template et remplacer le placeholder
        template = self._load_summary_template()
        summary_prompt = template.replace("{HISTORIQUE_COMPLET}", full_history)
        
        # Nettoyer aussi le prompt final
        clean_prompt = self._clean_text_for_api(summary_prompt)
        
        return clean_prompt
    
    def summarize_history(self, api_call_function: Callable[[str], str]) -> bool:
        """
        Génère un résumé de l'historique et remplace l'historique complet
        Avec protection contre les boucles d'erreur
        """
        try:
            # Vérification de sécurité : éviter la boucle infinie
            if self.summary_count > 10:
                self.logger.error("Trop de résumés générés - arrêt pour éviter une boucle")
                return False
            
            # Construire le prompt de résumé
            summary_prompt = self._build_summary_prompt()
            
            # Vérification de la longueur du prompt
            if len(summary_prompt) > 50000:  # Limite de sécurité
                self.logger.error("Prompt de résumé trop long - abandon pour éviter les erreurs")
                # En cas d'urgence, vider l'historique
                self.conversation_history.clear()
                return False
            
            self.logger.info("Génération du résumé en cours...")
            
            # Appeler l'API pour générer le résumé
            summary_response = api_call_function(summary_prompt)
            
            if not summary_response or not summary_response.strip():
                self.logger.error("Résumé vide reçu de l'API")
                return False
            
            # Nettoyer le résumé reçu
            cleaned_summary = self._clean_text_for_api(summary_response.strip())
            
            # NOUVELLE LOGIQUE : Remplacer tout l'historique par le résumé
            # Plus de conservation des messages récents
            self.current_summary = cleaned_summary
            self.conversation_history.clear()  # Vider complètement l'historique
            self.summary_count += 1
            
            summary_word_count = len(self.current_summary.split())
            summary_sentence_count = len(re.split(r'[.!?]+', self.current_summary.strip()))
            
            self.logger.info(f"Résumé #{self.summary_count} généré: {summary_word_count} mots, {summary_sentence_count} phrases")
            self.logger.info("Historique complètement remplacé par le résumé")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération du résumé: {e}")
            # En cas d'erreur critique, vider l'historique pour éviter la boucle
            if "curl" in str(e).lower() or "resolve host" in str(e).lower():
                self.logger.warning("Erreur curl détectée - vidage de l'historique pour éviter la boucle")
                self.conversation_history.clear()
                self.current_summary = None
            return False
    
    def get_messages_for_api(self) -> List[Dict[str, Any]]:
        """
        Retourne l'historique formaté pour l'API Gemini
        """
        api_messages = []
        
        # Inclure le résumé comme contexte si disponible
        if self.current_summary:
            api_messages.append({
                'role': 'model',
                'parts': [{'text': f"[Contexte de conversation]\n{self.current_summary}"}]
            })
        
        # Ajouter les messages de l'historique actuel
        for message in self.conversation_history:
            api_messages.append({
                'role': message['role'],
                'parts': [{'text': message['content']}]
            })
        
        return api_messages
    
    def get_display_history(self) -> str:
        """
        Retourne l'historique formaté pour l'affichage dans l'interface
        """
        display_lines = []
        
        # Afficher le résumé s'il existe
        if self.current_summary:
            display_lines.append(f"[📋 Résumé de conversation #{self.summary_count}]\n{self.current_summary}\n")
        
        # Afficher les messages actuels
        for message in self.conversation_history:
            role_label = "Question" if message['role'] == 'user' else "Réponse"
            display_lines.append(f"{role_label} : {message['content']}")
        
        return "\n".join(display_lines)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques détaillées de la conversation
        """
        current_words = self.get_current_history_word_count()
        current_sentences = self.get_current_history_sentence_count()
        current_tokens = self._get_current_history_token_count()
        
        stats = {
            'total_words': current_words,
            'words_threshold': self.words_threshold,
            'words_enabled': getattr(self, 'words_enabled', True),
            'total_sentences': current_sentences,
            'sentences_threshold': self.sentences_threshold,
            'sentences_enabled': getattr(self, 'sentences_enabled', True),
            'total_tokens': current_tokens,
            'tokens_threshold': self.tokens_threshold,
            'tokens_enabled': getattr(self, 'tokens_enabled', False),
            'summary_count': self.summary_count,
            'messages_count': len(self.conversation_history),
            'has_summary': self.current_summary is not None,
            'intelligent_management': getattr(self, 'intelligent_management', True),
            'show_indicators': self.show_indicators
        }
        
        # Calculer les pourcentages seulement pour les seuils activés
        if stats['words_enabled']:
            stats['words_percentage'] = (current_words / self.words_threshold) * 100
        
        if stats['sentences_enabled']:
            stats['sentences_percentage'] = (current_sentences / self.sentences_threshold) * 100
            
        if stats['tokens_enabled'] and self.tokens_threshold > 0:
            stats['tokens_percentage'] = (current_tokens / self.tokens_threshold) * 100
        
        # CORRECTION: Calculer next_summary_needed directement sans appeler should_summarize()
        # pour éviter la récursion infinie
        stats['next_summary_needed'] = self._check_thresholds_exceeded(stats)
        
        return stats
    
    def _check_thresholds_exceeded(self, stats: Dict[str, Any]) -> bool:
        """
        Vérifie si les seuils sont dépassés sans récursion
        """
        if not getattr(self, 'intelligent_management', True):
            # Logique par défaut simple
            words_exceeded = stats['total_words'] >= self.words_threshold
            sentences_exceeded = stats['total_sentences'] >= self.sentences_threshold
            return words_exceeded or sentences_exceeded
        
        # Vérifier chaque seuil activé
        if stats.get('words_enabled', False) and stats['total_words'] >= self.words_threshold:
            return True
        
        if stats.get('sentences_enabled', False) and stats['total_sentences'] >= self.sentences_threshold:
            return True
        
        if stats.get('tokens_enabled', False) and stats['total_tokens'] >= self.tokens_threshold:
            return True
        
        return False
    
    def _get_current_history_token_count(self) -> int:
        """
        Compte le nombre de tokens dans l'historique actuel
        """
        if not self.tokens_enabled or not self.token_encoder:
            return 0
        
        total_tokens = 0
        
        # Compter les tokens du résumé s'il existe
        if self.current_summary:
            total_tokens += self._count_tokens(self.current_summary)
        
        # Compter les tokens de chaque message
        for message in self.conversation_history:
            for part in message.get('parts', []):
                total_tokens += self._count_tokens(part.get('text', ''))
        
        return total_tokens
    
    def get_status_indicator(self) -> str:
        """
        Retourne un indicateur visuel du statut de la conversation
        """
        if not self.show_indicators:
            return ""
        
        stats = self.get_stats()
        
        # Déterminer le niveau d'alerte
        max_percentage = max(stats['words_percentage'], stats['sentences_percentage'])
        
        if max_percentage < 50:
            indicator = "🟢"  # Vert - OK
        elif max_percentage < 80:
            indicator = "🟡"  # Jaune - Attention
        else:
            indicator = "🔴"  # Rouge - Seuil proche
        
        # Construire l'indicateur
        status_parts = []
        
        if stats['has_summary']:
            status_parts.append(f"📋×{stats['summary_count']}")
        
        status_parts.append(f"{stats['total_words']}/{stats['words_threshold']}mots")
        status_parts.append(f"{stats['total_sentences']}/{stats['sentences_threshold']}phrases")
        
        if stats['next_summary_needed']:
            status_parts.append("⚡RÉSUMÉ")
        
        return f"{indicator} {' | '.join(status_parts)}"

    def reset_conversation(self) -> None:
        """
        Remet à zéro la conversation (nouveau chat)
        """
        self.conversation_history.clear()
        self.current_summary = None
        self.summary_count = 0
        self.logger.info("Conversation réinitialisée")
    
    def get_custom_instructions(self) -> str:
        """
        Retourne les instructions personnalisées pour le résumé
        """
        return self.custom_instructions
    
    def set_custom_instructions(self, instructions: str) -> None:
        """
        Définit les instructions personnalisées pour le résumé
        """
        self.custom_instructions = instructions
        self.config["custom_instructions"] = instructions
        self.logger.info(f"Instructions personnalisées mises à jour: {instructions[:50]}...")


# Fonction simulée pour les tests (à remplacer par l'intégration réelle)
def simulate_api_call(prompt: str) -> str:
    """
    Fonction simulée pour tester le système de résumé
    À remplacer par l'appel réel à l'API Gemini
    """
    # Simulation basique d'un résumé
    word_count = len(prompt.split())
    return f"Résumé simulé de la conversation précédente ({word_count} mots analysés). Les points principaux abordés incluent les échanges entre l'utilisateur et l'assistant sur divers sujets techniques."


# Exemple d'utilisation et de test
if __name__ == "__main__":
    # Configuration du logging pour les tests
    logging.basicConfig(level=logging.INFO)
    
    # Test du ConversationManager
    manager = ConversationManager(summary_threshold_words=50)  # Seuil bas pour les tests
    
    print("=== Test ConversationManager ===")
    
    # Simulation d'une conversation
    test_messages = [
        ("user", "Bonjour, comment allez-vous ?"),
        ("model", "Bonjour ! Je vais très bien, merci. Comment puis-je vous aider aujourd'hui ?"),
        ("user", "J'aimerais en savoir plus sur l'intelligence artificielle et ses applications."),
        ("model", "L'IA a de nombreuses applications : reconnaissance vocale, vision par ordinateur, traitement du langage naturel, recommandations personnalisées, conduite autonome, diagnostic médical, etc."),
        ("user", "Pouvez-vous me donner des exemples concrets d'utilisation de l'IA dans le domaine médical ?"),
        ("model", "Certainement ! En médecine, l'IA aide pour : diagnostic par imagerie (détection de cancers sur radios), analyse de données génomiques, découverte de médicaments, chirurgie assistée par robot, prédiction d'épidémies, personnalisation des traitements.")
    ]
    
    for role, content in test_messages:
        manager.add_message(role, content)
        stats = manager.get_stats()
        print(f"Ajouté: {role} | Mots total: {stats['total_words']}/{stats['threshold_words']}")
        
        if manager.should_summarize():
            print("🔄 Génération du résumé...")
            success = manager.summarize_history(simulate_api_call)
            if success:
                print("✅ Résumé généré avec succès")
                new_stats = manager.get_stats()
                print(f"📊 Nouveaux stats: {new_stats['total_words']} mots, {new_stats['messages_count']} messages")
            else:
                print("❌ Échec de la génération du résumé")
    
    print("\n=== Historique final ===")
    print(manager.get_display_history())
    
    print("\n=== Messages pour API ===")
    api_messages = manager.get_messages_for_api()
    for i, msg in enumerate(api_messages):
        print(f"{i+1}. {msg['role']}: {msg['parts'][0]['text'][:100]}...")
