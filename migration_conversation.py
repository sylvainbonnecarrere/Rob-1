#!/usr/bin/env python3
"""
Script de migration pour ajouter la configuration de conversation
aux profils existants.

Ce script met à jour automatiquement tous les profils JSON existants
avec la nouvelle configuration de conversation requise pour le ConversationManager.
"""

import os
import sys
import json
from pathlib import Path
from config_manager import ConfigManager
import logging

def setup_logging():
    """Configuration du logging pour la migration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('migration_conversation.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def migrate_profiles():
    """
    Migre tous les profils existants pour ajouter la configuration de conversation
    """
    logger = setup_logging()
    logger.info("=== DÉBUT MIGRATION CONVERSATION ===")
    
    try:
        # Initialiser le ConfigManager
        config_manager = ConfigManager()
        
        # Obtenir la liste des profils existants
        profiles_dir = Path("profiles")
        if not profiles_dir.exists():
            logger.warning("Répertoire profiles/ non trouvé")
            return False
        
        # Lister tous les fichiers .json dans profiles/
        profile_files = list(profiles_dir.glob("*.json"))
        
        if not profile_files:
            logger.info("Aucun profil JSON trouvé")
            return True
        
        logger.info(f"Profils trouvés : {len(profile_files)}")
        
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        for profile_file in profile_files:
            profile_name = profile_file.stem
            logger.info(f"Migration du profil : {profile_name}")
            
            try:
                # Charger le profil existant
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                
                # Vérifier si la configuration conversation existe déjà
                if 'conversation' in profile_data:
                    logger.info(f"  → {profile_name} : déjà migré, ignoré")
                    skipped_count += 1
                    continue
                
                # Ajouter la configuration de conversation
                profile_data['conversation'] = {
                    "summary_enabled": True,
                    "summary_threshold": {
                        "words": 300,
                        "sentences": 6
                    },
                    "summary_template_id": "default_summary",
                    "show_indicators": True
                }
                
                # Sauvegarder avec le ConfigManager pour validation
                success = config_manager.save_profile(profile_name, profile_data)
                
                if success:
                    logger.info(f"  → {profile_name} : migré avec succès")
                    migrated_count += 1
                else:
                    logger.error(f"  → {profile_name} : échec de sauvegarde")
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"  → {profile_name} : erreur - {e}")
                error_count += 1
        
        # Résumé de la migration
        logger.info(f"=== RÉSUMÉ MIGRATION ===")
        logger.info(f"Profils migrés    : {migrated_count}")
        logger.info(f"Profils ignorés   : {skipped_count}")
        logger.info(f"Erreurs           : {error_count}")
        logger.info(f"Total traité      : {len(profile_files)}")
        
        # Vérifier que le template de conversation existe
        template_created = config_manager.save_conversation_template(
            "default_summary",
            """Veuillez analyser la conversation suivante et créer un résumé concis qui préserve les informations essentielles pour maintenir la continuité de la discussion.

INSTRUCTIONS DE RÉSUMÉ :
- Conservez les points clés et décisions importantes
- Maintenez le contexte nécessaire pour les prochaines questions
- Soyez concis mais informatif (maximum 150 mots)
- Organisez par thèmes si plusieurs sujets sont abordés

CONVERSATION À RÉSUMER :
{HISTORIQUE_COMPLET}

RÉSUMÉ CONTEXTUEL :"""
        )
        
        if template_created:
            logger.info("Template de conversation 'default_summary' créé/vérifié")
        
        logger.info("=== FIN MIGRATION ===")
        return error_count == 0
        
    except Exception as e:
        logger.error(f"Erreur générale de migration : {e}")
        return False

def backup_profiles():
    """
    Crée une sauvegarde des profils avant migration
    """
    logger = logging.getLogger(__name__)
    
    try:
        profiles_dir = Path("profiles")
        backup_dir = Path("profiles_backup_conversation")
        
        if not profiles_dir.exists():
            return True
        
        # Créer le répertoire de sauvegarde
        backup_dir.mkdir(exist_ok=True)
        
        # Copier tous les fichiers JSON
        import shutil
        profile_files = list(profiles_dir.glob("*.json"))
        
        for profile_file in profile_files:
            backup_path = backup_dir / profile_file.name
            shutil.copy2(profile_file, backup_path)
            logger.info(f"Sauvegarde : {profile_file.name}")
        
        logger.info(f"Sauvegarde créée dans : {backup_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur de sauvegarde : {e}")
        return False

def main():
    """Point d'entrée principal du script de migration"""
    print("🔄 Migration des profils pour la gestion de conversation")
    print("=" * 60)
    
    # Créer une sauvegarde
    print("📁 Création de sauvegarde...")
    if not backup_profiles():
        print("❌ Échec de la sauvegarde - arrêt")
        return False
    
    print("✅ Sauvegarde créée")
    
    # Exécuter la migration
    print("\n🚀 Début de la migration...")
    success = migrate_profiles()
    
    if success:
        print("\n✅ Migration terminée avec succès!")
        print("📋 Vérifiez le fichier migration_conversation.log pour les détails")
        return True
    else:
        print("\n❌ Migration terminée avec des erreurs")
        print("📋 Consultez migration_conversation.log pour les détails")
        print("💾 Restaurez depuis profiles_backup_conversation/ si nécessaire")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
