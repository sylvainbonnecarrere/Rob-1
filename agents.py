import yaml
from tkinter import messagebox
import requests
import sys
import os

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

chemin_fichier = get_resource_path("config.yaml")

def charger_configuration(chemin_fichier):
    """Charge la configuration des agents depuis un fichier YAML."""
    try:
        with open(chemin_fichier, 'r') as fichier:
            return yaml.safe_load(fichier)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de charger la configuration : {e}")
        return None

def verifier_ou_demander_cle_api():
    """Supprime le prompt de demande de clé API au démarrage. La configuration se fait désormais via le menu SETUP."""
    api_key_file = get_resource_path("api_key.txt")
    if os.path.exists(api_key_file):
        with open(api_key_file, "r") as file:
            api_key = file.read().strip()
            return api_key
    return None  # Retourne None si aucune clé API n'est trouvée

def tester_agent(agent_config, payload):
    """Teste un agent donné en envoyant une requête à son API."""
    try:
        response = requests.post(agent_config['api_url'], json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"erreur": f"Code HTTP {response.status_code}"}
    except Exception as e:
        return {"erreur": str(e)}