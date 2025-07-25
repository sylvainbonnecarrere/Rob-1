"""
System Profile Generator - Génère automatiquement les profils système
Remplace le fichier [profil]system_windows.yaml par une approche plus propre
"""

import json
import os
import platform
import sys
import psutil
import shutil
from datetime import datetime
from typing import Dict, Any, List
import logging

class SystemProfileGenerator:
    """Générateur de profils système optimisés"""
    
    def __init__(self, app_directory: str = "."):
        self.app_directory = os.path.abspath(app_directory)
        self.logger = logging.getLogger(__name__)
    
    def get_os_info(self) -> Dict[str, str]:
        """Récupère les informations sur le système d'exploitation"""
        return {
            "name": platform.system(),
            "version": platform.release(),
            "architecture": platform.machine()
        }
    
    def get_python_info(self) -> Dict[str, str]:
        """Récupère les informations Python"""
        return {
            "version": platform.python_version(),
            "executable": sys.executable
        }
    
    def get_hardware_info(self) -> Dict[str, Any]:
        """Récupère les informations matérielles essentielles"""
        try:
            # Informations mémoire
            memory = psutil.virtual_memory()
            total_memory_gb = round(memory.total / (1024**3), 2)
            
            # Informations disque pour le répertoire de l'application
            disk_usage = shutil.disk_usage(self.app_directory)
            disk_free_gb = round(disk_usage.free / (1024**3), 1)
            
            # Nombre de cœurs CPU
            cpu_cores = psutil.cpu_count(logical=False) or psutil.cpu_count()
            
            return {
                "cpu_cores": cpu_cores,
                "total_memory_gb": total_memory_gb,
                "disk_free_gb": disk_free_gb
            }
        except Exception as e:
            self.logger.warning(f"Erreur récupération infos matériel : {e}")
            return {
                "cpu_cores": 0,
                "total_memory_gb": 0.0,
                "disk_free_gb": 0.0
            }
    
    def get_app_info(self) -> Dict[str, Any]:
        """Récupère les informations sur l'application (sans détails Git)"""
        try:
            # Fichiers clés de l'application (pas l'arborescence complète !)
            key_files = []
            for item in os.listdir(self.app_directory):
                if os.path.isfile(os.path.join(self.app_directory, item)):
                    # Filtrer les fichiers importants
                    if any(item.endswith(ext) for ext in ['.py', '.yaml', '.json', '.md', '.txt']):
                        if not item.startswith('.') and not item.startswith('debug_'):
                            key_files.append(item)
            
            # Trier pour cohérence
            key_files.sort()
            
            return {
                "directory": self.app_directory,
                "script_path": os.path.join(self.app_directory, "main.py"),
                "key_files": key_files[:10]  # Limiter à 10 fichiers max
            }
        except Exception as e:
            self.logger.warning(f"Erreur récupération infos app : {e}")
            return {
                "directory": self.app_directory,
                "script_path": "",
                "key_files": []
            }
    
    def generate_system_profile(self) -> Dict[str, Any]:
        """Génère un profil système complet et optimisé"""
        return {
            "generated_at": datetime.now().isoformat(),
            "os_info": self.get_os_info(),
            "python_info": self.get_python_info(),
            "hardware_info": self.get_hardware_info(),
            "app_info": self.get_app_info()
        }
    
    def save_system_profile(self, output_dir: str = None) -> bool:
        """Sauvegarde le profil système en JSON"""
        try:
            if output_dir is None:
                output_dir = os.path.join(self.app_directory, "system", "hardware")
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Nom de fichier basé sur l'OS et la date
            os_name = platform.system().lower()
            date_str = datetime.now().strftime("%Y%m%d")
            filename = f"{os_name}_profile_{date_str}.json"
            
            profile_data = self.generate_system_profile()
            
            file_path = os.path.join(output_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Profil système sauvegardé : {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde profil système : {e}")
            return False
    
    def load_latest_system_profile(self, profile_dir: str = None) -> Dict[str, Any]:
        """Charge le profil système le plus récent"""
        try:
            if profile_dir is None:
                profile_dir = os.path.join(self.app_directory, "system", "hardware")
            
            if not os.path.exists(profile_dir):
                return {}
            
            # Trouver le fichier le plus récent
            profile_files = [f for f in os.listdir(profile_dir) if f.endswith('_profile_*.json')]
            if not profile_files:
                return {}
            
            # Trier par date dans le nom de fichier
            profile_files.sort(reverse=True)
            latest_file = profile_files[0]
            
            file_path = os.path.join(profile_dir, latest_file)
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Erreur chargement profil système : {e}")
            return {}
    
    def cleanup_old_profiles(self, profile_dir: str = None, keep_count: int = 5) -> bool:
        """Nettoie les anciens profils système (garde les N plus récents)"""
        try:
            if profile_dir is None:
                profile_dir = os.path.join(self.app_directory, "system", "hardware")
            
            if not os.path.exists(profile_dir):
                return True
            
            # Lister tous les profils
            profile_files = [f for f in os.listdir(profile_dir) if f.endswith('_profile_*.json')]
            if len(profile_files) <= keep_count:
                return True
            
            # Trier par date (nom de fichier)
            profile_files.sort(reverse=True)
            
            # Supprimer les anciens
            files_to_delete = profile_files[keep_count:]
            for file_to_delete in files_to_delete:
                file_path = os.path.join(profile_dir, file_to_delete)
                os.remove(file_path)
                self.logger.info(f"Profil système ancien supprimé : {file_to_delete}")
            
            return True
        except Exception as e:
            self.logger.error(f"Erreur nettoyage profils système : {e}")
            return False
    
    def auto_generate_and_cleanup(self) -> bool:
        """Génère automatiquement et nettoie les profils (fonction de commodité)"""
        success = self.save_system_profile()
        if success:
            self.cleanup_old_profiles()
        return success

def generate_system_profile_at_startup(app_directory: str = ".") -> bool:
    """Fonction utilitaire pour génération automatique au démarrage"""
    try:
        generator = SystemProfileGenerator(app_directory)
        return generator.auto_generate_and_cleanup()
    except Exception as e:
        logging.error(f"Erreur génération profil système au démarrage : {e}")
        return False
