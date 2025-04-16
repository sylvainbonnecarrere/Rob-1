import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog, Toplevel, Listbox, Menu, filedialog
from agents import charger_configuration, tester_agent
from api import envoyer_requete
import subprocess
import os
import json
import chardet
import sys
import yaml
import requests

PROFILES_DIR = "profiles"
os.makedirs(PROFILES_DIR, exist_ok=True)

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def enregistrer_comportement():
    """Placeholder function for registering a behavior."""
    messagebox.showinfo("Enregistrer Comportement", "Cette fonctionnalité sera implémentée prochainement.")

def tester_requete_api():
    """Placeholder function for testing the API."""
    messagebox.showinfo("Tester Requête API", "Cette fonctionnalité sera implémentée prochainement.")

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
                with open(chemin_fichier, 'r') as f:
                    profil = yaml.safe_load(f)
                    if profil.get("default", False):
                        return profil
        # Si aucun profil n'est marqué comme défaut, charger Gemini
        chemin_gemini = os.path.join(PROFILES_DIR, "Gemini.yaml")
        if os.path.exists(chemin_gemini):
            with open(chemin_gemini, 'r') as f:
                return yaml.safe_load(f)
        else:
            messagebox.showerror("Erreur", "Le profil Gemini est introuvable. Veuillez le configurer dans SETUP.")
            return None
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lire les profils : {e}")
        return None

def ouvrir_fenetre_test_api():
    """Ouvre une fenêtre pour tester l'API avec le profil par défaut."""
    fenetre = tk.Tk()
    fenetre.title("Test API")

    # Charger le profil par défaut ou utiliser Gemini si aucun n'est défini
    profil_defaut = lire_profil_defaut()
    profil_nom = "Gemini"  # Par défaut

    # Identifier le nom du fichier du profil par défaut
    for fichier in os.listdir(PROFILES_DIR):
        if fichier.endswith(".yaml"):
            chemin_fichier = os.path.join(PROFILES_DIR, fichier)
            with open(chemin_fichier, 'r') as f:
                profil = yaml.safe_load(f)
                if profil.get("default", False):
                    profil_nom = fichier[:-5]  # Retirer l'extension .yaml
                    break

    # Charger le profil par défaut avant de loguer
    profil_defaut = lire_profil_defaut()

    # Charger le profil par défaut si les informations du profil ne sont pas trouvées
    if not profil_defaut:
        profil_defaut = lire_profil_defaut()
        print("[INFO] Aucun profil trouvé, chargement du profil par défaut.")

    # Log du profil utilisé à l'arrivée sur l'écran TESTAPI
    if profil_defaut:
        print(f"Profil API utilisé dans TESTAPI : {profil_defaut.get('nom', profil_nom)}")

    # Surcharge temporaire pour le test Gemini
    if profil_defaut and profil_defaut.get('model', '').lower() == 'gemini':
        profil_defaut['curl_exe'] = (
            "curl \"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=GEMINI_API_KEY\" "
            "-H 'Content-Type: application/json' "
            "-X POST "
            "-d '{\"contents\": [{\"parts\":[{\"text\": \"Explain how AI works\"}]}]}'"
        )
        profil_defaut['api_key'] = 'AIzaSyAI56WaXrkK1iFHNxp3_akHMFTN5-kabBk'

    # Champ pour la question (Q)
    label_question = ttk.Label(fenetre, text="Question :")
    label_question.grid(row=0, column=0, sticky="w", padx=10, pady=5)

    champ_question = scrolledtext.ScrolledText(fenetre, width=60, height=5)
    champ_question.grid(row=1, column=0, columnspan=2, padx=10, pady=5)

    bouton_envoyer = ttk.Button(fenetre, text="Envoyer", command=lambda: envoyer_requete(profil_defaut.get('api_key', ''), champ_question.get("1.0", tk.END).strip()))
    bouton_envoyer.grid(row=2, column=0, padx=10, pady=5, sticky="w")

    # Champ pour la réponse (R)
    label_reponse = ttk.Label(fenetre, text="Réponse :")
    label_reponse.grid(row=3, column=0, sticky="w", padx=10, pady=5)

    champ_reponse = scrolledtext.ScrolledText(fenetre, width=60, height=10, state="normal")
    champ_reponse.grid(row=4, column=0, columnspan=2, padx=10, pady=5)

    bouton_effacer_reponse = ttk.Button(fenetre, text="Effacer R", command=lambda: champ_reponse.delete("1.0", tk.END))
    bouton_effacer_reponse.grid(row=5, column=0, padx=10, pady=5, sticky="w")

    fenetre.mainloop()

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
            with open(chemin_fichier, 'r') as fichier:
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

    # Fonction pour définir un seul profil comme défaut
    def definir_profil_defaut(profil_selectionne):
        for fichier in os.listdir(PROFILES_DIR):
            if fichier.endswith(".yaml"):
                chemin_fichier = os.path.join(PROFILES_DIR, fichier)
                try:
                    with open(chemin_fichier, 'r') as fichier_yaml:
                        config = yaml.safe_load(fichier_yaml)

                    # Mettre à jour la clé "default"
                    config["default"] = (fichier[:-5] == profil_selectionne)

                    with open(chemin_fichier, 'w') as fichier_yaml:
                        yaml.dump(config, fichier_yaml)
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur lors de la mise à jour du profil {fichier} : {e}")

    # Charger le profil par défaut au démarrage
    def charger_profil_defaut():
        """Charge le profil marqué comme défaut ou retourne Gemini si aucun n'est défini."""
        for fichier in os.listdir(PROFILES_DIR):
            if fichier.endswith(".yaml"):
                chemin_fichier = os.path.join(PROFILES_DIR, fichier)
                try:
                    with open(chemin_fichier, 'r') as fichier_yaml:
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

    # URL de l'API
    api_url_label = ttk.Label(setup_window, text="URL de l'API :")
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

    # Champ curl_exe
    curl_exe_label = ttk.Label(setup_window, text="curl_exe :")
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
            "curl_exe": curl_exe_var.get()
        }

        chemin_fichier = os.path.join(PROFILES_DIR, f"{profil_selectionne}.yaml")
        try:
            with open(chemin_fichier, 'w') as fichier:
                yaml.dump(config_data, fichier)
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

def QuestionAPI_filter(question):
    """
    Prépare et filtre la commande CURL pour le profil 'Gemini'.
    """
    # Charger le profil par défaut
    profil_path = os.path.join(PROFILES_DIR, "Gemini.yaml")
    with open(profil_path, 'r') as file:
        profil = yaml.safe_load(file)

    # Vérifier si le profil est 'Gemini'
    if profil.get('model', '').lower() == 'gemini':
        # Récupérer la commande CURL de 'curl_exe'
        curl_command = profil.get('curl_exe', '')

        # Remplacer 'GEMINI_API_KEY' par la clé API
        api_key = profil.get('api_key', '')
        curl_command = curl_command.replace('GEMINI_API_KEY', api_key)

        # Préparer la question avec 'PrepareAPI_question'
        prepared_question = PrepareAPI_question(question, profil)

        # Remplacer 'Explain how AI works' par la question préparée
        curl_command = curl_command.replace('Explain how AI works', prepared_question)

        # Logs en console
        print("--- Validation Requête API ---")
        print(f"Profil utilisé: {profil.get('model', 'Inconnu')}")
        print(f"URL API: {profil.get('api_url', 'Inconnu')}")
        print(f"Clé API (tronquée): {api_key[:5]}...")
        print(f"Commande CURL finale: {curl_command}")

        # Affichage d'une fenêtre de validation
        validation_window = tk.Toplevel()
        validation_window.title("Validation de la Requête API")

        tk.Label(validation_window, text="Profil utilisé:").pack()
        tk.Label(validation_window, text=profil.get('model', 'Inconnu')).pack()

        tk.Label(validation_window, text="URL API:").pack()
        tk.Label(validation_window, text=profil.get('api_url', 'Inconnu')).pack()

        tk.Label(validation_window, text="Clé API (tronquée):").pack()
        tk.Label(validation_window, text=f"{api_key[:5]}...").pack()

        tk.Label(validation_window, text="Commande CURL finale:").pack()
        curl_text = tk.Text(validation_window, height=10, width=80)
        curl_text.insert(tk.END, curl_command)
        curl_text.pack()

        def confirmer_et_executer():
            validation_window.destroy()
            try:
                resultat = subprocess.check_output(curl_command, shell=True, text=True)
                messagebox.showinfo("Succès", "Requête exécutée avec succès.")
                print("Résultat:", resultat)
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'exécution de la commande: {e}")

        def annuler():
            validation_window.destroy()

        tk.Button(validation_window, text="Confirmer et Exécuter", command=confirmer_et_executer).pack()
        tk.Button(validation_window, text="Annuler", command=annuler).pack()

        return curl_command
    else:
        raise ValueError("Le profil actuel n'est pas 'Gemini'.")

def PrepareAPI_question(question, profil):
    """
    Prépare le texte de la question pour l'API Gemini et remplace les placeholders spécifiques.
    """
    # Exemple de traitement : suppression des espaces inutiles et encodage
    question_prepared = question.strip()

    # Si le profil est Gemini, remplacer GEMINI_API_KEY par la clé API
    if profil.get('model', '').lower() == 'gemini':
        api_key = profil.get('api_key', '')
        question_prepared = question_prepared.replace('GEMINI_API_KEY', api_key)

    return question_prepared

def APIPreRequest(profil_api, question):
    """
    Prépare une commande CURL en fonction du profil API sélectionné et de la question utilisateur.
    """
    model_type = profil_api.get('model', '').lower()  # Identifier le type d'API
    curl_command = ""

    if not model_type:
        print("Erreur : Le champ 'model' est vide ou absent dans le profil API.")
        return ""

    if model_type not in ['gemini', 'chatgpt', 'claude']:
        print(f"Type d'API non supporté: {model_type}")
        return ""

    if model_type == 'gemini':
        curl_exe = profil_api.get('curl_exe', "")
        curl_command_with_key = curl_exe.replace('GEMINI_API_KEY', profil_api.get('api_key', ""))
        default_question = "Explain how AI works"  # Identifier la question par défaut
        role = profil_api.get('role', "")
        behavior = profil_api.get('behavior', "")

        new_question = "En tant que "
        if role:
            new_question += role
        if behavior:
            new_question += f" Tu as le comportement suivant : {behavior}"
        new_question += f". Ma question est la suivante : {question}"

        curl_command = curl_command_with_key.replace(default_question, new_question)
    elif model_type == 'chatgpt':
        curl_command = profil_api.get('curl_exe', "")
        # Traitement spécifique ChatGPT (à venir)
    elif model_type == 'claude':
        curl_command = profil_api.get('curl_exe', "")
        # Traitement spécifique Claude (à venir)
    else:
        print(f"Type d'API non supporté: {model_type}")
        return ""

    return curl_command

def creer_interface():
    """Crée l'interface graphique principale avec une barre de menu."""
    global root
    root = tk.Tk()
    root.title("ROB-1")

    # Barre de menu principale
    menu_bar = Menu(root)

    # Menu API (anciennement Test API)
    menu_api = Menu(menu_bar, tearoff=0)
    menu_api.add_command(label="Test API", command=ouvrir_fenetre_test_api)
    menu_api.add_command(label="Set up API", command=open_setup_menu)
    menu_bar.add_cascade(label="API", menu=menu_api)

    # Configuration de la barre de menu
    root.config(menu=menu_bar)

    # Zone principale pour afficher les résultats
    resultats_text = scrolledtext.ScrolledText(root, width=80, height=20, wrap=tk.WORD)
    resultats_text.pack(pady=10)

    resultats_text.tag_config('reussi', foreground='green')
    resultats_text.tag_config('erreur', foreground='red')

    root.mainloop()

# Appel de la fonction au démarrage de l'application
creer_interface()