# Set Up File - Configuration de Génération de Fichiers

Ce document décrit la fonctionnalité "Set Up File" qui permet de configurer la génération automatique de fichiers à partir des réponses API dans l'application ROB-1.

## Vue d'ensemble

Le menu "Set Up File" permet de configurer comment les interactions avec les APIs (questions et réponses) seront sauvegardées sous forme de fichiers dans le dossier `conversations/`. Cette fonctionnalité propose deux modes d'utilisation distincts.

## Modes de Fonctionnement

### Mode Simple (Conservation)
Ce mode est conçu pour archiver les conversations de manière simple et structurée.

**Caractéristiques :**
- Sauvegarde automatique des conversations
- Options de personnalisation du contenu :
  - Intégrer la question (optionnel)
  - Intégrer la réponse (optionnel)
- Configuration du nom de fichier de base
- Option d'écriture dans le même fichier ou création de nouveaux fichiers

**Utilisation typique :** Conservation d'historiques de conversations, archivage des interactions importantes.

### Mode Développement (Code)
Ce mode est spécialement conçu pour la génération de code et de fichiers techniques.

**Caractéristiques :**
- Sélection de l'extension de fichier (.py, .js, .html, .css, .txt, .md, .json, .xml, .c, .cpp, .java)
- Génération de fichiers prêts à l'usage
- Nommage personnalisé pour chaque requête (intégration future avec Test API)

**Utilisation typique :** Génération de scripts, de composants, de documentation technique, de snippets de code.

## Configuration

### Accès au Menu
1. Ouvrir l'application ROB-1
2. Cliquer sur le menu "API"
3. Sélectionner "Set up File"

### Paramètres Disponibles

#### Activation
- **Case à cocher :** "Activer la génération de fichiers"
- Cette option active ou désactive complètement la fonctionnalité

#### Sélection du Mode
- **Radio boutons :** Choix entre "Mode Simple (Conservation)" et "Mode Développement (Code)"

#### Configuration Mode Simple
- **Intégrer la question :** Include la question posée dans le fichier généré
- **Intégrer la réponse :** Include la réponse de l'API dans le fichier généré
- **Nom du fichier :** Nom de base pour les fichiers générés (ex: "conversation")
- **Écrire dans le même fichier :** Ajoute les nouvelles interactions au même fichier ou crée de nouveaux fichiers

#### Configuration Mode Développement
- **Extension :** Sélection de l'extension de fichier appropriée dans la liste déroulante

## Stockage et Persistance

- Les configurations sont sauvegardées dans le profil API actuel (fichier YAML dans le dossier `profiles/`)
- Les fichiers générés sont stockés dans le dossier `conversations/`
- La configuration est chargée automatiquement au démarrage selon le profil par défaut

## Structure de Configuration (YAML)

La configuration est ajoutée au profil API existant sous la section `file_generation` :

```yaml
file_generation:
  enabled: true
  mode: "simple"  # ou "development"
  simple_config:
    include_question: true
    include_response: true
    base_filename: "conversation"
    same_file: true
  dev_config:
    extension: ".py"
```

## Validation

Le système inclut une validation en temps réel :
- Le bouton "Enregistrer" n'est activé que si la configuration est valide
- En mode Simple : au moins une option (question ou réponse) doit être sélectionnée et le nom de fichier ne peut pas être vide
- En mode Développement : une extension doit être sélectionnée
- L'activation générale doit être cochée pour valider la configuration

## Intégration Future

Cette configuration sera utilisée par l'interface "Test API" pour :
- Générer automatiquement des fichiers après chaque requête réussie
- Proposer un champ de saisie de nom de fichier en mode Développement
- Appliquer les règles configurées pour le contenu et le format des fichiers

## Sécurité

- Les configurations sont stockées localement
- Le dossier `conversations/` est exclu du contrôle de version Git
- Aucune donnée sensible n'est exposée dans les fichiers générés au-delà du contenu des conversations
