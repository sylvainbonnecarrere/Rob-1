#!/usr/bin/env python3
"""
Module de gestion des fichiers payload JSON pour curl
Phase 1 - Implémentation curl sécurisé via fichier JSON
"""

import os
import json
import time
import tempfile
from pathlib import Path

class PayloadManager:
    """Gestionnaire de fichiers payload JSON temporaires par profil API"""
    
    def __init__(self, workspace_dir=None, api_profile=None):
        """Initialize PayloadManager avec dossier de travail et profil API"""
        if workspace_dir is None:
            workspace_dir = os.getcwd()
        
        if api_profile is None:
            api_profile = "default"
        
        # Structure: conversation_api/{profil}/temp/
        self.temp_dir = Path(workspace_dir) / "conversation_api" / api_profile.lower() / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[PayloadManager] Dossier temporaire pour {api_profile}: {self.temp_dir}")
    
    def create_payload_file(self, payload_data, prefix="payload"):
        """
        Crée un fichier JSON temporaire avec le payload
        
        Args:
            payload_data (dict): Données à sérialiser en JSON
            prefix (str): Préfixe pour le nom de fichier
            
        Returns:
            str: Chemin vers le fichier créé
        """
        # Générer nom unique avec timestamp
        timestamp = int(time.time() * 1000)  # millisecondes pour unicité
        filename = f"{prefix}_{timestamp}.json"
        filepath = self.temp_dir / filename
        
        try:
            # Sérialiser en JSON avec formatage propre
            json_content = json.dumps(payload_data, ensure_ascii=False, indent=2)
            
            # Écrire dans le fichier
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_content)
            
            print(f"[PayloadManager] Fichier créé: {filepath} ({len(json_content)} chars)")
            return str(filepath)
            
        except Exception as e:
            print(f"[PayloadManager] ERREUR création fichier {filepath}: {e}")
            raise
    
    def cleanup_payload_file(self, filepath):
        """
        Supprime le fichier payload temporaire
        
        Args:
            filepath (str): Chemin vers le fichier à supprimer
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"[PayloadManager] Fichier supprimé: {filepath}")
            else:
                print(f"[PayloadManager] Fichier déjà absent: {filepath}")
                
        except Exception as e:
            print(f"[PayloadManager] ERREUR suppression {filepath}: {e}")
    
    def cleanup_old_files(self, max_age_seconds=3600):
        """
        Nettoie les anciens fichiers payload (sécurité)
        
        Args:
            max_age_seconds (int): Âge maximum en secondes (défaut: 1h)
        """
        current_time = time.time()
        cleaned_count = 0
        
        try:
            for file_path in self.temp_dir.glob("payload_*.json"):
                file_age = current_time - file_path.stat().st_mtime
                
                if file_age > max_age_seconds:
                    file_path.unlink()
                    cleaned_count += 1
                    print(f"[PayloadManager] Ancien fichier supprimé: {file_path}")
            
            if cleaned_count > 0:
                print(f"[PayloadManager] Nettoyage: {cleaned_count} anciens fichiers supprimés")
                
        except Exception as e:
            print(f"[PayloadManager] ERREUR nettoyage: {e}")

def extract_json_from_curl(curl_command):
    """
    Extrait le payload JSON d'une commande curl existante
    Version corrigée pour gestion des guillemets échappés dans le JSON
    
    Args:
        curl_command (str): Commande curl complète
        
    Returns:
        tuple: (base_command, json_data) ou (curl_command, None) si échec
    """
    import re
    
    try:
        # Chercher le début de -d et le type de guillemet
        d_start_match = re.search(r"-d\s+(['\"])", curl_command)
        
        if d_start_match:
            quote_char = d_start_match.group(1)
            start_pos = d_start_match.end() - 1  # Position du guillemet ouvrant
            
            print(f"[PayloadManager] Recherche JSON entre guillemets '{quote_char}'")
            
            # NOUVELLE APPROCHE: Chercher depuis la fin
            # Le guillemet de fermeture est le dernier guillemet de ce type dans la commande
            json_start = start_pos + 1
            json_end = -1
            
            # Chercher le dernier guillemet correspondant
            for i in range(len(curl_command) - 1, start_pos, -1):
                if curl_command[i] == quote_char:
                    json_end = i
                    break
            
            if json_end == -1:
                print(f"[PayloadManager] Pas de guillemet de fermeture trouvé")
                return curl_command, None
            
            # Extraire le JSON complet
            json_content = curl_command[json_start:json_end]
            
            print(f"[PayloadManager] JSON extrait: de position {json_start} à {json_end} ({len(json_content)} chars)")
            
            # Déséchapper selon le type de guillemets
            if quote_char == '"':
                # Déséchapper les caractères JSON échappés pour double-quotes
                json_content = json_content.replace('\\"', '"')
                json_content = json_content.replace('\\\\', '\\')
                json_content = json_content.replace('\\n', '\n')
                json_content = json_content.replace('\\t', '\t')
                json_content = json_content.replace('\\r', '\r')
            
            print(f"[PayloadManager] JSON après désérialisation: {len(json_content)} chars")
            
            # Parser le JSON avec gestion robuste des erreurs
            try:
                json_data = json.loads(json_content)
            except json.JSONDecodeError as json_err:
                print(f"[PayloadManager] Erreur JSON parsing: {json_err}")
                print(f"[PayloadManager] Contenu problématique: {repr(json_content[:200])}")
                
                # Tentative de nettoyage des caractères de contrôle
                import re
                json_content_clean = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_content)
                json_data = json.loads(json_content_clean)
                print(f"[PayloadManager] JSON nettoyé et parsé avec succès")
            
            # Extraire la commande de base (sans -d)
            base_command = curl_command[:d_start_match.start()].strip()
            
            print(f"[PayloadManager] JSON extrait avec succès")
            return base_command, json_data
            
    except Exception as e:
        print(f"[PayloadManager] ERREUR extraction JSON: {e}")
    
    return curl_command, None

# Instance globale pour faciliter l'utilisation
_payload_managers = {}

def get_payload_manager(api_profile="default"):
    """Retourne l'instance PayloadManager pour le profil API spécifié"""
    global _payload_managers
    if api_profile not in _payload_managers:
        _payload_managers[api_profile] = PayloadManager(api_profile=api_profile)
    return _payload_managers[api_profile]

def create_payload_file(payload_data, api_profile="default", prefix="payload"):
    """Fonction utilitaire pour créer un fichier payload"""
    return get_payload_manager(api_profile).create_payload_file(payload_data, prefix)

def cleanup_payload_file(filepath, api_profile="default"):
    """Fonction utilitaire pour nettoyer un fichier payload"""
    get_payload_manager(api_profile).cleanup_payload_file(filepath)

if __name__ == "__main__":
    # Tests unitaires du module
    print("=== TESTS PayloadManager ===")
    
    # Test 1: Création et suppression fichier pour Gemini
    pm = PayloadManager(api_profile="gemini")
    
    test_payload = {
        "system_instruction": {
            "parts": [
                {"text": "Tu es un assistant IA utile avec des réponses courtes."}
            ]
        },
        "contents": [
            {
                "parts": [
                    {"text": "Salut, comment ça va ? Test avec accents: é à ù ç"}
                ]
            }
        ]
    }
    
    filepath = pm.create_payload_file(test_payload, "test")
    print(f"Fichier créé: {filepath}")
    
    # Vérifier contenu
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"Contenu ({len(content)} chars):")
        print(content[:200] + "..." if len(content) > 200 else content)
    
    # Nettoyer
    pm.cleanup_payload_file(filepath)
    
    # Test 2: Plusieurs profils API
    print(f"\nTest multi-profils:")
    for api in ["claude", "openai", "kimi"]:
        pm_api = PayloadManager(api_profile=api)
        test_file = pm_api.create_payload_file({"test": f"payload for {api}"}, f"test_{api}")
        print(f"Créé pour {api}: {test_file}")
        pm_api.cleanup_payload_file(test_file)
    
    # Test 3: Extraction JSON depuis curl
    test_curl = 'curl "https://api.example.com" -H "Content-Type: application/json" -d "{\\"test\\": \\"value with \\\\\\"quotes\\\\\\"\\", \\"accents\\": \\"café\\"}"'
    base_cmd, json_data = extract_json_from_curl(test_curl)
    
    print(f"\nTest extraction:")
    print(f"Base command: {base_cmd}")
    print(f"JSON data: {json_data}")
    
    print("\n=== TESTS TERMINÉS ===")
