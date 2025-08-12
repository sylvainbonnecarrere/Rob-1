#!/usr/bin/env python3
"""
Nettoyage complet du dossier debug - Garde uniquement l'analyse finale
"""

import os
import shutil
from pathlib import Path

def cleanup_debug_folder():
    """Nettoie complètement le dossier debug"""
    print("🧹 NETTOYAGE COMPLET DOSSIER DEBUG")
    print("=" * 40)
    
    debug_dir = Path("debug")
    if not debug_dir.exists():
        print("❌ Dossier debug introuvable")
        return
    
    # Fichiers à conserver
    keep_files = [
        "analyse_historique_v2.py"  # Notre analyse finale pour l'architecte
    ]
    
    all_files = list(debug_dir.glob("*"))
    files_to_delete = []
    files_to_keep = []
    
    for file_path in all_files:
        if file_path.name in keep_files:
            files_to_keep.append(file_path)
        else:
            files_to_delete.append(file_path)
    
    print(f"📊 Analyse: {len(files_to_delete)} à supprimer, {len(files_to_keep)} à conserver")
    
    print("\n📄 FICHIERS À CONSERVER:")
    for file_path in files_to_keep:
        print(f"   ✅ {file_path.name}")
    
    print(f"\n🗑️  FICHIERS À SUPPRIMER ({len(files_to_delete)}):")
    for i, file_path in enumerate(files_to_delete[:10]):  # Afficher les 10 premiers
        print(f"   - {file_path.name}")
    if len(files_to_delete) > 10:
        print(f"   ... et {len(files_to_delete) - 10} autres")
    
    # Confirmation
    response = input(f"\nSupprimer {len(files_to_delete)} fichiers ? (o/N): ").lower()
    if response != 'o':
        print("❌ Nettoyage annulé")
        return
    
    # Suppression
    deleted_count = 0
    for file_path in files_to_delete:
        try:
            if file_path.is_file():
                file_path.unlink()
                deleted_count += 1
            elif file_path.is_dir():
                shutil.rmtree(file_path)
                deleted_count += 1
        except Exception as e:
            print(f"❌ Erreur suppression {file_path.name}: {e}")
    
    print(f"\n✅ {deleted_count}/{len(files_to_delete)} fichiers supprimés")
    
    # Vérification finale
    remaining_files = list(debug_dir.glob("*"))
    print(f"\n📊 Dossier debug final: {len(remaining_files)} fichiers")
    for file_path in remaining_files:
        print(f"   📄 {file_path.name}")

def check_profiles_backup():
    """Vérifie et supprime définitivement profiles_backup_conversation"""
    print(f"\n{'='*40}")
    print("🔍 VÉRIFICATION PROFILES_BACKUP_CONVERSATION")
    print("=" * 40)
    
    backup_dir = Path("profiles_backup_conversation")
    
    if backup_dir.exists():
        print("⚠️  Le dossier profiles_backup_conversation existe encore")
        
        # Vérifier le contenu
        content = list(backup_dir.glob("*"))
        if content:
            print(f"   📁 Contient {len(content)} éléments:")
            for item in content:
                print(f"     - {item.name}")
        else:
            print("   📁 Dossier vide")
        
        # Proposer suppression
        response = input("Supprimer définitivement ce dossier ? (o/N): ").lower()
        if response == 'o':
            try:
                shutil.rmtree(backup_dir)
                print("✅ profiles_backup_conversation supprimé définitivement")
            except Exception as e:
                print(f"❌ Erreur suppression: {e}")
        else:
            print("⚠️  Dossier conservé")
    else:
        print("✅ profiles_backup_conversation déjà supprimé")

def main():
    """Nettoyage complet"""
    cleanup_debug_folder()
    check_profiles_backup()
    
    print(f"\n{'='*40}")
    print("📊 NETTOYAGE COMPLET TERMINÉ")
    print("=" * 40)
    print("✅ Setup History V2 opérationnel")
    print("✅ Architecture V2 propre")
    print("📄 Analyse historique disponible pour architecte")
    print("🎯 Prêt pour phase suivante: Gestion historique robuste")

if __name__ == "__main__":
    main()
