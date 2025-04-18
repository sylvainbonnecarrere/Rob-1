import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, Toplevel, Menu
import os
import sys
import yaml
import subprocess
import json

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

def get_default_profile():
    """Charge le profil par défaut ou retourne Gemini si aucun n'est défini."""
    for fichier in os.listdir(PROFILES_DIR):
        if fichier.endswith(".yaml"):
            chemin_fichier = os.path.join(PROFILES_DIR, fichier)
            with open(chemin_fichier, 'r') as f:
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
                print(f"Erreur lors du chargement du profil {fichier} : {e}")

    if not profil_trouve:
        chemin_gemini = os.path.join(profils_dir, "Gemini.yaml")
        if os.path.exists(chemin_gemini):
            with open(chemin_gemini, "r", encoding="utf-8") as f:
                profilAPIActuel = yaml.safe_load(f)
            nom_profil_charge = "Gemini.yaml"
        else:
            profilAPIActuel = {}
            nom_profil_charge = "Aucun profil trouvé"

    print(f"Profil>{nom_profil_charge} chargé")
    return nom_profil_charge, profilAPIActuel

# Correction pour s'assurer que GEMINI_API_KEY est remplacé correctement

def preparer_requete_curl(final_prompt):
    """
    Prépare une commande curl en utilisant le final_prompt et retourne une chaîne de caractères.
    """
    curl_exe = profilAPIActuel.get('curl_exe', '')
    api_key = profilAPIActuel.get('api_key', '')

    # Si le profil est Gemini, remplacer GEMINI_API_KEY par api_key
    if 'GEMINI_API_KEY' in curl_exe:
        curl_exe = curl_exe.replace('GEMINI_API_KEY', api_key)

    # Remplacer uniquement la chaîne de caractère api_url par final_prompt
    api_url = profilAPIActuel.get('api_url', '')
    if api_url in curl_exe:
        curl_exe = curl_exe.replace(api_url, final_prompt)

    return curl_exe

def corriger_commande_curl(commande):
    """
    Corrige une commande curl pour Windows en échappant correctement les guillemets et en reformattant le JSON.
    """
    import json

    # Supprimer les barres obliques inverses et les sauts de ligne
    commande_corrigee = commande.replace('\\\n', '').replace('\n', '').strip()

    # Identifier et reformater les données JSON dans la commande
    if '-d' in commande_corrigee:
        try:
            # Extraire la partie JSON après '-d'
            debut_json = commande_corrigee.index('-d') + 2
            json_brut = commande_corrigee[debut_json:].strip()

            # Nettoyer les guillemets simples et reformater en JSON valide
            json_brut = json_brut.strip("'")
            json_data = json.loads(json_brut)  # Charger en tant qu'objet Python
            json_valide = json.dumps(json_data)  # Reformater en JSON compact

            # Échapper les guillemets pour Windows
            json_valide = json_valide.replace('"', '\\"')

            # Remplacer l'ancien JSON par le nouveau
            commande_corrigee = commande_corrigee[:debut_json] + f' "{json_valide}"'
        except Exception as e:
            print("Erreur lors du reformatage du JSON :", e)

    # Remplacer les guillemets simples dans les en-têtes par des guillemets doubles
    commande_corrigee = commande_corrigee.replace("'Content-Type: application/json'", '"Content-Type: application/json"')

    return commande_corrigee

def charger_profil_api():
    """
    Charge le profil API par défaut ou retourne Gemini si aucun n'est défini.
    """
    nom_profil_charge, profil = selectionProfilDefaut()
    print(f"Profil chargé : {nom_profil_charge}")
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

def executer_commande_curl(requete_curl):
    """
    Exécute la commande curl et retourne le résultat.
    """
    print("Commande corrigée avant exécution :", requete_curl)
    resultat = subprocess.run(requete_curl, shell=True, capture_output=True, text=True)
    print("Code de retour :", resultat.returncode)
    print("stdout :", resultat.stdout)
    print("stderr :", resultat.stderr)
    return resultat

def afficher_resultat(resultat, requete_curl, champ_r):
    """
    Affiche le résultat de la commande curl dans le champ R.
    """
    champ_r.delete('1.0', tk.END)  # Nettoyer le champ avant d'afficher le résultat

    if resultat.returncode == 0:
        try:
            # Charger la réponse JSON
            reponse_json = json.loads(resultat.stdout)

            # Extraire le texte cible : candidates[0].content.parts[0].text
            texte_cible = reponse_json["candidates"][0]["content"]["parts"][0]["text"]

            # Afficher uniquement le texte extrait
            champ_r.insert(tk.END, texte_cible)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            champ_r.insert(tk.END, "Erreur lors de l'extraction du texte ou du parsing JSON :\n")
            champ_r.insert(tk.END, str(e))
    else:
        champ_r.insert(tk.END, f"Erreur lors de l'exécution :\n{resultat.stderr}\n")

def soumettreQuestionAPI(champ_q, champ_r):
    question = champ_q.get('1.0', tk.END).strip()
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
    resultat = executer_commande_curl(requete_curl)
    afficher_resultat(resultat, requete_curl, champ_r)
    champ_r.config(state="disabled")

def ouvrir_fenetre_apitest():
    """
    Ouvre la fenêtre unique du module APItest avec navigation interne, chargement du profil par défaut,
    création de la commande API, et gestion des champs Q/R.
    """
    import json
    fenetre = tk.Toplevel(root)
    fenetre.title("APItest")
    fenetre.geometry("700x500")

    def on_close():
        root.destroy()  # Ferme toute l'application proprement
    fenetre.protocol("WM_DELETE_WINDOW", on_close)

    # 1. Chargement du profil par défaut (log affiché une seule fois)
    nom_profil_charge, profilAPIActuel = selectionProfilDefaut()

    # 2. Création de la commande API (champ caché)
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

    # 3. Interface utilisateur
    label_profil = ttk.Label(fenetre, text=f"Profil API utilisé : {profilAPIActuel.get('profil', 'Inconnu')}")
    label_profil.pack(pady=5)

    # Champ Q (question)
    label_q = ttk.Label(fenetre, text="Q :")
    label_q.pack(anchor="w", padx=10)
    champ_q = scrolledtext.ScrolledText(fenetre, width=80, height=5)
    champ_q.pack(padx=10, pady=5)

    # Champ R (réponse)
    label_r = ttk.Label(fenetre, text="R :")
    label_r.pack(anchor="w", padx=10)
    champ_r = scrolledtext.ScrolledText(fenetre, width=80, height=10, state="normal")
    champ_r.pack(padx=10, pady=5)

    # 4. Bouton Valider (soumission)
    bouton_valider = ttk.Button(fenetre, text="Valider", command=lambda: soumettreQuestionAPI(champ_q, champ_r))
    bouton_valider.pack(pady=10)

    # 5. (Optionnel) Navigation interne (Retour/Avant)
    # À implémenter si historique souhaité

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

def creer_interface():
    """Crée l'interface graphique principale avec une barre de menu."""
    global root
    root = tk.Tk()
    root.title("ROB-1")

    # Barre de menu principale
    menu_bar = Menu(root)

    # Menu API (anciennement Test API)
    menu_api = Menu(menu_bar, tearoff=0)
    menu_api.add_command(label="Test API", command=ouvrir_fenetre_apitest)
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