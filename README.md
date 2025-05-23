# Rob-1

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
