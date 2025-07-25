import logging
import os
import yaml
import subprocess
from gui import creer_interface

# Modification de la configuration des logs pour inclure la console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("application.log"),
        logging.StreamHandler()  # Ajout d'un gestionnaire pour afficher les logs dans la console
    ]
)

PROFILES_DIR = "profiles"
CONVERSATIONS_DIR = "conversations"
os.makedirs(PROFILES_DIR, exist_ok=True)
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)

def creer_fichiers_configuration():
    """Crée les fichiers de configuration pour Gemini, OpenAI et Claude."""
    configurations = {
        "Gemini": {
            "profil": "Gemini",
            "nom": "Gemini",
            "api_key": "",
            "api_url": "",
            "behavior": "",
            "curl_exe": "",
            "default": False,
            "history": False,
            "role": "",
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
        },
        "OpenAI": {
            "profil": "OpenAI",
            "nom": "OpenAI",
            "api_key": "",
            "api_url": "",
            "behavior": "",
            "curl_exe": "",
            "default": False,
            "history": False,
            "role": "",
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
        },
        "Claude": {
            "profil": "Claude",
            "nom": "Claude",
            "api_key": "",
            "api_url": "",
            "behavior": "",
            "curl_exe": "",
            "default": False,
            "history": False,
            "role": "",
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

def execute_curl():
    curl_command = [
        "curl",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=AIzaSyAI56WaXrkK1iFHNxp3_akHMFTN5-kabBk",
        "-H", "Content-Type: application/json",
        "-X", "POST",
        "-d", '{"contents": [{"parts":[{"text": "En tant qu\'expert vendeur. Ton comportement est défini ainsi : excité. J\'aimerais te poser la question suivante : "}]}]}'
    ]

    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        print("Réponse de l'API :")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Erreur lors de l'exécution de la requête CURL :")
        print(e.stderr)

def main():
    """Point d'entrée principal de l'application."""
    logging.info("Application démarrée.")
    # Ajout d'un log pour indiquer le lancement initial de l'application
    logging.info("Lancement initial de l'application.")
    try:
        creer_interface()
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution de l'interface : {e}")
        raise
    finally:
        logging.info("Application terminée.")

if __name__ == "__main__":
    logging.info("Initialisation de l'application... (Première instance)")
    try:
        main()
    except Exception as e:
        logging.critical(f"Erreur critique : {e}")
        print("Une erreur critique est survenue. Consultez les logs pour plus de détails.")