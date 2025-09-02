# Rob-1

Ce projet a pour objectif de créer une application permettant  de gérer plusieurs agents spécialisés. 

L'application est indépendante et multi-plateformes : 
- MacOS, Linux, Windows... 
- pas de navigateur web
- autonome : installation et gestion de dépendances automatique mais superviséee
- debug mode

Mémoire et historique :
- contournement du principe stateless des API
- gestion fine de l'historisation et de la mémoire

Enregistrement et sortie
- Le système permet de conserver les interactions
- le principe est d'autoriser des interactions entre des modèles d'origines diverses

Choix de LLM, SML possibles et possibilité d'utilisation d'un LLM Local
- grand choix de LLMs et leurs modèles pour créer un agent
- sécurisation avec utilisation de SML/LLM sur un réseau ou un PC local
- méthodes API en CURL ou Python natif

  cette application permet de se connecter sur différentes API LLM définies dans un fichier de configuration. Cette première version permet l'organisation et la sortie de fichiers, ainsi qu'un contournement de la contrainte stateless de l'api pour gérer un historique de conversations. 

## Prérequis

* Python 3.x
* Librairies : `PyYAML`, `Flask` (installer avec `pip install pyyaml flask`) etc...
* En principe, si vous avez cette version de Python les dépendances s'installeront automatiquement.

## Configuration

1.  La configuration des APIs est le préalable pour utiliser les API LLM  et l'application. Pour cela utiliser le menu Setup API et choisissez un LLM en cochant la case default

2.  Utilisez les champs rôle et comportement pour créer un agent.
  Exemples : 
    Rôle : un professeur d'histoire de France - Comportement : rigoureux, pédagogue, cite des sources

    Rôle : un juriste expert en droit des affaires - Comportement : précis, intéressé, méticuleux
    
    Rôle : un architecte développeur d'applications - Comportement : utilise bonnes pratiques et design pattern, force de proposition 

3.  Testez votre configuration d' agent. Allez sur Config>test API

4.  Test de fonction de mémoire et d'historisation
      Dans setup API, cochez la case historique et si vous souhaitez une configuration spéciale avec un seuil de mots ou tokens ou un comportement de résumé particulier, utilisez setup History.
      Aller sur test API et lancer les conversations en API historisées.

## Lancement

### Méthode 1 : Lancement direct 

À la première installation, ouvrir une invite de commandes et éxécutez le script `main.py` :

```bash
python main.py
```
Cette commande peut être utilisée par la suite pour lancer l'appli.

Lors du premier lancement, l'application créera automatiquement un lanceur adapté à votre système d'exploitation :
- **Windows** : `RUN.bat` 
- **Linux/macOS** : `run.sh` - Exécutez `./run.sh` dans le terminal

### Méthode 2 : Une fois le lanceur créé

Double cliquez sur le lanceur précédemment créé


> 💡 **Note Windows** : Le lanceur utilise `pythonw` pour éviter l'affichage de la console Python en arrière-plan.

**Linux/macOS :**
```bash
./run.sh
```

### Méthode 3 : Regénérer le lanceur

Si vous souhaitez recréer le lanceur, utilisez :

```bash
python create_launcher.py
```

Ce script vous permettra de générer un nouveau lanceur ou de remplacer l'existant.

## Interconnexion des Agents

(Cette section sera détaillée ultérieurement)
