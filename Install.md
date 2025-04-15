# Création d'un Système d'Agents Spécialisés avec Fichier de Configuration et Exécutable Windows

Ce document décrit les étapes pour créer un système permettant de lancer plusieurs agents spécialisés définis dans un fichier de configuration, avec la possibilité de compiler le tout en un exécutable Windows.

## 1. Conception du Fichier de Configuration

* **Format :** YAML ou JSON (YAML est recommandé pour sa lisibilité).
* **Structure :** Un fichier contenant une section principale (`agents`) où chaque agent est défini par un identifiant unique et des propriétés telles que :
    * `nom`: Nom convivial de l'agent.
    * `description`: Brève description de la fonction de l'agent.
    * `api_url`: URL de l'API de l'agent (incluant potentiellement le port).
    * `parametres`: Dictionnaire de paramètres spécifiques à l'agent.
* **Exemple (YAML) :**
    ```yaml
    agents:
      agent_redacteur:
        nom: "Rédacteur d'articles"
        description: "Génère des articles de blog sur des sujets spécifiques."
        api_url: "http://localhost:5000/redacteur"
        parametres:
          style: "informatif"
          ton: "neutre"
      agent_traducteur:
        nom: "Traducteur multilingue"
        description: "Traduit du texte d'une langue à une autre."
        api_url: "http://localhost:5001/traducteur"
        parametres:
          langue_source: "fr"
          langue_cible: "en"
    ```

## 2. Développement du Script Python

* **Objectif :** Lire le fichier de configuration et lancer les APIs pour chaque agent.
* **Librairies suggérées :**
    * `yaml`: Pour lire le fichier de configuration YAML.
    * `flask` ou `fastapi`: Pour créer les APIs des agents.
    * `requests`: Pour permettre aux agents de communiquer entre eux via des appels d'API.
* **Fonctionnalités clés :**
    * Fonction pour charger le fichier de configuration.
    * Fonction pour créer une application API (Flask/FastAPI) pour un agent donné, intégrant sa logique (utilisation de Gemini et des paramètres).
    * Boucle principale pour itérer sur les agents configurés et lancer leurs APIs sur des URLs/ports spécifiés.
* **Gestion du lancement :** Considérer l'utilisation de gestionnaires de processus (comme Supervisor sous Linux ou des services Windows) pour assurer la robustesse et le fonctionnement en arrière-plan des APIs. Pour une simple exécution locale, le script pourrait lancer les serveurs séquentiellement (à des fins de test).

## 3. Création de l'Exécutable Windows

* **Outil suggéré :** PyInstaller.
* **Étapes générales :**
    1.  Installer PyInstaller (`pip install pyinstaller`).
    2.  Créer un fichier `.spec` (optionnel mais recommandé) ou utiliser la commande `pyinstaller` directement.
    3.  S'assurer d'inclure le fichier de configuration (`config.yaml`) dans l'exécutable (via l'option `--add-data` ou en modifiant le fichier `.spec`).
    4.  Compiler le script Python en un seul fichier exécutable (`pyinstaller --onefile votre_script.py --add-data "config.yaml;."` ou `pyinstaller votre_script.spec`).
* **Points importants :** Gestion des chemins de fichiers dans l'exécutable, inclusion des dépendances.

## 4. Interconnexion des Agents (Concept)

* **Méthodes possibles :**
    * Appels d'API directs (via `requests`).
    * Système de messagerie (RabbitMQ, Kafka).
    * Base de données partagée.
* **Choix de la méthode :** Dépend de la complexité et du type d'interaction souhaitée entre les agents.

## Vérification de la Clé API

Avant de lancer l'application, assurez-vous que la clé API est configurée. Si elle n'est pas présente, l'application affichera un prompt pour demander la clé API et l'enregistrera dans un fichier `api_key.txt`.

### Étapes :

1. Lors du premier lancement de l'application, si le fichier `api_key.txt` n'existe pas ou est vide, un prompt s'affichera pour demander la clé API.
2. Entrez la clé API dans le prompt.
3. La clé sera enregistrée dans le fichier `api_key.txt` pour les utilisations futures.

### Exemple de Code :

```python
# Vérification ou demande de la clé API
def verifier_ou_demander_cle_api():
    api_key_file = "api_key.txt"
    if os.path.exists(api_key_file):
        with open(api_key_file, "r") as file:
            return file.read().strip()
    else:
        api_key = simpledialog.askstring("Clé API", "Entrez votre clé API Gemini :")
        if api_key:
            with open(api_key_file, "w") as file:
                file.write(api_key)
            return api_key
        else:
            messagebox.showerror("Erreur", "Clé API non fournie. L'application va se fermer.")
            exit()
```

---

**Fichiers pour GitHub Copilot Chat AI :**

Pour aider Copilot Chat AI à comprendre le projet, voici les fichiers que nous pourrions créer initialement :

1.  **`config.yaml` (Exemple de fichier de configuration) :**

    ```yaml
    agents:
      agent_redacteur:
        nom: "Rédacteur d'articles"
        description: "Génère des articles de blog sur des sujets spécifiques."
        api_url: "http://localhost:5000/redacteur"
        parametres:
          style: "informatif"
          ton: "neutre"
      agent_traducteur:
        nom: "Traducteur multilingue"
        description: "Traduit du texte d'une langue à une autre."
        api_url: "http://localhost:5001/traducteur"
        parametres:
          langue_source: "fr"
          langue_cible: "en"
    ```

2.  **`main.py` (Structure de base du script Python pour lancer les APIs) :**

    ```python
    import yaml
    from flask import Flask, request, jsonify
    import threading

    def charger_configuration(chemin_fichier):
        with open(chemin_fichier, 'r') as fichier:
            try:
                return yaml.safe_load(fichier)
            except yaml.YAMLError as e:
                print(f"Erreur lors de la lecture du fichier de configuration : {e}")
                return None

    def creer_app_agent(agent_config):
        app = Flask(agent_config['nom'])

        @app.route('/', methods=['POST'])
        def handler():
            data = request.get_json()
            resultat = f"Traitement par l'agent '{agent_config['nom']}' avec les données : {data} et les paramètres : {agent_config['parametres']}"
            return jsonify({"resultat": resultat})

        return app

    def run_app(app, host, port):
        app.run(host=host, port=port)

    if __name__ == "__main__":
        config = charger_configuration('config.yaml')

        if config and 'agents' in config:
            threads = []
            for agent_id, agent_config in config['agents'].items():
                print(f"Démarrage de l'agent : {agent_config['nom']} sur {agent_config['api_url']}")
                try:
                    url_parts = agent_config['api_url'].split(':')
                    host = url_parts[1][2:]  # Extract host from http://host:port
                    port = int(url_parts[2].split('/')[0]) # Extract port
                    app = creer_app_agent(agent_config)
                    thread = threading.Thread(target=run_app, args=(app, host, port))
                    threads.append(thread)
                    thread.start()
                except IndexError:
                    print(f"Erreur : URL de l'agent '{agent_config['nom']}' mal formatée.")

            for thread in threads:
                thread.join() # Attendre que tous les threads se terminent (pour cet exemple simple)

        else:
            print("Aucun agent configuré trouvé dans le fichier de configuration.")
    ```

3.  **`README.md` (Introduction et instructions de base) :**

    ```markdown
    # Système d'Agents Spécialisés

    Ce projet vise à créer un système permettant de lancer et de gérer plusieurs agents spécialisés définis dans un fichier de configuration.

    ## Prérequis

    * Python 3.x
    * Librairies : `PyYAML`, `Flask` (installer avec `pip install pyyaml flask`)

    ## Configuration

    1.  Créez ou modifiez le fichier `config.yaml` pour définir vos agents et leurs configurations.

    ## Lancement

    Exécutez le script `main.py` :

    ```bash
    python main.py
    ```

    Cela lancera les APIs des agents définis dans le fichier de configuration. Vous pourrez ensuite interagir avec ces APIs via des requêtes HTTP POST.

    ## Création de l'exécutable Windows (Instructions)

    Pour créer un exécutable Windows, suivez ces étapes :

    1.  Installez PyInstaller : `pip install pyinstaller`
    2.  Exécutez la commande suivante dans le répertoire du projet :
        ```bash
        pyinstaller --onefile --add-data "config.yaml;." main.py
        ```
    3.  L'exécutable sera créé dans le dossier `dist`.

    ## Interconnexion des Agents

    (Cette section sera détaillée ultérieurement)

    ```