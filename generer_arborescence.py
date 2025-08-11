#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur d'arborescence complète du projet ROB-1
"""
import os
import sys

def generer_arborescence(chemin_racine, prefixe="", max_depth=4, current_depth=0):
    """
    Génère l'arborescence d'un répertoire avec limitation de profondeur
    """
    if current_depth > max_depth:
        return []
    
    items = []
    
    try:
        # Obtenir tous les éléments du répertoire
        elements = sorted(os.listdir(chemin_racine))
        
        # Séparer dossiers et fichiers
        dossiers = [e for e in elements if os.path.isdir(os.path.join(chemin_racine, e))]
        fichiers = [e for e in elements if os.path.isfile(os.path.join(chemin_racine, e))]
        
        # Filtrer les éléments à exclure
        exclusions = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.vscode', 
                     'profiles_backup_conversation', 'development', 'conversations'}
        
        dossiers = [d for d in dossiers if d not in exclusions]
        
        # Filtrer certains fichiers de test/debug
        fichiers_exclus = {'.env', '.env.example', '.gitignore', 'debug_curl.log', 
                          'application.log'}
        fichiers = [f for f in fichiers if f not in fichiers_exclus]
        
        # Afficher les dossiers en premier
        for i, dossier in enumerate(dossiers):
            est_dernier_dossier = (i == len(dossiers) - 1) and len(fichiers) == 0
            symbole = "└── " if est_dernier_dossier else "├── "
            items.append(f"{prefixe}{symbole}{dossier}/")
            
            # Récursion pour les sous-dossiers
            chemin_sous_dossier = os.path.join(chemin_racine, dossier)
            nouveau_prefixe = prefixe + ("    " if est_dernier_dossier else "│   ")
            sous_items = generer_arborescence(chemin_sous_dossier, nouveau_prefixe, 
                                            max_depth, current_depth + 1)
            items.extend(sous_items)
        
        # Puis afficher les fichiers
        for i, fichier in enumerate(fichiers):
            est_dernier = (i == len(fichiers) - 1)
            symbole = "└── " if est_dernier else "├── "
            items.append(f"{prefixe}{symbole}{fichier}")
            
    except PermissionError:
        items.append(f"{prefixe}[Permission refusée]")
    except Exception as e:
        items.append(f"{prefixe}[Erreur: {e}]")
    
    return items

def main():
    """Fonction principale"""
    print("🌳 ARBORESCENCE PROJET ROB-1")
    print("=" * 60)
    
    chemin_projet = os.path.dirname(os.path.abspath(__file__))
    nom_projet = os.path.basename(chemin_projet)
    
    print(f"📁 {nom_projet}/")
    
    # Générer l'arborescence avec profondeur limitée
    arborescence = generer_arborescence(chemin_projet, max_depth=3)
    
    for ligne in arborescence:
        print(ligne)
    
    print()
    print("=" * 60)
    
    # Statistiques
    total_lignes = len(arborescence)
    dossiers_count = len([l for l in arborescence if l.strip().endswith('/')])
    fichiers_count = total_lignes - dossiers_count
    
    print(f"📊 Statistiques:")
    print(f"   • {dossiers_count} dossiers")
    print(f"   • {fichiers_count} fichiers")
    print(f"   • Total: {total_lignes} éléments")
    
    # Fichiers principaux
    print(f"\n🎯 Fichiers principaux:")
    fichiers_principaux = [
        "main.py - Point d'entrée principal",
        "gui.py - Interface utilisateur",
        "config_manager.py - Gestionnaire de configuration", 
        "conversation_manager.py - Gestionnaire de conversations",
        "api_response_parser.py - Parseur de réponses API",
        "core/api_manager.py - Gestionnaire centralisé des APIs",
        "templates/chat/gemini/curl_basic.txt - Template Gemini"
    ]
    
    for fichier in fichiers_principaux:
        if fichier.split(' - ')[0] in '\n'.join(arborescence):
            print(f"   ✅ {fichier}")
        else:
            print(f"   ❓ {fichier}")

if __name__ == "__main__":
    main()
