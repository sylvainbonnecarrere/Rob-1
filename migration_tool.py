"""
Migration Tool - Outil de migration YAML vers JSON
Convertit les anciens profils YAML vers la nouvelle structure JSON
"""

import yaml
import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from config_manager import ConfigManager

class YAMLToJSONMigrator:
    """Migrateur YAML vers JSON avec sauvegarde et validation"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.profiles_dir = os.path.join(base_dir, "profiles")
        self.backup_dir = os.path.join(base_dir, "profiles_backup_yaml")
        self.config_manager = ConfigManager(base_dir)
        self.logger = logging.getLogger(__name__)
    
    def backup_yaml_profiles(self) -> bool:
        """Sauvegarde tous les profils YAML avant migration"""
        try:
            if os.path.exists(self.backup_dir):
                # Créer un backup horodaté si le dossier existe déjà
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = f"{self.backup_dir}_{timestamp}"
            else:
                backup_dir = self.backup_dir
            
            os.makedirs(backup_dir, exist_ok=True)
            
            yaml_files = [f for f in os.listdir(self.profiles_dir) if f.endswith('.yaml')]
            
            for yaml_file in yaml_files:
                src = os.path.join(self.profiles_dir, yaml_file)
                dst = os.path.join(backup_dir, yaml_file)
                shutil.copy2(src, dst)
                self.logger.info(f"Backup : {yaml_file} -> {backup_dir}")
            
            return True
        except Exception as e:
            self.logger.error(f"Erreur backup YAML : {e}")
            return False
    
    def extract_curl_template(self, curl_exe: str, profile_name: str) -> str:
        """Extrait et nettoie le template curl"""
        try:
            if not curl_exe:
                return ""
            
            # Nettoyer le template curl des caractères d'échappement YAML
            cleaned_template = curl_exe.replace('\\n', '\n').strip()
            
            # Sauvegarder le template séparément
            template_id = f"{profile_name.lower()}_chat"
            self.config_manager.save_template(template_id, cleaned_template)
            
            return template_id
        except Exception as e:
            self.logger.warning(f"Erreur extraction template curl pour {profile_name} : {e}")
            return ""
    
    def convert_yaml_to_json_structure(self, yaml_data: Dict[str, Any], profile_name: str) -> Dict[str, Any]:
        """Convertit la structure YAML vers JSON"""
        try:
            # Fonction helper pour gérer les valeurs None
            def safe_get(key: str, default: str = '') -> str:
                value = yaml_data.get(key, default)
                return value if value is not None else default
            
            # Extraire le template curl
            curl_exe = yaml_data.get('curl_exe', '')
            template_id = self.extract_curl_template(curl_exe, profile_name)
            
            # Structure JSON standardisée
            json_structure = {
                "name": profile_name,
                "api_key": safe_get('api_key'),
                "api_url": safe_get('api_url'),
                "behavior": safe_get('behavior'),
                "role": safe_get('role'),
                "default": yaml_data.get('default', False),
                "history": yaml_data.get('history', False),
                "replace_apikey": safe_get('replace_apikey'),
                "template_id": template_id,
                "file_generation": {
                    "enabled": False,
                    "mode": "simple",
                    "simple_config": {
                        "include_question": True,
                        "include_response": True,
                        "base_filename": "conversation",
                        "same_file": True
                    },
                    "dev_config": {
                        "extension": ".py"
                    }
                }
            }
            
            # Migrer la configuration file_generation si elle existe
            if 'file_generation' in yaml_data:
                existing_config = yaml_data['file_generation']
                json_structure['file_generation'].update(existing_config)
            
            return json_structure
        except Exception as e:
            self.logger.error(f"Erreur conversion structure {profile_name} : {e}")
            return {}
    
    def migrate_single_profile(self, yaml_file: str) -> bool:
        """Migre un seul profil YAML vers JSON"""
        try:
            profile_name = yaml_file.replace('.yaml', '').replace('.yml', '')
            yaml_path = os.path.join(self.profiles_dir, yaml_file)
            
            # Charger le YAML avec gestion d'encodage robuste
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
            
            if not yaml_data:
                self.logger.warning(f"Fichier YAML vide : {yaml_file}")
                return False
            
            # Convertir vers structure JSON
            json_data = self.convert_yaml_to_json_structure(yaml_data, profile_name)
            
            if not json_data:
                return False
            
            # Sauvegarder avec ConfigManager
            success = self.config_manager.save_profile(profile_name, json_data)
            
            if success:
                self.logger.info(f"Migration réussie : {profile_name}")
            
            return success
        except Exception as e:
            self.logger.error(f"Erreur migration {yaml_file} : {e}")
            return False
    
    def migrate_all_profiles(self) -> Dict[str, bool]:
        """Migre tous les profils YAML vers JSON"""
        results = {}
        
        try:
            yaml_files = [f for f in os.listdir(self.profiles_dir) 
                         if f.endswith('.yaml') or f.endswith('.yml')]
            
            if not yaml_files:
                self.logger.info("Aucun fichier YAML à migrer")
                return results
            
            self.logger.info(f"Migration de {len(yaml_files)} profils YAML")
            
            for yaml_file in yaml_files:
                results[yaml_file] = self.migrate_single_profile(yaml_file)
            
            # Résumé
            success_count = sum(1 for success in results.values() if success)
            self.logger.info(f"Migration terminée : {success_count}/{len(yaml_files)} réussies")
            
            return results
        except Exception as e:
            self.logger.error(f"Erreur migration globale : {e}")
            return results
    
    def cleanup_yaml_files(self, migration_results: Dict[str, bool]) -> bool:
        """Supprime les fichiers YAML après migration réussie"""
        try:
            cleanup_count = 0
            
            for yaml_file, success in migration_results.items():
                if success:
                    yaml_path = os.path.join(self.profiles_dir, yaml_file)
                    if os.path.exists(yaml_path):
                        os.remove(yaml_path)
                        cleanup_count += 1
                        self.logger.info(f"Supprimé : {yaml_file}")
            
            self.logger.info(f"Nettoyage terminé : {cleanup_count} fichiers YAML supprimés")
            return True
        except Exception as e:
            self.logger.error(f"Erreur nettoyage YAML : {e}")
            return False
    
    def perform_full_migration(self, cleanup_yaml: bool = True) -> bool:
        """Effectue la migration complète avec toutes les étapes"""
        try:
            self.logger.info("=== DÉBUT MIGRATION YAML → JSON ===")
            
            # 1. Backup
            if not self.backup_yaml_profiles():
                self.logger.error("Échec backup, arrêt de la migration")
                return False
            
            # 2. Migration
            results = self.migrate_all_profiles()
            
            if not results:
                self.logger.info("Aucune migration à effectuer")
                return True
            
            # 3. Vérification
            all_success = all(results.values())
            if not all_success:
                failed_files = [f for f, success in results.items() if not success]
                self.logger.warning(f"Échecs de migration : {failed_files}")
            
            # 4. Nettoyage (optionnel)
            if cleanup_yaml and all_success:
                self.cleanup_yaml_files(results)
            
            self.logger.info("=== FIN MIGRATION YAML → JSON ===")
            return all_success
        except Exception as e:
            self.logger.error(f"Erreur migration complète : {e}")
            return False
    
    def verify_migration(self) -> bool:
        """Vérifie que la migration s'est bien déroulée"""
        try:
            # Vérifier que les profils JSON existent et sont valides
            json_profiles = self.config_manager.list_profiles()
            
            if not json_profiles:
                self.logger.error("Aucun profil JSON trouvé après migration")
                return False
            
            # Vérifier qu'un profil par défaut existe
            default_profile = self.config_manager.get_default_profile()
            if not default_profile:
                self.logger.error("Aucun profil par défaut trouvé")
                return False
            
            self.logger.info(f"Vérification réussie : {len(json_profiles)} profils JSON valides")
            return True
        except Exception as e:
            self.logger.error(f"Erreur vérification migration : {e}")
            return False

def migrate_yaml_profiles_to_json(base_dir: str = ".") -> bool:
    """Fonction utilitaire pour migration automatique"""
    try:
        migrator = YAMLToJSONMigrator(base_dir)
        success = migrator.perform_full_migration()
        
        if success:
            return migrator.verify_migration()
        
        return False
    except Exception as e:
        logging.error(f"Erreur migration YAML → JSON : {e}")
        return False
