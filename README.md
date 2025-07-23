# Rob-1

Ce projet vise à créer un système permettant de lancer et de gérer plusieurs agents spécialisés définis dans un fichier de configuration.

## Prérequis

* Python 3.x
* Librairies : `PyYAML`, `Flask` (installer avec `pip install pyyaml flask`)
* En principe, si vous avez cette version de Python les dépendances s'installeront automatiquement.

## Configuration

1.  La configuration des APIs est le préalable pour utiliser les API LLM  et l'application. Pour cela utiliser le menu Setup API

2.  Utilisez les champs rôle et comportement pour créer un agent.
  Exemples : 
    Rôle : un professeur d'histoire de France - Comportement : rigoureux, pédagogue, cite des sources
    Rôle : un juriste expert en droit des affaires - Comportement : précis, intéressé, méticuleux
    Rôle : un architecte développeur d'applications - Comportement : utilise bonnes pratiques et design pattern, force de proposition 

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
