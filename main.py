import logging
import os
import yaml
from gui import creer_interface

# Configure logging
logging.basicConfig(
    filename="application.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

PROFILES_DIR = "profiles"
os.makedirs(PROFILES_DIR, exist_ok=True)

def creer_fichiers_configuration():
    """Crée les fichiers de configuration pour Gemini, OpenAI et Claude."""
    configurations = {
        "Gemini": {
            "nom": "Gemini",
            "api_key": "",
            "api_url": "",
            "behavior": "",
            "curl_exe": "",
            "default": False,
            "history": False,
            "role": ""
        },
        "OpenAI": {
            "nom": "OpenAI",
            "api_key": "",
            "api_url": "",
            "behavior": "",
            "curl_exe": "",
            "default": False,
            "history": False,
            "role": ""
        },
        "Claude": {
            "nom": "Claude",
            "api_key": "",
            "api_url": "",
            "behavior": "",
            "curl_exe": "",
            "default": False,
            "history": False,
            "role": ""
        }
    }

    for nom, config in configurations.items():
        chemin_fichier = os.path.join(PROFILES_DIR, f"{nom}.yaml")
        if not os.path.exists(chemin_fichier):
            try:
                with open(chemin_fichier, 'w') as fichier:
                    yaml.dump(config, fichier)
                print(f"Fichier de configuration créé : {chemin_fichier}")
            except Exception as e:
                print(f"Erreur lors de la création du fichier {chemin_fichier} : {e}")

def verifier_profil_gemini():
    """Vérifie si le profil Gemini existe, sinon le crée avec des valeurs par défaut."""
    gemini_profile_path = os.path.join(PROFILES_DIR, "Gemini.yaml")

    if not os.path.exists(gemini_profile_path):
        gemini_default_config = {
            "model": "Gemini",
            "api_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            "api_key": "VOTRE_CLE_API_GEMINI_ICI",
            "behavior": "comportement initial",
            "history": False
        }

        try:
            with open(gemini_profile_path, 'w') as f:
                yaml.dump(gemini_default_config, f)
            print(f"Profil Gemini créé avec succès : {gemini_profile_path}")
        except Exception as e:
            print(f"Erreur lors de la création du profil Gemini : {e}")

def verifier_et_mettre_a_jour_profils():
    """Vérifie et met à jour les profils pour inclure la clé 'default'."""
    configurations = {
        "Gemini": {
            "default": True
        },
        "OpenAI": {
            "default": False
        },
        "Claude": {
            "default": False
        }
    }

    for nom, config_update in configurations.items():
        chemin_fichier = os.path.join(PROFILES_DIR, f"{nom}.yaml")
        if os.path.exists(chemin_fichier):
            try:
                with open(chemin_fichier, 'r') as fichier:
                    config = yaml.safe_load(fichier)

                # Mettre à jour la clé 'default'
                config.update(config_update)

                with open(chemin_fichier, 'w') as fichier:
                    yaml.dump(config, fichier)
                print(f"Profil {nom} mis à jour avec la clé 'default'.")
            except Exception as e:
                print(f"Erreur lors de la mise à jour du profil {nom} : {e}")

def verifier_ou_demander_cle_api():
    """Supprimé : La clé API sera configurée via le formulaire SETUP."""
    pass

def main():
    """Point d'entrée principal de l'application."""
    logging.info("Application démarrée.")
    try:
        creer_interface()
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution de l'interface : {e}")
        raise

if __name__ == "__main__":
    main()