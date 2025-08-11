#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Restauration de gui.py - fonction corriger_commande_curl
Remplace la fonction cassée par une version simple
"""

import sys
import os

# Lire le fichier gui.py
gui_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gui.py")

with open(gui_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Trouver le début et la fin de la fonction corriger_commande_curl
start_marker = "def corriger_commande_curl(commande):"
end_marker = "\ndef executer_commande_curl"  # Prochaine fonction

start_pos = content.find(start_marker)
end_pos = content.find(end_marker, start_pos)

if start_pos == -1 or end_pos == -1:
    print("❌ Impossible de localiser la fonction corriger_commande_curl")
    sys.exit(1)

# Nouvelle fonction simple
new_function = """def corriger_commande_curl(commande):
    \"\"\"Fonction temporaire simplifiée\"\"\"
    import re
    if not commande:
        return commande
    print("[DEBUG] Correction curl simplifiée")
    corrected = commande.replace('\\\\\\n', ' ').replace('\\n', ' ')
    corrected = re.sub(r'\\s+', ' ', corrected).strip()
    return corrected

"""

# Remplacer la fonction
new_content = content[:start_pos] + new_function + content[end_pos:]

# Sauvegarder
with open(gui_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Fonction corriger_commande_curl restaurée avec version simplifiée")
print("✅ Fichier gui.py réparé")
