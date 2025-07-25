"""
Script de nettoyage final - Suppression des anciens fichiers YAML
Exécute les étapes 3 & 4 de la migration avec vérifications de sécurité
"""

import os
import shutil
import json
from datetime import datetime
from config_manager import ConfigManager

def cleanup_migration():
    """Nettoyage complet après migration réussie"""
    print("🧹 NETTOYAGE POST-MIGRATION")
    print("=" * 50)
    
    config_manager = ConfigManager(".")
    
    # Étape 1: Vérifier que tous les profils JSON sont valides
    print("\n=== VÉRIFICATION FINALE DES PROFILS JSON ===")
    profiles = config_manager.list_profiles()
    
    if not profiles:
        print("❌ ARRÊT : Aucun profil JSON trouvé ! Nettoyage annulé.")
        return False
    
    valid_profiles = []
    for profile_name in profiles:
        profile = config_manager.load_profile(profile_name)
        if profile:
            valid_profiles.append(profile_name)
            print(f"✅ {profile_name} : profil JSON valide")
        else:
            print(f"❌ {profile_name} : profil JSON INVALIDE")
    
    if len(valid_profiles) != len(profiles):
        print("❌ ARRÊT : Certains profils JSON sont invalides ! Nettoyage annulé.")
        return False
    
    print(f"✅ Tous les {len(profiles)} profils JSON sont valides")
    
    # Étape 2: Vérifier que les templates existent
    print("\n=== VÉRIFICATION DES TEMPLATES ===")
    templates_ok = True
    for profile_name in valid_profiles:
        profile = config_manager.load_profile(profile_name)
        template_id = profile.get('template_id', '')
        if template_id:
            template = config_manager.load_template(template_id)
            if template:
                print(f"✅ Template {template_id} : présent ({len(template)} chars)")
            else:
                print(f"❌ Template {template_id} : MANQUANT")
                templates_ok = False
    
    if not templates_ok:
        print("❌ ARRÊT : Certains templates sont manquants ! Nettoyage annulé.")
        return False
    
    # Étape 3: Supprimer les fichiers YAML
    print("\n=== SUPPRESSION DES FICHIERS YAML ===")
    profiles_dir = "profiles"
    yaml_files = []
    
    if os.path.exists(profiles_dir):
        yaml_files = [f for f in os.listdir(profiles_dir) if f.endswith('.yaml')]
    
    if not yaml_files:
        print("ℹ️  Aucun fichier YAML à supprimer")
    else:
        print(f"📁 Fichiers YAML à supprimer : {yaml_files}")
        
        # Confirmation de sécurité
        response = input("⚠️  Confirmer la suppression des fichiers YAML ? (oui/non) : ")
        if response.lower() in ['oui', 'o', 'yes', 'y']:
            suppressed_count = 0
            for yaml_file in yaml_files:
                try:
                    yaml_path = os.path.join(profiles_dir, yaml_file)
                    os.remove(yaml_path)
                    print(f"🗑️  Supprimé : {yaml_file}")
                    suppressed_count += 1
                except Exception as e:
                    print(f"❌ Erreur suppression {yaml_file} : {e}")
            
            print(f"✅ {suppressed_count}/{len(yaml_files)} fichiers YAML supprimés")
        else:
            print("ℹ️  Suppression YAML annulée par l'utilisateur")
    
    # Étape 4: Nettoyer le fichier [profil]system_windows.yaml
    print("\n=== NETTOYAGE PROFIL SYSTÈME ANCIEN ===")
    old_system_file = "[profil]system_windows.yaml"
    
    if os.path.exists(old_system_file):
        print(f"📄 Ancien profil système trouvé : {old_system_file}")
        
        # Vérifier qu'on a un nouveau profil système
        new_system_dir = "system/hardware"
        if os.path.exists(new_system_dir):
            system_files = [f for f in os.listdir(new_system_dir) if f.endswith('.json')]
            if system_files:
                print(f"✅ Nouveau profil système trouvé : {system_files[-1]}")
                
                response = input("⚠️  Confirmer la suppression de l'ancien profil système ? (oui/non) : ")
                if response.lower() in ['oui', 'o', 'yes', 'y']:
                    try:
                        os.remove(old_system_file)
                        print(f"🗑️  Supprimé : {old_system_file}")
                    except Exception as e:
                        print(f"❌ Erreur suppression {old_system_file} : {e}")
                else:
                    print("ℹ️  Suppression profil système annulée")
            else:
                print("❌ Aucun nouveau profil système trouvé ! Conservation de l'ancien.")
        else:
            print("❌ Répertoire system/hardware introuvable ! Conservation de l'ancien.")
    else:
        print("ℹ️  Aucun ancien profil système à supprimer")
    
    # Étape 5: Supprimer les anciens répertoires de backup
    print("\n=== NETTOYAGE DES BACKUPS YAML ===")
    backup_dirs = []
    for item in os.listdir("."):
        if item.startswith("profiles_backup_yaml"):
            backup_dirs.append(item)
    
    if backup_dirs:
        print(f"📁 Répertoires de backup trouvés : {backup_dirs}")
        response = input("⚠️  Garder les backups YAML pour sécurité ? (oui/non) : ")
        if response.lower() in ['non', 'n', 'no']:
            for backup_dir in backup_dirs:
                try:
                    shutil.rmtree(backup_dir)
                    print(f"🗑️  Supprimé : {backup_dir}")
                except Exception as e:
                    print(f"❌ Erreur suppression {backup_dir} : {e}")
        else:
            print("ℹ️  Backups YAML conservés pour sécurité")
    else:
        print("ℹ️  Aucun répertoire de backup à nettoyer")
    
    # Étape 6: Rapport final
    print("\n" + "=" * 50)
    print("🎉 NETTOYAGE TERMINÉ !")
    print("📊 STATUT FINAL :")
    
    # Compter les fichiers restants
    remaining_yaml = len([f for f in os.listdir(profiles_dir) if f.endswith('.yaml')])
    json_profiles = len(config_manager.list_profiles())
    
    print(f"  - Profils JSON actifs : {json_profiles}")
    print(f"  - Fichiers YAML restants : {remaining_yaml}")
    print(f"  - Templates disponibles : {len([f for f in os.listdir('templates/api_commands') if f.endswith('.txt')])}")
    print(f"  - Ancien système profil : {'❌ Supprimé' if not os.path.exists(old_system_file) else '✅ Conservé'}")
    
    if remaining_yaml == 0 and json_profiles >= 3:
        print("\n🎊 MIGRATION 100% COMPLÈTE !")
        print("✨ Votre application utilise maintenant exclusivement l'architecture JSON")
        print("🔧 Avantages obtenus :")
        print("  ✅ Résolution des problèmes d'encodage UTF-8")
        print("  ✅ Validation stricte des configurations")
        print("  ✅ Séparation claire templates/profils")
        print("  ✅ Organisation système améliorée")
        print("  ✅ Profils système dans /system/hardware/")
    else:
        print("\n⚠️  Migration partiellement terminée")
        print("📝 Actions recommandées : finaliser la suppression si tests OK")
    
    return True

if __name__ == "__main__":
    print("🚀 SCRIPT DE NETTOYAGE POST-MIGRATION")
    print("Exécution sécurisée avec vérifications...")
    print()
    
    success = cleanup_migration()
    
    if success:
        print("\n✅ Script terminé avec succès")
    else:
        print("\n❌ Script interrompu pour sécurité")
