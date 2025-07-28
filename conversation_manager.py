"""
ConversationManager - Gestionnaire intelligent d'historique avec résumé contextuel
Version intégrée avec ConfigManager et indicateurs visuels
Remplace la concaténation simple par une gestion intelligente des conversations
"""

import json
import logging
import re
import unicodedata
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

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
        
        # Seuils configurables avec fusion intelligente des configurations
        self.words_threshold = self._get_config_value("summary_threshold", {}).get("words", self.default_config["summary_threshold"]["words"])
        self.sentences_threshold = self._get_config_value("summary_threshold", {}).get("sentences", self.default_config["summary_threshold"]["sentences"])
        self.summary_enabled = self._get_config_value("summary_enabled", self.default_config["summary_enabled"])
        self.show_indicators = self._get_config_value("show_indicators", self.default_config["show_indicators"])
        self.template_id = self._get_config_value("summary_template_id", self.default_config["summary_template_id"])
        
        # État de la conversation
        self.conversation_history: List[Dict[str, str]] = []
        self.current_summary: Optional[str] = None
        self.summary_count = 0
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"ConversationManager initialisé pour API '{self.api_type}' - Seuils: {self.words_threshold} mots / {self.sentences_threshold} phrases")
    
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
    
    def _clean_text_for_api(self, text: str) -> str:
        """
        Nettoie le texte pour éviter les problèmes d'échappement dans les commandes curl
        Remplace les caractères problématiques par des équivalents sûrs
        """
        if not text:
            return ""
        
        # Dictionnaire de remplacement pour les caractères français problématiques
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
        
        # Appliquer les remplacements
        cleaned_text = text
        for original, replacement in replacements.items():
            cleaned_text = cleaned_text.replace(original, replacement)
        
        # Normaliser les caractères unicode restants
        try:
            cleaned_text = unicodedata.normalize('NFKD', cleaned_text)
            cleaned_text = ''.join(c for c in cleaned_text if ord(c) < 128)
        except Exception as e:
            self.logger.warning(f"Erreur normalisation unicode: {e}")
        
        # Nettoyer les caractères de contrôle dangereux pour curl
        cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', cleaned_text)
        
        # Remplacer les guillemets doubles par des simples pour éviter les problèmes JSON
        cleaned_text = cleaned_text.replace('"', "'")
        
        # Nettoyer les espaces multiples
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        return cleaned_text
    
    def add_message(self, role: str, content: str) -> None:
        """
        Ajoute un nouveau message à l'historique
        
        Args:
            role: 'user' ou 'model'
            content: Contenu du message
        """
        if role not in ['user', 'model']:
            raise ValueError("Le rôle doit être 'user' ou 'model'")
        
        # Nettoyer le contenu pour éviter les problèmes d'échappement
        cleaned_content = self._clean_text_for_api(content.strip())
        
        message = {
            'role': role,
            'content': cleaned_content,
            'timestamp': datetime.now().isoformat(),
            'word_count': len(cleaned_content.split()),
            'sentence_count': len(re.split(r'[.!?]+', cleaned_content.strip()))
        }
        
        self.conversation_history.append(message)
        self.logger.debug(f"Message ajouté: {role} - {message['word_count']} mots, {message['sentence_count']} phrases")
        
        # Log d'avertissement si le contenu original contenait des caractères problématiques
        if content.strip() != cleaned_content:
            self.logger.info("Contenu nettoyé pour éviter les problèmes d'échappement")
    
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
        """
        if not self.summary_enabled:
            return False
        
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
            
            self.logger.info(f"Seuil atteint ({', '.join(reason)}) - Résumé nécessaire")
        
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
        
        return {
            'total_words': current_words,
            'words_threshold': self.words_threshold,
            'total_sentences': current_sentences,
            'sentences_threshold': self.sentences_threshold,
            'summary_count': self.summary_count,
            'messages_count': len(self.conversation_history),
            'has_summary': self.current_summary is not None,
            'words_percentage': (current_words / self.words_threshold) * 100,
            'sentences_percentage': (current_sentences / self.sentences_threshold) * 100,
            'next_summary_needed': self.should_summarize(),
            'summary_enabled': self.summary_enabled,
            'show_indicators': self.show_indicators
        }
    
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
