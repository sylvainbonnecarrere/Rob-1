import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, Toplevel, Menu, PhotoImage
import os
import sys
import yaml
import subprocess
import json
import charset_normalizer
import logging

# Configure logging to log initialization events
logging.basicConfig(
    filename="application.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Application started.")
logging.info("Checking and initializing default profiles.")

PROFILES_DIR = "profiles"
CONVERSATIONS_DIR = "conversations"
DEVELOPMENT_DIR = "development"
os.makedirs(PROFILES_DIR, exist_ok=True)
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
os.makedirs(DEVELOPMENT_DIR, exist_ok=True)

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
        "Gemini.yaml": {
            "api_key": "",
            "api_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            "behavior": "excité, ronchon, répond en une phrase ou deux",
            "curl_exe": "curl \"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=GEMINI_API_KEY\" \\\n  -H 'Content-Type: application/json' \\\n  -X POST \\\n  -d '{\"contents\": [{\"parts\": [{\"text\": \"Explain how AI works\"}]}]}'",
            "default": True,
            "history": True,
            "role": "alien rigolo",
            "replace_apikey": "GEMINI_API_KEY"
        },
        "OpenAI.yaml": {
            "api_key": "",
            "api_url": "https://api.openai.com/v1/completions",
            "behavior": "comportement initial",
            "curl_exe": "",
            "default": False,
            "history": False,
            "model": "OpenAI",
            "replace_apikey": ""
        },
        "Claude.yaml": {
            "api_key": "",
            "api_url": "https://api.anthropic.com/v1/claude",
            "behavior": "comportement initial",
            "curl_exe": "",
            "default": False,
            "history": False,
            "role": "",
            "replace_apikey": ""
        }
    }

    for nom_fichier, contenu in profils_par_defaut.items():
        chemin_fichier = os.path.join(PROFILES_DIR, nom_fichier)
        if not os.path.exists(chemin_fichier):
            with open(chemin_fichier, "w", encoding="utf-8") as fichier:
                yaml.dump(contenu, fichier, default_flow_style=False, allow_unicode=True)

# Appeler cette fonction au démarrage si aucun fichier YAML n'est trouvé
if not any(f.endswith(".yaml") for f in os.listdir(PROFILES_DIR)):
    logging.info("No YAML profiles found. Initializing default profiles.")
    initialiser_profils_par_defaut()
else:
    logging.info("YAML profiles found. Skipping default profile initialization.")

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
    """Charge le profil par défaut ou retourne Gemini si aucun n'est défini."""
    for fichier in os.listdir(PROFILES_DIR):
        if fichier.endswith(".yaml"):
            chemin_fichier = os.path.join(PROFILES_DIR, fichier)
            with open(chemin_fichier, 'r', encoding='utf-8') as f:
                profil = yaml.safe_load(f)
                if profil.get("default", False):
                    return fichier[:-5]  # Retirer l'extension .yaml
    return "Gemini"  # Retourne Gemini par défaut si aucun profil n'est marqué comme défaut

def selectionProfilDefaut():
    """
    Parcourt les fichiers de profils dans 'profiles/', cherche le profil par défaut ('default: True'),
    charge son contenu avec chargementProfil, sinon charge 'Gemini' par défaut.
    Affiche le nom du profil chargé en haut de la fenêtre testAPI et logue le contenu.
    """
    import yaml
    import os
    global profilAPIActuel
    profils_dir = "profiles"
    profil_trouve = False
    nom_profil_charge = None

    for fichier in os.listdir(profils_dir):
        if fichier.endswith(".yaml") or fichier.endswith(".yml") or fichier.endswith(".json"):
            chemin_fichier = os.path.join(profils_dir, fichier)
            try:
                with open(chemin_fichier, "r", encoding="utf-8") as f:
                    if fichier.endswith(".json"):
                        import json
                        profil = json.load(f)
                    else:
                        profil = yaml.safe_load(f)
                if profil and profil.get("default", False):
                    profilAPIActuel = profil
                    nom_profil_charge = fichier
                    profil_trouve = True
                    break
            except Exception as e:
                pass

    if not profil_trouve:
        chemin_gemini = os.path.join(profils_dir, "Gemini.yaml")
        if os.path.exists(chemin_gemini):
            with open(chemin_gemini, "r", encoding="utf-8") as f:
                profilAPIActuel = yaml.safe_load(f)
            nom_profil_charge = "Gemini.yaml"
        else:
            profilAPIActuel = {}
            nom_profil_charge = "Aucun profil trouvé"

    return nom_profil_charge, profilAPIActuel

# Correction pour s'assurer que GEMINI_API_KEY est remplacé correctement

def preparer_requete_curl(final_prompt):
    """
    Prépare une commande curl en utilisant le final_prompt et retourne une chaîne de caractères.
    """
    curl_exe = profilAPIActuel.get('curl_exe', '')
    api_key = profilAPIActuel.get('api_key', '')
    replace_apikey = profilAPIActuel.get('replace_apikey', '')
    
    # Debug: Log des valeurs initiales
    print(f"[DEBUG] curl_exe initial: {curl_exe[:100]}...")
    print(f"[DEBUG] api_key: {api_key[:10]}..." if api_key else "[DEBUG] api_key: vide")
    print(f"[DEBUG] replace_apikey: {replace_apikey}")
    print(f"[DEBUG] final_prompt: {final_prompt[:100]}...")

    # Remplacer la variable définie dans replace_apikey par la clé API si elle est spécifiée
    if replace_apikey and replace_apikey in curl_exe:
        curl_exe = curl_exe.replace(replace_apikey, api_key)
        print(f"[DEBUG] Après remplacement clé API: {curl_exe[:100]}...")

    # Remplacer uniquement le texte dans le JSON, pas dans l'URL
    # Chercher le pattern "text": "..." dans le JSON
    import re
    pattern = r'"text":\s*"[^"]*"'
    match = re.search(pattern, curl_exe)
    if match:
        # Échapper les caractères spéciaux pour JSON
        final_prompt_escaped = (final_prompt
                               .replace('\\', '\\\\')  # Échapper les backslash d'abord
                               .replace('"', '\\"')    # Puis les guillemets
                               .replace('\n', '\\n')   # Retours à la ligne
                               .replace('\r', '\\r')   # Retours chariot
                               .replace('\t', '\\t'))  # Tabulations
        nouveau_text = f'"text": "{final_prompt_escaped}"'
        curl_exe = curl_exe.replace(match.group(), nouveau_text)
        print(f"[DEBUG] Après remplacement du texte JSON: {curl_exe[:100]}...")
    else:
        print(f"[DEBUG] Pattern text JSON non trouvé, utilisation méthode de fallback")
        # Fallback : remplacer seulement "Explain how AI works" si présent
        if "Explain how AI works" in curl_exe:
            final_prompt_escaped = (final_prompt
                                   .replace('\\', '\\\\')  # Échapper les backslash d'abord
                                   .replace('"', '\\"')    # Puis les guillemets
                                   .replace('\n', '\\n')   # Retours à la ligne
                                   .replace('\r', '\\r')   # Retours chariot
                                   .replace('\t', '\\t'))  # Tabulations
            curl_exe = curl_exe.replace("Explain how AI works", final_prompt_escaped)
            print(f"[DEBUG] Fallback appliqué: {curl_exe[:100]}...")

    return curl_exe

def corriger_commande_curl(commande):
    """
    Corrige une commande curl pour Windows en échappant correctement les guillemets et en reformattant le JSON.
    """
    import json
    
    print(f"[DEBUG] Commande avant correction: {commande[:200]}...")

    # Supprimer les barres obliques inverses et les sauts de ligne
    commande_corrigee = commande.replace('\\\n', '').replace('\n', '').strip()
    print(f"[DEBUG] Après nettoyage: {commande_corrigee[:200]}...")

    # Identifier et reformater les données JSON dans la commande
    if '-d' in commande_corrigee:
        try:
            # Extraire la partie JSON après '-d'
            debut_json = commande_corrigee.index('-d') + 2
            json_brut = commande_corrigee[debut_json:].strip()
            print(f"[DEBUG] JSON brut extrait: {json_brut[:200]}...")

            # Nettoyer les guillemets simples au début et à la fin
            json_brut = json_brut.strip("'\"")
            
            # Vérifier si le JSON est valide avant de le reformater
            json_data = json.loads(json_brut)  # Charger en tant qu'objet Python
            json_valide = json.dumps(json_data, ensure_ascii=False, separators=(',', ':'))  # JSON compact

            # Échapper les guillemets pour Windows et nettoyer les doubles échappements
            json_valide = json_valide.replace('\\\\', '\\')  # Réduire les doubles backslash
            json_valide = json_valide.replace('"', '\\"')    # Échapper pour Windows

            # Remplacer l'ancien JSON par le nouveau
            commande_corrigee = commande_corrigee[:debut_json] + f' "{json_valide}"'
            print(f"[DEBUG] Après correction JSON: {commande_corrigee[:200]}...")
        except json.JSONDecodeError as e:
            print(f"[DEBUG] Erreur JSON: {e}")
            print(f"[DEBUG] Tentative de récupération du JSON...")
            
            # Essayer de récupérer en extrayant seulement le JSON valide
            try:
                # Chercher les accolades ouvrantes et fermantes pour isoler le JSON
                start_brace = json_brut.find('{')
                if start_brace != -1:
                    # Compter les accolades pour trouver la fermeture
                    brace_count = 0
                    end_pos = start_brace
                    for i, char in enumerate(json_brut[start_brace:], start_brace):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_pos = i + 1
                                break
                    
                    json_recupere = json_brut[start_brace:end_pos]
                    print(f"[DEBUG] JSON récupéré: {json_recupere[:200]}...")
                    
                    json_data = json.loads(json_recupere)
                    json_valide = json.dumps(json_data, ensure_ascii=False, separators=(',', ':'))
                    # Nettoyer les doubles échappements avant d'échapper pour Windows
                    json_valide = json_valide.replace('\\\\', '\\')  # Réduire les doubles backslash
                    json_valide = json_valide.replace('"', '\\"')    # Échapper pour Windows
                    commande_corrigee = commande_corrigee[:debut_json] + f' "{json_valide}"'
                    print(f"[DEBUG] JSON récupéré et corrigé: {commande_corrigee[:200]}...")
                else:
                    print(f"[DEBUG] Impossible de récupérer le JSON, conservation de l'original")
            except Exception as e2:
                print(f"[DEBUG] Échec de récupération JSON: {e2}")
                # En dernier recours, nettoyer manuellement
                print(f"[DEBUG] Nettoyage manuel du JSON...")
                # Nettoyer les caractères problématiques
                json_brut_clean = (json_brut
                                 .replace('\n', '\\n')
                                 .replace('\r', '\\r')
                                 .replace('\\\\', '\\')  # Réduire les doubles backslash
                                 .replace('\\"', '"'))   # Dé-échapper temporairement
                
                # Ré-échapper pour Windows
                json_brut_clean = json_brut_clean.replace('"', '\\"')
                commande_corrigee = commande_corrigee[:debut_json] + f' "{json_brut_clean}"'
        except Exception as e:
            print(f"[DEBUG] Erreur correction JSON: {e}")

    # Remplacer les guillemets simples dans les en-têtes par des guillemets doubles
    commande_corrigee = commande_corrigee.replace("'Content-Type: application/json'", '"Content-Type: application/json"')
    
    print(f"[DEBUG] Commande finale: {commande_corrigee[:200]}...")
    return commande_corrigee

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

# Correction pour s'assurer que l'historique est bien concaténé avec le prompt Q et envoyé comme valeur
def soumettreQuestionAPI(champ_q, champ_r, champ_history):
    question = champ_q.get('1.0', tk.END).strip()

    # Log du contenu de l'historique et du prompt Q
    historique = champ_history.get('1.0', tk.END).strip()
    log_variable = f"Historique discussion : {historique} \nNouvelle question : {question}"
    print(log_variable)

    # Transformation du prompt Q si history est activé
    if profilAPIActuel.get('history', False):
        question = f"{historique}\n{question}".strip()

    champ_r.config(state="normal")
    champ_r.delete('1.0', tk.END)
    if not question:
        champ_r.insert('1.0', "Veuillez saisir une question.")
        champ_r.config(state="disabled")
        return

    profil = charger_profil_api()
    prompt_concatene = generer_prompt(question, profil)
    requete_curl = preparer_requete_curl(prompt_concatene)
    requete_curl = corriger_commande_curl(requete_curl)

    # Exécuter la commande curl et afficher le résultat
    resultat = executer_commande_curl(requete_curl)
    afficher_resultat(resultat, requete_curl, champ_r, champ_q)

    # Mettre à jour l'historique avec la nouvelle question et réponse
    if resultat.returncode == 0:
        try:
            reponse_json = json.loads(resultat.stdout)
            texte_cible = reponse_json["candidates"][0]["content"]["parts"][0]["text"]
            nouveau_historique = f"Question : {question}\nRéponse : {texte_cible}"
            champ_history.delete('1.0', tk.END)
            champ_history.insert(tk.END, f"{historique}\n{nouveau_historique}".strip())
        except Exception as e:
            champ_r.insert(tk.END, f"Erreur lors de la mise à jour de l'historique : {e}\n")

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

    # Création de la commande API (champ caché)
    def creerCommandeAPI(profil):
        if not profil:
            return ""
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

    bouton_valider = ttk.Button(frame_boutons, text="Envoyer la question", command=lambda: soumettreQuestionAPI(champ_q, champ_r, champ_history))
    bouton_valider.pack(side="left", padx=10)
    
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
        profils = []
        for fichier in os.listdir(PROFILES_DIR):
            if fichier.endswith(".yaml"):
                profils.append(fichier[:-5])  # Retirer l'extension .yaml
        return profils

    # Fonction pour charger les données d'un profil sélectionné
    def charger_donnees_profil(profil):
        chemin_fichier = os.path.join(PROFILES_DIR, f"{profil}.yaml")
        try:
            with open(chemin_fichier, 'r', encoding='utf-8') as fichier:
                return yaml.safe_load(fichier)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger le profil {profil} : {e}")
            return {}

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
        curl_exe_var.set(donnees_profil.get("curl_exe", ""))
        replace_apikey_var.set(donnees_profil.get("replace_apikey", ""))

    # Fonction pour définir un seul profil comme défaut
    def definir_profil_defaut(profil_selectionne):
        for fichier in os.listdir(PROFILES_DIR):
            if fichier.endswith(".yaml"):
                chemin_fichier = os.path.join(PROFILES_DIR, fichier)
                try:
                    with open(chemin_fichier, 'r', encoding='utf-8') as fichier_yaml:
                        config = yaml.safe_load(fichier_yaml)

                    # Mettre à jour la clé "default"
                    config["default"] = (fichier[:-5] == profil_selectionne)

                    with open(chemin_fichier, 'w', encoding='utf-8') as fichier_yaml:
                        yaml.dump(config, fichier_yaml, default_flow_style=False, allow_unicode=True)
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur lors de la mise à jour du profil {fichier} : {e}")

    # Charger le profil par défaut au démarrage
    def charger_profil_defaut():
        """Charge le profil marqué comme défaut ou retourne Gemini si aucun n'est défini."""
        for fichier in os.listdir(PROFILES_DIR):
            if fichier.endswith(".yaml"):
                chemin_fichier = os.path.join(PROFILES_DIR, fichier)
                try:
                    with open(chemin_fichier, 'r', encoding='utf-8') as fichier_yaml:
                        config = yaml.safe_load(fichier_yaml)
                        if config.get("default", False):
                            return fichier[:-5]
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur lors du chargement du profil par défaut : {e}")
        return "Gemini"  # Retourne Gemini par défaut si aucun profil n'est marqué comme défaut

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
        curl_exe_var.set(donnees_profil.get("curl_exe", ""))
        replace_apikey_var.set(donnees_profil.get("replace_apikey", ""))

    def enregistrer_configuration():
        profil_selectionne = selected_model.get()
        if not profil_selectionne:
            messagebox.showerror("Erreur", "Veuillez sélectionner un profil.")
            return

        config_data = {
            "api_url": api_url_entry.get(),
            "api_key": api_key_entry.get().strip(),
            "role": role_entry.get(),
            "behavior": default_behavior_var.get(),
            "history": history_checkbutton_var.get(),
            "default": default_profile_var.get(),
            "curl_exe": curl_exe_var.get(),
            "replace_apikey": replace_apikey_var.get()
        }

        chemin_fichier = os.path.join(PROFILES_DIR, f"{profil_selectionne}.yaml")
        try:
            with open(chemin_fichier, 'w', encoding='utf-8') as fichier:
                yaml.dump(config_data, fichier, default_flow_style=False, allow_unicode=True)
            if default_profile_var.get():
                definir_profil_defaut(profil_selectionne)
            messagebox.showinfo("Succès", f"Profil sauvegardé sous : {chemin_fichier}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde du profil : {e}")

        setup_window.destroy()

    bouton_enregistrer = ttk.Button(setup_window, text="Enregistrer", command=enregistrer_configuration)
    bouton_enregistrer.grid(row=9, column=0, columnspan=3, pady=10)

    bouton_annuler = ttk.Button(setup_window, text="Annuler", command=setup_window.destroy)
    bouton_annuler.grid(row=10, column=0, columnspan=3, pady=5)

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
    enabled_var = tk.BooleanVar(value=False)
    
    # Extensions disponibles
    extensions = [".py", ".js", ".html", ".css", ".txt", ".md", ".json", ".xml", ".c", ".cpp", ".java"]
    
    # Charger la configuration actuelle
    def charger_config_actuelle():
        try:
            profil_actuel = lire_profil_defaut()
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
                extension_var.set(dev_config.get("extension", ".py"))
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
    nom_profil_charge, _ = selectionProfilDefaut()
    nom_api = nom_profil_charge.split('.')[0] if nom_profil_charge else "API"
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
    
    extension_frame = ttk.Frame(frame_development)
    extension_frame.pack(fill="x", pady=5)
    ttk.Label(extension_frame, text="Extension :").pack(side="left")
    extension_combo = ttk.Combobox(extension_frame, textvariable=extension_var, values=extensions, width=15)
    extension_combo.pack(side="left", padx=(5, 0))
    extension_combo.bind('<<ComboboxSelected>>', lambda e: update_button_state())
    extension_combo.bind('<KeyRelease>', lambda e: update_button_state())
    
    # Bouton Enregistrer - créé ici pour être accessible aux fonctions
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x", pady=20)
    
    def enregistrer_config():
        try:
            # Charger le profil actuel
            nom_profil_charge, profil_actuel = selectionProfilDefaut()
            
            if not profil_actuel:
                messagebox.showerror("Erreur", "Impossible de charger le profil actuel.")
                return
            
            # Mise à jour de la configuration
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
            
            # Sauvegarder dans le fichier
            nom_fichier = nom_profil_charge.replace('.yaml', '') if nom_profil_charge else 'Gemini'
            chemin_fichier = os.path.join(PROFILES_DIR, f"{nom_fichier}.yaml")
            
            with open(chemin_fichier, 'w', encoding="utf-8") as fichier:
                yaml.dump(profil_actuel, fichier, default_flow_style=False, allow_unicode=True)
            
            messagebox.showinfo("Succès", f"Configuration sauvegardée dans {nom_fichier}")
            setup_file_window.destroy()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {e}")
            logging.error(f"Erreur sauvegarde config file : {e}")
    
    bouton_enregistrer = ttk.Button(button_frame, text="Enregistrer", command=enregistrer_config, state="disabled")
    bouton_enregistrer.pack(anchor="center")
    
    # Initialisation
    charger_config_actuelle()
    update_panels()
    update_button_state()

def creer_interface():
    """Crée l'interface graphique principale avec une barre de menu."""
    global root
    root = tk.Tk()
    root.title("ROB-1")

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