import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, Toplevel, Menu, PhotoImage
import os
import sys
import re
import platform
import yaml
import subprocess
import json
import charset_normalizer
import logging
from datetime import datetime

# Importer notre nouveau système de configuration
from config_manager import ConfigManager
from core.api_manager import ProfileManagerFactory
from conversation_manager import ConversationManager
from system_profile_generator import generate_system_profile_at_startup
from payload_manager import PayloadManager, extract_json_from_curl
from native_manager import NativeManager

# Configure logging to log initialization events
logging.basicConfig(
    filename="application.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Application started.")
logging.info("Initializing new JSON configuration system.")

class ToolTip:
    """Classe pour créer des infobulles sur les widgets tkinter"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        
        # Lier les événements
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 20
        
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify='left',
                        background="#ffffcc", relief='solid', borderwidth=1,
                        font=("Arial", 8), wraplength=300)
        label.pack(ipadx=5, ipady=3)
    
    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

PROFILES_DIR = "profiles"
CONVERSATIONS_DIR = "conversations"
DEVELOPMENT_DIR = "development"
os.makedirs(PROFILES_DIR, exist_ok=True)
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
os.makedirs(DEVELOPMENT_DIR, exist_ok=True)

# Initialiser le gestionnaire de configuration JSON
# Initialisation APIManager pour gestion centralisée des profils
api_manager = ProfileManagerFactory.create_api_manager_with_validation()
if not api_manager:
    print("ERREUR: Impossible d'initialiser APIManager")
    sys.exit(1)

# Garder ConfigManager pour les opérations de sauvegarde (temporaire)
config_manager = ConfigManager(".")

# Initialiser le nouveau gestionnaire API (Phase 2 - Refactorisation)
api_manager = ProfileManagerFactory.create_api_manager_with_validation()

# Initialiser le gestionnaire de conversation (sera configuré via Setup History)
conversation_manager = None

# Variable globale pour stocker le profil API actuellement chargé
profilAPIActuel = {}

def charger_profil_api():
    """
    Retourne le profil API actuellement chargé.
    """
    global profilAPIActuel
    return profilAPIActuel

def generer_prompt(question, profil):
    """
    Génère un prompt complet avec le rôle et le comportement du profil.
    """
    if not profil:
        return question
    
    role = profil.get('role', '')
    behavior = profil.get('behavior', '')
    
    if role and behavior:
        return f"Tu es {role}. Tu dois être {behavior}. Question: {question}"
    elif role:
        return f"Tu es {role}. Question: {question}"
    elif behavior:
        return f"Tu dois être {behavior}. Question: {question}"
    else:
        return question

def generer_fichier_simple(question, reponse, profil):
    """
    Génère un fichier simple avec la question et la réponse.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nom_fichier = f"conversation_{timestamp}.txt"
        chemin_fichier = os.path.join("conversations", nom_fichier)
        
        with open(chemin_fichier, 'w', encoding='utf-8') as f:
            f.write(f"=== CONVERSATION ===\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Profil: {profil.get('name', 'Inconnu') if profil else 'Aucun'}\n")
            f.write(f"Question: {question}\n\n")
            f.write(f"Réponse: {reponse}\n")
        
        print(f"Fichier sauvegardé: {chemin_fichier}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")

def generer_fichier_development(nom_fichier, extension, contenu):
    """
    Génère un fichier de développement dans le dossier development.
    """
    try:
        if not nom_fichier.endswith(f".{extension}"):
            nom_fichier = f"{nom_fichier}.{extension}"
        
        chemin_fichier = os.path.join("development", nom_fichier)
        
        with open(chemin_fichier, 'w', encoding='utf-8') as f:
            f.write(contenu)
        
        print(f"Fichier de développement sauvegardé: {chemin_fichier}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du fichier de développement: {e}")

# Générer le profil système au démarrage
generate_system_profile_at_startup(".")

# Assurer que les profils par défaut existent
config_manager.create_default_profiles()

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def initialiser_profils_par_defaut():
    """
    Initialise les fichiers de profils par défaut (Gemini, OpenAI, Claude) si aucun fichier YAML n'est trouvé.
    Les clés API seront laissées vides.
    """
    profils_par_defaut = {
        "Gemini.json": {
            "name": "Gemini",
            "api_key": "",
            "behavior": "excité, ronchon, répond en une phrase ou deux",
            "curl_exe": "curl \"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=GEMINI_API_KEY\" \\\n  -H 'Content-Type: application/json' \\\n  -X POST \\\n  -d '{\"contents\": [{\"parts\": [{\"text\": \"Explain how AI works\"}]}]}'",
            "default": True,
            "history": True,
            "role": "alien rigolo",
            "replace_apikey": "GEMINI_API_KEY",
            "template_id": "gemini_chat"
        },
        "OpenAI.json": {
            "name": "OpenAI",
            "api_key": "",
            "behavior": "comportement initial",
            "curl_exe": "",
            "default": False,
            "history": False,
            "role": "",
            "replace_apikey": "",
            "template_id": "openai_chat"
        },
        "Claude.json": {
            "name": "Claude",
            "api_key": "",
            "behavior": "comportement initial",
            "curl_exe": "",
            "default": False,
            "history": False,
            "role": "",
            "replace_apikey": "",
            "template_id": "claude_chat"
        }
    }

    for nom_fichier, contenu in profils_par_defaut.items():
        chemin_fichier = os.path.join(PROFILES_DIR, nom_fichier)
        if not os.path.exists(chemin_fichier):
            with open(chemin_fichier, "w", encoding="utf-8") as fichier:
                json.dump(contenu, fichier, indent=2, ensure_ascii=False)

# DÉSACTIVÉ - DIRECTIVE ARCHITECTE: ConfigManager gère maintenant toute l'initialisation
# La fonction initialiser_profils_par_defaut() créait des profils INCOMPLETS sans response_path
# ConfigManager.create_default_profiles() utilise les templates .json.template COMPLETS
# 
# if not any(f.endswith(".json") and not f.endswith(".json.template") for f in os.listdir(PROFILES_DIR)):
#     logging.info("No JSON profiles found. Initializing default profiles.")
#     initialiser_profils_par_defaut()
# else:
#     logging.info("JSON profiles found. Skipping default profile initialization.")

def ouvrir_fenetre_comportement():
    """Ouvre une fenêtre pour gérer les comportements."""
    fenetre_comportement = Toplevel()
    fenetre_comportement.title("Gestion des Comportements")

    label = ttk.Label(fenetre_comportement, text="Enregistrer un comportement")
    label.pack(pady=10)

    comportement_entry = ttk.Entry(fenetre_comportement, width=50)
    comportement_entry.pack(pady=5)

    def enregistrer():
        comportement = comportement_entry.get()
        if comportement:
            comportement_file = get_resource_path("comportement.txt")
            with open(comportement_file, "w") as file:
                file.write(comportement)
            messagebox.showinfo("Succès", f"Comportement '{comportement}' enregistré avec succès.")
        else:
            messagebox.showerror("Erreur", "Veuillez entrer un comportement valide.")

    bouton_enregistrer = ttk.Button(fenetre_comportement, text="Enregistrer", command=enregistrer)
    bouton_enregistrer.pack(pady=10)

def lire_profil_defaut():
    """Lit le profil marqué comme défaut dans le répertoire des profils ou retourne Gemini si aucun n'est défini."""
    try:
        for fichier in os.listdir(PROFILES_DIR):
            if fichier.endswith(".yaml"):
                chemin_fichier = os.path.join(PROFILES_DIR, fichier)
                with open(chemin_fichier, 'r', encoding='utf-8') as f:
                    profil = yaml.safe_load(f)
                    if profil.get("default", False):
                        return profil
        # Si aucun profil n'est marqué comme défaut, charger Gemini
        chemin_gemini = os.path.join(PROFILES_DIR, "Gemini.yaml")
        if os.path.exists(chemin_gemini):
            with open(chemin_gemini, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            messagebox.showerror("Erreur", "Le profil Gemini est introuvable. Veuillez le configurer dans SETUP.")
            return None
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lire les profils : {e}")
        return None

def get_default_profile():
    """Charge le profil par défaut via le ConfigManager."""
    try:
        default_profile = api_manager.get_default_profile()
        if default_profile:
            return default_profile['name']
        return "Gemini"  # Fallback
    except Exception as e:
        logging.error(f"Erreur lors du chargement du profil par défaut : {e}")
        return "Gemini"

def selectionProfilDefaut():
    """
    Charge le profil par défaut via ConfigManager.
    Affiche le nom du profil chargé en haut de la fenêtre testAPI et logue le contenu.
    """
    global profilAPIActuel
    
    try:
        profil_defaut = api_manager.get_default_profile()
        if profil_defaut:
            profilAPIActuel = profil_defaut
            nom_profil_charge = f"{profil_defaut['name']}.json"
            logging.info(f"Profil par défaut chargé : {profil_defaut['name']}")
            return nom_profil_charge, profilAPIActuel
        else:
            # Fallback
            profilAPIActuel = {}
            nom_profil_charge = "Aucun profil trouvé"
            logging.warning("Aucun profil par défaut trouvé")
            return nom_profil_charge, profilAPIActuel
    except Exception as e:
        logging.error(f"Erreur lors du chargement du profil par défaut : {e}")
        profilAPIActuel = {}
        nom_profil_charge = "Erreur de chargement"
        return nom_profil_charge, profilAPIActuel

# Correction pour s'assurer que GEMINI_API_KEY est remplacé correctement

def preparer_requete_curl(final_prompt):
    """
    Phase 1 - Nouvelle implémentation avec fichier JSON temporaire
    Prépare une commande curl sécurisée en utilisant un fichier payload externe
    """
    print(f"[DEBUG] === PHASE 1 - CURL SÉCURISÉ VIA FICHIER JSON ===")
    
    # Récupérer le profil API actuel avec mapping V2
    provider = profilAPIActuel.get('name', '').lower()
    chat_config = profilAPIActuel.get('chat', {})
    method = chat_config.get('method', 'curl')
    template_type = 'chat'  # Fixe en V2
    
    # Construire l'ID du template selon la structure V2 et la méthode
    if method == 'native':
        template_id = f"{provider}_{template_type}_native"
    else:
        template_id = f"{provider}_{template_type}"
    
    print(f"[DEBUG] Provider: {provider}")
    print(f"[DEBUG] Method: {method}")
    print(f"[DEBUG] Template ID: {template_id}")
    print(f"[DEBUG] Final prompt: {final_prompt[:100]}...")
    
    try:
        # Étape 1: Obtenir la commande curl avec template APIManager
        curl_command = api_manager.get_processed_template(template_id, profilAPIActuel, final_prompt)
        
        if not curl_command:
            print(f"[ERROR] Aucun template trouvé pour {template_id}")
            return None
        
        print(f"[DEBUG] Template curl obtenu ({len(curl_command)} chars)")
        
        # Étape 2: Extraire le JSON du template curl
        base_command, json_payload = extract_json_from_curl(curl_command)
        
        if json_payload is None:
            print(f"[ERROR] Impossible d'extraire le JSON du template")
            return curl_command  # Fallback vers ancien système
        
        print(f"[DEBUG] JSON payload extrait avec succès")
        print(f"[DEBUG] Base command: {base_command[:100]}...")
        
        # Étape 3: Créer le fichier payload temporaire
        payload_manager = PayloadManager(api_profile=provider)
        payload_file = payload_manager.create_payload_file(json_payload, prefix="request")
        
        print(f"[DEBUG] Fichier payload créé: {payload_file}")
        
        # Étape 4: Construire la nouvelle commande curl avec -d @fichier
        # Normaliser pour Windows PowerShell
        if platform.system().lower() == 'windows':
            # Convertir les continuations en ligne unique
            base_command = base_command.replace('\\\n', ' ').replace('\n', ' ')
            base_command = re.sub(r'\s+', ' ', base_command).strip()
            
            # Supprimer les backslashes orphelins en fin
            base_command = base_command.rstrip(' \\')
            
            # Ajuster les guillemets pour PowerShell
            base_command = base_command.replace("-H 'Content-Type: application/json'", 
                                             '-H "Content-Type: application/json"')
        
        # Construire la commande finale avec référence au fichier
        final_command = f'{base_command} -d @"{payload_file}"'
        
        print(f"[DEBUG] Commande curl finale construite")
        print(f"[DEBUG] Utilisation fichier: {payload_file}")
        
        return final_command, payload_file  # Retourner aussi le chemin pour nettoyage
        
    except Exception as e:
        print(f"[ERROR] Erreur dans preparer_requete_curl Phase 1: {e}")
        # Fallback vers ancien système en cas d'erreur
        return api_manager.get_processed_template(template_id, profilAPIActuel, final_prompt), None



def corriger_commande_curl(commande):
    """Fonction temporaire simplifiée"""
    import re
    if not commande:
        return commande
    print("[DEBUG] Correction curl simplifiée")
    corrected = commande.replace('\\\n', ' ').replace('\n', ' ')
    corrected = re.sub(r'\s+', ' ', corrected).strip()
    return corrected


def executer_commande_curl(requete_curl, payload_file=None):
    """
    Phase 1 - Exécute la commande curl et nettoie le fichier payload
    Gestion automatique du nettoyage des fichiers temporaires
    """
    print(f"[DEBUG] === EXÉCUTION CURL PHASE 1 ===")
    
    # Nettoyer et normaliser la commande curl
    requete_curl = requete_curl.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')

    # Loguer la commande dans debug_curl.log
    with open("debug_curl.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"\n--- Commande exécutée ---\n{requete_curl}\n")
        if payload_file:
            log_file.write(f"--- Fichier payload utilisé ---\n{payload_file}\n")

    try:
        # Exécuter la commande sans forcer l'encodage UTF-8
        resultat = subprocess.run(requete_curl, shell=True, capture_output=True, text=False)
        
        # Décoder la sortie avec détection automatique d'encodage
        stdout_decoded = ""
        stderr_decoded = ""
        
        if resultat.stdout:
            try:
                # Tentative de décodage UTF-8 d'abord
                stdout_decoded = resultat.stdout.decode('utf-8')
            except UnicodeDecodeError:
                # Fallback avec détection automatique
                detection = charset_normalizer.detect(resultat.stdout)
                encoding = detection.get('encoding', 'utf-8')
                stdout_decoded = resultat.stdout.decode(encoding, errors='ignore')
        
        if resultat.stderr:
            try:
                stderr_decoded = resultat.stderr.decode('utf-8')
            except UnicodeDecodeError:
                detection = charset_normalizer.detect(resultat.stderr)
                encoding = detection.get('encoding', 'utf-8')
                stderr_decoded = resultat.stderr.decode(encoding, errors='ignore')
        
        # Créer un objet résultat avec les chaînes décodées
        class ResultatDecode:
            def __init__(self, returncode, stdout, stderr):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr
        
        resultat_decode = ResultatDecode(resultat.returncode, stdout_decoded, stderr_decoded)
        
        # Loguer le résultat
        with open("debug_curl.log", "a", encoding="utf-8") as log_file:
            log_file.write(f"Return code: {resultat_decode.returncode}\n")
            log_file.write(f"Stdout: {resultat_decode.stdout[:500]}...\n" if len(resultat_decode.stdout) > 500 else f"Stdout: {resultat_decode.stdout}\n")
            if resultat_decode.stderr:
                log_file.write(f"Stderr: {resultat_decode.stderr}\n")
        
        print(f"[DEBUG] Curl exécuté - Code retour: {resultat_decode.returncode}")
        
        return resultat_decode
    
    except Exception as e:
        print(f"[ERROR] Erreur exécution curl: {e}")
        # Créer un résultat d'erreur
        class ResultatErreur:
            def __init__(self):
                self.returncode = -1
                self.stdout = ""
                self.stderr = f"Erreur Python: {str(e)}"
        
        return ResultatErreur()
    
    finally:
        # ÉTAPE 3: Nettoyage automatique du fichier payload
        if payload_file and os.path.exists(payload_file):
            try:
                os.remove(payload_file)
                print(f"[DEBUG] Fichier payload nettoyé: {payload_file}")
            except Exception as e:
                print(f"[WARNING] Impossible de nettoyer {payload_file}: {e}")

# Plan de tests pour les logs en console
# 1. Vérifier que les commandes curl s'exécutent correctement et que la sortie est capturée en UTF-8.
# 2. Simuler une réponse contenant des caractères spéciaux pour s'assurer qu'ils sont correctement affichés.
# 3. Tester avec des profils contenant des caractères non-ASCII dans les champs (par exemple, rôle ou comportement).
# 4. Vérifier que les erreurs de décodage (UnicodeDecodeError) ne se produisent plus.
# 5. Ajouter des logs en console pour afficher les étapes critiques :
#    - Commande curl exécutée
#    - Résultat brut de la commande
#    - Texte extrait après traitement.

def afficher_resultat(resultat, requete_curl, champ_r, champ_q):
    """
    Affiche le résultat de la commande curl dans le champ R.
    Gère les erreurs et affiche des messages clairs en cas de problème.
    VERSION ÉVOLUTIVE: Support multi-API (Gemini, OpenAI, Claude)
    """
    # Import du parseur évolutif
    try:
        from api_response_parser import get_response_parser
        parser = get_response_parser()
    except ImportError:
        # Fallback si le module n'est pas disponible
        parser = None
    
    champ_r.delete('1.0', tk.END)  # Nettoyer le champ avant d'affichage

    if resultat.returncode == 0:
        try:
            reponse_json = json.loads(resultat.stdout)

            if parser:
                # === NOUVEAU SYSTÈME ÉVOLUTIF ===
                # PHASE 3: Récupérer le provider correctement depuis le template_id ou name
                profil = charger_profil_api()
                
                # Essayer d'abord avec template_id (ex: "gemini_chat" -> "gemini")
                template_id = profil.get('template_id', '')
                if template_id and '_' in template_id:
                    provider = template_id.split('_')[0].lower()
                else:
                    # Fallback sur name en minuscules
                    provider = profil.get('name', '').lower() if profil else 'auto'
                
                print(f"[DEBUG] Provider détecté: {provider} (template_id: {template_id})")
                
                success, texte_cible, api_detectee = parser.parse_response(reponse_json, provider)
                
                if not success and provider != 'auto':
                    # Fallback vers auto si le provider spécifique échoue
                    print(f"[DEBUG] Parsing {provider} échoué, essai avec auto...")
                    success, texte_cible, api_detectee = parser.parse_response(reponse_json, 'auto')
                
                if success:
                    print(f"[DEBUG] Parsing réussi avec provider: {api_detectee}")
                    print(f"🎯 API détectée: {api_detectee}")
                    print(f"📝 Texte extrait: {texte_cible[:100]}...")
                    
                    # Corriger l'encodage du texte
                    texte_cible_corrige = texte_cible.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                    
                    # Afficher le texte corrigé dans le champ R
                    champ_r.insert(tk.END, texte_cible_corrige)
                    
                    # Génération de fichier si activée
                    question_originale = champ_q.get('1.0', tk.END).strip()
                    generer_fichier_simple(question_originale, texte_cible_corrige, profil)
                    
                    # Supprimer le contenu du prompteur Q
                    champ_q.delete('1.0', tk.END)
                    
                else:
                    champ_r.insert(tk.END, f"Erreur API ({api_detectee}): {texte_cible}")
                    
            else:
                # === FALLBACK ANCIEN SYSTÈME (Gemini seulement) ===
                if "error" in reponse_json:
                    erreur_message = reponse_json["error"].get("message", "Erreur inconnue")
                    champ_r.insert(tk.END, f"Erreur API : {erreur_message}\n")
                    return

                # Extraire le texte cible si disponible (Gemini uniquement)
                if "candidates" in reponse_json:
                    texte_cible = reponse_json["candidates"][0]["content"]["parts"][0]["text"]
                    texte_cible_corrige = texte_cible.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                    champ_r.insert(tk.END, texte_cible_corrige)
                    
                    question_originale = champ_q.get('1.0', tk.END).strip()
                    profil = charger_profil_api()
                    generer_fichier_simple(question_originale, texte_cible_corrige, profil)
                    champ_q.delete('1.0', tk.END)
                else:
                    champ_r.insert(tk.END, "La réponse ne contient pas de candidats valides.\n")
                    
        except json.JSONDecodeError as e:
            champ_r.insert(tk.END, f"Erreur de parsing JSON: {e}\n\nRéponse brute:\n{resultat.stdout}")
        except Exception as e:
            champ_r.insert(tk.END, f"Erreur lors de l'analyse de la réponse : {e}\n{resultat.stdout}")
    else:
        champ_r.insert(tk.END, f"Erreur lors de l'exécution :\n{resultat.stderr}\n")

# Nouvelle logique avec ConversationManager
def soumettreQuestionAPI(champ_q, champ_r, champ_history, conversation_manager=None, status_label=None):
    """
    Version améliorée avec gestion intelligente de l'historique via ConversationManager
    Support pour méthodes curl et native (V2)
    """
    question = champ_q.get('1.0', tk.END).strip()
    
    champ_r.config(state="normal")
    champ_r.delete('1.0', tk.END)
    
    if not question:
        champ_r.insert('1.0', "Veuillez saisir une question.")
        champ_r.config(state="disabled")
        return

    # Récupérer la méthode depuis le profil chargé - Mapping V2
    profil = charger_profil_api()
    if profil:
        chat_config = profil.get('chat', {})
        method = chat_config.get('method', 'curl')
    else:
        method = 'curl'
    
    # Indicateur de méthode utilisée (discret)
    method_indicator = "🌐" if method == 'curl' else "⚡" if method == 'native' else "📡"
    champ_r.insert(tk.END, f"{method_indicator} Traitement ({method})...\n")
    champ_r.update_idletasks()

    try:
        # 1. Vérifier si un résumé est nécessaire AVANT d'ajouter la nouvelle question
        if conversation_manager:
            if conversation_manager.should_summarize():
                print("🔄 Seuil atteint - Génération du résumé...")
                champ_r.insert(tk.END, "🔄 Génération du résumé contextuel...\n")
                champ_r.update_idletasks()
                
                # Activer l'indicateur de synthèse en cours (couleur orange)
                if 'synthesis_control' in globals():
                    synthesis_control(True)
                
                # Importer la fonction synthèse depuis synthesis_manager  
                from synthesis_manager import api_summary_call
                
                # Générer le résumé sur l'historique existant
                success = conversation_manager.summarize_history(api_summary_call)
                
                # Désactiver l'indicateur de synthèse en cours (retour couleur normale)
                if 'synthesis_control' in globals():
                    synthesis_control(False)
                
                if success:
                    stats = conversation_manager.get_stats()
                    print(f"✅ Résumé #{stats['summary_count']} généré")
                    champ_r.delete('1.0', tk.END)  # Nettoyer le message de progression
                else:
                    print("❌ Échec du résumé - continue avec l'historique complet")
                    champ_r.insert(tk.END, "⚠️ Échec du résumé - conversation continue\n")
            
            # 2. MAINTENANT ajouter la nouvelle question à l'historique (après résumé)
            conversation_manager.add_message('user', question)
            
            # 3. Construire le prompt final avec l'historique déjà échappé
            # Le ConversationManager fournit déjà un contenu échappé et sécurisé
            prompt_parts = []
            
            # Inclure le résumé s'il existe
            if conversation_manager.current_summary:
                prompt_parts.append(f"[Contexte de conversation]\\n{conversation_manager.current_summary}")
            
            # Ajouter tous les messages de l'historique
            for message in conversation_manager.conversation_history:
                role_label = "Utilisateur" if message['role'] == 'user' else "Assistant"
                # Le contenu est déjà échappé par escape_for_json() lors de l'ajout
                prompt_parts.append(f"{role_label}: {message['content']}")
            
            # Construire le prompt final - PAS d'échappement supplémentaire nécessaire
            question_finale = "\\n".join(prompt_parts)
            
            print(f"[DEBUG] Prompt construit avec historique sécurisé ({len(question_finale)} chars)")
        else:
            # Fallback vers l'ancienne méthode si pas de ConversationManager
            historique = champ_history.get('1.0', tk.END).strip()
            if profilAPIActuel.get('history', False):
                question_finale = f"{historique}\\n{question}".strip()
            else:
                question_finale = question

        # 5. Exécuter l'appel API principal
        profil = charger_profil_api()
        
        # DÉCISION: Méthode curl ou native
        if method == 'native':
            # ===== MODE NATIVE =====
            print("[DEBUG] === UTILISATION MODE NATIVE ===")
            
            # Initialiser le NativeManager
            native_manager = NativeManager()
            
            # Préparer les variables pour le template - Mapping V2
            chat_config = profil.get('chat', {})
            values_config = chat_config.get('values', {})
            
            variables = {
                'USER_PROMPT': question_finale,
                'LLM_MODEL': values_config.get('llm_model', ''),
                'API_KEY': values_config.get('api_key', ''),
                'SYSTEM_PROMPT_ROLE': values_config.get('role', ''),
                'SYSTEM_PROMPT_BEHAVIOR': values_config.get('behavior', '')
            }
            
            print(f"[DEBUG] Variables V2 natives: {variables}")
            
            # Construire le chemin du template native selon la structure V2
            provider_name = profil.get('name', '').lower()
            template_path = f"templates/chat/{provider_name}/native_basic.py"  # Utiliser native_basic.py avec placeholders
            
            if not os.path.exists(template_path):
                raise FileNotFoundError(f"Template Python non trouvé: {template_path}")
            
            print(f"[DEBUG] Template native: {template_path}")
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_string = f.read()
            
            # Exécuter en mode native
            resultat_native = native_manager.execute_native_request(
                template_string, variables, provider_name
            )
            
            # Adapter le format de retour pour compatibilité avec le reste du code
            class NativeResult:
                def __init__(self, native_result):
                    if native_result['status'] == 'success':
                        self.returncode = 0
                        self.stdout = native_result['output']
                        self.stderr = ""
                    else:
                        self.returncode = 1
                        self.stdout = ""
                        self.stderr = native_result['errors']
            
            resultat = NativeResult(resultat_native)
            
        else:
            # ===== MODE CURL (par défaut) =====
            print("[DEBUG] === UTILISATION PHASE 1 - PAYLOAD MANAGER ===")
            resultat_preparation = preparer_requete_curl(question_finale)
            
            # Vérifier si on a un fichier payload ou ancien système
            if isinstance(resultat_preparation, tuple) and len(resultat_preparation) == 2:
                # Nouveau système Phase 1 avec fichier payload
                requete_curl, payload_file = resultat_preparation
                print(f"[DEBUG] Phase 1 - Fichier payload: {payload_file}")
            else:
                # Ancien système fallback
                requete_curl = resultat_preparation
                payload_file = None
                print(f"[DEBUG] Fallback ancien système")
            
            # ÉTAPE 2 DEBUG : Journaliser la requête JSON finale
            print("=" * 60)
            print("🔍 ÉTAPE 2 - REQUÊTE CURL PHASE 1")
            print("=" * 60)
            print(f"Question finale (après échappement): {len(question_finale)} chars")
            print(f"Requête curl: {len(requete_curl)} chars")
            if payload_file:
                print(f"Fichier payload: {payload_file}")
            print("")
            print("CONTENU question_finale:")
            print(question_finale[:500] + "..." if len(question_finale) > 500 else question_finale)
            print("")
            print("REQUÊTE CURL COMPLÈTE:")
            print(requete_curl)
            print("=" * 60)
            
            # Exécuter avec le nouveau système qui gère automatiquement le nettoyage
            resultat = executer_commande_curl(requete_curl, payload_file)
            
            # ÉTAPE 2 DEBUG : Journaliser la réponse brute
            print("=" * 60)
            print("🔍 RÉPONSE API BRUTE")
            print("=" * 60)
            print(f"Return code: {resultat.returncode}")
            if resultat.returncode == 0:
                print(f"Stdout length: {len(resultat.stdout)} chars")
                print("RÉPONSE JSON BRUTE:")
                print(resultat.stdout[:1000] + "..." if len(resultat.stdout) > 1000 else resultat.stdout)
            else:
                print(f"Stderr: {resultat.stderr}")
            print("=" * 60)
        
        # 6. Traiter la réponse
        if resultat.returncode == 0:
            try:
                reponse_json = json.loads(resultat.stdout)
                
                # PHASE 2: Utiliser le nouveau système response_parser générique
                try:
                    from response_parser import parse_response
                    
                    # Lire le response_path depuis le profil - Mapping V2
                    chat_config = profil.get('chat', {})
                    response_path = chat_config.get('response_path', profil.get('response_path', []))
                    provider = profil.get('name', 'unknown')
                    
                    print(f"[DEBUG] Parsing Phase 2 avec provider: {provider}")
                    print(f"[DEBUG] Response path: {response_path}")
                    
                    # Extraction générique avec le nouveau parser
                    texte_reponse = parse_response(reponse_json, response_path)
                    
                    if not texte_reponse:
                        # Si le parsing échoue, afficher l'erreur avec structure debug
                        from response_parser import debug_json_structure
                        structure = debug_json_structure(reponse_json, max_depth=2)
                        champ_r.insert('1.0', f"❌ Erreur parsing {provider} avec path {response_path}\\n"
                                           f"Structure JSON: {structure}\\n")
                        return
                        
                    print(f"✅ Parsing Phase 2 réussi avec {provider}: {len(texte_reponse)} chars")
                    
                except ImportError:
                    # Fallback vers l'ancien système hardcodé (Gemini seulement)
                    print("[DEBUG] Fallback vers ancien parsing Gemini")
                    texte_reponse = reponse_json["candidates"][0]["content"]["parts"][0]["text"]
                
                # 7. Ajouter la réponse au ConversationManager
                if conversation_manager:
                    conversation_manager.add_message('model', texte_reponse)
                    
                    # 8. Mettre à jour l'affichage de l'historique
                    nouvel_historique = conversation_manager.get_display_history()
                    champ_history.delete('1.0', tk.END)
                    champ_history.insert(tk.END, nouvel_historique)
                    
                    # 9. Mettre à jour l'indicateur de statut
                    if status_label:
                        status_indicator = conversation_manager.get_status_indicator()
                        status_label.config(text=status_indicator)
                        
                    # 10. Logging des statistiques
                    stats = conversation_manager.get_stats()
                    print(f"📊 Stats: {stats['total_words']} mots, {stats['total_sentences']} phrases")
                    if stats['next_summary_needed']:
                        print("⚠️ Prochain message déclenchera un résumé")
                
                else:
                    # Fallback vers l'ancienne méthode d'historique
                    historique = champ_history.get('1.0', tk.END).strip()
                    nouveau_historique = f"Question : {question}\nRéponse : {texte_reponse}"
                    champ_history.delete('1.0', tk.END)
                    champ_history.insert(tk.END, f"{historique}\n{nouveau_historique}".strip())
                
                # Afficher la réponse
                champ_r.insert('1.0', texte_reponse)
                
                # 11. GÉNÉRATION DE FICHIERS (restauré)
                # Vérifier si la génération de fichiers est activée dans le profil
                if profil.get('file_generation', {}).get('enabled', False):
                    try:
                        mode = profil.get('file_generation', {}).get('mode', 'simple')
                        if mode == 'simple':
                            generer_fichier_simple(question, texte_reponse, profil)
                            print("📁 Fichier simple généré")
                        elif mode == 'development':
                            config_dev = profil.get('file_generation', {}).get('dev_config', {})
                            extension = config_dev.get('extension', '.py')
                            nom_fichier = f"dev_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            generer_fichier_development(nom_fichier, extension, texte_reponse)
                            print(f"📁 Fichier development généré: {nom_fichier}{extension}")
                    except Exception as e:
                        print(f"⚠️ Erreur génération fichier: {e}")
                
                # Supprimer le contenu du champ question
                champ_q.delete('1.0', tk.END)
                
            except json.JSONDecodeError as e:
                champ_r.insert('1.0', f"Erreur de parsing JSON: {e}")
                print(f"❌ Erreur JSON: {e}")
        else:
            champ_r.insert('1.0', f"Erreur API: {resultat.stderr}")
            print(f"❌ Erreur API: {resultat.stderr}")
            
    except Exception as e:
        champ_r.insert('1.0', f"Erreur système: {e}")
        print(f"❌ Erreur système: {e}")
    
    finally:
        champ_r.config(state="disabled")

# Modification pour rendre le champ historique caché tout en conservant sa fonctionnalité
def copier_au_presse_papier(champ_r):
    """Copie le contenu du champ R dans le presse-papier et remet le focus sur le champ R."""
    contenu = champ_r.get('1.0', tk.END).strip()
    if contenu:
        root.clipboard_clear()
        root.clipboard_append(contenu)
        root.update()  # Met à jour le presse-papier
    champ_r.focus_set()  # Remet le focus sur le champ R

# Amélioration du design de l'interface utilisateur pour une meilleure ergonomie et lisibilité
# Ajout de styles et réorganisation des widgets

def ouvrir_fenetre_apitest():
    """
    Ouvre la fenêtre unique du module APItest avec navigation interne, chargement du profil par défaut,
    création de la commande API, et gestion des champs Q/R.
    """
    import json
    fenetre = tk.Toplevel(root)
    fenetre.title("APItest")
    fenetre.geometry("800x600")  # Augmentation de la taille pour plus d'espace

    print("[DEBUG] Ouverture de la fenêtre APItest")

    def on_close():
        print("[DEBUG] Fermeture de la fenêtre APItest")
        fenetre.destroy()
        if not root.winfo_children():  # Si aucune autre fenêtre n'est ouverte
            print("[DEBUG] Aucune autre fenêtre ouverte, fermeture de l'application principale")
            root.quit()  # Quitte proprement l'application

    fenetre.protocol("WM_DELETE_WINDOW", on_close)

    # Chargement du profil par défaut
    nom_profil_charge, profilAPIActuel = selectionProfilDefaut()
    
    # === INITIALISATION DU CONVERSATION MANAGER ===
    conversation_manager = None
    status_label = None
    
    # Vérifier si l'historique est activé et initialiser ConversationManager
    # Mapping V2: chat.values.history
    historique_active = profilAPIActuel.get('chat', {}).get('values', {}).get('history', False)
    if historique_active:
        try:
            # Lire la configuration directement depuis le profil principal
            nom_profil = nom_profil_charge.split('.')[0]
            profile_main_path = os.path.join("profiles", f"{nom_profil}.json")
            
            if os.path.exists(profile_main_path):
                with open(profile_main_path, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                
                # Récupérer la configuration conversation_management
                conversation_config = profile_data.get('conversation_management', {})
                
                # Si pas de configuration, utiliser les défauts
                if not conversation_config:
                    conversation_config = {
                        "words_enabled": True,
                        "sentences_enabled": True,
                        "tokens_enabled": False,
                        "word_threshold": 300,
                        "sentence_threshold": 15,
                        "token_threshold": 1000,
                        "summary_template": f"Template {nom_profil}",
                        "custom_instructions": "Résume la conversation précédente en conservant les points clés et le contexte important.",
                        "auto_save": True
                    }
                    
                    # Ajouter la configuration par défaut au profil
                    profile_data["conversation_management"] = conversation_config
                    with open(profile_main_path, 'w', encoding='utf-8') as f:
                        json.dump(profile_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ Configuration conversation_management ajoutée à {profile_main_path}")
                
                # Initialiser ConversationManager avec la vraie configuration
                conversation_manager = ConversationManager(
                    config_manager=config_manager,
                    profile_config=conversation_config
                )
                print(f"✅ ConversationManager initialisé depuis profil principal: {profile_main_path}")
                print(f"   Seuils: {conversation_config.get('word_threshold', 300)}mots, {conversation_config.get('sentence_threshold', 15)}phrases, {conversation_config.get('token_threshold', 1000)}tokens")
                
            else:
                print(f"❌ Profil principal {profile_main_path} non trouvé")
                conversation_manager = None
            
        except Exception as e:
            # En cas d'erreur (données corrompues), popup et fermeture
            messagebox.showerror("Erreur Configuration", 
                               f"Erreur lors du chargement de la configuration d'historique:\n{e}\n\nLa fenêtre va se fermer.")
            fenetre.destroy()
            return
    else:
        print("ℹ️  Historique désactivé - ConversationManager non initialisé")

    # Création de la commande API (champ caché) - Compatible V2
    def creerCommandeAPI(profil):
        if not profil:
            return ""
        
        # Récupérer méthode et informations V2
        chat_config = profil.get('chat', {})
        method = chat_config.get('method', 'curl')
        template_type = 'chat'  # Fixe pour V2
        provider = profil.get('name', '').lower()
        
        # PHASE 3.1.2: Utiliser APIManager centralisé pour tous les templates
        if method == 'curl':
            # Construire l'ID du template selon la structure V2
            template_id = f"{provider}_{template_type}"
            
            # NOUVEAU: Utiliser get_processed_template avec placeholders (Phase 2)
            template_content = api_manager.get_processed_template(template_id, profil, "Test API message")
            
            # Fallback vers template_id du profil si nécessaire
            if not template_content:
                template_id = profil.get('template_id', '')
                if template_id:
                    template_content = api_manager.get_processed_template(template_id, profil, "Test API message")
            
            if template_content:
                print(f"[DEBUG] Template traité avec placeholders: {template_content[:200]}...")
                return template_content
            else:
                print(f"[DEBUG] Aucun template trouvé pour {template_id}")
                return ""
                
        elif method == 'native':
            # PHASE 3.1.2: Pour le mode natif, utiliser APIManager centralisé
            template_id = f"{provider}_{template_type}_native"
            template_content = api_manager.get_template_content(template_id)
            if template_content:
                return f"# Mode Native SDK - {provider.title()}\n{template_content}"
            else:
                return f"# Mode Native SDK - {provider.title()}\n# Template natif non encore disponible"
        
        # Fallback final : ancien système curl_exe (pour compatibilité)
        curl_exe = profil.get('curl_exe', '')
        api_key = profil.get('api_key', '')
        if curl_exe and api_key:
            replace_key = profil.get('replace_apikey', 'GEMINI_API_KEY')
            return curl_exe.replace(replace_key, api_key)
        return curl_exe

    cmd_api = creerCommandeAPI(profilAPIActuel)
    fenetre.cmd_api = cmd_api  # champ caché

    # Interface utilisateur
    # Ajout d'un cadre principal pour organiser les widgets
    cadre_principal = ttk.Frame(fenetre, padding="10")
    cadre_principal.pack(fill="both", expand=True)

    # Afficher le nom du profil API par défaut et les informations de méthode
    label_profil = ttk.Label(cadre_principal, text=f"Profil chargé : {nom_profil_charge.split('.')[0]}", font=("Arial", 12, "bold"))
    label_profil.pack(pady=5)
    
    # === INDICATEUR MÉTHODE ET CONFIGURATION V2 ===
    def get_method_info():
        """Récupère et formate les informations de méthode depuis le profil chargé"""
        chat_config = profilAPIActuel.get('chat', {})
        values_config = chat_config.get('values', {})
        method = chat_config.get('method', 'curl')
        template_type = 'chat'  # Fixe pour V2
        llm_model = values_config.get('llm_model', '')
        
        # Formater l'affichage selon la méthode
        if method == 'curl':
            method_display = "🌐 Curl"
            if llm_model:
                method_part = f"{method_display} | {template_type.title()} | {llm_model}"
            else:
                method_part = f"{method_display} | {template_type.title()}"
        elif method == 'native':
            method_display = "⚡ Native SDK"
            if llm_model:
                method_part = f"{method_display} | {template_type.title()} | {llm_model}"
            else:
                method_part = f"{method_display} | {template_type.title()}"
        else:
            method_part = f"📡 {method.title()} | {template_type.title()}"
        
        # Ajouter les informations de résumé
        if conversation_manager and hasattr(conversation_manager, 'resume_profile'):
            try:
                resume_profile = conversation_manager.resume_profile
                template = resume_profile.get("template_type", "défaut")
                
                # Formater l'affichage
                if template.startswith("Template "):
                    template_display = template.replace("Template ", "")
                else:
                    template_display = template
                
                resume_part = f"📋 Résumé: {template_display}"
                
            except Exception as e:
                print(f"Erreur récupération profil résumé: {e}")
                resume_part = "📋 Résumé: défaut"
        else:
            resume_part = "📋 Résumé: défaut"
            
        # Indicateur historique géré séparément
        return f"{method_part} | {resume_part}"
    
    # Label consolidé avec méthode, modèle, et résumé sur une ligne
    info_frame = ttk.Frame(cadre_principal)
    info_frame.pack(pady=2)
    
    method_info_label = ttk.Label(info_frame, text=get_method_info(), 
                                 font=("Arial", 9), foreground="darkblue")
    method_info_label.pack(side="left")
    
    # Label séparé pour l'indicateur éclair avec couleur dynamique
    flash_indicator_label = ttk.Label(info_frame, text="", 
                                     font=("Arial", 9), foreground="darkblue")
    flash_indicator_label.pack(side="left")
    
    # Mettre à jour l'affichage initial de l'indicateur éclair
    values_config = profilAPIActuel.get('chat', {}).get('values', {})
    if values_config.get('history', False):
        flash_indicator_label.config(text=" | ⚡", foreground="darkblue")
    
    # Fonctions pour gérer l'indicateur historique dynamique
    def set_synthesis_in_progress(in_progress=True):
        """Active/désactive l'état de synthèse en cours"""
        get_method_info.synthesis_in_progress = in_progress
        # Mettre à jour l'affichage du label principal
        method_info_label.config(text=get_method_info())
        
        # Changer seulement la couleur du symbole éclair
        values_config = profilAPIActuel.get('chat', {}).get('values', {})
        if values_config.get('history', False):
            if in_progress:
                flash_indicator_label.config(foreground="gold")  # Jaune/doré pour synthèse en cours
            else:
                flash_indicator_label.config(foreground="darkblue")  # Retour à la couleur normale
    
    # Initialiser l'état de synthèse et rendre la fonction accessible globalement
    get_method_info.synthesis_in_progress = False
    
    # Stocker la fonction dans l'espace global pour y accéder depuis valider()
    global synthesis_control
    synthesis_control = set_synthesis_in_progress
    
    # Ajouter infobulle avec informations détaillées selon la méthode
    chat_config = profilAPIActuel.get('chat', {})
    method = chat_config.get('method', 'curl')
    if method == 'curl':
        tooltip_text = "Mode Curl: Utilisation des commandes curl pour les requêtes API.\nMode par défaut compatible avec tous les systèmes."
    elif method == 'native':
        tooltip_text = "Mode Native SDK: Utilisation des SDK natifs Python pour des performances optimales.\n"
        provider = profilAPIActuel.get('name', '').lower()
        if provider == 'openai':
            tooltip_text += "SDK requis: pip install openai"
        elif provider == 'gemini':
            tooltip_text += "SDK requis: pip install google-generativeai"
        elif provider == 'claude':
            tooltip_text += "SDK requis: pip install anthropic"
        else:
            tooltip_text += f"SDK natif pour {provider}"
    else:
        tooltip_text = f"Mode {method.title()}: Méthode personnalisée"
    
    # Créer l'infobulle
    ToolTip(method_info_label, tooltip_text)
    
    # === INDICATEUR DE STATUT CONVERSATION ===
    if conversation_manager and conversation_manager.show_indicators:
        status_label = ttk.Label(cadre_principal, text="🟢 0/300mots | 0/6phrases", 
                                font=("Arial", 9), foreground="gray")
        status_label.pack(pady=2)
        
        # Mise à jour initiale de l'indicateur
        initial_status = conversation_manager.get_status_indicator()
        status_label.config(text=initial_status)

    # Champ Q (question)
    label_q = ttk.Label(cadre_principal, text="Question (Q) :", font=("Arial", 10))
    label_q.pack(anchor="w", pady=(10,5))
    champ_q = scrolledtext.ScrolledText(cadre_principal, width=90, height=5, wrap="word", font=("Arial", 10))
    champ_q.pack(pady=5)

    # Champ R (réponse)
    label_r = ttk.Label(cadre_principal, text="Réponse (R) :", font=("Arial", 10))
    label_r.pack(anchor="w", pady=5)
    champ_r = scrolledtext.ScrolledText(cadre_principal, width=90, height=10, wrap="word", font=("Arial", 10), state="normal")
    champ_r.pack(pady=5)

    # Champ Historique (caché)
    champ_history = scrolledtext.ScrolledText(cadre_principal, width=90, height=5, wrap="word", font=("Arial", 10))
    champ_history.pack_forget()  # Rendre le champ invisible

    # Interface développement (conditionnelle)
    frame_dev = None
    champ_nom_fichier = None
    bouton_enregistrer_fichier = None
    
    # Vérifier si le mode développement est activé
    file_generation_config = profilAPIActuel.get('file_generation', {})
    generation_active = file_generation_config.get('enabled', False)
    mode_development = file_generation_config.get('mode', 'simple') == 'development'
    
    if generation_active and mode_development:
        dev_config = file_generation_config.get('dev_config', {})
        extension_configuree = dev_config.get('extension', '.py')
        
        # Frame pour les contrôles développement
        frame_dev = ttk.Frame(cadre_principal)
        frame_dev.pack(pady=10)
        
        # Label et champ nom du fichier
        ttk.Label(frame_dev, text="Nom du fichier :", font=("Arial", 10)).pack(side="left", padx=(0, 5))
        champ_nom_fichier = ttk.Entry(frame_dev, width=30, font=("Arial", 10))
        champ_nom_fichier.pack(side="left", padx=(0, 5))
        
        # Label extension
        ttk.Label(frame_dev, text=extension_configuree, font=("Arial", 10, "bold")).pack(side="left")

    # Boutons sur une ligne horizontale
    frame_boutons = ttk.Frame(cadre_principal)
    frame_boutons.pack(pady=10)

    bouton_copier = ttk.Button(frame_boutons, text="Copier la réponse", command=lambda: copier_au_presse_papier(champ_r))
    bouton_copier.pack(side="left", padx=10)

    # Bouton adaptatif selon la méthode - Mapping V2
    chat_config = profilAPIActuel.get('chat', {})
    method = chat_config.get('method', 'curl')
    if method == 'curl':
        bouton_text = "🌐 Envoyer (Curl)"
    elif method == 'native':
        bouton_text = "⚡ Envoyer (Native)"
    else:
        bouton_text = "📡 Envoyer la question"
        
    bouton_valider = ttk.Button(frame_boutons, text=bouton_text, 
                                command=lambda: soumettreQuestionAPI(champ_q, champ_r, champ_history, conversation_manager, status_label))
    bouton_valider.pack(side="left", padx=10)
    
    # Bouton pour réinitialiser la conversation (si ConversationManager actif)
    if conversation_manager:
        def reset_conversation():
            conversation_manager.reset_conversation()
            champ_history.delete('1.0', tk.END)
            if status_label:
                status_label.config(text=conversation_manager.get_status_indicator())
            print("🔄 Conversation réinitialisée")
        
        bouton_reset = ttk.Button(frame_boutons, text="Nouvelle conversation", command=reset_conversation)
        bouton_reset.pack(side="left", padx=10)
    
    # Bouton enregistrer fichier (mode développement uniquement)
    if generation_active and mode_development:
        def validation_nom_fichier(*args):
            """Valide le champ nom de fichier et active/désactive le bouton."""
            if champ_nom_fichier and bouton_enregistrer_fichier:
                nom = champ_nom_fichier.get().strip()
                if nom:
                    bouton_enregistrer_fichier.config(state="normal")
                else:
                    bouton_enregistrer_fichier.config(state="disabled")
        
        def enregistrer_fichier_dev():
            """Enregistre la réponse dans un fichier de développement."""
            if champ_nom_fichier:
                nom_fichier = champ_nom_fichier.get().strip()
                reponse = champ_r.get('1.0', tk.END).strip()
                
                if nom_fichier and reponse:
                    dev_config = file_generation_config.get('dev_config', {})
                    extension = dev_config.get('extension', '.py')
                    
                    # Enregistrer le fichier sans vider le champ nom
                    generer_fichier_development(nom_fichier, extension, reponse)
        
        bouton_enregistrer_fichier = ttk.Button(frame_boutons, text="Enregistrer le fichier", 
                                               command=enregistrer_fichier_dev, state="disabled")
        bouton_enregistrer_fichier.pack(side="left", padx=10)
        
        # Lier la validation au champ nom de fichier
        if champ_nom_fichier:
            champ_nom_fichier.bind('<KeyRelease>', validation_nom_fichier)
            champ_nom_fichier.bind('<FocusOut>', validation_nom_fichier)

    # Boutons grisés pour indiquer les options activées
    frame_options = ttk.Frame(cadre_principal)
    frame_options.pack(pady=10)
    
    # Bouton historique
    historique_active = profilAPIActuel.get('history', False)
    texte_historique = "Historique activé" if historique_active else "Historique désactivé"
    bouton_historique = ttk.Button(frame_options, text=texte_historique, state="disabled")
    bouton_historique.pack(side="left", padx=10)
    
    # Bouton génération de fichiers
    file_generation_config = profilAPIActuel.get('file_generation', {})
    generation_active = file_generation_config.get('enabled', False)
    if generation_active:
        mode_generation = file_generation_config.get('mode', 'simple')
        texte_generation = f"Génération fichier : {mode_generation}"
    else:
        texte_generation = "Génération fichier : désactivée"
    
    bouton_generation = ttk.Button(frame_options, text=texte_generation, state="disabled")
    bouton_generation.pack(side="left", padx=10)

    # Associer la touche Entrée au bouton Valider dans la fenêtre Test API
    fenetre.bind('<Return>', lambda event: bouton_valider.invoke())

def open_setup_menu():
    setup_window = tk.Toplevel(root)
    setup_window.title("SETUP API - Configuration")
    
    # Calcul automatique de la taille optimale (80% de l'écran, max 600x500)
    screen_width = setup_window.winfo_screenwidth()
    screen_height = setup_window.winfo_screenheight()
    
    # Taille optimale : largeur fixée à 1000 pixels
    optimal_width = min(1000, int(screen_width * 0.80))  # Largeur fixée à 1000px
    optimal_height = min(750, int(screen_height * 0.80))  # Augmenté de 600 à 750 (+25%)
    
    # Centrer la fenêtre
    x = (screen_width // 2) - (optimal_width // 2)
    y = (screen_height // 2) - (optimal_height // 2)
    
    setup_window.geometry(f"{optimal_width}x{optimal_height}+{x}+{y}")
    setup_window.resizable(True, True)
    setup_window.minsize(900, 690)  # Taille minimale ajustée pour largeur 1000
    
    # Frame principal pour organiser le contenu
    main_frame = ttk.Frame(setup_window)
    main_frame.pack(fill="both", expand=True, padx=5, pady=5)  # Réduire padx de 10 à 5
    
    # Créer un canvas avec scrollbar pour gérer la hauteur
    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Gestion du scroll avec la molette de la souris
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def bind_mousewheel(event=None):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def unbind_mousewheel(event=None):
        canvas.unbind_all("<MouseWheel>")
    
    # Bind events pour scroll
    canvas.bind('<Enter>', bind_mousewheel)
    canvas.bind('<Leave>', unbind_mousewheel)
    
    # Configuration grid
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Configurer les colonnes pour une meilleure répartition et éviter débordement
    scrollable_frame.grid_columnconfigure(0, weight=0, minsize=150)  # Colonne labels : largeur fixe
    scrollable_frame.grid_columnconfigure(1, weight=1, minsize=250)  # Colonne champs : flexible mais limitée
    scrollable_frame.grid_columnconfigure(2, weight=0, minsize=50)   # Colonne extra : petite

    # Fonction pour charger les profils disponibles
    def charger_profils():
        """Charge les profils via APIManager (Phase 2 - Refactorisation)"""
        return api_manager.list_available_profiles()

    # Fonction pour charger les données d'un profil sélectionné
    def charger_donnees_profil(profil):
        """Charge un profil via ConfigManager avec fallback robuste"""
        try:
            # Essayer d'abord de charger le profil tel quel (via APIManager)
            profile_data = api_manager.load_profile(profil)
            if profile_data:
                return profile_data
            
            # Si ça échoue, essayer avec différentes extensions
            for extension in ['.json', '.yaml']:
                try:
                    if not profil.endswith(extension):
                        test_profil = profil + extension
                        profile_data = api_manager.load_profile(test_profil.replace(extension, ''))
                        if profile_data:
                            return profile_data
                except:
                    continue
            
            # Si tout échoue, retourner des valeurs par défaut pour éviter l'erreur
            print(f"[DEBUG] Profil {profil} non trouvé, utilisation des valeurs par défaut")
            return {
                "api_key": "",
                "role": "",
                "behavior": "",
                "history": False,
                "default": False,
                "replace_apikey": "",
                "template_id": "gemini_chat" if "gemini" in profil.lower() else ""
            }
            
        except Exception as e:
            print(f"[DEBUG] Erreur lors du chargement du profil {profil}: {e}")
            # Retourner des valeurs par défaut au lieu d'afficher une popup d'erreur
            return {
                "api_key": "",
                "role": "",
                "behavior": "",
                "history": False,
                "default": False,
                "replace_apikey": "",
                "template_id": "gemini_chat" if "gemini" in profil.lower() else ""
            }

    # Fonction helper pour charger les données avec le nouveau mapping
    def charger_donnees_avec_nouveau_mapping(donnees_profil):
        """Helper pour charger les données depuis la nouvelle structure chat.values/placeholders"""
        print(f"[DEBUG] charger_donnees_avec_nouveau_mapping appelé avec: {type(donnees_profil)}")
        print(f"[DEBUG] Clés disponibles: {list(donnees_profil.keys()) if isinstance(donnees_profil, dict) else 'Pas un dict'}")
        
        chat_data = donnees_profil.get("chat", {})
        values_data = chat_data.get("values", {})
        placeholders_data = chat_data.get("placeholders", {})
        
        print(f"[DEBUG] chat_data trouvé: {bool(chat_data)}")
        print(f"[DEBUG] values_data: {values_data}")
        print(f"[DEBUG] placeholders_data: {placeholders_data}")
        
        # 1. VALEURS UTILISATEUR (depuis chat.values)
        api_key_var.set(values_data.get("api_key", ""))
        role_var.set(values_data.get("role", ""))
        set_default_behavior_text(values_data.get("behavior", ""))  # Utiliser la fonction pour Text widget
        history_checkbutton_var.set(values_data.get("history", False))
        default_profile_var.set(values_data.get("default", False))
        selected_llm_model.set(values_data.get("llm_model", ""))  # Ajout du modèle LLM
        
        # 2. PLACEHOLDERS (depuis chat.placeholders)
        placeholder_model_var.set(placeholders_data.get("placeholder_model", ""))
        placeholder_role_var.set(placeholders_data.get("placeholder_role", ""))
        set_behavior_text(placeholders_data.get("placeholder_behavior", ""))  # Utiliser la fonction pour Text widget
        user_prompt_var.set(placeholders_data.get("placeholder_user_prompt", ""))
        replace_apikey_var.set(placeholders_data.get("placeholder_api_key", ""))
        
        # 3. RESPONSE_PATH (depuis chat.response_path)
        response_path = chat_data.get("response_path", ["candidates", 0, "content", "parts", 0, "text"])
        set_response_path_text(response_path)
        
        print(f"[DEBUG] Placeholders chargés:")
        print(f"  - placeholder_model_var: {placeholder_model_var.get()}")
        print(f"  - placeholder_role_var: {placeholder_role_var.get()}")
        print(f"  - user_prompt_var: {user_prompt_var.get()}")
        print(f"  - replace_apikey_var: {replace_apikey_var.get()}")
        
        # 4. FALLBACK: Support ancien format pour compatibilité
        if not chat_data:
            print(f"[DEBUG] Ancien format détecté, utilisation format legacy")
            api_key_var.set(donnees_profil.get("api_key", ""))
            role_var.set(donnees_profil.get("role", ""))
            set_default_behavior_text(donnees_profil.get("behavior", ""))  # Utiliser la fonction pour Text widget
            history_checkbutton_var.set(donnees_profil.get("history", False))
            default_profile_var.set(donnees_profil.get("default", False))
            replace_apikey_var.set(donnees_profil.get("replace_apikey", ""))
            selected_llm_model.set(donnees_profil.get("llm_model", ""))
            # Response path par défaut pour ancien format
            set_response_path_text(["candidates", 0, "content", "parts", 0, "text"])
        
        return chat_data

    # Fonction pour mettre à jour les champs du formulaire en fonction du profil sélectionné
    def mettre_a_jour_champs(event):
        profil_selectionne = selected_model.get()
        print(f"[DEBUG] mettre_a_jour_champs appelé pour profil: {profil_selectionne}")
        
        donnees_profil = charger_donnees_profil(profil_selectionne)
        print(f"[DEBUG] Données profil chargées: {type(donnees_profil)}")
        if isinstance(donnees_profil, dict):
            print(f"[DEBUG] Clés du profil: {list(donnees_profil.keys())}")

        print(f"[DEBUG] Changement de profil vers: {profil_selectionne}")
        
        # Utiliser la fonction helper pour le mapping
        chat_data = charger_donnees_avec_nouveau_mapping(donnees_profil)
        print(f"[DEBUG] chat_data retourné: {bool(chat_data)}")
        
        # NOUVELLE LOGIQUE: Chargement commande selon méthode du profil
        if chat_data:
            method = chat_data.get("method", "curl")
            llm_name = profil_selectionne.lower()
            template_type = "chat"  # Par défaut pour Setup API
            
            print(f"[DEBUG] Chargement template: {llm_name}/{template_type}/{method}")
            print(f"[DEBUG] Path recherché: templates/{template_type}/{llm_name}/{method}.txt ou {method}.py")
            
            # SOLID V2: Charger le template via APIManager
            if method == 'native':
                template_id_full = f"{llm_name}_{template_type}_native"
            else:
                template_id_full = f"{llm_name}_{template_type}"
            
            template_content = api_manager.get_template_content(template_id_full)
            if template_content:
                curl_exe_var.set(template_content)
            else:
                curl_exe_var.set(f"# Template {template_id_full} non trouvé")
            
        else:
            # FALLBACK: Support ancien format pour compatibilité
            template_id = donnees_profil.get("template_id", "")
            if template_id:
                # Extraire provider et type du template_id
                provider = template_id.split('_')[0] if '_' in template_id else profil_selectionne.lower()
                template_type = template_id.split('_')[1] if '_' in template_id and len(template_id.split('_')) > 1 else 'chat'
                
                # SOLID V2: Utiliser APIManager directement
                method = donnees_profil.get("method", "curl")
                if method == 'native':
                    template_id_full = f"{provider}_{template_type}_native"
                else:
                    template_id_full = f"{provider}_{template_type}"
                
                template_content = api_manager.get_template_content(template_id_full)
                if template_content:
                    curl_exe_var.set(template_content)
                else:
                    curl_exe_var.set(f"# Template {template_id_full} non trouvé")
            else:
                # Fallback vers curl_exe pour compatibilité
                curl_exe_var.set(donnees_profil.get("curl_exe", ""))

    # Fonction centralisée pour charger le bon template selon la méthode
    def load_smart_template(provider, template_type="chat", method=None, for_display=True):
        """
        Fonction centralisée intelligente pour charger les templates
        Remplace les appels directs à api_manager.get_template_content()
        
        Args:
            provider: nom du provider (gemini, claude, etc.)
            template_type: type de template (chat par défaut) 
            method: méthode (curl/native). Si None, détecte automatiquement
            for_display: True pour affichage interface, False pour exécution
        
        Returns:
            str: contenu du template approprié
        """
        # Détection automatique de la méthode si non fournie
        if method is None:
            current_provider = selected_model.get().lower()
            if current_provider == provider:
                try:
                    profile_data = charger_donnees_profil(provider.title())
                    if profile_data:
                        # Utiliser la structure JSON V2 pour détecter la méthode
                        chat_data = profile_data.get('chat', {})
                        if chat_data:
                            method = chat_data.get('method', 'curl')
                            print(f"[DEBUG] load_smart_template: méthode détectée depuis chat.method {provider}: {method}")
                        else:
                            # Fallback vers l'ancien format
                            method = profile_data.get('method', 'curl')
                            print(f"[DEBUG] load_smart_template: méthode détectée depuis profil legacy {provider}: {method}")
                    else:
                        method = selected_method.get()
                        print(f"[DEBUG] load_smart_template: profil {provider} non trouvé, utilisation selected_method: {method}")
                except Exception as e:
                    method = selected_method.get()
                    print(f"[DEBUG] load_smart_template: erreur détection profil {provider}, utilisation selected_method: {method} (erreur: {e})")
            else:
                method = 'curl'
                print(f"[DEBUG] load_smart_template: provider différent, utilisation curl par défaut")
        
        print(f"[DEBUG] load_smart_template: {provider} {template_type} {method} (display={for_display})")
        
        # Charger le template principal selon la méthode
        if method == 'native':
            # Mode native : charger native.py
            try:
                native_template_path = f"templates/{template_type}/{provider}/native.py"
                with open(native_template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"[DEBUG] Template native.py chargé: {len(content)} caractères")
                    return content
            except FileNotFoundError:
                print(f"[DEBUG] Template native introuvable: {native_template_path}")
                return f"# Template Python pour {provider} non trouvé"
            except Exception as e:
                print(f"[DEBUG] Erreur lecture template native: {e}")
                return f"# Erreur chargement template Python pour {provider}"
        
        else:
            # Mode curl : utiliser l'APIManager
            template_id = f"{provider}_{template_type}"
            try:
                content = api_manager.get_template_content(template_id)
                print(f"[DEBUG] Template curl chargé via APIManager: {template_id}")
                return content
            except Exception as e:
                print(f"[DEBUG] Erreur APIManager pour {template_id}: {e}")
                return f"# Template curl pour {provider} non trouvé"

    def load_basic_template(provider, template_type="chat", method=None):
        """
        Charge le fichier _basic correspondant selon la méthode (curl_basic.txt ou native_basic.py)
        
        Args:
            provider: nom du provider (gemini, claude, etc.)
            template_type: type de template (chat par défaut) 
            method: méthode (curl/native). Si None, détecte automatiquement
        
        Returns:
            str: contenu du fichier _basic correspondant
        """
        # Détection automatique de la méthode si non fournie
        if method is None:
            current_provider = selected_model.get().lower()
            if current_provider == provider:
                try:
                    profile_data = charger_donnees_profil(provider.title())
                    if profile_data:
                        # Utiliser la structure JSON V2 pour détecter la méthode
                        chat_data = profile_data.get('chat', {})
                        if chat_data:
                            method = chat_data.get('method', 'curl')
                            print(f"[DEBUG] load_basic_template: méthode détectée depuis chat.method {provider}: {method}")
                        else:
                            # Fallback vers l'ancien format
                            method = profile_data.get('method', 'curl')
                            print(f"[DEBUG] load_basic_template: méthode détectée depuis profil legacy {provider}: {method}")
                    else:
                        method = selected_method.get()
                        print(f"[DEBUG] load_basic_template: profil {provider} non trouvé, utilisation selected_method: {method}")
                except Exception as e:
                    method = selected_method.get()
                    print(f"[DEBUG] load_basic_template: erreur détection profil {provider}, utilisation selected_method: {method} (erreur: {e})")
            else:
                method = 'curl'
                print(f"[DEBUG] load_basic_template: provider différent, utilisation curl par défaut")
        
        print(f"[DEBUG] load_basic_template: {provider} {template_type} {method}")
        
        # Déterminer le fichier basic à charger selon la méthode
        if method == 'native':
            basic_file = f"templates/{template_type}/{provider}/native_basic.py"
        else:
            basic_file = f"templates/{template_type}/{provider}/curl_basic.txt"
        
        try:
            with open(basic_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"[DEBUG] Fichier basic chargé: {basic_file} ({len(content)} caractères)")
                return content
        except FileNotFoundError:
            print(f"[DEBUG] Fichier basic introuvable: {basic_file}")
            return f"# Fichier basic pour {provider} ({method}) non trouvé"
        except Exception as e:
            print(f"[DEBUG] Erreur lecture fichier basic: {e}")
            return f"# Erreur chargement fichier basic pour {provider}"
        
        if method == "native":
            # Mode native : charger native.py
            if for_display:
                native_template_path = f"templates/{template_type}/{provider}/native.py"
                if os.path.exists(native_template_path):
                    try:
                        with open(native_template_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        print(f"[DEBUG] Template native chargé: {native_template_path}")
                        return content
                    except Exception as e:
                        print(f"[DEBUG] Erreur lecture native: {e}")
                        return f"# Erreur lecture template native {native_template_path}\n# {e}"
                else:
                    # Template par défaut
                    default_template = f"""#!/usr/bin/env python3
# Template Python natif pour {provider.upper()}
# Provider: {provider}

import os

# Configuration
api_key = os.environ.get('{provider.upper()}_API_KEY')
if not api_key:
    print("ERROR: {provider.upper()}_API_KEY not found in environment")
    exit(1)

model = "{{{{LLM_MODEL}}}}"
user_prompt = "{{{{USER_PROMPT}}}}"
system_role = "{{{{SYSTEM_PROMPT_ROLE}}}}"
system_behavior = "{{{{SYSTEM_PROMPT_BEHAVIOR}}}}"

# TODO: Implémenter l'appel API pour {provider}
print("Template native à implémenter pour {provider}")
"""
                    print(f"[DEBUG] Template native par défaut généré pour {provider}")
                    return default_template
            else:
                # Pour exécution : charger native_basic.py
                native_basic_path = f"templates/{template_type}/{provider}/native_basic.py"
                if os.path.exists(native_basic_path):
                    try:
                        with open(native_basic_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        print(f"[DEBUG] Template native_basic chargé: {native_basic_path}")
                        return content
                    except Exception as e:
                        print(f"[DEBUG] Erreur lecture native_basic: {e}")
                        return f"# Erreur lecture template native_basic {native_basic_path}\n# {e}"
                else:
                    print(f"[DEBUG] Template native_basic non trouvé: {native_basic_path}")
                    return f"# Template native_basic non trouvé pour {provider}"
        else:
            # Mode curl : utiliser APIManager
            template_id = f"{provider}_{template_type}"
            template_content = api_manager.get_template_content(template_id)
            if template_content:
                print(f"[DEBUG] Template curl chargé via APIManager: {template_id}")
                return template_content
            else:
                print(f"[DEBUG] Template curl non trouvé: {template_id}")
                return f"# Template curl non trouvé pour {provider}"

    def load_template_by_method(provider, template_type="chat", method=None):
        """
        Charge le template approprié pour l'AFFICHAGE INTERFACE selon la méthode sélectionnée
        SOLID V2: Utilise APIManager refactorisé pour curl et native
        
        Args:
            provider: nom du provider (gemini, claude, etc.)
            template_type: type de template (chat par défaut)
            method: méthode explicite (curl/native). Si None, détecte automatiquement
        """
        # Détection automatique de la méthode si non fournie
        if method is None:
            current_provider = selected_model.get().lower()
            if current_provider == provider:
                try:
                    profile_data = charger_donnees_profil(provider.title())
                    if profile_data:
                        # Utiliser la structure JSON V2 pour détecter la méthode
                        chat_data = profile_data.get('chat', {})
                        if chat_data:
                            method = chat_data.get('method', 'curl')
                        else:
                            # Fallback vers l'ancien format
                            method = profile_data.get('method', 'curl')
                    else:
                        method = selected_method.get()
                except Exception as e:
                    method = selected_method.get()
            else:
                method = 'curl'
        
        print(f"[DEBUG] load_template_by_method: {provider} {template_type} {method}")
        
        # SOLID: Utiliser APIManager pour tous les templates
        if method == 'native':
            template_id = f"{provider}_{template_type}_native"
        else:
            template_id = f"{provider}_{template_type}"
        
        # Charger le template principal via APIManager
        content = api_manager.get_template_content(template_id)
        if content:
            curl_exe_var.set(content)
        else:
            curl_exe_var.set(f"# Template {template_id} non trouvé")
        
        # Charger aussi le contenu basic pour le champ "Placeholder Command"
        basic_content = api_manager.get_template_basic_content(template_id)
        if basic_content:
            placeholder_command_var.set(basic_content)
        else:
            placeholder_command_var.set(f"# Template basic {template_id} non trouvé")
        
        return content

    def get_execution_template(provider, method, template_type="chat"):
        """
        Obtient le template pour l'EXÉCUTION (avec placeholders _basic)
        SOLID V2: Utilise APIManager refactorisé
        
        Args:
            provider: nom du provider (gemini, claude, etc.)
            method: méthode (curl ou native)
            template_type: type de template (chat par défaut)
        
        Returns:
            str: contenu du template basic pour exécution
        """
        # SOLID: Construire l'ID selon la méthode
        if method == 'native':
            template_id = f"{provider}_{template_type}_native"
        else:
            template_id = f"{provider}_{template_type}"
        
        # Charger le template basic via APIManager
        content = api_manager.get_template_basic_content(template_id)
        
        if content:
            print(f"[DEBUG] get_execution_template: template basic chargé pour {template_id}")
            return content
        else:
            print(f"[DEBUG] get_execution_template: template basic non trouvé pour {template_id}")
            return f"# Template basic {template_id} non trouvé"

    # Fonction pour définir un seul profil comme défaut
    def definir_profil_defaut(profil_selectionne):
        """Utilise ConfigManager pour définir le profil par défaut"""
        try:
            config_manager.set_default_profile(profil_selectionne)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la mise à jour du profil par défaut : {e}")

    # Charger le profil par défaut au démarrage via ConfigManager
    def charger_profil_defaut():
        """Charge le profil marqué comme défaut selon la nouvelle logique chat.values.default"""
        try:
            # NOUVELLE LOGIQUE: Chercher dans tous les profils celui avec chat.values.default = true
            profils_disponibles = charger_profils()
            
            for profil_name in profils_disponibles:
                try:
                    donnees_profil = charger_donnees_profil(profil_name)
                    chat_data = donnees_profil.get("chat", {})
                    values_data = chat_data.get("values", {})
                    
                    if values_data.get("default", False):
                        print(f"[DEBUG] Profil par défaut trouvé: {profil_name}")
                        return profil_name
                except Exception as e:
                    print(f"[DEBUG] Erreur lors de la vérification du profil {profil_name}: {e}")
                    continue
            
            # FALLBACK: Si aucun profil avec default=true, prendre le premier disponible
            if profils_disponibles:
                print(f"[DEBUG] Aucun profil par défaut trouvé, utilisation du premier: {profils_disponibles[0]}")
                return profils_disponibles[0]
            
            return "Gemini"  # Fallback final
        except Exception as e:
            logging.error(f"Erreur lors du chargement du profil par défaut Setup API : {e}")
            return "Gemini"

    # Choix du provider (liste déroulante des profils existants)
    provider_label = ttk.Label(scrollable_frame, text="Provider LLM :")
    provider_label.grid(row=0, column=0, sticky="w", pady=(0, 1), padx=(5, 5))  # Coller en haut
    selected_model = tk.StringVar(value=charger_profil_defaut())
    model_combobox = ttk.Combobox(scrollable_frame, textvariable=selected_model, values=charger_profils(), width=60)
    model_combobox.grid(row=0, column=1, columnspan=2, sticky="w", pady=(0, 1), padx=(0, 5))  # Coller en haut
    model_combobox.bind("<<ComboboxSelected>>", mettre_a_jour_champs)

    # Méthode de connexion
    method_label = ttk.Label(scrollable_frame, text="Méthode :")
    method_label.grid(row=1, column=0, sticky="w", pady=1, padx=(5,5))
    selected_method = tk.StringVar(value="curl")
    method_combobox = ttk.Combobox(scrollable_frame, textvariable=selected_method, 
                                   values=["curl", "native"], state="readonly", width=60)
    method_combobox.grid(row=1, column=1, columnspan=2, sticky="w", pady=1, padx=(0,5))
    
    # Fonction pour mettre à jour l'affichage selon la méthode
    def update_method_fields(*args):
        method = selected_method.get()
        if method == "curl":
            # Mode curl : afficher les champs curl
            # NOTE: Le texte du label sera géré par creer_champs_dynamiques()
            curl_exe_label.grid(row=15, column=0, sticky="nw", pady=5, padx=(10,5))
            curl_frame.grid(row=15, column=1, columnspan=2, sticky="ew", pady=5, padx=(0,10))
            curl_exe_label.config(text="Commande Curl :")
            placeholder_command_label.config(text="Placeholder Command (curl_basic.txt) :")
        elif method == "native":
            # Mode native : afficher le template Python
            user_prompt_label.config(text="Paramètres template :")
            curl_exe_label.grid(row=15, column=0, sticky="nw", pady=5, padx=(10,5))
            curl_frame.grid(row=15, column=1, columnspan=2, sticky="ew", pady=5, padx=(0,10))
            curl_exe_label.config(text="Template Python Native :")
            placeholder_command_label.config(text="Placeholder Command (native_basic.py) :")
        
        # Basculer le contenu affiché selon la méthode sélectionnée
        switch_template_content()
        
        # Recharger le template selon la nouvelle méthode (explicite)
        current_provider = selected_model.get()
        current_method = selected_method.get()
        if current_provider and current_method:
            load_template_by_method(current_provider.lower(), "chat", method=current_method)
    
    # Lier la fonction au changement de méthode
    selected_method.trace('w', update_method_fields)

    # Type de template
    template_type_label = ttk.Label(scrollable_frame, text="Type Template :")
    template_type_label.grid(row=2, column=0, sticky="w", pady=1, padx=(5,5))
    selected_template_type = tk.StringVar(value="chat")
    template_type_combobox = ttk.Combobox(scrollable_frame, textvariable=selected_template_type,
                                          values=["chat", "completion (futur)", "embedding (futur)"], 
                                          state="readonly", width=60)
    template_type_combobox.grid(row=2, column=1, columnspan=2, sticky="w", pady=1, padx=(0,5))

    # Modèle LLM spécifique
    llm_model_label = ttk.Label(scrollable_frame, text="Modèle LLM :")
    llm_model_label.grid(row=3, column=0, sticky="w", pady=1, padx=(5,5))
    selected_llm_model = tk.StringVar(value="")
    llm_model_combobox = ttk.Combobox(scrollable_frame, textvariable=selected_llm_model, 
                                      state="readonly", width=60)
    llm_model_combobox.grid(row=3, column=1, columnspan=2, sticky="w", pady=1, padx=(0,5))

    # Fonction pour charger les modèles depuis un fichier JSON
    def load_models_from_json(provider, template_type="chat"):
        """
        Charge les modèles depuis le fichier modeles.json du provider
        
        Args:
            provider: nom du provider (gemini, claude, etc.)
            template_type: type de template (chat par défaut)
        
        Returns:
            tuple: (liste des modèles, modèle par défaut)
        """
        import json
        
        models_file = f"templates/{template_type}/{provider}/modeles.json"
        
        try:
            with open(models_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                models = data.get('models', [])
                default_model = data.get('default', models[0] if models else "")
                print(f"[DEBUG] Modèles chargés depuis {models_file}: {len(models)} modèles")
                return models, default_model
        except FileNotFoundError:
            print(f"[DEBUG] Fichier modèles introuvable: {models_file}, utilisation fallback")
            return get_fallback_models(provider), ""
        except Exception as e:
            print(f"[DEBUG] Erreur lecture fichier modèles {models_file}: {e}")
            return get_fallback_models(provider), ""

    def get_fallback_models(provider):
        """Modèles de fallback si le fichier JSON n'existe pas"""
        fallback_models = {
            "openai": ["gpt-5-mini-2025-08-07", "gpt-5-2025-08-07", "gpt-5-nano-2", "gpt-4.1-2025-04-14", "gpt-4o", "gpt-4o-mini", "gpt-4o-turbo", "gpt-oss-120b", "gpt-oss-20b", "o4-mini-deep-research-2025-06-26"],
            "gemini": ["gemini-1.5-flash", "gemini-2.0-flash-lite", "gemini-2.0-flash", "gemini-2.5-flash"],
            "claude": ["claude-3-5-haiku-20241022", "claude-3-7-sonnet-20250219", "claude-sonnet-4-20250514", "claude-opus-4-20250514"],
            "anthropic": ["claude-3-5-haiku-20241022", "claude-3-7-sonnet-20250219", "claude-sonnet-4-20250514", "claude-opus-4-20250514"],
            "grok": ["grok-3-mini", "grok-3", "grok-4", "grok-4-0709"],
            "qwen": ["qwen-flash", "qwen-turbo", "qwen-omni-turbo", "qwen-max", "qwen/qwen3-coder:free"],
            "mistral": ["mistral-medium-2508", "magistral-medium-2507", "ministral-8b-2410", "ministral-3b-2410", "mistral-small-2407", "codestral-2508", "devstral-medium-2507"],
            "kimi": ["moonshotai/kimi-k2", "moonshotai/kimi-dev-72b:free", "moonshotai/kimi-vl-a3b-thinking", "moonshotai/moonlight-16b-a3b-instruct"],
            "deepseek": ["deepseek/deepseek-r1-0528-qwen3-8b:free", "deepseek-chat", "deepseek-reasoning"],
            "lmstudio": ["lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF", "TheBloke/Mistral-7B-Instruct-v0.2-GGUF", "TheBloke/CodeLlama-34B-Instruct-GGUF", "google/gemma-3-1b", "lmstudio-community/gemma-3-12b-it-GGUF", "lmstudio-community/MiniCPM-V-2_6-GGUF"]
        }
        return fallback_models.get(provider, ["model-default"])

    # Fonction pour mettre à jour les modèles disponibles selon le provider
    def mettre_a_jour_modeles(*args):
        provider = selected_model.get().lower()
        template_type = selected_template_type.get()
        
        # Charger les modèles depuis le fichier JSON
        models, default_model = load_models_from_json(provider, template_type)
        
        llm_model_combobox['values'] = models
        if models:
            # Utiliser le modèle par défaut du JSON ou le premier si pas spécifié
            selected_llm_model.set(default_model if default_model else models[0])
        
        # IMPORTANT: Charger le template selon le provider et sa méthode
        # Ceci assure que le changement de provider charge le bon template
        print(f"[DEBUG] mettre_a_jour_modeles: provider changed to {provider}")
        # Note: mettre_a_jour_placeholders() sera appelée après et gérera le profil complet
    
    # Bind pour mise à jour automatique des modèles
    selected_model.trace('w', mettre_a_jour_modeles)

    def mettre_a_jour_placeholders(*args):
        """Met à jour tous les placeholders quand le provider change + charge le profil complet"""
        # Petit délai pour éviter les conflits avec mettre_a_jour_modeles
        import time
        time.sleep(0.1)
        
        provider = selected_model.get().lower()
        if provider:
            print(f"[DEBUG] mettre_a_jour_placeholders: Changement de provider vers: {provider}")
            
            # 1. Charger le profil correspondant au nouveau provider
            try:
                # Chercher le profil correspondant (avec première lettre majuscule)
                profil_name = provider.capitalize()
                profil_data = charger_donnees_profil(profil_name)
                
                if profil_data:
                    print(f"[DEBUG] Profil {profil_name} trouvé, chargement des données...")
                    
                    # 2. Mettre à jour la méthode selon le profil
                    profile_method = profil_data.get('method', 'curl')
                    print(f"[DEBUG] Méthode du profil {profil_name}: {profile_method}")
                    print(f"[DEBUG] selected_method avant: {selected_method.get()}")
                    selected_method.set(profile_method)
                    print(f"[DEBUG] selected_method après: {selected_method.get()}")
                    print(f"[DEBUG] Méthode mise à jour: {profile_method}")
                    
                    # 3. Charger les autres données du profil
                    if "placeholder_model" in profil_data:
                        placeholder_model_var.set(profil_data["placeholder_model"])
                    if "placeholder_user_prompt" in profil_data:
                        user_prompt_var.set(profil_data["placeholder_user_prompt"])
                    if "placeholder_role" in profil_data:
                        placeholder_role_var.set(profil_data["placeholder_role"])
                    if "placeholder_behavior" in profil_data:
                        set_behavior_text(profil_data["placeholder_behavior"])  # Utiliser la fonction pour Text widget
                    if "placeholder_api_key" in profil_data:
                        replace_apikey_var.set(profil_data["placeholder_api_key"])
                    
                    # 4. Charger le template selon la méthode du profil (explicite)
                    load_template_by_method(provider, "chat", method=profile_method)
                    print(f"[DEBUG] Template {profile_method} chargé pour {provider}")
                    
                    # 5. Forcer la mise à jour de l'interface (labels, champs)
                    update_method_fields()
                    print(f"[DEBUG] Interface mise à jour pour méthode {profile_method}")
                    
                else:
                    print(f"[DEBUG] Aucun profil trouvé pour {profil_name}, utilisation des valeurs par défaut")
                    # Fallback vers méthode curl et extraction depuis templates
                    selected_method.set('curl')
                    
                    template_id = f"{provider}_chat"
                    valeurs_defaut = extraire_valeurs_par_defaut_du_template(template_id)
                    if valeurs_defaut:
                        if "placeholder_model" in valeurs_defaut:
                            placeholder_model_var.set(valeurs_defaut["placeholder_model"])
                        if "placeholder_user_prompt" in valeurs_defaut:
                            user_prompt_var.set(valeurs_defaut["placeholder_user_prompt"])
                        if "placeholder_role" in valeurs_defaut:
                            placeholder_role_var.set(valeurs_defaut["placeholder_role"])
                        if "placeholder_behavior" in valeurs_defaut:
                            set_behavior_text(valeurs_defaut["placeholder_behavior"])  # Utiliser la fonction pour Text widget
                        if "placeholder_api_key" in valeurs_defaut:
                            replace_apikey_var.set(valeurs_defaut["placeholder_api_key"])
                    
                    # Charger template curl par défaut
                    load_template_by_method(provider, "chat")
                    
            except Exception as e:
                print(f"[DEBUG] Erreur chargement profil {provider}: {e}")
                # En cas d'erreur, revenir à curl par défaut
                selected_method.set('curl')
                load_template_by_method(provider, "chat")
    
    # Bind pour mise à jour automatique des placeholders quand provider change
    selected_model.trace('w', mettre_a_jour_placeholders)

    def extraire_modele_du_template(template_content: str, provider: str) -> str:
        """Extrait le modèle du template curl pour compatibilité"""
        if not template_content:
            return ""
            
        if provider == "openai" and '"model":' in template_content:
            import re
            match = re.search(r'"model":\s*"([^"]+)"', template_content)
            return match.group(1) if match else ""
        elif provider == "gemini" and "models/" in template_content:
            import re
            match = re.search(r'models/([^:?]+)', template_content)
            return match.group(1) if match else ""
        elif provider == "claude" and '"model":' in template_content:
            import re
            match = re.search(r'"model":\s*"([^"]+)"', template_content)
            return match.group(1) if match else ""
        elif provider == "deepseek" and '"model":' in template_content:
            import re
            match = re.search(r'"model":\s*"([^"]+)"', template_content)
            return match.group(1) if match else ""
        
        return ""

    def extraire_valeurs_par_defaut_du_template(template_id: str) -> dict:
        """
        ÉTAPE 1: Extraction correcte basée sur la directive v2
        1. Lit curl_basic.txt pour identifier les placeholders (structure du formulaire)
        2. Lit curl.txt pour extraire les valeurs par défaut correspondantes
        """
        try:
            # Construire les chemins vers les deux fichiers template
            provider = template_id.split('_')[0]
            template_type = template_id.split('_')[1]
            basic_template_path = f"templates/{template_type}/{provider}/curl_basic.txt"
            concrete_template_path = f"templates/{template_type}/{provider}/curl.txt"
            
            import os
            import re
            
            # ÉTAPE 1A: Lire curl_basic.txt pour identifier les placeholders
            basic_full_path = os.path.join(".", basic_template_path)
            if not os.path.exists(basic_full_path):
                print(f"Template basic introuvable : {basic_full_path}")
                return {}
                
            with open(basic_full_path, 'r', encoding='utf-8') as f:
                basic_content = f.read()
            
            # Identifier tous les placeholders dans curl_basic.txt
            placeholders_found = re.findall(r'\{\{([^}]+)\}\}', basic_content)
            print(f"[DEBUG] Placeholders trouvés dans {template_id}: {placeholders_found}")
            
            # ÉTAPE 1B: Lire curl.txt pour extraire les valeurs par défaut
            concrete_full_path = os.path.join(".", concrete_template_path)
            if not os.path.exists(concrete_full_path):
                print(f"Template concret introuvable : {concrete_full_path}")
                return {}
                
            with open(concrete_full_path, 'r', encoding='utf-8') as f:
                concrete_content = f.read()
            
            valeurs_defaut = {}
            
            # ÉTAPE 1C: Pour chaque placeholder trouvé, extraire sa valeur du fichier concret
            for placeholder in placeholders_found:
                if placeholder == "API_KEY":
                    # Extraire la clé API
                    api_key_patterns = [
                        r'Bearer \$([A-Z_]+)',        # OpenAI/Claude/Mistral: Bearer $OPENAI_API_KEY
                        r'x-goog-api-key: \$([A-Z_]+)',  # Gemini: x-goog-api-key: $GEMINI_API_KEY
                        r'x-api-key: \$([A-Z_]+)',    # Claude: x-api-key: $CLAUDE_API_KEY
                    ]
                    for pattern in api_key_patterns:
                        match = re.search(pattern, concrete_content)
                        if match:
                            valeurs_defaut["placeholder_api_key"] = f"${match.group(1)}"
                            break
                
                elif placeholder == "LLM_MODEL":
                    # Extraire le modèle LLM
                    model_patterns = [
                        r'"model":\s*"([^"]+)"',  # OpenAI/Claude/Mistral: "model": "gpt-5"
                        r'models/([^:?&\s/]+)',   # Gemini: models/gemini-2.5-flash
                    ]
                    for pattern in model_patterns:
                        match = re.search(pattern, concrete_content)
                        if match:
                            valeurs_defaut["placeholder_model"] = match.group(1)
                            break
                
                elif placeholder == "USER_PROMPT":
                    # Extraire le prompt utilisateur avec gestion spécifique par provider
                    provider = template_id.split('_')[0]
                    
                    if provider == "claude":
                        # Claude: structure complexe avec content array et "text" field
                        text_pattern = r'"text":\s*"([^"]+)"'
                        matches = re.findall(text_pattern, concrete_content, re.DOTALL)
                        if matches:
                            valeurs_defaut["placeholder_user_prompt"] = matches[-1]  # Dernier text trouvé
                    
                    elif provider in ["kimi", "qwen"]:
                        # Kimi/Qwen: Prendre le PREMIER message user, pas l'assistant
                        user_msg_pattern = r'"role":\s*"user"[^}]*"content":\s*"([^"]+)"'
                        match = re.search(user_msg_pattern, concrete_content, re.DOTALL)
                        if match:
                            valeurs_defaut["placeholder_user_prompt"] = match.group(1)
                    
                    else:
                        # Autres providers: patterns standards
                        user_prompt_patterns = [
                            (r'"input":\s*"([^"]+)"', 1),  # OpenAI: "input": "prompt"
                            (r'"contents":\s*\[.*?"text":\s*"([^"]+)"', 1),  # Gemini contents (2ème text)
                            (r'"content":\s*"([^"]+)"', -1),  # Mistral: dernier "content"
                            (r'"messages":\s*\[.*?"content":\s*"([^"]+)"', -1),  # OpenRouter: dernier message content
                        ]
                        for pattern, index in user_prompt_patterns:
                            if index == -1:  # Prendre le dernier match
                                matches = re.findall(pattern, concrete_content, re.DOTALL)
                                if matches:
                                    valeurs_defaut["placeholder_user_prompt"] = matches[-1]
                                    break
                            else:  # Prendre le match à l'index donné
                                matches = re.findall(pattern, concrete_content, re.DOTALL)
                                if len(matches) >= index:
                                    valeurs_defaut["placeholder_user_prompt"] = matches[index-1]
                                    break
                
                elif placeholder == "SYSTEM_PROMPT_ROLE":
                    # Extraire le rôle système avec gestion spécifique par provider
                    provider = template_id.split('_')[0]
                    
                    if provider == "claude":
                        # Claude: "system": "Assistant, spécialisé en code moderne"
                        system_pattern = r'"system":\s*"([^"]+)"'
                        match = re.search(system_pattern, concrete_content)
                        if match:
                            system_text = match.group(1)
                            # Séparer rôle et comportement par virgule
                            if ',' in system_text:
                                parts = system_text.split(',', 1)
                                valeurs_defaut["placeholder_role"] = parts[0].strip()
                                if "SYSTEM_PROMPT_BEHAVIOR" in placeholders_found:
                                    valeurs_defaut["placeholder_behavior"] = parts[1].strip()
                            else:
                                valeurs_defaut["placeholder_role"] = system_text
                    
                    elif provider in ["kimi", "qwen"]:
                        # Kimi/Qwen: prendre le message assistant content
                        assistant_pattern = r'"role":\s*["\']assistant["\'][^}]*"content":\s*"([^"]+)"'
                        match = re.search(assistant_pattern, concrete_content, re.DOTALL)
                        if match:
                            assistant_text = match.group(1)
                            # Si pas de virgule, tout va dans role
                            if ',' in assistant_text:
                                parts = assistant_text.split(',', 1)
                                valeurs_defaut["placeholder_role"] = parts[0].strip()
                                if "SYSTEM_PROMPT_BEHAVIOR" in placeholders_found:
                                    valeurs_defaut["placeholder_behavior"] = parts[1].strip()
                            else:
                                valeurs_defaut["placeholder_role"] = assistant_text
                    
                    else:
                        # Autres providers: patterns standards
                        system_prompt_patterns = [
                            r'"instructions":\s*"([^"]+)"',  # OpenAI: "instructions": "system"
                            r'"system_instruction".*?"text":\s*"([^"]+)"',  # Gemini system_instruction
                            r'"role":\s*"system"[^}]*"content":\s*"([^"]+)"',  # Messages avec role system
                        ]
                        system_text = None
                        for pattern in system_prompt_patterns:
                            match = re.search(pattern, concrete_content, re.DOTALL)
                            if match:
                                system_text = match.group(1)
                                break
                        
                        if system_text:
                            # Séparer rôle et comportement si possible
                            if ',' in system_text:  # "Talk like a pirate, be funny"
                                parts = system_text.split(',', 1)
                                valeurs_defaut["placeholder_role"] = parts[0].strip()
                                if "SYSTEM_PROMPT_BEHAVIOR" in placeholders_found:
                                    valeurs_defaut["placeholder_behavior"] = parts[1].strip()
                            elif '. ' in system_text:  # "You are a cat. Your name is Neko."
                                parts = system_text.split('. ', 1)
                                valeurs_defaut["placeholder_role"] = parts[0].strip()
                                if "SYSTEM_PROMPT_BEHAVIOR" in placeholders_found and len(parts) > 1:
                                    behavior = parts[1].strip()
                                    if behavior.endswith('.'):
                                        behavior = behavior[:-1]
                                    valeurs_defaut["placeholder_behavior"] = behavior
                            else:
                                # Pas de séparation évidente, tout va dans le rôle
                                valeurs_defaut["placeholder_role"] = system_text
                
                elif placeholder == "SYSTEM_PROMPT_BEHAVIOR":
                    # Géré dans SYSTEM_PROMPT_ROLE si les deux existent
                    pass
            
            print(f"[DEBUG] Valeurs extraites pour {template_id}: {valeurs_defaut}")
            return valeurs_defaut
            
        except Exception as e:
            print(f"Erreur lors de l'extraction des valeurs par défaut: {e}")
            return {}

    def creer_champs_dynamiques(placeholders_found: list, valeurs_defaut: dict):
        """
        LOGIQUE SIMPLE ET SOLID: 
        1. VIDER et MASQUER tous les champs
        2. AFFICHER et PRÉREMPLIR seulement les champs nécessaires
        """
        print(f"[DEBUG] Création champs dynamiques pour placeholders: {placeholders_found}")
        
        # Dictionnaire de mapping des champs existants
        champs_mapping = {
            "LLM_MODEL": {
                "label": placeholder_model_label,
                "entry": placeholder_model_entry,
                "var": placeholder_model_var,
                "row": 4,
                "text": "Placeholder Modèle LLM :",
                "value_key": "placeholder_model"
            },
            "SYSTEM_PROMPT_ROLE": {
                "label": placeholder_role_label, 
                "entry": placeholder_role_entry,
                "var": placeholder_role_var,
                "row": 6,
                "text": "Placeholder Rôle :",
                "value_key": "placeholder_role"
            },
            "SYSTEM_PROMPT_BEHAVIOR": {
                "label": placeholder_behavior_label,
                "entry": placeholder_behavior_entry,  # Widget Entry
                "var": placeholder_behavior_var,
                "row": 8,
                "text": "Placeholder Comportement :",
                "value_key": "placeholder_behavior"
            },
            "USER_PROMPT": {
                "label": user_prompt_label,
                "entry": user_prompt_entry,
                "var": user_prompt_var,
                "row": 9,
                "text": "Placeholder User Prompt :",
                "value_key": "placeholder_user_prompt"
            },
            "API_KEY": {
                "label": replace_apikey_label,
                "entry": replace_apikey_entry,
                "var": replace_apikey_var,
                "row": 11,
                "text": "Placeholder Clé API :",
                "value_key": "placeholder_api_key"
            }
        }
        
        # ÉTAPE 1: VIDER et MASQUER TOUS LES CHAMPS (reset complet)
        print("[DEBUG] ÉTAPE 1: Reset complet de tous les champs")
        for placeholder, config in champs_mapping.items():
            try:
                # Vider le champ
                config["var"].set("")
                # Masquer le champ
                config["label"].grid_remove()
                config["entry"].grid_remove()
                print(f"[DEBUG] Champ {placeholder} vidé et masqué")
            except Exception as e:
                print(f"[DEBUG] Erreur reset {placeholder}: {e}")
        
        # ÉTAPE 2: AFFICHER et PRÉREMPLIR seulement les champs nécessaires
        print(f"[DEBUG] ÉTAPE 2: Affichage des champs nécessaires: {placeholders_found}")
        for placeholder in placeholders_found:
            if placeholder in champs_mapping:
                config = champs_mapping[placeholder]
                
                print(f"[DEBUG] Traitement champ {placeholder}")
                
                # Afficher le champ
                config["label"].grid(row=config["row"], column=0, sticky="w", pady=3, padx=(10,5))
                config["entry"].grid(row=config["row"], column=1, columnspan=2, sticky="ew", pady=3, padx=(0,10))
                
                # Forcer le bon texte du label
                config["label"].config(text=config["text"])
                
                # Préremplir avec la valeur par défaut (ou vide si pas de valeur)
                if config["value_key"] in valeurs_defaut:
                    config["var"].set(valeurs_defaut[config["value_key"]])
                    print(f"[DEBUG] Champ {placeholder} prérempli avec: {valeurs_defaut[config['value_key']]}")
                else:
                    config["var"].set("")  # Assurer que c'est vide
                    print(f"[DEBUG] Champ {placeholder} laissé vide (pas de valeur)")
        
        print(f"[DEBUG] Reset et création dynamique terminés")

    def update_form_with_llm_data(template_id: str):
        """
        ÉTAPE 2: Orchestration complète du processus
        1. Extrait les placeholders et valeurs du template
        2. Crée les champs dynamiques correspondants
        3. Prérempli les champs avec les valeurs par défaut
        4. Charge le contenu template selon la méthode (curl ou native)
        """
        print(f"[DEBUG] Mise à jour formulaire pour template: {template_id}")
        
        # Étape 1: Extraction des données
        valeurs_defaut = extraire_valeurs_par_defaut_du_template(template_id)
        
        # Déterminer les placeholders présents (depuis curl_basic.txt)
        provider = template_id.split('_')[0]
        template_type = template_id.split('_')[1]
        basic_template_path = f"templates/{template_type}/{provider}/curl_basic.txt"
        
        import os
        import re
        placeholders_found = []
        
        basic_full_path = os.path.join(".", basic_template_path)
        if os.path.exists(basic_full_path):
            with open(basic_full_path, 'r', encoding='utf-8') as f:
                basic_content = f.read()
            placeholders_found = re.findall(r'\{\{([^}]+)\}\}', basic_content)
        
        print(f"[DEBUG] Orchestration: placeholders={placeholders_found}, valeurs={valeurs_defaut}")
        
        # Étape 2: Création et configuration dynamique des champs
        creer_champs_dynamiques(placeholders_found, valeurs_defaut)
        
        # Étape 3: Charger le contenu template selon la méthode (centralisé)
        load_template_by_method(provider, template_type)
        
        return valeurs_defaut

    # Placeholder Modèle LLM
    placeholder_model_label = ttk.Label(scrollable_frame, text="Placeholder Modèle LLM :")
    placeholder_model_label.grid(row=4, column=0, sticky="w", pady=1, padx=(5,5))
    placeholder_model_var = tk.StringVar(value="")
    placeholder_model_entry = ttk.Entry(scrollable_frame, textvariable=placeholder_model_var, width=60)
    placeholder_model_entry.grid(row=4, column=1, columnspan=2, sticky="w", pady=1, padx=(0,5))

    # Champs pour les placeholders - CORRECTION ARCHITECTE
    # Champ Rôle
    role_label = ttk.Label(scrollable_frame, text="Rôle :")
    role_label.grid(row=5, column=0, sticky="w", pady=1, padx=(5,5))
    role_var = tk.StringVar(value="")
    role_entry = ttk.Entry(scrollable_frame, textvariable=role_var, width=60)
    role_entry.grid(row=5, column=1, columnspan=2, sticky="w", pady=1, padx=(0,5))

    # Placeholder Rôle
    placeholder_role_label = ttk.Label(scrollable_frame, text="Placeholder Rôle :")
    placeholder_role_label.grid(row=6, column=0, sticky="w", pady=1, padx=(5,5))
    placeholder_role_var = tk.StringVar(value="")
    placeholder_role_entry = ttk.Entry(scrollable_frame, textvariable=placeholder_role_var, width=60)
    placeholder_role_entry.grid(row=6, column=1, columnspan=2, sticky="w", pady=1, padx=(0,5))

    # Comportement Enregistré - Textarea avec 3 lignes et scrollbar
    default_behavior_label = ttk.Label(scrollable_frame, text="Comportement par Défaut :")
    default_behavior_label.grid(row=7, column=0, sticky="nw", pady=1, padx=(5,5))
    
    # Frame pour le textarea avec scrollbar
    default_behavior_frame = ttk.Frame(scrollable_frame)
    default_behavior_frame.grid(row=7, column=1, columnspan=2, sticky="w", pady=1, padx=(0,5))
    default_behavior_frame.grid_columnconfigure(0, weight=0)
    
    # Textarea avec scrollbar verticale (3 lignes) - largeur uniforme
    default_behavior_text = tk.Text(default_behavior_frame, height=3, width=60, wrap=tk.WORD)
    default_behavior_scrollbar = ttk.Scrollbar(default_behavior_frame, orient="vertical", command=default_behavior_text.yview)
    default_behavior_text.configure(yscrollcommand=default_behavior_scrollbar.set)
    
    default_behavior_text.grid(row=0, column=0, sticky="w")
    default_behavior_scrollbar.grid(row=0, column=1, sticky="ns")
    
    # Variable pour compatibilité avec le code existant
    default_behavior_var = tk.StringVar(value="")
    
    # Fonctions helper pour synchroniser StringVar avec Text widget
    def set_default_behavior_text(value):
        """Met à jour le contenu du Text widget"""
        default_behavior_text.delete(1.0, tk.END)
        default_behavior_text.insert(1.0, value)
    
    def get_default_behavior_text():
        """Récupère le contenu du Text widget"""
        return default_behavior_text.get(1.0, tk.END).strip()
    
    # Synchroniser avec StringVar pour compatibilité
    def on_default_behavior_text_change(*args):
        default_behavior_var.set(get_default_behavior_text())
    
    default_behavior_text.bind('<KeyRelease>', on_default_behavior_text_change)
    default_behavior_text.bind('<Button-1>', on_default_behavior_text_change)

    # Placeholder Comportement - Entry simple sur 1 ligne
    placeholder_behavior_label = ttk.Label(scrollable_frame, text="Placeholder Comportement :")
    placeholder_behavior_label.grid(row=8, column=0, sticky="nw", pady=3, padx=(10,5))
    
    # Entry simple au lieu de Text widget multi-lignes
    placeholder_behavior_var = tk.StringVar(value="")
    placeholder_behavior_entry = ttk.Entry(scrollable_frame, textvariable=placeholder_behavior_var, width=60)
    placeholder_behavior_entry.grid(row=8, column=1, columnspan=2, sticky="w", pady=1, padx=(0,5))
    
    # Fonctions helper pour compatibilité avec le code existant
    def set_behavior_text(value):
        placeholder_behavior_var.set(value)
    
    # Placeholder User Prompt
    user_prompt_label = ttk.Label(scrollable_frame, text="Placeholder User Prompt :")
    user_prompt_label.grid(row=9, column=0, sticky="w", pady=1, padx=(5,5))
    user_prompt_var = tk.StringVar(value="")
    user_prompt_entry = ttk.Entry(scrollable_frame, textvariable=user_prompt_var, width=60)
    user_prompt_entry.grid(row=9, column=1, columnspan=2, sticky="w", pady=1, padx=(0,5))

    # Clé API
    api_key_label = ttk.Label(scrollable_frame, text="Clé API :")
    api_key_label.grid(row=10, column=0, sticky="w", pady=1, padx=(5,5))
    api_key_var = tk.StringVar(value="")
    api_key_entry = ttk.Entry(scrollable_frame, textvariable=api_key_var, show="*", width=60)
    api_key_entry.grid(row=10, column=1, columnspan=2, sticky="w", pady=1, padx=(0,5))

    # Placeholder Clé API - DIRECTEMENT SOUS CLÉ API
    replace_apikey_label = ttk.Label(scrollable_frame, text="Placeholder Clé API :")
    replace_apikey_label.grid(row=11, column=0, sticky="w", pady=1, padx=(5,5))
    replace_apikey_var = tk.StringVar(value="")
    replace_apikey_entry = ttk.Entry(scrollable_frame, textvariable=replace_apikey_var, width=60)
    replace_apikey_entry.grid(row=11, column=1, columnspan=2, sticky="w", pady=1, padx=(0,5))

    # Checkboxes Historique et Défaut sur la même ligne
    # Frame pour contenir les checkboxes côte à côte
    checkboxes_frame = ttk.Frame(scrollable_frame)
    checkboxes_frame.grid(row=12, column=0, columnspan=3, sticky="ew", pady=(2,1), padx=(5,5))  # Réduire espacement
    
    # Historique - colonne 0
    history_checkbutton_var = tk.BooleanVar(value=False)
    history_checkbutton = ttk.Checkbutton(checkboxes_frame, text="Historique", variable=history_checkbutton_var)
    history_checkbutton.grid(row=0, column=0, sticky="w", padx=(0,20))

    # Case à cocher pour définir le profil par défaut - colonne 1
    default_profile_var = tk.BooleanVar(value=False)
    default_profile_checkbutton = ttk.Checkbutton(checkboxes_frame, text="Défaut", variable=default_profile_var)
    default_profile_checkbutton.grid(row=0, column=1, sticky="w")

    # Champ Structure réponse - Textarea 2 lignes
    response_path_label = ttk.Label(scrollable_frame, text="Structure réponse :")
    response_path_label.grid(row=13, column=0, sticky="nw", pady=(2,1), padx=(5,5))
    
    # Frame pour le textarea avec scrollbar
    response_path_frame = ttk.Frame(scrollable_frame)
    response_path_frame.grid(row=13, column=1, columnspan=2, sticky="w", pady=(2,1), padx=(0,5))
    response_path_frame.grid_columnconfigure(0, weight=0)
    
    # Textarea avec scrollbar verticale - largeur uniforme
    response_path_text = tk.Text(response_path_frame, height=2, width=60, wrap="word")
    response_path_scrollbar = ttk.Scrollbar(response_path_frame, orient="vertical", command=response_path_text.yview)
    response_path_text.configure(yscrollcommand=response_path_scrollbar.set)
    
    response_path_text.grid(row=0, column=0, sticky="w")
    response_path_scrollbar.grid(row=0, column=1, sticky="ns")

    # Fonction pour récupérer le contenu du champ response_path
    def get_response_path_text():
        """Récupère le contenu du Text widget response_path"""
        content = response_path_text.get(1.0, tk.END).strip()
        if content:
            try:
                # Essayer de parser comme JSON si ça ressemble à un array
                if content.startswith('[') and content.endswith(']'):
                    import json
                    return json.loads(content)
                else:
                    # Sinon traiter comme une chaîne de chemin (ex: "candidates.0.content.parts.0.text")
                    return content.replace('.', ',').split(',')
            except:
                # En cas d'erreur, traiter comme une simple chaîne
                return content.split(',') if ',' in content else [content]
        return ["candidates", 0, "content", "parts", 0, "text"]  # Valeur par défaut
    
    # Fonction pour définir le contenu du champ response_path
    def set_response_path_text(value):
        """Met à jour le contenu du Text widget response_path"""
        response_path_text.delete(1.0, tk.END)
        if isinstance(value, list):
            # Convertir la liste en format lisible
            import json
            display_value = json.dumps(value, ensure_ascii=False)
        else:
            display_value = str(value)
        response_path_text.insert(1.0, display_value)

    # Commande curl - Textarea multi-lignes - RAPPROCHÉ DU CHAMP RESPONSE_PATH
    curl_exe_label = ttk.Label(scrollable_frame, text="Commande curl :")
    curl_exe_label.grid(row=15, column=0, sticky="nw", pady=(1,3), padx=(5,5))  # Décalé à la ligne 15
    
    # Frame pour le textarea avec scrollbar
    curl_frame = ttk.Frame(scrollable_frame)
    curl_frame.grid(row=15, column=1, columnspan=2, sticky="w", pady=(1,3), padx=(0,5))  # Décalé à la ligne 15
    curl_frame.grid_columnconfigure(0, weight=0)
    
    # Textarea avec scrollbar verticale - largeur uniforme
    curl_exe_text = tk.Text(curl_frame, height=5, width=60, wrap=tk.WORD)
    curl_exe_scrollbar = ttk.Scrollbar(curl_frame, orient="vertical", command=curl_exe_text.yview)
    curl_exe_text.configure(yscrollcommand=curl_exe_scrollbar.set)
    
    curl_exe_text.grid(row=0, column=0, sticky="w")
    curl_exe_scrollbar.grid(row=0, column=1, sticky="ns")
    
    # Variable pour compatibilité avec le code existant
    curl_exe_var = tk.StringVar(value="")
    native_exe_var = tk.StringVar(value="")  # Variable séparée pour le contenu native
    
    # Fonctions helper pour synchroniser StringVar avec Text widget
    def set_curl_text(value):
        """Met à jour le contenu du Text widget selon la méthode sélectionnée"""
        curl_exe_text.delete(1.0, tk.END)
        curl_exe_text.insert(1.0, value)
        
        # Sauvegarder dans la bonne variable selon la méthode actuelle
        current_method = selected_method.get()
        if current_method == "curl":
            # Sauvegarder dans curl_exe_var interne (pas le Text widget)
            original_set(value)
        else:  # native
            # Sauvegarder dans native_exe_var
            native_exe_var.set(value)
    
    def get_curl_text():
        """Récupère le contenu du Text widget"""
        content = curl_exe_text.get(1.0, tk.END).rstrip('\n')
        
        # Sauvegarder aussi dans la bonne variable selon la méthode actuelle
        current_method = selected_method.get()
        if current_method == "curl":
            original_set(content)
        else:  # native
            native_exe_var.set(content)
            
        return content
    
    def switch_template_content():
        """Bascule le contenu affiché selon la méthode sélectionnée"""
        current_method = selected_method.get()
        if current_method == "curl":
            # Afficher le contenu curl stocké
            content = original_get()
        else:  # native
            # Afficher le contenu native stocké
            content = native_exe_var.get()
        
        # Mettre à jour l'affichage sans déclencher la sauvegarde
        curl_exe_text.delete(1.0, tk.END)
        curl_exe_text.insert(1.0, content)
    
    # Redéfinir les méthodes de la StringVar pour utiliser le Text widget
    original_set = curl_exe_var.set
    original_get = curl_exe_var.get
    curl_exe_var.set = set_curl_text
    curl_exe_var.get = get_curl_text

    # Placeholder Command - Nouveau champ sous la commande curl
    placeholder_command_label = ttk.Label(scrollable_frame, text="Placeholder Command :")
    placeholder_command_label.grid(row=14, column=0, sticky="nw", pady=(1,3), padx=(5,5))
    
    # Frame pour le textarea avec scrollbar
    placeholder_command_frame = ttk.Frame(scrollable_frame)
    placeholder_command_frame.grid(row=14, column=1, columnspan=2, sticky="w", pady=(1,3), padx=(0,5))
    placeholder_command_frame.grid_columnconfigure(0, weight=0)
    
    # Textarea avec scrollbar verticale - largeur uniforme
    placeholder_command_text = tk.Text(placeholder_command_frame, height=5, width=60, wrap=tk.WORD)
    placeholder_command_scrollbar = ttk.Scrollbar(placeholder_command_frame, orient="vertical", command=placeholder_command_text.yview)
    placeholder_command_text.configure(yscrollcommand=placeholder_command_scrollbar.set)
    
    placeholder_command_text.grid(row=0, column=0, sticky="w")
    placeholder_command_scrollbar.grid(row=0, column=1, sticky="ns")
    
    # Variable pour compatibilité avec le code existant
    placeholder_command_var = tk.StringVar(value="")
    
    # Fonctions helper pour synchroniser StringVar avec Text widget
    def set_placeholder_command_text(value):
        """Met à jour le contenu du Text widget"""
        placeholder_command_text.delete(1.0, tk.END)
        placeholder_command_text.insert(1.0, value)
    
    def get_placeholder_command_text():
        """Récupère le contenu du Text widget"""
        return placeholder_command_text.get(1.0, tk.END).rstrip('\n')
    
    # Redéfinir les méthodes de la StringVar pour utiliser le Text widget
    original_placeholder_set = placeholder_command_var.set
    original_placeholder_get = placeholder_command_var.get
    placeholder_command_var.set = set_placeholder_command_text
    placeholder_command_var.get = get_placeholder_command_text

    # Charger le profil par défaut au démarrage
    profil_defaut = charger_profil_defaut()
    if profil_defaut:
        donnees_profil = charger_donnees_profil(profil_defaut)
        
        # Utiliser la fonction helper pour le nouveau mapping
        chat_data = charger_donnees_avec_nouveau_mapping(donnees_profil)
        
        # Charger le template selon la méthode sélectionnée
        template_id = donnees_profil.get("template_id", "")
        if template_id:
            # Extraire provider et type du template_id
            provider = template_id.split('_')[0]
            template_type = template_id.split('_')[1] if '_' in template_id else 'chat'
            # Utiliser la fonction centralisée qui respecte la méthode
            load_template_by_method(provider, template_type)
        else:
            # Fallback vers curl_exe pour compatibilité
            curl_exe_var.set(donnees_profil.get("curl_exe", ""))
        
        # Si les placeholders sont vides, essayer de les remplir avec les valeurs par défaut du template
        if template_id:
            valeurs_defaut = extraire_valeurs_par_defaut_du_template(template_id)
            if valeurs_defaut:
                # Toujours remplir avec les valeurs par défaut si elles existent
                if "placeholder_model" in valeurs_defaut:
                    placeholder_model_var.set(valeurs_defaut["placeholder_model"])
                if "placeholder_user_prompt" in valeurs_defaut:
                    user_prompt_var.set(valeurs_defaut["placeholder_user_prompt"])
                if "placeholder_role" in valeurs_defaut:
                    placeholder_role_var.set(valeurs_defaut["placeholder_role"])
                if "placeholder_behavior" in valeurs_defaut:
                    set_behavior_text(valeurs_defaut["placeholder_behavior"])  # Utiliser la fonction pour Text widget
                if "placeholder_api_key" in valeurs_defaut:
                    replace_apikey_var.set(valeurs_defaut["placeholder_api_key"])
        
        # Charger méthode et type template (nouveaux champs V2)
        if chat_data:
            selected_method.set(chat_data.get("method", "curl"))
            print(f"[DEBUG] Méthode chargée depuis chat_data: {chat_data.get('method', 'curl')}")
        else:
            # Fallback pour ancien format
            selected_method.set(donnees_profil.get("method", "curl"))
            print(f"[DEBUG] Méthode chargée depuis donnees_profil (fallback): {donnees_profil.get('method', 'curl')}")
        
        selected_template_type.set(donnees_profil.get("template_type", "chat"))
        
        # Initialiser les modèles et sélectionner le modèle courant
        mettre_a_jour_modeles()
        current_model = donnees_profil.get("llm_model", "")
        if current_model and current_model in llm_model_combobox['values']:
            selected_llm_model.set(current_model)
        else:
            # Extraire le modèle du template curl si disponible
            template_content = curl_exe_var.get()
            model_extracted = extraire_modele_du_template(template_content, profil_defaut.lower())
            if model_extracted:
                selected_llm_model.set(model_extracted)

    def enregistrer_configuration():
        profil_selectionne = selected_model.get()
        if not profil_selectionne:
            messagebox.showerror("Erreur", "Veuillez sélectionner un profil.")
            return

        # Mettre à jour le template avec le modèle sélectionné
        template_content = curl_exe_var.get()
        llm_model = selected_llm_model.get()
        
        if llm_model and template_content:
            template_content = mettre_a_jour_modele_dans_template(template_content, llm_model, profil_selectionne.lower())
            curl_exe_var.set(template_content)

        # 🔧 CORRECTION ARCHITECTE: Charger d'abord le template complet
        # puis modifier seulement les champs saisis par l'utilisateur
        template_path = os.path.join("profiles", f"{profil_selectionne}.json.template")
        
        if os.path.exists(template_path):
            # Charger le template complet avec tous les champs (y compris response_path)
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                print(f"✅ Setup API: Template {profil_selectionne} chargé avec {len(config_data)} champs")
            except Exception as e:
                print(f"❌ Erreur chargement template {template_path}: {e}")
                # Fallback vers ancien système si le template est corrompu
                config_data = {}
        else:
            print(f"⚠️ Template {template_path} introuvable - création profil minimal")
            config_data = {}

        # Mettre à jour seulement les champs modifiés par l'utilisateur SELON LA NOUVELLE STRUCTURE V2
        # Structure V2: organiser les données dans les bonnes sections
        
        # S'assurer que la structure chat existe
        if "chat" not in config_data:
            config_data["chat"] = {
                "method": "curl",
                "values": {},
                "placeholders": {},
                "response_path": ["candidates", 0, "content", "parts", 0, "text"]
            }
        
        # Mettre à jour la section chat.values (données utilisateur)
        config_data["chat"]["values"].update({
            "llm_model": selected_llm_model.get(),
            "api_key": api_key_var.get().strip(),  # Corriger: utiliser api_key_var au lieu de api_key_entry
            "role": role_var.get(),  # Corriger: utiliser role_var au lieu de role_entry
            "behavior": get_default_behavior_text(),  # Utiliser la fonction pour Text widget
            "history": history_checkbutton_var.get(),
            "default": default_profile_var.get()
        })
        
        # Mettre à jour la section chat.placeholders (valeurs par défaut)
        config_data["chat"]["placeholders"].update({
            "placeholder_model": placeholder_model_var.get(),
            "placeholder_api_key": replace_apikey_var.get(),
            "placeholder_role": placeholder_role_var.get(),
            "placeholder_behavior": placeholder_behavior_var.get(),
            "placeholder_user_prompt": user_prompt_var.get()  # Corriger: utiliser user_prompt_var au lieu de user_prompt_entry
        })
        
        # Mettre à jour la méthode et type de template
        config_data["chat"]["method"] = selected_method.get()
        
        # Mettre à jour le response_path depuis le champ de l'interface
        config_data["chat"]["response_path"] = get_response_path_text()
        
        # Données générales du profil (niveau racine)
        config_data.update({
            "name": profil_selectionne
        })
        
        # Assurer que file_generation existe (peut venir du template ou par défaut)
        if "file_generation" not in config_data:
            config_data["file_generation"] = {
                "enabled": False,
                "mode": "simple",
                "simple_config": {
                    "include_question": True,
                    "include_response": True,
                    "base_filename": "conversation",
                    "same_file": True
                },
                "dev_config": {
                    "extension": ".py"
                }
            }

        try:
            # Sauvegarder via ConfigManager
            success = config_manager.save_profile(profil_selectionne, config_data)
            if success:
                # Sauvegarder le template principal selon la méthode sélectionnée
                method = selected_method.get()
                
                # Récupérer le contenu depuis la bonne variable
                if method == "curl":
                    template_content = original_get()  # Contenu curl stocké
                else:  # native
                    template_content = native_exe_var.get()  # Contenu native stocké
                
                if template_content.strip():
                    # Chemin du fichier template selon la méthode
                    if method == "curl":
                        template_filepath = os.path.join("templates", "chat", profil_selectionne.lower(), "curl.txt")
                    else:  # native
                        template_filepath = os.path.join("templates", "chat", profil_selectionne.lower(), "native.py")
                    
                    # Sauvegarder directement dans le bon fichier
                    try:
                        os.makedirs(os.path.dirname(template_filepath), exist_ok=True)
                        with open(template_filepath, 'w', encoding='utf-8') as f:
                            f.write(template_content)
                        print(f"✅ Template {method} sauvegardé: {template_filepath} ({len(template_content)} caractères)")
                    except Exception as e:
                        print(f"❌ Erreur sauvegarde template {method}: {e}")
                
                # Sauvegarder le template placeholder command si fourni
                placeholder_command = placeholder_command_text.get("1.0", tk.END).strip()
                if placeholder_command:
                    # Sauvegarder dans le fichier _basic correspondant
                    if method == "curl":
                        basic_filepath = os.path.join("templates", "chat", profil_selectionne.lower(), "curl_basic.txt")
                    else:  # native
                        basic_filepath = os.path.join("templates", "chat", profil_selectionne.lower(), "native_basic.py")
                    
                    try:
                        os.makedirs(os.path.dirname(basic_filepath), exist_ok=True)
                        with open(basic_filepath, 'w', encoding='utf-8') as f:
                            f.write(placeholder_command)
                        print(f"✅ Placeholder command sauvegardé: {basic_filepath} ({len(placeholder_command)} caractères)")
                    except Exception as e:
                        print(f"❌ Erreur sauvegarde placeholder command: {e}")
                
                # Définir comme profil par défaut si nécessaire
                if default_profile_var.get():
                    config_manager.set_default_profile(profil_selectionne)
                
                messagebox.showinfo("Succès", f"Profil sauvegardé avec succès dans le nouveau format JSON")
            else:
                messagebox.showerror("Erreur", "Erreur lors de la validation/sauvegarde du profil")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde du profil : {e}")

        setup_window.destroy()
    
    def mettre_a_jour_modele_dans_template(template: str, model: str, provider: str) -> str:
        """Met à jour le modèle dans le template curl"""
        import re
        
        if provider == "openai":
            # Remplacer "model": "ancien-model" par "model": "nouveau-model"
            return re.sub(r'"model":\s*"[^"]+"', f'"model": "{model}"', template)
        elif provider == "gemini":
            # Remplacer models/ancien-model: par models/nouveau-model:
            return re.sub(r'models/[^:?]+', f'models/{model}', template)
        elif provider == "claude":
            # Remplacer "model": "ancien-model" par "model": "nouveau-model"
            return re.sub(r'"model":\s*"[^"]+"', f'"model": "{model}"', template)
        elif provider == "deepseek":
            # Remplacer "model": "ancien-model" par "model": "nouveau-model"
            return re.sub(r'"model":\s*"[^"]+"', f'"model": "{model}"', template)
        
        return template

    # Frame pour disposer les boutons côte à côte - dans le cadre scrollable, en bas
    boutons_frame = ttk.Frame(scrollable_frame)
    boutons_frame.grid(row=16, column=0, columnspan=3, pady=(10, 5), padx=(5, 5), sticky="ew")
    
    bouton_enregistrer = ttk.Button(boutons_frame, text="Enregistrer", command=enregistrer_configuration)
    bouton_enregistrer.pack(side="left", padx=(0, 10))

    bouton_annuler = ttk.Button(boutons_frame, text="Annuler", command=setup_window.destroy)
    bouton_annuler.pack(side="left")

    # Charger les données du profil par défaut au démarrage (sans event)
    try:
        profil_selectionne = selected_model.get()
        donnees_profil = charger_donnees_profil(profil_selectionne)
        
        # Utiliser la fonction helper pour le nouveau mapping
        chat_data = charger_donnees_avec_nouveau_mapping(donnees_profil)
        
        # Charger le template selon la méthode sélectionnée
        template_id = donnees_profil.get("template_id", "")
        print(f"[DEBUG] Template ID trouvé: '{template_id}'")
        if template_id:
            # Extraire provider et type du template_id
            provider = template_id.split('_')[0]
            template_type = template_id.split('_')[1] if '_' in template_id else 'chat'
            # Utiliser la fonction centralisée qui respecte la méthode
            load_template_by_method(provider, template_type)
            print(f"[DEBUG] Template chargé avec load_template_by_method pour {template_id}")
        else:
            fallback_curl = donnees_profil.get("curl_exe", "")
            curl_exe_var.set(fallback_curl)
            print(f"[DEBUG] Pas de template_id, utilisation de curl_exe: {len(fallback_curl)} caractères")
        
        print(f"[DEBUG] Profil par défaut chargé avec succès: {profil_selectionne}")
        
        # INITIALISATION DES PLACEHOLDERS - Priorité aux valeurs sauvegardées
        if template_id:
            print(f"[DEBUG] Initialisation des placeholders pour template: {template_id}")
            # D'abord charger le template (structure des champs)
            update_form_with_llm_data(template_id)
            # PUIS appliquer les valeurs sauvegardées par-dessus
            if chat_data and chat_data.get("placeholders"):
                print(f"[DEBUG] Application des placeholders sauvegardés par-dessus le template")
                charger_donnees_avec_nouveau_mapping(donnees_profil)
        else:
            # Template par défaut Gemini si aucun trouvé
            print(f"[DEBUG] Pas de template_id, initialisation Gemini par défaut")
            update_form_with_llm_data("gemini_chat")
            # PUIS appliquer les valeurs sauvegardées par-dessus  
            if chat_data and chat_data.get("placeholders"):
                print(f"[DEBUG] Application des placeholders sauvegardés Gemini par défaut")
                charger_donnees_avec_nouveau_mapping(donnees_profil)
    except Exception as e:
        print(f"[DEBUG] Erreur lors du chargement initial du profil par défaut Setup API: {e}")
        # Valeurs par défaut de sécurité
        user_prompt_var.set("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent")
        role_var.set("assistant IA")
        set_default_behavior_text("utile et informatif")  # Utiliser la fonction pour Text widget

def open_setup_file_menu():
    """Ouvre le formulaire de configuration de génération de fichiers."""
    setup_file_window = tk.Toplevel(root)
    setup_file_window.title("Set Up File")
    setup_file_window.geometry("500x500")
    
    # Variables
    mode_var = tk.StringVar(value="simple")
    include_question_var = tk.BooleanVar(value=True)
    include_response_var = tk.BooleanVar(value=True)
    base_filename_var = tk.StringVar(value="conversation")
    same_file_var = tk.BooleanVar(value=True)
    extension_var = tk.StringVar(value=".py")
    langage_var = tk.StringVar(value="Python")  # Nouvelle variable pour le nom du langage
    enabled_var = tk.BooleanVar(value=False)
    
    # Extensions disponibles
    extensions = [".py", ".js", ".ts", ".html", ".css", ".php", ".rb", ".go", ".kt", ".swift", 
                  ".rs", ".dart", ".vue", ".jsx", ".tsx", ".scss", ".sass", ".less", ".sql", 
                  ".txt", ".md", ".json", ".xml", ".yaml", ".yml", ".c", ".cpp", ".java", ".cs", ".sh", ".csv", ".markup"]
    
    # Correspondance langages/extensions pour interface utilisateur
    langages_extensions = {
        "C": ".c",
        "C++": ".cpp", 
        "C#": ".cs",
        "CSS": ".css",
        "CSV": ".csv",
        "Dart": ".dart",
        "Go": ".go",
        "HTML": ".html",
        "Java": ".java",
        "JavaScript": ".js",
        "JSON": ".json",
        "Kotlin": ".kt",
        "Less": ".less",
        "Markdown": ".md",
        "Markup": ".markup",
        "PHP": ".php",
        "Python": ".py",
        "Ruby": ".rb",
        "Rust": ".rs",
        "Sass": ".sass",
        "SCSS": ".scss",
        "Shell": ".sh",
        "SQL": ".sql",
        "Swift": ".swift",
        "Text": ".txt",
        "TypeScript": ".ts",
        "TypeScript JSX": ".tsx",
        "Vue.js": ".vue",
        "XML": ".xml",
        "YAML": ".yaml",
        "YAML (alt)": ".yml",
        "React JSX": ".jsx"
    }
    
    # Liste des langages triés alphabétiquement
    langages_tries = sorted(langages_extensions.keys())
    
    # Charger la configuration actuelle via ConfigManager
    def charger_config_actuelle():
        try:
            profil_actuel = api_manager.get_default_profile()
            if profil_actuel and "file_generation" in profil_actuel:
                config = profil_actuel["file_generation"]
                enabled_var.set(config.get("enabled", False))
                mode_var.set(config.get("mode", "simple"))
                
                simple_config = config.get("simple_config", {})
                include_question_var.set(simple_config.get("include_question", True))
                include_response_var.set(simple_config.get("include_response", True))
                base_filename_var.set(simple_config.get("base_filename", "conversation"))
                same_file_var.set(simple_config.get("same_file", True))
                
                dev_config = config.get("dev_config", {})
                extension_actuelle = dev_config.get("extension", ".py")
                extension_var.set(extension_actuelle)
                
                # Trouver le langage correspondant à l'extension
                langage_trouve = "Python"  # Défaut
                for langage, ext in langages_extensions.items():
                    if ext == extension_actuelle:
                        langage_trouve = langage
                        break
                langage_var.set(langage_trouve)
        except Exception as e:
            logging.error(f"Erreur lors du chargement de la configuration : {e}")
    
    # Validation des champs
    def valider_formulaire():
        # Si la génération est désactivée, la configuration est toujours valide
        if not enabled_var.get():
            return True
        
        # Si la génération est activée, valider selon le mode
        if mode_var.get() == "simple":
            if not base_filename_var.get().strip():
                return False
            if not (include_question_var.get() or include_response_var.get()):
                return False
        elif mode_var.get() == "development":
            if not extension_var.get().strip():
                return False
        
        return True
    
    # Mise à jour de l'état du bouton
    def update_button_state():
        if valider_formulaire():
            bouton_enregistrer.config(state="normal")
        else:
            bouton_enregistrer.config(state="disabled")
    
    # Mise à jour des panels selon le mode
    def update_panels():
        if mode_var.get() == "simple":
            frame_simple.pack(fill="x", padx=10, pady=5)
            frame_development.pack_forget()
        else:
            frame_simple.pack_forget()
            frame_development.pack(fill="x", padx=10, pady=5)
        update_button_state()
    
    # Interface principale
    main_frame = ttk.Frame(setup_file_window, padding="10")
    main_frame.pack(fill="both", expand=True)
    
    # Titre avec nom de l'API par défaut
    try:
        profil_defaut = api_manager.get_default_profile()
        nom_api = profil_defaut.get('name', 'API') if profil_defaut else "API"
    except:
        nom_api = "API"
    
    title_label = ttk.Label(main_frame, text=f"Configuration de Génération de Fichiers avec l'API {nom_api}", font=("Arial", 12, "bold"))
    title_label.pack(pady=(0, 10))
    
    # Activation de la génération
    enabled_frame = ttk.Frame(main_frame)
    enabled_frame.pack(fill="x", pady=5)
    enabled_checkbox = ttk.Checkbutton(enabled_frame, text="Activer la génération de fichiers", 
                                      variable=enabled_var, command=update_button_state)
    enabled_checkbox.pack(anchor="w")
    
    # Choix du mode
    mode_frame = ttk.LabelFrame(main_frame, text="Mode d'utilisation", padding="10")
    mode_frame.pack(fill="x", pady=10)
    
    mode_simple_radio = ttk.Radiobutton(mode_frame, text="Mode Simple (Conservation)", 
                                       variable=mode_var, value="simple", command=update_panels)
    mode_simple_radio.pack(anchor="w", pady=2)
    
    mode_dev_radio = ttk.Radiobutton(mode_frame, text="Mode Développement (Code)", 
                                    variable=mode_var, value="development", command=update_panels)
    mode_dev_radio.pack(anchor="w", pady=2)
    
    # Panel Mode Simple
    frame_simple = ttk.LabelFrame(main_frame, text="Configuration Mode Simple", padding="10")
    
    include_question_checkbox = ttk.Checkbutton(frame_simple, text="Intégrer la question", 
                                               variable=include_question_var, command=update_button_state)
    include_question_checkbox.pack(anchor="w", pady=2)
    
    include_response_checkbox = ttk.Checkbutton(frame_simple, text="Intégrer la réponse", 
                                              variable=include_response_var, command=update_button_state)
    include_response_checkbox.pack(anchor="w", pady=2)
    
    same_file_checkbox = ttk.Checkbutton(frame_simple, text="Écrire dans le même fichier", 
                                        variable=same_file_var, command=update_button_state)
    same_file_checkbox.pack(anchor="w", pady=2)
    
    filename_frame = ttk.Frame(frame_simple)
    filename_frame.pack(fill="x", pady=5)
    ttk.Label(filename_frame, text="Nom du fichier :").pack(side="left")
    filename_entry = ttk.Entry(filename_frame, textvariable=base_filename_var, width=20)
    filename_entry.pack(side="left", padx=(5, 0))
    filename_entry.bind('<KeyRelease>', lambda e: update_button_state())
    
    # Panel Mode Développement
    frame_development = ttk.LabelFrame(main_frame, text="Configuration Mode Développement", padding="10")
    
    # Fonction pour mettre à jour l'extension quand le langage change
    def on_langage_change(event=None):
        langage_selectionne = langage_var.get()
        if langage_selectionne in langages_extensions:
            extension_var.set(langages_extensions[langage_selectionne])
        update_button_state()
    
    extension_frame = ttk.Frame(frame_development)
    extension_frame.pack(fill="x", pady=5)
    ttk.Label(extension_frame, text="Langage :").pack(side="left")
    langage_combo = ttk.Combobox(extension_frame, textvariable=langage_var, values=langages_tries, width=20, state="readonly")
    langage_combo.pack(side="left", padx=(5, 0))
    langage_combo.bind('<<ComboboxSelected>>', on_langage_change)
    
    # Affichage de l'extension correspondante (lecture seule)
    extension_info_frame = ttk.Frame(frame_development)
    extension_info_frame.pack(fill="x", pady=5)
    ttk.Label(extension_info_frame, text="Extension :").pack(side="left")
    extension_info_label = ttk.Label(extension_info_frame, textvariable=extension_var, font=("Arial", 9, "italic"))
    extension_info_label.pack(side="left", padx=(5, 0))
    
    # Bouton Enregistrer - créé ici pour être accessible aux fonctions
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x", pady=20)
    
    def enregistrer_config():
        try:
            # Charger le profil actuel via ConfigManager
            profil_actuel = api_manager.get_default_profile()
            
            if not profil_actuel:
                messagebox.showerror("Erreur", "Impossible de charger le profil actuel.")
                return
            
            # Mise à jour de la configuration file_generation
            profil_actuel["file_generation"] = {
                "enabled": enabled_var.get(),
                "mode": mode_var.get(),
                "simple_config": {
                    "include_question": include_question_var.get(),
                    "include_response": include_response_var.get(),
                    "base_filename": base_filename_var.get().strip(),
                    "same_file": same_file_var.get()
                },
                "dev_config": {
                    "extension": extension_var.get().strip()
                }
            }
            
            # Sauvegarder via ConfigManager
            nom_profil = profil_actuel.get('name', 'Gemini')
            success = config_manager.save_profile(nom_profil, profil_actuel)
            
            if success:
                messagebox.showinfo("Succès", f"Configuration de génération sauvegardée pour {nom_profil}")
                setup_file_window.destroy()
                
                # Mettre à jour le profil global pour refléter les changements immédiatement
                global profilAPIActuel
                profilAPIActuel = profil_actuel
                
                logging.info(f"Configuration file_generation mise à jour pour {nom_profil}")
            else:
                messagebox.showerror("Erreur", "Erreur lors de la validation ou sauvegarde du profil")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {e}")
            logging.error(f"Erreur sauvegarde config file : {e}")
    
    bouton_enregistrer = ttk.Button(button_frame, text="Enregistrer", command=enregistrer_config, state="disabled")
    bouton_enregistrer.pack(side="left", padx=(0, 10))
    
    bouton_annuler = ttk.Button(button_frame, text="Annuler", command=setup_file_window.destroy)
    bouton_annuler.pack(side="left")
    
    # Initialisation
    charger_config_actuelle()
    update_panels()
    update_button_state()

def open_setup_history_menu():
    """
    Interface Setup History - Gestion intelligente des conversations
    Intègre le ConversationManager avec tiktoken pour une gestion avancée
    """
    global conversation_manager, config_manager
    
    # Créer la fenêtre principale
    setup_history_window = Toplevel(root)
    setup_history_window.title("🕐 Setup History - Gestion Intelligente des Conversations")
    setup_history_window.geometry("788x656")
    setup_history_window.resizable(True, True)
    
    # Variables pour l'interface
    # Variables pour les modes de déclenchement (checkboxes multiples)
    words_enabled_var = tk.BooleanVar(value=True)
    sentences_enabled_var = tk.BooleanVar(value=True) 
    tokens_enabled_var = tk.BooleanVar(value=True)
    word_threshold_var = tk.IntVar(value=500)
    sentence_threshold_var = tk.IntVar(value=25)
    token_threshold_var = tk.IntVar(value=1000)
    
    # Initialiser avec le profil par défaut directement
    profil_defaut = api_manager.get_default_profile()
    template_initial = f"Template {profil_defaut.get('name', 'Gemini')}" if profil_defaut else "Template Gemini"
    template_var = tk.StringVar(value=template_initial)
    
    # FONCTION DE CHANGEMENT DE TEMPLATE - DANS LE BON SCOPE
    def on_template_change_setup(*args):
        """Fonction appelée quand le template change dans Setup API - met à jour le formulaire dynamiquement"""
        template_name = template_var.get()
        print(f"[DEBUG] Changement template Setup API: {template_name}")
        
        # Extraire le template_id depuis le nom affiché
        if "Template " in template_name:
            profile_name = template_name.replace("Template ", "")
            
            # MAPPING DYNAMIQUE - Auto-détection des templates disponibles
            # Plus de mapping hardcodé - système SOLID qui s'adapte automatiquement
            try:
                # Essayer de charger le profil pour récupérer son template_id
                profile_data = api_manager.load_profile(profile_name)
                if profile_data and 'template_id' in profile_data:
                    template_id = profile_data['template_id']
                    print(f"[DEBUG] Template Setup auto-détecté: {profile_name} -> {template_id}")
                else:
                    # Fallback: construire template_id par convention {provider}_chat
                    template_id = f"{profile_name.lower()}_chat"
                    print(f"[DEBUG] Template Setup fallback: {profile_name} -> {template_id}")
            except Exception as e:
                print(f"[DEBUG] Erreur détection template pour {profile_name}: {e}")
                template_id = "gemini_chat"  # Fallback de sécurité
            
            print(f"[DEBUG] Template détecté pour Setup History: {template_id}")
    
    auto_save_var = tk.BooleanVar(value=True)
    
    # Frame principal avec scrollbar
    main_canvas = tk.Canvas(setup_history_window)
    scrollbar = ttk.Scrollbar(setup_history_window, orient="vertical", command=main_canvas.yview)
    scrollable_frame = ttk.Frame(main_canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
    )
    
    main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    main_canvas.configure(yscrollcommand=scrollbar.set)
    
    # === SECTION 0: PROFIL D'HISTORIQUE ===
    section0 = ttk.LabelFrame(scrollable_frame, text="👤 Profil d'historique", padding=15)
    section0.pack(fill="x", padx=20, pady=10)
    
    # Affichage du profil actuel
    profile_info_frame = ttk.Frame(section0)
    profile_info_frame.pack(fill="x", pady=(0, 10))
    
    def update_profile_display():
        """Met à jour l'affichage du profil actuel"""
        profil_actuel = api_manager.get_default_profile()
        if profil_actuel:
            nom_profil = profil_actuel.get('name', 'Inconnu')
            profile_label.config(text=f"Profil actuel: {nom_profil}")
            # Mettre à jour les templates disponibles selon le profil
            template_combo['values'] = get_available_templates()
            # Recharger la configuration quand le profil change
            load_current_config()
        else:
            profile_label.config(text="Profil actuel: Non défini")
    
    profile_label = ttk.Label(profile_info_frame, text="Profil actuel: Chargement...", font=("Arial", 10, "bold"))
    profile_label.pack(anchor="w")
    
    # Templates de résumé dans le profil d'historique
    template_frame = ttk.Frame(section0)
    template_frame.pack(fill="x", pady=(15, 10))
    
    ttk.Label(template_frame, text="Template de résumé:", font=("Arial", 10, "bold")).pack(anchor="w")
    
    # Note explicative sur la flexibilité
    help_template_label = ttk.Label(template_frame, 
                                   text="Choisissez le profil d'historique à configurer. Vous pouvez associer n'importe quel profil d'historique à n'importe quelle API.", 
                                   font=("Arial", 8, "italic"), foreground="gray", wraplength=400)
    help_template_label.pack(anchor="w", pady=(2, 5))
    
    # Récupérer les templates disponibles depuis les APIs
    def get_available_templates():
        templates = []  # Liste des templates disponibles depuis les profils
        try:
            # Récupérer TOUTES les APIs configurées (pas seulement celles avec historique activé)
            api_profiles = api_manager.list_available_profiles()
            for api_name in api_profiles:
                template_name = f"Template {api_name}"
                if template_name not in templates:
                    templates.append(template_name)
            
            print(f"📋 Templates disponibles: {templates}")
            
        except Exception as e:
            print(f"Erreur récupération templates: {e}")
        return templates
    
    template_combo = ttk.Combobox(template_frame, textvariable=template_var, state="readonly", width=40)
    template_combo['values'] = get_available_templates()
    template_combo.pack(anchor="w", pady=(5, 0))
    
    # Instructions personnalisées pour le résumé
    preview_frame = ttk.Frame(section0)
    preview_frame.pack(fill="x", pady=(10, 0))
    
    ttk.Label(preview_frame, text="Instructions pour le résumé (éditable):", font=("Arial", 9, "bold")).pack(anchor="w")
    
    # Note explicative
    help_label = ttk.Label(preview_frame, text="Ces instructions seront envoyées à l'API pour générer le résumé dans Test API", 
                          font=("Arial", 8, "italic"), foreground="gray")
    help_label.pack(anchor="w", pady=(2, 5))
    
    # Zone de texte éditable pour les instructions personnalisées
    template_preview = tk.Text(
        preview_frame, 
        height=4, 
        wrap=tk.WORD, 
        bg="white",  # Fond blanc pour montrer que c'est éditable
        relief="solid", 
        borderwidth=1,
        font=("Arial", 9)
    )
    template_preview.pack(fill="x", pady=(5, 0))
    
    # === SECTION 1: CONFIGURATION DES SEUILS ===
    section1 = ttk.LabelFrame(scrollable_frame, text="⚖️ Configuration des Seuils", padding=15)
    section1.pack(fill="x", padx=20, pady=10)
    
    # Mode de seuil
    threshold_mode_frame = ttk.Frame(section1)
    threshold_mode_frame.pack(fill="x", pady=(0, 15))
    
    ttk.Label(threshold_mode_frame, text="Types de seuils actifs:", font=("Arial", 10, "bold")).pack(anchor="w")
    
    modes_frame = ttk.Frame(threshold_mode_frame)
    modes_frame.pack(fill="x", pady=(5, 0))
    
    ttk.Checkbutton(modes_frame, text="Contrôler par nombre de mots", variable=words_enabled_var).pack(anchor="w")
    ttk.Checkbutton(modes_frame, text="Contrôler par nombre de phrases", variable=sentences_enabled_var).pack(anchor="w")
    ttk.Checkbutton(modes_frame, text="Contrôler par nombre de tokens", variable=tokens_enabled_var).pack(anchor="w")
    
    # Configuration des seuils individuels
    thresholds_frame = ttk.Frame(section1)
    thresholds_frame.pack(fill="x", pady=(10, 0))
    
    # Seuil de mots
    word_frame = ttk.Frame(thresholds_frame)
    word_frame.pack(fill="x", pady=5)
    ttk.Label(word_frame, text="Seuil de mots:", width=15).pack(side="left")
    word_spinbox = tk.Spinbox(word_frame, from_=100, to=2000, textvariable=word_threshold_var, width=10)
    word_spinbox.pack(side="left", padx=(10, 5))
    ttk.Label(word_frame, text="(100-2000)", font=("Arial", 8, "italic")).pack(side="left")
    
    # Seuil de phrases
    sentence_frame = ttk.Frame(thresholds_frame)
    sentence_frame.pack(fill="x", pady=5)
    ttk.Label(sentence_frame, text="Seuil de phrases:", width=15).pack(side="left")
    sentence_spinbox = tk.Spinbox(sentence_frame, from_=10, to=100, textvariable=sentence_threshold_var, width=10)
    sentence_spinbox.pack(side="left", padx=(10, 5))
    ttk.Label(sentence_frame, text="(10-100)", font=("Arial", 8, "italic")).pack(side="left")
    
    # Seuil de tokens
    token_frame = ttk.Frame(thresholds_frame)
    token_frame.pack(fill="x", pady=5)
    ttk.Label(token_frame, text="Seuil de tokens:", width=15).pack(side="left")
    token_spinbox = tk.Spinbox(token_frame, from_=500, to=4000, textvariable=token_threshold_var, width=10)
    token_spinbox.pack(side="left", padx=(10, 5))
    ttk.Label(token_frame, text="(500-4000)", font=("Arial", 8, "italic")).pack(side="left")
    
    # Variable pour stocker les instructions personnalisées
    custom_instructions_var = tk.StringVar()
    
    # === FONCTIONS D'UPDATE ===
    def update_template_preview(*args):
        """Met à jour seulement les instructions dans le textarea selon le template sélectionné"""
        selected_template = template_var.get()
        
        try:
            if selected_template.startswith("Template "):
                # Instructions pour cette API spécifique
                api_name = selected_template.replace("Template ", "")
                
                # Charger les instructions personnalisées depuis le profil principal
                default_instructions = f"Résume la conversation en utilisant le style et les préférences configurées pour {api_name}. Adapte le résumé au contexte et aux besoins spécifiques de cette API."
                
                main_profile_path = os.path.join("profiles", f"{api_name}.json")
                if os.path.exists(main_profile_path):
                    try:
                        with open(main_profile_path, 'r', encoding='utf-8') as f:
                            template_profile = json.load(f)
                        
                        template_conv_mgmt = template_profile.get("conversation_management", {})
                        custom_instructions = template_conv_mgmt.get("custom_instructions", "")
                        
                        if custom_instructions:
                            default_instructions = custom_instructions
                            
                    except Exception as e:
                        print(f"Erreur chargement instructions {api_name}: {e}")
                        
            else:
                # Template non reconnu
                default_instructions = "Résume la conversation précédente."
            
            # Mettre à jour le textarea uniquement
            template_preview.delete("1.0", tk.END)
            template_preview.insert("1.0", default_instructions)
                
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour du preview: {e}")
            template_preview.delete("1.0", tk.END)
            template_preview.insert("1.0", "Résume la conversation précédente.")
    
    def get_custom_instructions():
        """Récupère les instructions personnalisées saisies par l'utilisateur"""
        return template_preview.get("1.0", tk.END).strip()
    
    def set_custom_instructions(instructions):
        """Définit les instructions personnalisées dans le textarea"""
        template_preview.delete("1.0", tk.END)
        template_preview.insert("1.0", instructions)
    
    
    def load_current_config():
        """Charge la configuration selon le template sélectionné"""
        global conversation_manager
        try:
            selected_template = template_var.get()
            
            # Déterminer le profil à charger selon le template sélectionné
            if selected_template.startswith("Template "):
                # Utiliser le profil correspondant au template
                nom_profil = selected_template.replace("Template ", "")
            else:
                # Fallback sur le profil par défaut si template non reconnu
                profil_actuel = api_manager.get_default_profile()
                if not profil_actuel:
                    print("❌ Aucun profil par défaut défini")
                    return
                nom_profil = profil_actuel.get('name', 'Gemini')
            
            # Charger depuis le profil principal correspondant
            profile_path = os.path.join("profiles", f"{nom_profil}.json")
            
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                
                # Charger la configuration conversation_management si elle existe
                conv_mgmt = profile_data.get("conversation_management", {})
                
                if conv_mgmt:
                    # Charger les seuils
                    word_threshold_var.set(conv_mgmt.get("word_threshold", 300))
                    sentence_threshold_var.set(conv_mgmt.get("sentence_threshold", 15))
                    token_threshold_var.set(conv_mgmt.get("token_threshold", 1000))
                    
                    # Charger les modes actifs
                    words_enabled_var.set(conv_mgmt.get("words_enabled", True))
                    sentences_enabled_var.set(conv_mgmt.get("sentences_enabled", True))
                    tokens_enabled_var.set(conv_mgmt.get("tokens_enabled", False))
                    
                    # Charger l'auto-save
                    auto_save_var.set(conv_mgmt.get("auto_save", True))
                    
                    # Charger le template (maintenant libre, pas forcé au nom du profil)
                    template_var.set(conv_mgmt.get("summary_template", selected_template))
                    
                    # Charger les instructions personnalisées
                    custom_instructions = conv_mgmt.get("custom_instructions", "")
                    if custom_instructions:
                        set_custom_instructions(custom_instructions)
                    else:
                        update_template_preview()
                    
                    print(f"✅ Configuration chargée depuis {profile_path}")
                else:
                    # Créer configuration par défaut
                    default_config = {
                        "words_enabled": True,
                        "sentences_enabled": True,
                        "tokens_enabled": False,
                        "word_threshold": 300,
                        "sentence_threshold": 15,
                        "token_threshold": 1000,
                        "summary_template": selected_template,  # Utilise le template sélectionné
                        "custom_instructions": "Résume la conversation précédente en conservant les points clés et le contexte important.",
                        "auto_save": True
                    }
                    
                    profile_data["conversation_management"] = default_config
                    
                    # Sauvegarder le profil modifié
                    with open(profile_path, 'w', encoding='utf-8') as f:
                        json.dump(profile_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ Configuration par défaut ajoutée à {profile_path}")
                    
                    # Charger les valeurs par défaut dans l'interface
                    word_threshold_var.set(default_config["word_threshold"])
                    sentence_threshold_var.set(default_config["sentence_threshold"])
                    token_threshold_var.set(default_config["token_threshold"])
                    words_enabled_var.set(default_config["words_enabled"])
                    sentences_enabled_var.set(default_config["sentences_enabled"])
                    tokens_enabled_var.set(default_config["tokens_enabled"])
                    auto_save_var.set(default_config["auto_save"])
                    template_var.set(default_config["summary_template"])
                    
                    update_template_preview()
            else:
                print(f"❌ Profil {profile_path} non trouvé")
                update_template_preview()
                
        except Exception as e:
            messagebox.showwarning("Avertissement", f"Erreur lors du chargement: {e}")
            print(f"❌ Erreur chargement config: {e}")
            update_template_preview()
    
    def save_configuration():
        """Sauvegarde la configuration directement dans le profil principal"""
        global conversation_manager
        
        try:
            # 1. Déterminer le profil cible 
            profil_actuel = api_manager.get_default_profile()
            if not profil_actuel:
                messagebox.showerror("Erreur", "Aucun profil par défaut défini")
                return
            
            nom_profil = profil_actuel.get('name', 'Gemini')
            
            # 2. Chemin du profil principal
            profile_path = os.path.join("profiles", f"{nom_profil}.json")
            
            if not os.path.exists(profile_path):
                messagebox.showerror("Erreur", f"Profil principal {profile_path} non trouvé")
                return
            
            # 3. Charger le profil principal
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            # 4. Mettre à jour la section conversation_management
            custom_instructions = get_custom_instructions()
            
            profile_data["conversation_management"] = {
                "words_enabled": words_enabled_var.get(),
                "sentences_enabled": sentences_enabled_var.get(),
                "tokens_enabled": tokens_enabled_var.get(),
                "word_threshold": word_threshold_var.get(),
                "sentence_threshold": sentence_threshold_var.get(),
                "token_threshold": token_threshold_var.get(),
                "summary_template": template_var.get(),
                "custom_instructions": custom_instructions,
                "auto_save": auto_save_var.get()
            }
            
            # 5. Sauvegarder le profil principal modifié
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
            
            # 6. Mettre à jour le ConversationManager si nécessaire
            if conversation_manager:
                conversation_manager.config.update(profile_data["conversation_management"])
                conversation_manager.words_threshold = word_threshold_var.get()
                conversation_manager.sentences_threshold = sentence_threshold_var.get()
                conversation_manager.tokens_threshold = token_threshold_var.get()
                conversation_manager.words_enabled = words_enabled_var.get()
                conversation_manager.sentences_enabled = sentences_enabled_var.get()
                conversation_manager.tokens_enabled = tokens_enabled_var.get()
            
            messagebox.showinfo("Succès", f"Configuration sauvegardée dans le profil {nom_profil}")
            setup_history_window.destroy()
            logging.info(f"Configuration conversation_management sauvegardée: {profile_path}")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")
            logging.error(f"Erreur sauvegarde Setup History: {e}")
            import traceback
            traceback.print_exc()
    
    # === BOUTONS D'ACTION - En bas de la fenêtre, hors du scroll ===
    button_frame = ttk.Frame(setup_history_window)  # Corriger: setup_history_window
    button_frame.pack(fill="x", pady=(10, 5))  # Moins d'espace vertical
    
    # Bouton Sauvegarder
    ttk.Button(
        button_frame, 
        text="💾 Sauvegarder", 
        command=save_configuration
    ).pack(side="left", padx=(0, 10))
    
    # Bouton Annuler
    ttk.Button(
        button_frame, 
        text="❌ Annuler", 
        command=setup_history_window.destroy  # Corriger: setup_history_window
    ).pack(side="left")
    
    # === FONCTIONS D'UPDATE ===
    def on_template_change(*args):
        """Fonction appelée quand le template change - charge la config et met à jour le formulaire dynamiquement"""
        template_name = template_var.get()
        
        # Extraire le template_id depuis le nom affiché
        if "Template " in template_name:
            profile_name = template_name.replace("Template ", "")
            
            # MAPPING DYNAMIQUE - Auto-détection des templates disponibles
            # Plus de mapping hardcodé - système SOLID qui s'adapte automatiquement
            try:
                # Essayer de charger le profil pour récupérer son template_id
                profile_data = api_manager.load_profile(profile_name)
                if profile_data and 'template_id' in profile_data:
                    template_id = profile_data['template_id']
                    print(f"[DEBUG] Template History auto-détecté: {profile_name} -> {template_id}")
                else:
                    # Fallback: construire template_id par convention {provider}_chat
                    template_id = f"{profile_name.lower()}_chat"
                    print(f"[DEBUG] Template History fallback: {profile_name} -> {template_id}")
            except Exception as e:
                print(f"[DEBUG] Erreur détection template pour {profile_name}: {e}")
                template_id = "gemini_chat"  # Fallback de sécurité
            
            # Pas de mise à jour des placeholders ici - cette fonction concerne l'historique, pas Setup API
        
        # Garder les fonctions originales
        update_template_preview()
        load_current_config()
    
    # === INITIALISATION ===
    # Connecter les événements
    template_var.trace_add("write", on_template_change_setup)
    
    # Initialiser l'affichage du profil et définir le template par défaut
    update_profile_display()  
    
    # Définir le template initial basé sur le profil par défaut
    profil_initial = api_manager.get_default_profile()
    if profil_initial:
        nom_profil_initial = profil_initial.get('name', 'Gemini')
        template_var.set(f"Template {nom_profil_initial}")  # Utiliser directement le nom du profil par défaut
    
    # Charger la configuration initiale
    load_current_config()
    update_template_preview()
    
    # Mettre à jour la liste des templates disponibles
    template_combo['values'] = get_available_templates()
    
    # Configuration du scrolling
    main_canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

def creer_interface():
    """Crée l'interface graphique principale avec une barre de menu."""
    global root
    root = tk.Tk()
    root.title("ROB-1")

    # Note: L'initialisation des profils est maintenant gérée par ConfigManager

    # Gestion propre de la fermeture
    def on_closing():
        try:
            root.quit()
            root.destroy()
        except:
            pass

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Barre de menu principale
    menu_bar = Menu(root)

    # Menu Config (anciennement API)
    menu_api = Menu(menu_bar, tearoff=0)
    menu_api.add_command(label="Test API", command=ouvrir_fenetre_apitest)
    menu_api.add_command(label="Set up API", command=open_setup_menu)
    menu_api.add_command(label="Set up File", command=open_setup_file_menu)
    menu_api.add_command(label="Setup History", command=open_setup_history_menu)
    menu_bar.add_cascade(label="Config", menu=menu_api)

    # Configuration de la barre de menu
    root.config(menu=menu_bar)

    # Zone principale pour afficher les résultats
    resultats_text = scrolledtext.ScrolledText(root, width=80, height=20, wrap=tk.WORD)
    resultats_text.pack(pady=10)

    resultats_text.tag_config('reussi', foreground='green')
    resultats_text.tag_config('erreur', foreground='red')

    logging.info("GUI application setup complete.")

    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application fermée par l'utilisateur")
        on_closing()

# Fonction main alternative - non utilisée quand appelée depuis main.py
def main_simple():
    root = tk.Tk()
    root.title("Simple Window")

    # Add a label to the window
    label = ttk.Label(root, text="Welcome to the Simple Window")
    label.pack(pady=20)

    # Add a button to close the application
    close_button = ttk.Button(root, text="Close", command=root.destroy)
    close_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    # Si le fichier est exécuté directement, utiliser l'interface principale
    creer_interface()