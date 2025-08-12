#!/usr/bin/env python3
"""
🧹 SCRIPT DE NETTOYAGE POST-PHASE 2
=====================================

Ce script nettoie le projet après validation de la Phase 2:
- Supprime tous les fichiers de debug temporaires
- Vérifie qu'aucune clé API n'est exposée dans les fichiers versionnés
- Prépare le projet pour commit

Auteur: Phase 2 Response Parser - Validation Architecte ✅
Date: 12 août 2025
"""

import os
import glob
import re
import sys

def cleanup_debug_files():
    """Supprime tous les fichiers de debug sauf ce script"""
    print("🧹 NETTOYAGE DOSSIER DEBUG")
    print("=" * 50)
    
    debug_dir = os.path.dirname(os.path.abspath(__file__))
    current_file = os.path.basename(__file__)
    
    files_to_remove = []
    
    # Lister tous les fichiers dans debug/
    for file in os.listdir(debug_dir):
        if file != current_file and os.path.isfile(os.path.join(debug_dir, file)):
            files_to_remove.append(file)
    
    if not files_to_remove:
        print("✅ Aucun fichier à supprimer dans debug/")
        return
    
    print(f"📋 Fichiers à supprimer ({len(files_to_remove)}):")
    for file in files_to_remove:
        print(f"   - {file}")
    
    print("\n🗑️ Suppression en cours...")
    removed_count = 0
    
    for file in files_to_remove:
        try:
            file_path = os.path.join(debug_dir, file)
            os.remove(file_path)
            print(f"   ✅ {file}")
            removed_count += 1
        except Exception as e:
            print(f"   ❌ {file}: {e}")
    
    print(f"\n🎉 Nettoyage terminé: {removed_count}/{len(files_to_remove)} fichiers supprimés")

def check_api_keys():
    """Vérifie qu'aucune clé API n'est exposée dans les fichiers versionnés"""
    print("\n🔐 VÉRIFICATION CLÉS API")
    print("=" * 50)
    
    # Patterns de clés API courantes
    api_patterns = [
        r'AIzaSy[0-9A-Za-z_-]{33}',  # Google/Gemini API keys
        r'sk-[0-9A-Za-z]{48}',       # OpenAI API keys
        r'Bearer [A-Za-z0-9._-]+',   # Bearer tokens
        r'api[_-]?key["\s]*[:=]["\s]*[A-Za-z0-9._-]{20,}',  # Generic API keys
        r'token["\s]*[:=]["\s]*[A-Za-z0-9._-]{20,}',        # Generic tokens
    ]
    
    # Fichiers à vérifier (excluant les fichiers ignorés par git)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Extensions de fichiers à vérifier
    extensions = ['.py', '.json', '.md', '.txt', '.bat', '.ps1', '.js', '.ts']
    
    # Dossiers à ignorer
    ignore_dirs = {'__pycache__', '.git', 'node_modules', 'venv', 'env'}
    
    # Fichiers spécifiques à ignorer
    ignore_files = {'api_key.txt'}  # Ce fichier devrait être dans .gitignore
    
    # Patterns à ignorer (fichiers légitimes avec placeholders)
    ignore_patterns = ['profiles/*.json']  # Les .json sont ignorés par git, seuls les .template sont versionnés
    
    potential_leaks = []
    
    def scan_file(file_path):
        """Scanne un fichier pour des clés API"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            for line_num, line in enumerate(content.split('\n'), 1):
                for pattern in api_patterns:
                    matches = re.findall(pattern, line, re.IGNORECASE)
                    if matches:
                        rel_path = os.path.relpath(file_path, project_root)
                        for match in matches:
                            # Ignorer les faux positifs
                            if (match.startswith('YOUR_') and match.endswith('_HERE')) or \
                               'Bearer [A-Za-z0-9._-]+' in match or \
                               'replace_apikey' in line.lower() or \
                               'r\'Bearer' in line or \
                               'YOUR_' in match or \
                               match.endswith('_HERE'):
                                continue
                                
                            # Masquer partiellement la clé trouvée
                            masked = match[:8] + "..." + match[-4:] if len(match) > 12 else "***"
                            potential_leaks.append({
                                'file': rel_path,
                                'line': line_num,
                                'match': masked,
                                'full_line': line.strip()[:100]
                            })
        except Exception as e:
            print(f"   ⚠️ Erreur lecture {file_path}: {e}")
    
    print("🔍 Scan des fichiers du projet...")
    scanned_files = 0
    
    for root, dirs, files in os.walk(project_root):
        # Filtrer les dossiers à ignorer
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            if file in ignore_files:
                continue
                
            file_path = os.path.join(root, file)
            _, ext = os.path.splitext(file)
            
            # Ignorer les fichiers .json dans profiles/ (ils sont dans .gitignore)
            rel_path = os.path.relpath(file_path, project_root)
            if rel_path.startswith('profiles' + os.sep) and ext == '.json':
                continue
                
            if ext.lower() in extensions:
                scan_file(file_path)
                scanned_files += 1
    
    print(f"📊 {scanned_files} fichiers scannés")
    
    if potential_leaks:
        print(f"\n⚠️ ATTENTION: {len(potential_leaks)} potentielles fuites détectées:")
        print("-" * 60)
        
        for leak in potential_leaks:
            print(f"📁 {leak['file']}:{leak['line']}")
            print(f"🔑 Clé trouvée: {leak['match']}")
            print(f"📝 Ligne: {leak['full_line']}")
            print("-" * 60)
        
        print("\n🚨 ACTIONS REQUISES:")
        print("1. Vérifier que api_key.txt est dans .gitignore")
        print("2. Vérifier que profiles/*.json sont dans .gitignore (seuls les .template doivent être versionnés)")
        print("3. Supprimer les clés des fichiers versionnés (.template, .py, .md, etc.)")
        print("4. Utiliser des variables d'environnement ou des fichiers de config non versionnés")
        
        return False
    else:
        print("✅ Aucune clé API détectée dans les fichiers versionnés")
        return True

def check_gitignore():
    """Vérifie que les fichiers sensibles sont dans .gitignore"""
    print("\n📋 VÉRIFICATION .GITIGNORE")
    print("=" * 50)
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gitignore_path = os.path.join(project_root, '.gitignore')
    
    required_patterns = [
        'api_key.txt',
        '*.log',
        '__pycache__/',
        '*.pyc',
        '.env',
        'conversation_api/*/temp/'
    ]
    
    if not os.path.exists(gitignore_path):
        print("⚠️ .gitignore n'existe pas")
        print("🔧 Création recommandée avec ces patterns:")
        for pattern in required_patterns:
            print(f"   {pattern}")
        return False
    
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        gitignore_content = f.read()
    
    missing_patterns = []
    for pattern in required_patterns:
        if pattern not in gitignore_content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print(f"⚠️ Patterns manquants dans .gitignore ({len(missing_patterns)}):")
        for pattern in missing_patterns:
            print(f"   - {pattern}")
        return False
    else:
        print("✅ .gitignore configuré correctement")
        return True

def main():
    """Fonction principale"""
    print("🚀 NETTOYAGE POST-PHASE 2")
    print("=" * 50)
    print("Phase 2 Response Parser - Validation Architecte ✅")
    print("Préparation pour commit de la Phase 2 complète")
    print()
    
    # Étape 1: Nettoyage des fichiers debug
    cleanup_debug_files()
    
    # Étape 2: Vérification des clés API
    api_clean = check_api_keys()
    
    # Étape 3: Vérification .gitignore
    gitignore_ok = check_gitignore()
    
    # Résumé final
    print("\n🎯 RÉSUMÉ NETTOYAGE")
    print("=" * 50)
    print(f"🧹 Fichiers debug: ✅ Nettoyés")
    print(f"🔐 Clés API: {'✅ Sécurisées' if api_clean else '⚠️ À vérifier'}")
    print(f"📋 .gitignore: {'✅ OK' if gitignore_ok else '⚠️ À configurer'}")
    
    if api_clean and gitignore_ok:
        print("\n🎉 PROJET PRÊT POUR COMMIT!")
        print("📝 Message de commit suggéré:")
        print("   'feat: Phase 2 Response Parser - Generic API response handling'")
        print("   - Système générique de parsing des réponses API")
        print("   - Support universel pour tous les providers")
        print("   - Historisation complexe avec résumés automatiques")
    else:
        print("\n⚠️ ACTIONS REQUISES AVANT COMMIT")
        if not api_clean:
            print("   - Sécuriser les clés API")
        if not gitignore_ok:
            print("   - Configurer .gitignore")

if __name__ == "__main__":
    main()
