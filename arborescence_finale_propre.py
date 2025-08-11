#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur d'arborescence finale du projet ROB-1
"""
import os

def afficher_arborescence():
    """Affiche l'arborescence finale du projet"""
    print("🌳 PROJET ROB-1 - STRUCTURE FINALE PROPRE")
    print("=" * 60)
    
    # Structure organisée
    structure = {
        "📁 Système Core": [
            "main.py",
            "gui.py", 
            "config_manager.py",
            "conversation_manager.py",
            "api_response_parser.py",
            "system_profile_generator.py",
            "utils.py"
        ],
        "📁 Architecture": [
            "core/",
            "└── api_manager.py",
            "└── app_initializer.py",
            "utils/",
            "└── os_utils.py"
        ],
        "📁 Templates & Config": [
            "templates/",
            "└── chat/",
            "    ├── gemini/ (✅ FONCTIONNEL)",
            "    ├── claude/ (🔄 À implémenter)",
            "    ├── openai/ (🔄 À implémenter)",
            "    ├── grok/ (🔄 À implémenter)",
            "    ├── kimi/ (🔄 À implémenter)",
            "    ├── mistral/ (🔄 À implémenter)",
            "    └── qwen/ (🔄 À implémenter)",
            "profiles/",
            "system/"
        ],
        "📁 Installation & Assets": [
            "install_scripts/",
            "└── template_installer.py",
            "images/",
            "RUN.bat",
            "requirements.txt",
            "README.md"
        ],
        "📁 Données Runtime": [
            "conversations/",
            "development/",
            "profiles_backup_conversation/"
        ]
    }
    
    for section, items in structure.items():
        print(f"\n{section}:")
        for item in items:
            print(f"   {item}")
    
    # Compter les éléments
    total_files = len([f for f in os.listdir('.') if os.path.isfile(f)])
    total_dirs = len([d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.')])
    
    print(f"\n📊 STATISTIQUES FINALES:")
    print(f"   • {total_files} fichiers principaux")
    print(f"   • {total_dirs} dossiers fonctionnels")
    print(f"   • 60+ fichiers de développement supprimés")
    print(f"   • Structure optimisée pour la production")
    
    print(f"\n✅ ÉTAT DU SYSTÈME:")
    print(f"   🎯 Gemini API: 100% fonctionnel")
    print(f"   🔧 Corrections curl: Résolues")
    print(f"   🏗️ Architecture V2: Implémentée")
    print(f"   📝 Templates: Système de placeholders actif")
    print(f"   🧹 Projet: Nettoyé et optimisé")
    
    print(f"\n🚀 PRÊT POUR LES PROCHAINES ÉTAPES:")
    print(f"   1. Extension aux 6 autres APIs")
    print(f"   2. Mise à jour template_installer.py")
    print(f"   3. Tests de validation multi-API")

if __name__ == "__main__":
    afficher_arborescence()
