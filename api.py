import requests
import pandas as pd
import json

def envoyer_requete(api_key, prompt):
    """Envoie une requête à l'API Gemini avec la clé API et le prompt fourni."""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            # Assure que le texte est bien encodé en UTF-8
            response.encoding = 'utf-8'
            return response.json()
        else:
            return {"erreur": f"Erreur HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"erreur": f"Erreur inattendue : {e}"}

def convertir_en_tableau(data):
    """
    Convertit une structure de données complexe en un DataFrame pandas.
    """
    try:
        if isinstance(data, str):
            # Si l'entrée est une chaîne JSON, on la parse
            data = json.loads(data)

        if isinstance(data, list):
            # Si l'entrée est une liste de dictionnaires
            return pd.DataFrame(data)

        if isinstance(data, dict):
            # Si l'entrée est un dictionnaire
            return pd.DataFrame([data])

        return "Type de données non pris en charge pour la conversion en tableau."
    except Exception as e:
        return f"Erreur lors de la conversion en tableau : {e}"

def extraire_elements_text(data, chemin=""): 
    """
    Recherche récursive des éléments avec la clé 'text' dans une structure de données.
    """
    resultats = []

    if isinstance(data, dict):
        for cle, valeur in data.items():
            nouveau_chemin = f"{chemin}.{cle}" if chemin else cle
            if cle == "text":
                resultats.append((nouveau_chemin, valeur))
            else:
                resultats.extend(extraire_elements_text(valeur, nouveau_chemin))

    elif isinstance(data, list):
        for index, element in enumerate(data):
            nouveau_chemin = f"{chemin}[{index}]"
            resultats.extend(extraire_elements_text(element, nouveau_chemin))

    return resultats

# Exemple d'utilisation
data_complexe = {
    "reponse_api": {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "Ceci est le texte de la réponse de l'IA."
                        },
                        {"other_info": 123}
                    ],
                    "role": "model"
                },
                "finishReason": "STOP"
            }
        ],
        "usageMetadata": {"tokens": 45}
    },
    "autres_donnees": [
        {"cle": "valeur1", "info": {"text": "Autre texte pertinent"}},
        {"cle": "valeur2"}
    ]
}

# Conversion en tableau
dataframe = convertir_en_tableau(data_complexe)
print("Tableau converti :")
print(dataframe)

# Extraction des éléments 'text'
textes = extraire_elements_text(data_complexe)
print("\nÉléments 'text' extraits :")
for chemin, texte in textes:
    print(f"{chemin} : {texte}")