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
from conversation_manager import ConversationManager
from system_profile_generator import generate_system_profile_at_startup

# Configure logging to log initialization events
logging.basicConfig(
    filename="application.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Application started.")
logging.info("Initializing new JSON configuration system.")

PROFILES_DIR = "profiles"
CONVERSATIONS_DIR = "conversations"
DEVELOPMENT_DIR = "development"
os.makedirs(PROFILES_DIR, exist_ok=True)
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
os.makedirs(DEVELOPMENT_DIR, exist_ok=True)

# Initialiser le gestionnaire de configuration JSON
config_manager = ConfigManager(".")

# Initialiser le gestionnaire de conversation (sera configuré via Setup History)
conversation_manager = None

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
            "api_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
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
            "api_url": "https://api.openai.com/v1/completions",
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
            "api_url": "https://api.anthropic.com/v1/claude",
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

# Appeler cette fonction au démarrage si aucun fichier JSON n'est trouvé
if not any(f.endswith(".json") and not f.endswith(".json.template") for f in os.listdir(PROFILES_DIR)):
    logging.info("No JSON profiles found. Initializing default profiles.")
    initialiser_profils_par_defaut()
else:
    logging.info("JSON profiles found. Skipping default profile initialization.")

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
        default_profile = config_manager.get_default_profile()
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
        profil_defaut = config_manager.get_default_profile()
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
    Prépare une commande curl robuste et multiplateforme.
    Gère tous les caractères spéciaux de manière fiable sur Windows, Linux et macOS.
    """
    import json
    import re
    import platform
    
    # Nouveau système : utiliser les templates
    template_id = profilAPIActuel.get('template_id', '')
    curl_exe = ""
    
    if template_id:
        template_content = config_manager.load_template(template_id)
        if template_content:
            curl_exe = template_content
        else:
            # Fallback vers curl_exe si le template n'existe pas
            curl_exe = profilAPIActuel.get('curl_exe', '')
    else:
        # Fallback vers curl_exe pour compatibilité
        curl_exe = profilAPIActuel.get('curl_exe', '')
    
    api_key = profilAPIActuel.get('api_key', '')
    replace_apikey = profilAPIActuel.get('replace_apikey', 'GEMINI_API_KEY')
    
    # Détection de l'OS pour l'échappement approprié
    os_type = platform.system().lower()
    is_windows = os_type == 'windows'
    
    # Debug: Log des valeurs initiales
    print(f"[DEBUG] OS détecté: {os_type}")
    print(f"[DEBUG] template_id: {template_id}")
    print(f"[DEBUG] curl_exe initial: {curl_exe[:100]}...")
    print(f"[DEBUG] api_key: {api_key[:10]}..." if api_key else "[DEBUG] api_key: vide")
    print(f"[DEBUG] replace_apikey: {replace_apikey}")
    print(f"[DEBUG] final_prompt: {final_prompt[:100]}...")

    # Remplacer la variable définie dans replace_apikey par la clé API
    if replace_apikey and replace_apikey in curl_exe:
        curl_exe = curl_exe.replace(replace_apikey, api_key)
        print(f"[DEBUG] Après remplacement clé API: {curl_exe[:100]}...")

    try:
        # SOLUTION ROBUSTE MULTIPLATEFORME
        # Étape 1: Extraire la partie JSON de la commande curl
        json_match = re.search(r"-d\s+['\"](.+?)['\"](?:\s|$)", curl_exe, re.DOTALL)
        
        if json_match:
            json_string = json_match.group(1)
            print(f"[DEBUG] JSON extrait: {json_string}")
            
            # Étape 2: Parser le JSON template
            try:
                json_data = json.loads(json_string)
                print(f"[DEBUG] JSON parsé avec succès: {json_data}")
                
                # Étape 3: NORMALISATION DU PROMPT pour éviter les conflits d'échappement
                # Traiter les séquences d'échappement littérales comme du texte normal
                prompt_normalise = final_prompt
                
                # Pas de transformation des séquences - on garde le texte tel quel
                # json.dumps() se chargera de l'échappement correct
                print(f"[DEBUG] Prompt normalisé: {repr(prompt_normalise)}")
                
                # Étape 4: Mettre à jour le texte dans la structure JSON
                # Gestion robuste pour différentes structures d'API
                if 'contents' in json_data:
                    # Format Gemini
                    if isinstance(json_data['contents'], list) and len(json_data['contents']) > 0:
                        if 'parts' in json_data['contents'][0]:
                            if isinstance(json_data['contents'][0]['parts'], list) and len(json_data['contents'][0]['parts']) > 0:
                                json_data['contents'][0]['parts'][0]['text'] = prompt_normalise
                elif 'messages' in json_data:
                    # Format OpenAI/Claude
                    if isinstance(json_data['messages'], list):
                        # Chercher le message utilisateur le plus récent
                        for message in reversed(json_data['messages']):
                            if message.get('role') == 'user':
                                message['content'] = prompt_normalise
                                break
                        else:
                            # Si aucun message utilisateur trouvé, ajouter un nouveau
                            json_data['messages'].append({'role': 'user', 'content': prompt_normalise})
                elif 'prompt' in json_data:
                    # Format simple avec prompt direct
                    json_data['prompt'] = prompt_normalise
                else:
                    # Format inconnu, essayer de trouver un champ text
                    def update_text_recursively(obj, new_text):
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                if key == 'text' and isinstance(value, str):
                                    obj[key] = new_text
                                    return True
                                elif isinstance(value, (dict, list)):
                                    if update_text_recursively(value, new_text):
                                        return True
                        elif isinstance(obj, list):
                            for item in obj:
                                if update_text_recursively(item, new_text):
                                    return True
                        return False
                    
                    update_text_recursively(json_data, prompt_normalise)
                
                # Étape 5: Régénérer le JSON de manière propre et sûre
                # json.dumps gère automatiquement l'échappement des caractères spéciaux
                json_nouveau = json.dumps(json_data, ensure_ascii=False, separators=(',', ':'))
                print(f"[DEBUG] JSON régénéré: {json_nouveau}")
                
                # Étape 6: ÉCHAPPEMENT MULTIPLATEFORME pour la ligne de commande
                if is_windows:
                    # Windows: échapper les guillemets doubles pour cmd/PowerShell
                    json_escaped = json_nouveau.replace('"', '\\"')
                    curl_nouveau = curl_exe.replace(json_match.group(0), f'-d "{json_escaped}"')
                else:
                    # Linux/macOS: utiliser des guillemets simples (plus sûr pour bash)
                    # Échapper seulement les guillemets simples dans le JSON
                    json_escaped = json_nouveau.replace("'", "'\"'\"'")  # Technique bash pour échapper '
                    curl_nouveau = curl_exe.replace(json_match.group(0), f"-d '{json_escaped}'")
                
                print(f"[DEBUG] Commande finale ({os_type}): {curl_nouveau[:200]}...")
                
                # Étape 7: Validation finale - tester que le JSON est toujours valide
                try:
                    if is_windows:
                        # Extraire et tester le JSON Windows
                        test_json = json_escaped.replace('\\"', '"')
                    else:
                        # Extraire et tester le JSON Linux/macOS  
                        test_json = json_escaped.replace("'\"'\"'", "'")
                    
                    json.loads(test_json)
                    print(f"[DEBUG] ✅ JSON final validé avec succès")
                except json.JSONDecodeError as validation_error:
                    print(f"[DEBUG] ⚠️ Attention: JSON final invalide: {validation_error}")
                
                return curl_nouveau
                
            except json.JSONDecodeError as e:
                print(f"[DEBUG] Erreur parsing JSON: {e}, utilisation méthode de secours")
                # Méthode de secours si le JSON n'est pas parsable
                pass
        
        # MÉTHODE DE SECOURS MULTIPLATEFORME
        print("[DEBUG] Utilisation méthode de secours regex")
        
        # Fonction d'échappement sûre selon l'OS
        def escape_for_shell(text, is_windows_os):
            """Échappement adapté à l'OS"""
            if is_windows_os:
                # Windows: échapper pour JSON puis pour shell
                escaped = json.dumps(text, ensure_ascii=False)[1:-1]  # Retirer les guillemets externes
                return escaped.replace('"', '\\"')
            else:
                # Linux/macOS: utiliser l'échappement bash
                return text.replace("'", "'\"'\"'")
        
        final_prompt_escaped = escape_for_shell(final_prompt, is_windows)
        print(f"[DEBUG] Prompt échappé (secours): {final_prompt_escaped}")
        
        # Chercher et remplacer le texte dans le JSON avec regex robuste
        patterns = [
            r'"text":\s*"[^"]*"',     # Pattern Gemini
            r'"content":\s*"[^"]*"',   # Pattern OpenAI/Claude
            r'"prompt":\s*"[^"]*"',    # Pattern simple
        ]
        
        for pattern in patterns:
            match = re.search(pattern, curl_exe)
            if match:
                field_name = match.group().split(':')[0].strip()
                if is_windows:
                    nouveau_text = f'{field_name}: "{final_prompt_escaped}"'
                else:
                    nouveau_text = f"{field_name}: '{final_prompt_escaped}'"
                curl_exe = curl_exe.replace(match.group(), nouveau_text)
                print(f"[DEBUG] Pattern '{pattern}' trouvé et remplacé")
                break
        else:
            # Dernière chance: remplacer le texte par défaut s'il existe
            if "Explain how AI works" in curl_exe:
                if is_windows:
                    curl_exe = curl_exe.replace("Explain how AI works", final_prompt_escaped)
                else:
                    # Pour Linux/macOS, s'assurer que tout est entre guillemets simples
                    curl_exe = curl_exe.replace('"Explain how AI works"', f"'{final_prompt_escaped}'")
                print("[DEBUG] Remplacement texte par défaut effectué")
        
        return curl_exe
        
    except Exception as e:
        print(f"[DEBUG] Erreur inattendue dans preparer_requete_curl: {e}")
        # En cas d'erreur totale, retourner la commande originale
        return curl_exe

    return curl_exe

def corriger_commande_curl(commande):
    """
    Corrige une commande curl de manière robuste et multiplateforme.
    Fonctionne sur Windows, Linux et macOS.
    """
    import json
    import re
    import platform
    
    # Détection de l'OS
    os_type = platform.system().lower()
    is_windows = os_type == 'windows'
    
    print(f"[DEBUG] Correction curl pour OS: {os_type}")
    print(f"[DEBUG] Commande avant correction: {commande[:200]}...")

    try:
        # Nettoyer la commande des continuations de ligne
        commande_corrigee = commande.replace('\\\n', '').replace('\n', '').strip()
        print(f"[DEBUG] Après nettoyage continuations: {commande_corrigee[:200]}...")

        # Normaliser les en-têtes selon l'OS
        if is_windows:
            # Windows: préférer les guillemets doubles
            commande_corrigee = re.sub(r"-H\s+['\"]([^'\"]*)['\"]", r'-H "\1"', commande_corrigee)
        else:
            # Linux/macOS: préférer les guillemets simples pour bash
            commande_corrigee = re.sub(r"-H\s+['\"]([^'\"]*)['\"]", r"-H '\1'", commande_corrigee)
        
        print(f"[DEBUG] Après normalisation en-têtes: {commande_corrigee[:200]}...")

        # Traitement robuste de la partie JSON selon l'OS
        if is_windows:
            # Windows: chercher JSON entre guillemets doubles
            json_match = re.search(r'-d\s+"(.+?)"(?:\s|$)', commande_corrigee, re.DOTALL)
        else:
            # Linux/macOS: chercher JSON entre guillemets simples ou doubles
            json_match = re.search(r"-d\s+['\"](.+?)['\"](?:\s|$)", commande_corrigee, re.DOTALL)
        
        if json_match:
            json_string = json_match.group(1)
            print(f"[DEBUG] JSON extrait pour correction: {json_string}")
            
            try:
                # Pour Windows, dé-échapper d'abord si nécessaire
                if is_windows:
                    json_clean = json_string.replace('\\"', '"')
                else:
                    # Pour Linux/macOS, gérer les échappements bash
                    json_clean = json_string.replace("'\"'\"'", "'")
                
                # Tenter de parser et re-sérialiser proprement
                json_data = json.loads(json_clean)
                json_propre = json.dumps(json_data, ensure_ascii=False, separators=(',', ':'))
                
                print(f"[DEBUG] JSON nettoyé et re-sérialisé: {json_propre}")
                
                # Ré-échapper selon l'OS
                if is_windows:
                    json_escaped = json_propre.replace('"', '\\"')
                    commande_corrigee = commande_corrigee.replace(
                        json_match.group(0), 
                        f'-d "{json_escaped}"'
                    )
                else:
                    json_escaped = json_propre.replace("'", "'\"'\"'")
                    commande_corrigee = commande_corrigee.replace(
                        json_match.group(0), 
                        f"-d '{json_escaped}'"
                    )
                
                print(f"[DEBUG] JSON corrigé et remplacé: {commande_corrigee[:200]}...")
                
            except json.JSONDecodeError:
                print("[DEBUG] JSON non parsable, nettoyage manuel intelligent")
                
                # Nettoyage manuel adapté à l'OS
                if is_windows:
                    # Windows: gérer les échappements Windows
                    json_cleaned = (json_string
                                  .replace('\\"', '"')      # Dé-échapper temporairement
                                  .replace('\\\\', '\\')    # Simplifier backslashes
                                  .replace('\n', '\\n')     # Échapper nouvelles lignes
                                  .replace('\r', '\\r')     # Échapper retours chariot
                                  .replace('\t', '\\t'))    # Échapper tabulations
                    
                    # Ré-échapper pour Windows
                    json_cleaned = json_cleaned.replace('"', '\\"')
                    commande_corrigee = commande_corrigee.replace(
                        json_match.group(0), 
                        f'-d "{json_cleaned}"'
                    )
                else:
                    # Linux/macOS: nettoyage pour bash
                    json_cleaned = (json_string
                                  .replace("'\"'\"'", "'")  # Dé-échapper bash
                                  .replace('\n', '\\n')     # Échapper nouvelles lignes
                                  .replace('\r', '\\r')     # Échapper retours chariot
                                  .replace('\t', '\\t'))    # Échapper tabulations
                    
                    # Ré-échapper pour bash
                    json_cleaned = json_cleaned.replace("'", "'\"'\"'")
                    commande_corrigee = commande_corrigee.replace(
                        json_match.group(0), 
                        f"-d '{json_cleaned}'"
                    )
                
                print(f"[DEBUG] Nettoyage manuel appliqué: {commande_corrigee[:200]}...")

        else:
            print("[DEBUG] Aucune section -d trouvée dans la commande")

        # Vérification finale et normalisation selon l'OS
        if is_windows:
            # Windows: s'assurer que les URLs sont entre guillemets doubles
            commande_corrigee = re.sub(r'curl\s+[\'"]([^\'"]*)[\'"]', r'curl "\1"', commande_corrigee)
        else:
            # Linux/macOS: préférer les guillemets simples pour les URLs
            commande_corrigee = re.sub(r'curl\s+[\'"]([^\'"]*)[\'"]', r"curl '\1'", commande_corrigee)
        
        print(f"[DEBUG] Commande finale corrigée ({os_type}): {commande_corrigee[:200]}...")
        return commande_corrigee

    except Exception as e:
        print(f"[DEBUG] Erreur dans corriger_commande_curl: {e}")
        # En cas d'erreur, retourner la commande originale nettoyée au minimum
        commande_securisee = commande.replace('\\\n', '').replace('\n', '').strip()
        return commande_securisee

def charger_profil_api():
    """
    Charge le profil API par défaut ou retourne Gemini si aucun n'est défini.
    """
    nom_profil_charge, profil = selectionProfilDefaut()
    return profil

def generer_prompt(question, profil):
    """
    Génère le prompt à partir de la question et du profil API.
    """
    role = profil.get('role', '').strip() or "pédagogue"
    behavior = profil.get('behavior', '').strip() or "Précis, synthétique, court avec un résumé en bullet point."
    return (
        f"En tant que {role}, à la fois expert, pédagogue et synthétique, nous attendons de toi le comportement suivant : {behavior}. "
        f"Ma question est la suivante : {question}"
    )

def generer_fichier_development(nom_fichier, extension, reponse):
    """
    Génère un fichier de développement avec gestion de collision avancée.
    """
    try:
        # Validation des paramètres
        if not nom_fichier.strip():
            return False
        
        # Créer le nom complet du fichier
        nom_complet = f"{nom_fichier.strip()}{extension}"
        chemin_fichier = os.path.join(DEVELOPMENT_DIR, nom_complet)
        
        # Vérifier si le fichier existe déjà
        if os.path.exists(chemin_fichier):
            # Créer une fenêtre personnalisée pour les options
            choix_window = tk.Toplevel()
            choix_window.title("Fichier existant")
            choix_window.geometry("400x200")
            choix_window.grab_set()  # Rendre la fenêtre modale
            choix_window.transient()
            
            # Centrer la fenêtre
            choix_window.update_idletasks()
            x = (choix_window.winfo_screenwidth() // 2) - (400 // 2)
            y = (choix_window.winfo_screenheight() // 2) - (200 // 2)
            choix_window.geometry(f"400x200+{x}+{y}")
            
            choix_utilisateur = {"action": None}
            
            # Message
            label_message = ttk.Label(choix_window, 
                                    text=f"Le fichier '{nom_complet}' existe déjà.\nQue souhaitez-vous faire ?",
                                    font=("Arial", 10),
                                    justify="center")
            label_message.pack(pady=20)
            
            # Frame pour les boutons
            frame_boutons = ttk.Frame(choix_window)
            frame_boutons.pack(pady=10)
            
            def choisir_remplacer():
                choix_utilisateur["action"] = "remplacer"
                choix_window.destroy()
            
            def choisir_ajouter():
                choix_utilisateur["action"] = "ajouter"
                choix_window.destroy()
            
            def choisir_annuler():
                choix_utilisateur["action"] = "annuler"
                choix_window.destroy()
            
            # Boutons
            bouton_remplacer = ttk.Button(frame_boutons, text="Remplacer", command=choisir_remplacer)
            bouton_remplacer.pack(side="left", padx=10)
            
            bouton_ajouter = ttk.Button(frame_boutons, text="Ajouter à la fin", command=choisir_ajouter)
            bouton_ajouter.pack(side="left", padx=10)
            
            bouton_annuler = ttk.Button(frame_boutons, text="Annuler", command=choisir_annuler)
            bouton_annuler.pack(side="left", padx=10)
            
            # Attendre que l'utilisateur fasse un choix
            choix_window.wait_window()
            
            # Traiter le choix
            if choix_utilisateur["action"] == "annuler" or choix_utilisateur["action"] is None:
                return False
            elif choix_utilisateur["action"] == "remplacer":
                mode_ecriture = 'w'
            elif choix_utilisateur["action"] == "ajouter":
                mode_ecriture = 'a'
                # Ajouter simplement une ligne vide pour séparer le contenu
                reponse = f"\n\n{reponse}"
        else:
            mode_ecriture = 'w'
        
        # Écrire le fichier selon le mode choisi
        with open(chemin_fichier, mode_ecriture, encoding='utf-8') as fichier:
            fichier.write(reponse)
        
        # Message de succès adapté
        if os.path.exists(chemin_fichier) and mode_ecriture == 'a':
            message_succes = f"Contenu ajouté avec succès à la fin du fichier '{nom_complet}'."
        else:
            message_succes = f"Fichier '{nom_complet}' enregistré avec succès dans le dossier development."
        
        logging.info(f"Fichier développement généré avec succès : {chemin_fichier} (mode: {mode_ecriture})")
        messagebox.showinfo("Succès", message_succes)
        return True
        
    except Exception as e:
        logging.error(f"Erreur lors de la génération du fichier développement : {e}")
        messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {e}")
        return False

def generer_fichier_simple(question, reponse, profil):
    """
    Génère un fichier en mode simple selon la configuration du profil.
    """
    try:
        file_generation_config = profil.get('file_generation', {})
        
        # Vérifier si la génération est activée et en mode simple
        if not file_generation_config.get('enabled', False):
            return
        
        if file_generation_config.get('mode', 'simple') != 'simple':
            return
        
        simple_config = file_generation_config.get('simple_config', {})
        
        # Récupérer les options de configuration
        include_question = simple_config.get('include_question', True)
        include_response = simple_config.get('include_response', True)
        base_filename = simple_config.get('base_filename', 'conversation')
        same_file = simple_config.get('same_file', True)
        
        # Vérifier qu'au moins une option de contenu est activée
        if not (include_question or include_response):
            return
        
        # Préparer le contenu
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        contenu_lines = [f"=== Conversation du {timestamp} ==="]
        
        if include_question and question.strip():
            contenu_lines.append(f"Question : {question}")
        
        if include_response and reponse.strip():
            contenu_lines.append(f"Réponse : {reponse}")
        
        contenu_lines.append("=" * 50)
        contenu_lines.append("")  # Ligne vide pour séparer les conversations
        
        contenu = "\n".join(contenu_lines)
        
        # Déterminer le nom du fichier
        if same_file:
            # Fichier unique
            nom_fichier = f"{base_filename}.txt"
        else:
            # Fichier avec timestamp
            timestamp_fichier = datetime.now().strftime("%Y%m%d_%H%M%S")
            nom_fichier = f"{base_filename}_{timestamp_fichier}.txt"
        
        chemin_fichier = os.path.join(CONVERSATIONS_DIR, nom_fichier)
        
        # Écrire le fichier
        mode = 'a' if same_file else 'w'  # Append si même fichier, Write si nouveau fichier
        with open(chemin_fichier, mode, encoding='utf-8') as fichier:
            fichier.write(contenu)
        
        logging.info(f"Fichier généré avec succès : {chemin_fichier}")
        
    except Exception as e:
        logging.error(f"Erreur lors de la génération du fichier : {e}")

def executer_commande_curl(requete_curl):
    """
    Exécute la commande curl et retourne le résultat.
    Logue la commande et le résultat dans un fichier debug_curl.log.
    """
    # Nettoyer et normaliser la commande curl_exe
    requete_curl = requete_curl.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')

    # Loguer la commande dans debug_curl.log
    with open("debug_curl.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"\n--- Commande exécutée ---\n{requete_curl}\n")

    try:
        # Exécuter la commande sans forcer l'encodage UTF-8
        resultat = subprocess.run(requete_curl, shell=True, capture_output=True, text=False)
        
        # Décoder la sortie avec détection automatique d'encodage
        stdout_decoded = ""
        stderr_decoded = ""
        
        if resultat.stdout:
            try:
                # Essayer UTF-8 d'abord
                stdout_decoded = resultat.stdout.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    # Essayer Windows-1252 (encodage courant Windows)
                    stdout_decoded = resultat.stdout.decode('cp1252')
                except UnicodeDecodeError:
                    try:
                        # Essayer ISO-8859-1 en dernier recours
                        stdout_decoded = resultat.stdout.decode('iso-8859-1')
                    except UnicodeDecodeError:
                        # Forcer avec des caractères de remplacement
                        stdout_decoded = resultat.stdout.decode('utf-8', errors='replace')
        
        if resultat.stderr:
            try:
                stderr_decoded = resultat.stderr.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    stderr_decoded = resultat.stderr.decode('cp1252')
                except UnicodeDecodeError:
                    try:
                        stderr_decoded = resultat.stderr.decode('iso-8859-1')
                    except UnicodeDecodeError:
                        stderr_decoded = resultat.stderr.decode('utf-8', errors='replace')
        
        # Créer un objet résultat avec les chaînes décodées
        class ResultatDecode:
            def __init__(self, returncode, stdout, stderr):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr
        
        resultat_decode = ResultatDecode(resultat.returncode, stdout_decoded, stderr_decoded)
        
    except Exception as e:
        # En cas d'erreur, créer un résultat d'erreur
        class ResultatErreur:
            def __init__(self, erreur):
                self.returncode = 1
                self.stdout = ""
                self.stderr = f"Erreur d'exécution : {erreur}"
        
        resultat_decode = ResultatErreur(e)

    # Loguer le résultat dans debug_curl.log
    with open("debug_curl.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"--- Résultat ---\nCode de retour : {resultat_decode.returncode}\n")
        log_file.write(f"Sortie standard : {resultat_decode.stdout}\n")
        log_file.write(f"Sortie erreur : {resultat_decode.stderr}\n")

    return resultat_decode

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
    """
    champ_r.delete('1.0', tk.END)  # Nettoyer le champ avant d'afficher le résultat

    if resultat.returncode == 0:
        try:
            reponse_json = json.loads(resultat.stdout)

            # Vérifier si la réponse contient des erreurs
            if "error" in reponse_json:
                erreur_message = reponse_json["error"].get("message", "Erreur inconnue")
                champ_r.insert(tk.END, f"Erreur API : {erreur_message}\n")
                return

            # Extraire le texte cible si disponible
            if "candidates" in reponse_json:
                texte_cible = reponse_json["candidates"][0]["content"]["parts"][0]["text"]

                # Corriger l'encodage du texte avant de l'afficher dans le champ R
                texte_cible_corrige = texte_cible.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')

                # Afficher le texte corrigé dans le champ R
                champ_r.insert(tk.END, texte_cible_corrige)

                # Génération de fichier si activée
                question_originale = champ_q.get('1.0', tk.END).strip()
                profil = charger_profil_api()
                generer_fichier_simple(question_originale, texte_cible_corrige, profil)

                # Supprimer le contenu du prompteur Q si la réponse s'est bien déroulée
                champ_q.delete('1.0', tk.END)
            else:
                champ_r.insert(tk.END, "La réponse ne contient pas de candidats valides.\n")
        except Exception as e:
            champ_r.insert(tk.END, f"Erreur lors de l'analyse de la réponse : {e}\n{resultat.stdout}")
    else:
        champ_r.insert(tk.END, f"Erreur lors de l'exécution :\n{resultat.stderr}\n")

# Nouvelle logique avec ConversationManager
def soumettreQuestionAPI(champ_q, champ_r, champ_history, conversation_manager=None, status_label=None):
    """
    Version améliorée avec gestion intelligente de l'historique via ConversationManager
    """
    question = champ_q.get('1.0', tk.END).strip()
    
    champ_r.config(state="normal")
    champ_r.delete('1.0', tk.END)
    
    if not question:
        champ_r.insert('1.0', "Veuillez saisir une question.")
        champ_r.config(state="disabled")
        return

    try:
        # 1. Ajouter la question à l'historique du ConversationManager
        if conversation_manager:
            conversation_manager.add_message('user', question)
            
            # 2. Vérifier si un résumé est nécessaire AVANT l'appel API
            if conversation_manager.should_summarize():
                print("🔄 Seuil atteint - Génération du résumé...")
                champ_r.insert(tk.END, "🔄 Génération du résumé contextuel...\n")
                champ_r.update_idletasks()
                
                # Fonction wrapper pour l'appel API de résumé
                def api_summary_call(prompt_text):
                    profil = charger_profil_api()
                    prompt_avec_profil = generer_prompt(prompt_text, profil)
                    requete_curl = preparer_requete_curl(prompt_avec_profil)
                    requete_curl = corriger_commande_curl(requete_curl)
                    resultat = executer_commande_curl(requete_curl)
                    
                    if resultat.returncode == 0:
                        try:
                            reponse_json = json.loads(resultat.stdout)
                            return reponse_json["candidates"][0]["content"]["parts"][0]["text"]
                        except:
                            return "Erreur lors du résumé"
                    return "Erreur API lors du résumé"
                
                # Générer le résumé
                success = conversation_manager.summarize_history(api_summary_call)
                
                if success:
                    stats = conversation_manager.get_stats()
                    print(f"✅ Résumé #{stats['summary_count']} généré")
                    champ_r.delete('1.0', tk.END)  # Nettoyer le message de progression
                else:
                    print("❌ Échec du résumé - continue avec l'historique complet")
                    champ_r.insert(tk.END, "⚠️ Échec du résumé - conversation continue\n")
            
            # 3. Préparer les messages pour l'API
            api_messages = conversation_manager.get_messages_for_api()
            
            # 4. Construire le prompt final en concaténant tous les messages
            prompt_complet = ""
            for msg in api_messages:
                role_label = "Utilisateur" if msg['role'] == 'user' else "Assistant"
                prompt_complet += f"{role_label}: {msg['parts'][0]['text']}\n"
            
            # Utiliser le prompt complet au lieu de la question simple
            question_finale = prompt_complet.strip()
        else:
            # Fallback vers l'ancienne méthode si pas de ConversationManager
            historique = champ_history.get('1.0', tk.END).strip()
            if profilAPIActuel.get('history', False):
                question_finale = f"{historique}\n{question}".strip()
            else:
                question_finale = question

        # 5. Exécuter l'appel API principal
        profil = charger_profil_api()
        prompt_concatene = generer_prompt(question_finale, profil)
        requete_curl = preparer_requete_curl(prompt_concatene)
        requete_curl = corriger_commande_curl(requete_curl)
        
        resultat = executer_commande_curl(requete_curl)
        
        # 6. Traiter la réponse
        if resultat.returncode == 0:
            try:
                reponse_json = json.loads(resultat.stdout)
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
    if profilAPIActuel.get('history', False):
        # 1. Créer automatiquement le profil backup s'il n'existe pas
        nom_profil = nom_profil_charge.split('.')[0]
        backup_profile_path = os.path.join("profiles_backup_conversation", f"{nom_profil}.json")
        
        try:
            if not os.path.exists(backup_profile_path):
                # Créer le dossier backup s'il n'existe pas
                os.makedirs("profiles_backup_conversation", exist_ok=True)
                
                # Créer un profil backup par défaut
                backup_profile = profilAPIActuel.copy()
                backup_profile["conversation_management"] = {
                    "words_enabled": True,
                    "sentences_enabled": True,
                    "tokens_enabled": False,
                    "word_threshold": 500,
                    "sentence_threshold": 25,
                    "token_threshold": 1000,
                    "summary_template": "défaut",
                    "custom_instructions": "Résume la conversation précédente en conservant les points clés et le contexte important. Garde un ton professionnel et structure ton résumé de manière claire.",
                    "auto_save": True
                }
                
                with open(backup_profile_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_profile, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Profil backup par défaut créé: {backup_profile_path}")
            
            # 2. Charger la configuration depuis le profil backup
            with open(backup_profile_path, 'r', encoding='utf-8') as f:
                backup_profile = json.load(f)
            
            conversation_config = backup_profile.get('conversation_management', {})
            
            # 3. Initialiser ConversationManager avec la configuration du profil backup
            conversation_manager = ConversationManager(
                config_manager=config_manager,
                profile_config=conversation_config
            )
            print(f"✅ ConversationManager initialisé avec config depuis: {backup_profile_path}")
            print(f"   Seuils: {conversation_config.get('word_threshold', 500)}mots, {conversation_config.get('sentence_threshold', 25)}phrases, {conversation_config.get('token_threshold', 1000)}tokens")
            
        except Exception as e:
            # En cas d'erreur (données corrompues), popup et fermeture
            messagebox.showerror("Erreur Configuration", 
                               f"Erreur lors du chargement de la configuration d'historique:\n{e}\n\nLa fenêtre va se fermer.")
            fenetre.destroy()
            return
    else:
        print("ℹ️  Historique désactivé - ConversationManager non initialisé")

    # Création de la commande API (champ caché)
    def creerCommandeAPI(profil):
        if not profil:
            return ""
        
        # Nouveau système : utiliser les templates séparés
        template_id = profil.get('template_id', '')
        if template_id:
            template_content = config_manager.load_template(template_id)
            if template_content:
                # Remplacer la clé API dans le template
                api_key = profil.get('api_key', '')
                replace_key = profil.get('replace_apikey', 'GEMINI_API_KEY')
                if api_key and replace_key:
                    return template_content.replace(replace_key, api_key)
                return template_content
        
        # Fallback : ancien système curl_exe (pour compatibilité)
        curl_exe = profil.get('curl_exe', '')
        api_key = profil.get('api_key', '')
        if curl_exe and api_key:
            return curl_exe.replace('GEMINI_API_KEY', api_key)
        return curl_exe

    cmd_api = creerCommandeAPI(profilAPIActuel)
    fenetre.cmd_api = cmd_api  # champ caché

    # Interface utilisateur
    # Ajout d'un cadre principal pour organiser les widgets
    cadre_principal = ttk.Frame(fenetre, padding="10")
    cadre_principal.pack(fill="both", expand=True)

    # Afficher le nom du profil API par défaut ou le préfixe du fichier
    label_profil = ttk.Label(cadre_principal, text=f"Profil chargé : {nom_profil_charge.split('.')[0]}", font=("Arial", 12, "bold"))
    label_profil.pack(pady=10)
    
    # === INDICATEUR DE STATUT CONVERSATION ===
    if conversation_manager and conversation_manager.show_indicators:
        status_label = ttk.Label(cadre_principal, text="🟢 0/300mots | 0/6phrases", 
                                font=("Arial", 9), foreground="gray")
        status_label.pack(pady=2)
        
        # Mise à jour initiale de l'indicateur
        initial_status = conversation_manager.get_status_indicator()
        status_label.config(text=initial_status)
        
        # Indicateur du profil de résumé utilisé
        def get_resume_profile_info():
            """Récupère les informations sur le profil de résumé depuis la configuration active"""
            try:
                if conversation_manager and hasattr(conversation_manager, 'config'):
                    # Utiliser la configuration du ConversationManager actif
                    template = conversation_manager.config.get("summary_template", "défaut")
                else:
                    # Fallback: lire depuis le profil backup
                    nom_profil = profilAPIActuel.get('name', 'Inconnu')
                    backup_profile_path = os.path.join("profiles_backup_conversation", f"{nom_profil}.json")
                    
                    if os.path.exists(backup_profile_path):
                        with open(backup_profile_path, 'r', encoding='utf-8') as f:
                            backup_profile = json.load(f)
                        conv_mgmt = backup_profile.get("conversation_management", {})
                        template = conv_mgmt.get("summary_template", "défaut")
                    else:
                        template = "défaut"
                
                # Formater l'affichage
                if template.startswith("Template "):
                    template_display = template.replace("Template ", "")
                else:
                    template_display = template
                
                return f"📋 Résumé: {template_display}"
                
            except Exception as e:
                print(f"Erreur récupération profil résumé: {e}")
                return "📋 Résumé: défaut"
        
        resume_profile_label = ttk.Label(cadre_principal, text=get_resume_profile_info(), 
                                        font=("Arial", 9), foreground="blue")
        resume_profile_label.pack(pady=1)

    # Champ Q (question)
    label_q = ttk.Label(cadre_principal, text="Question (Q) :", font=("Arial", 10))
    label_q.pack(anchor="w", pady=5)
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

    bouton_valider = ttk.Button(frame_boutons, text="Envoyer la question", 
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
    setup_window.title("SETUP")

    # Fonction pour charger les profils disponibles
    def charger_profils():
        """Charge les profils via ConfigManager"""
        return config_manager.list_profiles()

    # Fonction pour charger les données d'un profil sélectionné
    def charger_donnees_profil(profil):
        """Charge un profil via ConfigManager avec fallback robuste"""
        try:
            # Essayer d'abord de charger le profil tel quel
            profile_data = config_manager.load_profile(profil)
            if profile_data:
                return profile_data
            
            # Si ça échoue, essayer avec différentes extensions
            for extension in ['.json', '.yaml']:
                try:
                    if not profil.endswith(extension):
                        test_profil = profil + extension
                        profile_data = config_manager.load_profile(test_profil.replace(extension, ''))
                        if profile_data:
                            return profile_data
                except:
                    continue
            
            # Si tout échoue, retourner des valeurs par défaut pour éviter l'erreur
            print(f"[DEBUG] Profil {profil} non trouvé, utilisation des valeurs par défaut")
            return {
                "api_url": "",
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
                "api_url": "",
                "api_key": "",
                "role": "",
                "behavior": "",
                "history": False,
                "default": False,
                "replace_apikey": "",
                "template_id": "gemini_chat" if "gemini" in profil.lower() else ""
            }

    # Fonction pour mettre à jour les champs du formulaire en fonction du profil sélectionné
    def mettre_a_jour_champs(event):
        profil_selectionne = selected_model.get()
        donnees_profil = charger_donnees_profil(profil_selectionne)

        api_url_var.set(donnees_profil.get("api_url", ""))
        api_key_var.set(donnees_profil.get("api_key", ""))
        role_var.set(donnees_profil.get("role", ""))
        default_behavior_var.set(donnees_profil.get("behavior", ""))
        history_checkbutton_var.set(donnees_profil.get("history", False))
        default_profile_var.set(donnees_profil.get("default", False))
        replace_apikey_var.set(donnees_profil.get("replace_apikey", ""))
        
        # Charger le template curl au lieu de curl_exe
        template_id = donnees_profil.get("template_id", "")
        if template_id:
            template_content = config_manager.load_template(template_id)
            curl_exe_var.set(template_content if template_content else "")
        else:
            # Fallback vers curl_exe pour compatibilité
            curl_exe_var.set(donnees_profil.get("curl_exe", ""))

    # Fonction pour définir un seul profil comme défaut
    def definir_profil_defaut(profil_selectionne):
        """Utilise ConfigManager pour définir le profil par défaut"""
        try:
            config_manager.set_default_profile(profil_selectionne)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la mise à jour du profil par défaut : {e}")

    # Charger le profil par défaut au démarrage via ConfigManager
    def charger_profil_defaut():
        """Charge le profil marqué comme défaut via ConfigManager."""
        try:
            profil_defaut = config_manager.get_default_profile()
            if profil_defaut:
                return profil_defaut.get('name', 'Gemini')
            return "Gemini"  # Fallback si aucun profil par défaut
        except Exception as e:
            logging.error(f"Erreur lors du chargement du profil par défaut Setup API : {e}")
            return "Gemini"

    # Choix du modèle (liste déroulante des profils existants)
    model_label = ttk.Label(setup_window, text="Nom de l'API :")
    model_label.grid(row=0, column=0, sticky="w", pady=5)
    selected_model = tk.StringVar(value=charger_profil_defaut())
    model_combobox = ttk.Combobox(setup_window, textvariable=selected_model, values=charger_profils())
    model_combobox.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)
    model_combobox.bind("<<ComboboxSelected>>", mettre_a_jour_champs)

    # Champ Rôle
    role_label = ttk.Label(setup_window, text="Rôle :")
    role_label.grid(row=1, column=0, sticky="w", pady=5)
    role_var = tk.StringVar(value="")
    role_entry = ttk.Entry(setup_window, textvariable=role_var)
    role_entry.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)

    # Comportement Enregistré
    default_behavior_label = ttk.Label(setup_window, text="Comportement par Défaut :")
    default_behavior_label.grid(row=2, column=0, sticky="w", pady=5)
    default_behavior_var = tk.StringVar(value="")
    default_behavior_entry = ttk.Entry(setup_window, textvariable=default_behavior_var)
    default_behavior_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=5)

    # Texte à remplacer
    api_url_label = ttk.Label(setup_window, text="Texte à remplacer :")
    api_url_label.grid(row=3, column=0, sticky="w", pady=5)
    api_url_var = tk.StringVar(value="")
    api_url_entry = ttk.Entry(setup_window, textvariable=api_url_var, width=50)
    api_url_entry.grid(row=3, column=1, columnspan=2, sticky="ew", pady=5)

    # Clé API
    api_key_label = ttk.Label(setup_window, text="Clé API :")
    api_key_label.grid(row=4, column=0, sticky="w", pady=5)
    api_key_var = tk.StringVar(value="")
    api_key_entry = ttk.Entry(setup_window, textvariable=api_key_var, show="*")
    api_key_entry.grid(row=4, column=1, columnspan=2, sticky="ew", pady=5)

    # Historique
    history_checkbutton_var = tk.BooleanVar(value=False)
    history_checkbutton = ttk.Checkbutton(setup_window, text="Historique", variable=history_checkbutton_var)
    history_checkbutton.grid(row=5, column=0, columnspan=2, sticky="w", pady=5)

    # Case à cocher pour définir le profil par défaut
    default_profile_var = tk.BooleanVar(value=False)
    default_profile_checkbutton = ttk.Checkbutton(setup_window, text="Défaut", variable=default_profile_var)
    default_profile_checkbutton.grid(row=6, column=0, columnspan=2, sticky="w", pady=5)

    # Champ replace_apikey
    replace_apikey_label = ttk.Label(setup_window, text="Remplacer API Key :")
    replace_apikey_label.grid(row=7, column=0, sticky="w", pady=5)
    replace_apikey_var = tk.StringVar(value="")
    replace_apikey_entry = ttk.Entry(setup_window, textvariable=replace_apikey_var)
    replace_apikey_entry.grid(row=7, column=1, columnspan=2, sticky="ew", pady=5)

    # Commande curl
    curl_exe_label = ttk.Label(setup_window, text="Commande curl :")
    curl_exe_label.grid(row=8, column=0, sticky="w", pady=5)
    curl_exe_var = tk.StringVar(value="")
    curl_exe_entry = ttk.Entry(setup_window, textvariable=curl_exe_var, width=50)
    curl_exe_entry.grid(row=8, column=1, columnspan=2, sticky="ew", pady=5)

    # Charger le profil par défaut au démarrage
    profil_defaut = charger_profil_defaut()
    if profil_defaut:
        donnees_profil = charger_donnees_profil(profil_defaut)
        api_url_var.set(donnees_profil.get("api_url", ""))
        api_key_var.set(donnees_profil.get("api_key", ""))
        role_var.set(donnees_profil.get("role", ""))
        default_behavior_var.set(donnees_profil.get("behavior", ""))
        history_checkbutton_var.set(donnees_profil.get("history", False))
        default_profile_var.set(donnees_profil.get("default", False))
        replace_apikey_var.set(donnees_profil.get("replace_apikey", ""))
        
        # Charger le template curl au lieu de curl_exe
        template_id = donnees_profil.get("template_id", "")
        if template_id:
            template_content = config_manager.load_template(template_id)
            curl_exe_var.set(template_content if template_content else "")
        else:
            # Fallback vers curl_exe pour compatibilité
            curl_exe_var.set(donnees_profil.get("curl_exe", ""))

    def enregistrer_configuration():
        profil_selectionne = selected_model.get()
        if not profil_selectionne:
            messagebox.showerror("Erreur", "Veuillez sélectionner un profil.")
            return

        config_data = {
            "name": profil_selectionne,
            "api_url": api_url_entry.get(),
            "api_key": api_key_entry.get().strip(),
            "role": role_entry.get(),
            "behavior": default_behavior_var.get(),
            "history": history_checkbutton_var.get(),
            "default": default_profile_var.get(),
            "replace_apikey": replace_apikey_var.get(),
            "template_id": f"{profil_selectionne.lower()}_chat",
            "file_generation": {
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
        }

        try:
            # Sauvegarder via ConfigManager
            success = config_manager.save_profile(profil_selectionne, config_data)
            if success:
                # Sauvegarder le template curl si fourni
                curl_exe = curl_exe_var.get()
                if curl_exe.strip():
                    config_manager.save_template(f"{profil_selectionne.lower()}_chat", curl_exe)
                
                # Définir comme profil par défaut si nécessaire
                if default_profile_var.get():
                    config_manager.set_default_profile(profil_selectionne)
                
                messagebox.showinfo("Succès", f"Profil sauvegardé avec succès dans le nouveau format JSON")
            else:
                messagebox.showerror("Erreur", "Erreur lors de la validation/sauvegarde du profil")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde du profil : {e}")

        setup_window.destroy()

    # Frame pour disposer les boutons côte à côte
    boutons_frame = ttk.Frame(setup_window)
    boutons_frame.grid(row=9, column=0, columnspan=3, pady=10)
    
    bouton_enregistrer = ttk.Button(boutons_frame, text="Enregistrer", command=enregistrer_configuration)
    bouton_enregistrer.pack(side="left", padx=(0, 10))

    bouton_annuler = ttk.Button(boutons_frame, text="Annuler", command=setup_window.destroy)
    bouton_annuler.pack(side="left")

    # Charger les données du profil par défaut au démarrage (sans event)
    try:
        profil_selectionne = selected_model.get()
        donnees_profil = charger_donnees_profil(profil_selectionne)
        
        api_url_var.set(donnees_profil.get("api_url", ""))
        api_key_var.set(donnees_profil.get("api_key", ""))
        role_var.set(donnees_profil.get("role", ""))
        default_behavior_var.set(donnees_profil.get("behavior", ""))
        history_checkbutton_var.set(donnees_profil.get("history", False))
        default_profile_var.set(donnees_profil.get("default", False))
        replace_apikey_var.set(donnees_profil.get("replace_apikey", ""))
        
        # Charger le template curl
        template_id = donnees_profil.get("template_id", "")
        if template_id:
            template_content = config_manager.load_template(template_id)
            curl_exe_var.set(template_content if template_content else "")
        else:
            curl_exe_var.set(donnees_profil.get("curl_exe", ""))
        
        print(f"[DEBUG] Profil par défaut chargé avec succès: {profil_selectionne}")
    except Exception as e:
        print(f"[DEBUG] Erreur lors du chargement initial du profil par défaut Setup API: {e}")
        # Valeurs par défaut de sécurité
        api_url_var.set("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent")
        role_var.set("assistant IA")
        default_behavior_var.set("utile et informatif")

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
                  ".txt", ".md", ".json", ".xml", ".yaml", ".yml", ".c", ".cpp", ".java", ".cs", ".sh"]
    
    # Correspondance langages/extensions pour interface utilisateur
    langages_extensions = {
        "C": ".c",
        "C++": ".cpp", 
        "C#": ".cs",
        "CSS": ".css",
        "Dart": ".dart",
        "Go": ".go",
        "HTML": ".html",
        "Java": ".java",
        "JavaScript": ".js",
        "JSON": ".json",
        "Kotlin": ".kt",
        "Less": ".less",
        "Markdown": ".md",
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
            profil_actuel = config_manager.get_default_profile()
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
        profil_defaut = config_manager.get_default_profile()
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
            profil_actuel = config_manager.get_default_profile()
            
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
    template_var = tk.StringVar(value="Template par défaut")  # Valeur par défaut avec nom clair
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
        profil_actuel = config_manager.get_default_profile()
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
        templates = ["Template par défaut"]  # Template par défaut avec nom plus clair
        try:
            # Récupérer TOUTES les APIs configurées (pas seulement celles avec historique activé)
            api_profiles = config_manager.list_profiles()
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
            if selected_template == "Template par défaut":
                # Instructions par défaut
                default_instructions = "Résume la conversation précédente en conservant les points clés et le contexte important. Garde un ton professionnel et structure ton résumé de manière claire."
                
            elif selected_template.startswith("Template "):
                # Instructions pour cette API spécifique
                api_name = selected_template.replace("Template ", "")
                
                # Essayer de charger les instructions personnalisées depuis le backup
                backup_profile_path = os.path.join("profiles_backup_conversation", f"{api_name}.json")
                default_instructions = f"Résume la conversation en utilisant le style et les préférences configurées pour {api_name}. Adapte le résumé au contexte et aux besoins spécifiques de cette API."
                
                if os.path.exists(backup_profile_path):
                    try:
                        with open(backup_profile_path, 'r', encoding='utf-8') as f:
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
        """Charge la configuration depuis le template sélectionné"""
        global conversation_manager
        try:
            selected_template = template_var.get()
            
            if selected_template == "Template par défaut":
                # Utiliser le profil par défaut
                profil_actuel = config_manager.get_default_profile()
                if profil_actuel:
                    nom_profil = profil_actuel.get('name', 'Gemini')
                else:
                    print("❌ Aucun profil par défaut défini")
                    return
            elif selected_template.startswith("Template "):
                # Utiliser le profil spécifique du template
                nom_profil = selected_template.replace("Template ", "")
            else:
                print(f"❌ Template non reconnu: {selected_template}")
                return
            
            # Charger depuis profiles_backup_conversation
            backup_profile_path = os.path.join("profiles_backup_conversation", f"{nom_profil}.json")
            
            if os.path.exists(backup_profile_path):
                with open(backup_profile_path, 'r', encoding='utf-8') as f:
                    backup_profile = json.load(f)
                
                # Charger la configuration conversation_management si elle existe
                conv_mgmt = backup_profile.get("conversation_management", {})
                
                if conv_mgmt:
                    # Charger les seuils
                    word_threshold_var.set(conv_mgmt.get("word_threshold", 500))
                    sentence_threshold_var.set(conv_mgmt.get("sentence_threshold", 25))
                    token_threshold_var.set(conv_mgmt.get("token_threshold", 1000))
                    
                    # Charger les modes actifs
                    words_enabled_var.set(conv_mgmt.get("words_enabled", True))
                    sentences_enabled_var.set(conv_mgmt.get("sentences_enabled", True))
                    tokens_enabled_var.set(conv_mgmt.get("tokens_enabled", False))
                    
                    # Charger les instructions personnalisées
                    custom_instructions = conv_mgmt.get("custom_instructions", "")
                    if custom_instructions:
                        set_custom_instructions(custom_instructions)
                    else:
                        update_template_preview()
                    
                    print(f"✅ Configuration chargée depuis {backup_profile_path}")
                else:
                    # Aucune configuration conversation_management, utiliser les défauts
                    print(f"⚠️  Aucune config conversation_management dans {nom_profil}, utilisation des défauts")
                    # Garder les valeurs par défaut mais charger les instructions selon le template
                    update_template_preview()
            else:
                # Fichier backup n'existe pas, utiliser les défauts
                print(f"⚠️  Profil backup {backup_profile_path} non trouvé, utilisation des défauts")
                # Charger les instructions par défaut pour ce template
                update_template_preview()
                
        except Exception as e:
            messagebox.showwarning("Avertissement", f"Erreur lors du chargement de la configuration: {e}")
            print(f"❌ Erreur chargement config: {e}")
            update_template_preview()
    
    def save_configuration():
        """Sauvegarde la configuration des préférences Setup History dans le profil sélectionné"""
        global conversation_manager
        
        try:
            # 1. Déterminer le profil cible selon le template sélectionné
            selected_template = template_var.get()
            
            if selected_template == "Template par défaut":
                # Utiliser le profil par défaut
                profil_actuel = config_manager.get_default_profile()
                if profil_actuel:
                    nom_profil = profil_actuel.get('name', 'Gemini')
                else:
                    messagebox.showerror("Erreur", "Aucun profil par défaut défini")
                    return
            elif selected_template.startswith("Template "):
                # Utiliser le profil spécifique du template
                nom_profil = selected_template.replace("Template ", "")
            else:
                messagebox.showerror("Erreur", f"Template non reconnu: {selected_template}")
                return
            
            # 2. Préparer la configuration conversation
            custom_instructions = get_custom_instructions()
            
            config_conv = {
                "word_threshold": word_threshold_var.get(),
                "sentence_threshold": sentence_threshold_var.get(),
                "token_threshold": token_threshold_var.get(),
                "words_enabled": words_enabled_var.get(),
                "sentences_enabled": sentences_enabled_var.get(),
                "tokens_enabled": tokens_enabled_var.get(),
                "summary_template": template_var.get(),
                "custom_instructions": custom_instructions
            }
            
            # 3. Mettre à jour le ConversationManager si nécessaire
            if not conversation_manager:
                conversation_manager = ConversationManager(profile_config=config_conv)
            else:
                conversation_manager.config.update(config_conv)
            
            # 4. Sauvegarder dans le profil backup conversation spécifique
            backup_profile_path = os.path.join("profiles_backup_conversation", f"{nom_profil}.json")
            
            if os.path.exists(backup_profile_path):
                # Charger le profil backup existant
                with open(backup_profile_path, 'r', encoding='utf-8') as f:
                    backup_profile = json.load(f)
            else:
                # Créer un nouveau profil backup basé sur le profil principal
                try:
                    profil_principal = config_manager.load_profile(nom_profil)
                    if profil_principal:
                        backup_profile = profil_principal.copy()
                    else:
                        # Profil principal n'existe pas, créer un profil minimal
                        backup_profile = {
                            "name": nom_profil,
                            "api_key": "",
                            "history": True
                        }
                except:
                    # En cas d'erreur, créer un profil minimal
                    backup_profile = {
                        "name": nom_profil,
                        "api_key": "",
                        "history": True
                    }
                
                print(f"✅ Création nouveau profil backup pour {nom_profil}")
            
            # 5. Mettre à jour la section conversation_management
            backup_profile["conversation_management"] = {
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
            
            # 6. Sauvegarder dans profiles_backup_conversation
            os.makedirs("profiles_backup_conversation", exist_ok=True)
            with open(backup_profile_path, 'w', encoding='utf-8') as f:
                json.dump(backup_profile, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Succès", f"Configuration Setup History sauvegardée pour {nom_profil}\ndans profiles_backup_conversation")
            setup_history_window.destroy()
            logging.info(f"Configuration conversation_management sauvegardée: {backup_profile_path}")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")
            logging.error(f"Erreur sauvegarde Setup History: {e}")
            import traceback
            traceback.print_exc()
    
    # === BOUTONS D'ACTION ===
    button_frame = ttk.Frame(scrollable_frame)
    button_frame.pack(fill="x", padx=20, pady=20)
    
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
        command=setup_history_window.destroy
    ).pack(side="left")
    
    # === FONCTIONS D'UPDATE ===
    def on_template_change(*args):
        """Fonction appelée quand le template change - charge la config et met à jour le preview"""
        update_template_preview()
        load_current_config()
    
    # === INITIALISATION ===
    # Connecter les événements
    template_var.trace_add("write", on_template_change)
    
    # Initialiser l'affichage du profil et définir le template par défaut
    update_profile_display()  
    
    # Définir le template initial basé sur le profil par défaut
    profil_initial = config_manager.get_default_profile()
    if profil_initial:
        nom_profil_initial = profil_initial.get('name', 'Gemini')
        template_var.set("Template par défaut")  # Commencer par défaut avec nouveau nom
    
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

    # === INITIALISATION DES PROFILS D'HISTORIQUE AU DÉMARRAGE ===
    def initialiser_profils_historique():
        """Crée les profils d'historique par défaut au démarrage"""
        try:
            backup_dir = "profiles_backup_conversation"
            os.makedirs(backup_dir, exist_ok=True)
            
            # 1. Créer le profil d'historique par défaut s'il n'existe pas
            default_profile_path = os.path.join(backup_dir, "default.json")
            if not os.path.exists(default_profile_path):
                default_profile = {
                    "name": "default",
                    "api_key": "",
                    "history": True,
                    "conversation_management": {
                        "words_enabled": True,
                        "sentences_enabled": True,
                        "tokens_enabled": False,
                        "word_threshold": 500,
                        "sentence_threshold": 25,
                        "token_threshold": 1000,
                        "summary_template": "Template par défaut",
                        "custom_instructions": "Résume la conversation précédente en conservant les points clés et le contexte important. Garde un ton professionnel et structure ton résumé de manière claire.",
                        "auto_save": True
                    }
                }
                
                with open(default_profile_path, 'w', encoding='utf-8') as f:
                    json.dump(default_profile, f, indent=2, ensure_ascii=False)
                print(f"✅ Profil d'historique par défaut créé: {default_profile_path}")
            
            # 2. Créer les profils d'historique pour toutes les APIs configurées
            try:
                api_profiles = config_manager.list_profiles()
                for api_name in api_profiles:
                    api_profile_path = os.path.join(backup_dir, f"{api_name}.json")
                    
                    if not os.path.exists(api_profile_path):
                        # Charger le profil API principal
                        api_data = config_manager.load_profile(api_name)
                        if api_data:
                            # Créer le profil d'historique basé sur l'API
                            history_profile = api_data.copy()
                            
                            # Ajouter/mettre à jour la section conversation_management
                            history_profile["conversation_management"] = {
                                "words_enabled": True,
                                "sentences_enabled": True,
                                "tokens_enabled": False,
                                "word_threshold": 500,
                                "sentence_threshold": 25,
                                "token_threshold": 1000,
                                "summary_template": f"Template {api_name}",
                                "custom_instructions": f"Résume la conversation en utilisant le style et les préférences configurées pour {api_name}. Adapte le résumé au contexte et aux besoins spécifiques de cette API.",
                                "auto_save": True
                            }
                            
                            with open(api_profile_path, 'w', encoding='utf-8') as f:
                                json.dump(history_profile, f, indent=2, ensure_ascii=False)
                            print(f"✅ Profil d'historique créé pour {api_name}")
            
            except Exception as e:
                print(f"⚠️  Erreur création profils API: {e}")
                
        except Exception as e:
            print(f"❌ Erreur initialisation profils historique: {e}")
    
    # Initialiser les profils d'historique au démarrage
    initialiser_profils_historique()

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

    # Menu API (anciennement Test API)
    menu_api = Menu(menu_bar, tearoff=0)
    menu_api.add_command(label="Test API", command=ouvrir_fenetre_apitest)
    menu_api.add_command(label="Set up API", command=open_setup_menu)
    menu_api.add_command(label="Set up File", command=open_setup_file_menu)
    menu_api.add_command(label="Setup History", command=open_setup_history_menu)
    menu_bar.add_cascade(label="API", menu=menu_api)

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