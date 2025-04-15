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

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def verifier_ou_demander_cle_api():
    """Vérifie si une clé API est configurée, sinon demande à l'utilisateur de la fournir."""
    api_key_file = get_resource_path("api_key.txt")
    if os.path.exists(api_key_file):
        with open(api_key_file, "r") as file:
            api_key = file.read().strip()
            if api_key:
                return api_key

    while True:
        api_key = simpledialog.askstring("Clé API", "Entrez votre clé API Gemini :")
        if api_key:
            with open(api_key_file, "w") as file:
                file.write(api_key)
            return api_key
        else:
            messagebox.showerror("Erreur", "Renseigner une clé API.")

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

def ouvrir_fenetre_test_api():
    """Ouvre une fenêtre pour tester l'API Gemini Studio."""
    fenetre_test_api = Toplevel()
    fenetre_test_api.title("Test de l'API Gemini Studio")

    label = ttk.Label(fenetre_test_api, text="Tester l'API Gemini Studio")
    label.pack(pady=10)

    # Champ pour la question posée (prompt)
    prompt_label = ttk.Label(fenetre_test_api, text="Entrez votre question :")
    prompt_label.pack(pady=5)

    prompt_entry = scrolledtext.ScrolledText(fenetre_test_api, width=60, height=5, wrap=tk.WORD)
    prompt_entry.pack(pady=5)

    # Champ pour le comportement
    comportement_label = ttk.Label(fenetre_test_api, text="Comportement enregistré :")
    comportement_label.pack(pady=5)

    comportement_entry = ttk.Entry(fenetre_test_api, width=50)
    comportement_entry.pack(pady=5)

    # Pré-remplir le comportement si déjà enregistré
    comportement_file = get_resource_path("comportement.txt")
    if os.path.exists(comportement_file):
        with open(comportement_file, "r") as file:
            comportement_entry.insert(0, file.read().strip())

    # Champ pour afficher la réponse de l'API
    reponse_label = ttk.Label(fenetre_test_api, text="Réponse de l'API :")
    reponse_label.pack(pady=5)

    reponse_text = scrolledtext.ScrolledText(fenetre_test_api, width=60, height=10, wrap=tk.WORD, state='disabled')
    reponse_text.pack(pady=5)

    def afficher_informations_complementaires():
        """Affiche un menu pour montrer/cacher les informations complémentaires."""
        menu_fenetre = Toplevel()
        menu_fenetre.title("Informations Complémentaires")

        # Zone pour afficher la réponse brute
        raw_response_label = ttk.Label(menu_fenetre, text="Réponse brute :")
        raw_response_label.pack(pady=5)

        raw_response_text = scrolledtext.ScrolledText(menu_fenetre, width=60, height=10, wrap=tk.WORD, state='normal')
        raw_response_text.pack(pady=5)
        raw_response_text.insert(tk.END, reponse_text.get("1.0", tk.END))
        raw_response_text.config(state='disabled')

        # Zone pour afficher les informations en bullet points
        bullet_points_label = ttk.Label(menu_fenetre, text="Informations en bullet points :")
        bullet_points_label.pack(pady=5)

        bullet_points_text = scrolledtext.ScrolledText(menu_fenetre, width=60, height=10, wrap=tk.WORD, state='normal')
        bullet_points_text.pack(pady=5)
        bullet_points_text.insert(tk.END, "- Exemple de point 1\n- Exemple de point 2\n")
        bullet_points_text.config(state='disabled')

        # Bouton pour fermer le menu
        close_button = ttk.Button(menu_fenetre, text="✖", command=menu_fenetre.destroy)
        close_button.pack(pady=10)

    # Bouton pour envoyer la requête
    def tester():
        prompt = prompt_entry.get("1.0", tk.END).strip()
        comportement = comportement_entry.get().strip()
        if prompt and comportement:
            api_key = verifier_ou_demander_cle_api()
            # Préparer la question en concaténant le comportement et le prompt
            question = f"Comporte toi en tant que {comportement}.\n{prompt}"
            reponse = envoyer_requete(api_key, question)
            reponse_text.config(state='normal')
            reponse_text.delete(1.0, tk.END)
            if "erreur" in reponse:
                reponse_text.insert(tk.END, reponse["erreur"], 'erreur')
            else:
                try:
                    # Extraire le texte de la réponse
                    text = reponse["candidates"][0]["content"]["parts"][0]["text"]
                    reponse_text.insert(tk.END, text)
                except (KeyError, IndexError):
                    reponse_text.insert(tk.END, "Erreur : Champ 'text' introuvable dans la réponse.", 'erreur')
            reponse_text.config(state='disabled')
        else:
            messagebox.showerror("Erreur", "Veuillez entrer une question et un comportement valide.")

    bouton_tester = ttk.Button(fenetre_test_api, text="Envoyer la requête", command=tester)
    bouton_tester.pack(pady=10)

    bouton_informations = ttk.Button(fenetre_test_api, text="Informations Complémentaires", command=afficher_informations_complementaires)
    bouton_informations.pack(pady=10)

    # Configure text tags for error styling
    reponse_text.tag_config('erreur', foreground='red')

def ouvrir_fenetre_setup_api():
    """Ouvre une fenêtre pour configurer les paramètres de l'API."""
    fenetre_setup_api = Toplevel()
    fenetre_setup_api.title("Configuration de l'API")

    # Simulation du comportement enregistré
    current_behavior = tk.StringVar(value="comportement initial")

    # URL de test CURL pour Gemini
    gemini_curl_url = "https://generativelanguage.googleapis.com/v1beta/models/"

    # Choix du modèle
    model_label = ttk.Label(fenetre_setup_api, text="Modèle de Langage :")
    model_label.grid(row=0, column=0, sticky="w", pady=5)
    selected_model = tk.StringVar(value="Gemini")
    model_combobox = ttk.Combobox(fenetre_setup_api, textvariable=selected_model, values=["Gemini", "ChatGPT", "Claude"])
    model_combobox.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)

    # Comportement Enregistré
    recorded_behavior_label = ttk.Label(fenetre_setup_api, text="Comportement Enregistré :")
    recorded_behavior_label.grid(row=1, column=0, sticky="w", pady=5)
    recorded_behavior_entry = ttk.Entry(fenetre_setup_api, textvariable=current_behavior, state="readonly")
    recorded_behavior_entry.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)

    # URL de l'API
    api_url_label = ttk.Label(fenetre_setup_api, text="URL de l'API Gemini :")
    api_url_label.grid(row=2, column=0, sticky="w", pady=5)
    api_url_var = tk.StringVar(value=gemini_curl_url)
    api_url_entry = ttk.Entry(fenetre_setup_api, textvariable=api_url_var, width=50)
    api_url_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=5)

    # Clé API
    api_key_label = ttk.Label(fenetre_setup_api, text="Clé API Gemini :")
    api_key_label.grid(row=3, column=0, sticky="w", pady=5)
    api_key_entry = ttk.Entry(fenetre_setup_api, width=50, show="*")
    api_key_entry.grid(row=3, column=1, columnspan=2, sticky="ew", pady=5)

    # Comportement par Défaut
    default_behavior_label = ttk.Label(fenetre_setup_api, text="Comportement par Défaut :")
    default_behavior_label.grid(row=4, column=0, sticky="w", pady=5)
    default_behavior_var = tk.StringVar(value=current_behavior.get())
    default_behavior_entry = ttk.Entry(fenetre_setup_api, textvariable=default_behavior_var)
    default_behavior_entry.grid(row=4, column=1, columnspan=2, sticky="ew", pady=5)

    # Fonction pour charger la configuration YAML
    def load_model_config(model_name):
        try:
            with open(f"{model_name.lower()}.yaml", 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}
        except yaml.YAMLError as e:
            return {}

    # Mise à jour dynamique des champs en fonction du modèle sélectionné
    def update_form_for_model(event):
        selected = model_combobox.get()
        config = load_model_config(selected)
        api_url_label.config(text=f"URL de l'API {selected}:")
        api_key_label.config(text=f"Clé API {selected}:")
        api_url_var.set(config.get('api_url', gemini_curl_url if selected == "Gemini" else ''))
        api_key_entry.delete(0, tk.END)
        api_key_entry.insert(0, config.get('api_key', ''))
        if selected == "Gemini":
            default_behavior_var.set(current_behavior.get())

    model_combobox.bind("<<ComboboxSelected>>", update_form_for_model)

    def enregistrer_configuration():
        selected_model_val = selected_model.get()
        api_url_val = api_url_entry.get()
        api_key = api_key_entry.get().strip()
        default_behavior_val = default_behavior_var.get()

        print("Modèle Sélectionné:", selected_model_val)
        print("URL de l'API:", api_url_val)
        print("Clé API:", api_key)
        print("Comportement par Défaut:", default_behavior_val)

        fenetre_setup_api.destroy()

    bouton_enregistrer = ttk.Button(fenetre_setup_api, text="Enregistrer", command=enregistrer_configuration)
    bouton_enregistrer.grid(row=5, column=0, columnspan=3, pady=10)

    bouton_annuler = ttk.Button(fenetre_setup_api, text="Annuler", command=fenetre_setup_api.destroy)
    bouton_annuler.grid(row=6, column=0, columnspan=3, pady=5)

def creer_interface():
    """Crée l'interface graphique principale avec une barre de menu."""
    root = tk.Tk()
    root.title("ROB-1")

    # Barre de menu principale
    menu_bar = Menu(root)

    # Menu Comportement
    menu_comportement = Menu(menu_bar, tearoff=0)
    menu_comportement.add_command(label="Ouvrir la fenêtre Comportement", command=ouvrir_fenetre_comportement)
    menu_bar.add_cascade(label="Comportement", menu=menu_comportement)

    # Menu Test API
    menu_test_api = Menu(menu_bar, tearoff=0)
    menu_test_api.add_command(label="Ouvrir la fenêtre Test API", command=ouvrir_fenetre_test_api)
    menu_test_api.add_command(label="Set up API", command=ouvrir_fenetre_setup_api)
    menu_bar.add_cascade(label="Test API", menu=menu_test_api)

    # Configuration de la barre de menu
    root.config(menu=menu_bar)

    # Zone principale pour afficher les résultats
    resultats_text = scrolledtext.ScrolledText(root, width=80, height=20, wrap=tk.WORD)
    resultats_text.pack(pady=10)

    resultats_text.tag_config('reussi', foreground='green')
    resultats_text.tag_config('erreur', foreground='red')

    root.mainloop()

# Appel de la fonction au démarrage de l'application
api_key = verifier_ou_demander_cle_api()