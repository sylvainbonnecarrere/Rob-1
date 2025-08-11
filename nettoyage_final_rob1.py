#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de nettoyage final du projet ROB-1
Supprime tous les fichiers de développement et de débogage
"""
import os
import sys

# Fichiers et dossiers à conserver (core de l'application)
FICHIERS_A_CONSERVER = {
    # Fichiers principaux
    'main.py',
    'gui.py', 
    'config_manager.py',
    'conversation_manager.py',
    'api_response_parser.py',
    'requirements.txt',
    'README.md',
    'RUN.bat',
    'utils.py',
    'system_profile_generator.py',
    # Dossiers complets à conserver
    'core/',
    'images/', 
    'install_scripts/',
    'profiles/',
    'system/',
    'templates/',
    'utils/',
    'conversations/',
    'development/',
    'profiles_backup_conversation/',
    '__pycache__/',
    '.git/',
    '.gitignore',
    '.env',
    '.env.example',
    # Script de nettoyage lui-même
    'nettoyage_final_rob1.py'
}

def supprimer_fichier(chemin):
    """Supprime un fichier en toute sécurité"""
    try:
        if os.path.exists(chemin):
            os.remove(chemin)
            print(f"✅ Supprimé: {chemin}")
            return True
        else:
            print(f"⚠️ Déjà absent: {chemin}")
            return False
    except Exception as e:
        print(f"❌ Erreur suppression {chemin}: {e}")
        return False

def main():
    """Fonction principale de nettoyage"""
    print("🧹 NETTOYAGE FINAL PROJET ROB-1")
    print("=" * 60)
    
    chemin_racine = os.path.dirname(os.path.abspath(__file__))
    os.chdir(chemin_racine)
    
    # Lister tous les fichiers dans le répertoire racine
    tous_fichiers = []
    for element in os.listdir('.'):
        if os.path.isfile(element):
            tous_fichiers.append(element)
    
    print(f"📁 Analyse de {len(tous_fichiers)} fichiers dans le répertoire racine...")
    
    # Identifier les fichiers à supprimer
    fichiers_a_supprimer = []
    for fichier in tous_fichiers:
        if fichier not in FICHIERS_A_CONSERVER:
            fichiers_a_supprimer.append(fichier)
    
    print(f"\n🎯 {len(fichiers_a_supprimer)} fichiers à supprimer:")
    for fichier in sorted(fichiers_a_supprimer):
        print(f"   • {fichier}")
    
    print(f"\n✅ {len(FICHIERS_A_CONSERVER) - 1} éléments à conserver:")  # -1 pour exclure le script
    for element in sorted(FICHIERS_A_CONSERVER):
        if element != 'nettoyage_final_rob1.py':
            print(f"   • {element}")
    
    # Demander confirmation
    print(f"\n⚠️ Êtes-vous sûr de vouloir supprimer {len(fichiers_a_supprimer)} fichiers ?")
    confirmation = input("Tapez 'OUI' pour confirmer: ")
    
    if confirmation != 'OUI':
        print("❌ Annulation du nettoyage")
        return
    
    # Procéder à la suppression
    print(f"\n🧹 Suppression en cours...")
    
    supprimes = 0
    erreurs = 0
    
    for fichier in fichiers_a_supprimer:
        if supprimer_fichier(fichier):
            supprimes += 1
        else:
            erreurs += 1
    
    # Nettoyage spécifique: backup dans install_scripts
    backup_file = os.path.join('install_scripts', 'template_installer.py.backup')
    if os.path.exists(backup_file):
        if supprimer_fichier(backup_file):
            supprimes += 1
    
    # Résumé final
    print(f"\n📊 RÉSUMÉ DU NETTOYAGE:")
    print(f"   ✅ {supprimes} fichiers supprimés")
    print(f"   ❌ {erreurs} erreurs")
    print(f"   📁 Structure core préservée")
    
    print(f"\n🎉 NETTOYAGE TERMINÉ!")
    print(f"Le projet ROB-1 est maintenant propre et prêt pour la production.")
    
    # Afficher la structure finale
    print(f"\n📁 STRUCTURE FINALE:")
    for element in sorted(os.listdir('.')):
        if os.path.isdir(element):
            print(f"   📁 {element}/")
        else:
            print(f"   📄 {element}")

if __name__ == "__main__":
    main()
