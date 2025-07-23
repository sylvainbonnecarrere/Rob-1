import requests
import json
import logging
from typing import Dict, Any, Optional, Tuple
import os

# Importation conditionnelle des clients spécifiques aux fournisseurs d'API
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logging.warning("Le package 'google-generativeai' n'est pas installé. Utilisation de requests comme fallback pour l'API Gemini.")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("Le package 'openai' n'est pas installé. Utilisation de requests comme fallback pour l'API OpenAI.")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logging.warning("Le package 'anthropic' n'est pas installé. Utilisation de requests comme fallback pour l'API Claude.")

def envoyer_requete_api(question: str, profil: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Envoie une requête à l'API configurée dans le profil en utilisant les SDK natifs quand disponibles
    ou fallback sur requests.
    
    Args:
        question: La question/prompt à envoyer à l'API
        profil: Le profil contenant la configuration de l'API
    
    Returns:
        Tuple contenant (succès, résultat)
        - succès: booléen indiquant si la requête a réussi
        - résultat: dictionnaire contenant soit la réponse de l'API, soit les détails de l'erreur
    """
    try:
        # Préparation des données selon le profil
        api_key = profil.get('api_key', '')
        replace_content = profil.get('replace_content', '')
        model = profil.get('model', 'gemini-2.0-flash')  # Valeur par défaut si non spécifié
        role = profil.get('role', '').strip() or "pédagogue"
        behavior = profil.get('behavior', '').strip() or "Précis, synthétique, court avec un résumé en bullet point."
        
        # Log pour le débogage
        logging.debug(f"Envoi d'une requête à {replace_content}")
        
        # Vérification des informations essentielles
        if not api_key:
            return False, {"erreur": "Clé API manquante dans le profil"}
            
        # Formatage du prompt avec le rôle et le comportement
        if "gemini" in replace_content.lower() or "google" in replace_content.lower():
            # Pour Gemini, nous utilisons la structure système pour le rôle et le comportement
            system_instruction = f"En tant que {role}, à la fois expert, pédagogue et synthétique, nous attendons de toi le comportement suivant : {behavior}."
            prompt_user = question
        else:
            # Pour les autres APIs, conservons le format original
            system_instruction = ""
            prompt_user = f"En tant que {role}, à la fois expert, pédagogue et synthétique, nous attendons de toi le comportement suivant : {behavior}. Ma question est la suivante : {question}"
        
        # Détecter le type d'API et utiliser le SDK approprié si disponible
        
        # --- GEMINI ---
        if ("gemini" in replace_content.lower() or "google" in replace_content.lower()) and GENAI_AVAILABLE:
            try:
                # Utiliser le SDK Google Generative AI
                client = genai.Client(api_key=api_key)
                
                # Extraire le nom du modèle depuis l'URL si possible
                model_name = "gemini-2.0-flash"  # Modèle par défaut
                if "models/" in replace_content:
                    model_parts = replace_content.split("models/")[1].split(":")
                    if len(model_parts) > 0:
                        model_name = model_parts[0]
                
                # Enregistrer la requête dans le fichier de logs pour débogage
                with open("debug_api.log", "a", encoding="utf-8") as log_file:
                    log_file.write(f"\n--- Requête envoyée à l'API Gemini via SDK ---\n")
                    log_file.write(f"Modèle: {model_name}\n")
                    log_file.write(f"System: {system_instruction}\n")
                    log_file.write(f"Prompt: {prompt_user}\n")
                
                # Envoi de la requête via le SDK
                model = client.get_model(model_name)
                generation_config = {
                    "temperature": 0.7,
                    "top_p": 1,
                    "top_k": 1,
                    "max_output_tokens": 2048,
                }
                
                response = model.generate_content(
                    [system_instruction, prompt_user],
                    generation_config=generation_config
                )
                
                # Transformer la réponse en format standard 
                reponse_standard = {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {"text": response.text}
                                ]
                            }
                        }
                    ]
                }
                
                # Enregistrer la réponse dans le fichier de logs
                with open("debug_api.log", "a", encoding="utf-8") as log_file:
                    log_file.write(f"--- Réponse reçue via SDK Gemini ---\n")
                    log_file.write(f"Texte: {response.text}\n")
                
                return True, reponse_standard
                
            except Exception as e:
                logging.error(f"Erreur avec le SDK Gemini, fallback sur requests: {str(e)}")
                # Continuer avec l'approche requests comme fallback
        
        # --- OPENAI ---
        elif "openai" in replace_content.lower() and OPENAI_AVAILABLE:
            try:
                # Utiliser le SDK OpenAI
                client = openai.Client(api_key=api_key)
                
                # Enregistrer la requête dans le fichier de logs
                with open("debug_api.log", "a", encoding="utf-8") as log_file:
                    log_file.write(f"\n--- Requête envoyée à l'API OpenAI via SDK ---\n")
                    log_file.write(f"Modèle: {model}\n")
                    log_file.write(f"Prompt: {prompt_user}\n")
                
                # Envoi de la requête via le SDK
                response = client.chat.completions.create(
                    model=model or "gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt_user}],
                    temperature=0.7,
                )
                
                # Transformer la réponse en format standard
                reponse_standard = {
                    "choices": [
                        {
                            "message": {
                                "content": response.choices[0].message.content
                            }
                        }
                    ]
                }
                
                # Enregistrer la réponse dans le fichier de logs
                with open("debug_api.log", "a", encoding="utf-8") as log_file:
                    log_file.write(f"--- Réponse reçue via SDK OpenAI ---\n")
                    log_file.write(f"Texte: {response.choices[0].message.content}\n")
                
                return True, reponse_standard
                
            except Exception as e:
                logging.error(f"Erreur avec le SDK OpenAI, fallback sur requests: {str(e)}")
                # Continuer avec l'approche requests comme fallback
        
        # --- CLAUDE ---
        elif ("anthropic" in replace_content.lower() or "claude" in replace_content.lower()) and ANTHROPIC_AVAILABLE:
            try:
                # Utiliser le SDK Anthropic
                client = anthropic.Client(api_key=api_key)
                
                # Enregistrer la requête dans le fichier de logs
                with open("debug_api.log", "a", encoding="utf-8") as log_file:
                    log_file.write(f"\n--- Requête envoyée à l'API Claude via SDK ---\n")
                    log_file.write(f"Modèle: {model}\n")
                    log_file.write(f"Prompt: {prompt_user}\n")
                
                # Envoi de la requête via le SDK
                response = client.messages.create(
                    model=model or "claude-3-sonnet-20240229",
                    messages=[{"role": "user", "content": prompt_user}],
                    temperature=0.7,
                    max_tokens=1000,
                )
                
                # Transformer la réponse en format standard
                reponse_standard = {
                    "content": [
                        {"text": response.content[0].text}
                    ]
                }
                
                # Enregistrer la réponse dans le fichier de logs
                with open("debug_api.log", "a", encoding="utf-8") as log_file:
                    log_file.write(f"--- Réponse reçue via SDK Claude ---\n")
                    log_file.write(f"Texte: {response.content[0].text}\n")
                
                return True, reponse_standard
                
            except Exception as e:
                logging.error(f"Erreur avec le SDK Claude, fallback sur requests: {str(e)}")
                # Continuer avec l'approche requests comme fallback
                
        # --- FALLBACK SUR REQUESTS POUR TOUS LES CAS ---
        
        # Déterminer le type d'API et formater la requête en conséquence
        headers = {"Content-Type": "application/json"}
        
        # Structure de la requête selon le fournisseur d'API
        if "gemini" in replace_content.lower() or "google" in replace_content.lower():
            # Structure pour Gemini API avec system prompt et user prompt séparés
            data = {
                "contents": [
                    {"role": "user", "parts": [{"text": system_instruction}]},
                    {"role": "user", "parts": [{"text": prompt_user}]}
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 1,
                    "topK": 1,
                    "maxOutputTokens": 2048,
                }
            }
            
        elif "openai" in replace_content.lower():
            # Format pour OpenAI API
            if not replace_content:
                replace_content = "https://api.openai.com/v1/chat/completions"
                
            headers["Authorization"] = f"Bearer {api_key}"
            data = {
                "model": model or "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt_user}],
                "temperature": 0.7
            }
            
        elif "anthropic" in replace_content.lower() or "claude" in replace_content.lower():
            # Format pour Claude/Anthropic API
            if not api_url:
                api_url = "https://api.anthropic.com/v1/messages"
                
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"  # Utilisez la dernière version disponible
            data = {
                "model": model or "claude-3-sonnet-20240229",
                "messages": [{"role": "user", "content": prompt_user}],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
        else:
            # Structure par défaut pour les autres APIs (comme OpenAI)
            data = {
                "model": "gpt-4-turbo",
                "messages": [
                    {"role": "user", "content": prompt_user}
                ],
                "temperature": 0.7,
                "max_tokens": 2048
            }
        
        # Enregistrer la requête dans le fichier de logs pour débogage
        with open("debug_api.log", "a", encoding="utf-8") as log_file:
            log_file.write(f"\n--- Requête envoyée à {api_url} (fallback requests) ---\n")
            log_file.write(f"Headers: {json.dumps(headers, ensure_ascii=False)}\n")
            log_file.write(f"Data: {json.dumps(data, ensure_ascii=False)}\n")
        
        # Envoi de la requête avec timeout pour éviter de bloquer l'interface
        response = requests.post(api_url, json=data, headers=headers, timeout=30)
        
        # Analyser la réponse
        if response.status_code == 200:
            reponse_json = response.json()
            
            # Enregistrer la réponse dans le fichier de logs
            with open("debug_api.log", "a", encoding="utf-8") as log_file:
                log_file.write(f"--- Réponse reçue (Code {response.status_code}) ---\n")
                log_file.write(f"{json.dumps(reponse_json, ensure_ascii=False, indent=2)}\n")
            
            return True, reponse_json
        else:
            erreur = f"Erreur HTTP {response.status_code}: {response.text}"
            
            # Enregistrer l'erreur dans le fichier de logs
            with open("debug_api.log", "a", encoding="utf-8") as log_file:
                log_file.write(f"--- Erreur (Code {response.status_code}) ---\n")
                log_file.write(f"{response.text}\n")
            
            return False, {"erreur": erreur}
            
    except requests.exceptions.Timeout:
        erreur = "La requête a expiré (timeout). Le serveur met trop de temps à répondre."
        logging.error(erreur)
        return False, {"erreur": erreur}
    except requests.exceptions.ConnectionError:
        erreur = "Erreur de connexion. Vérifiez votre connexion internet ou l'URL de l'API."
        logging.error(erreur)
        return False, {"erreur": erreur}
    except json.JSONDecodeError:
        erreur = "La réponse du serveur n'est pas au format JSON valide."
        logging.error(erreur)
        return False, {"erreur": erreur}
    except Exception as e:
        erreur = f"Erreur inattendue lors de l'envoi de la requête: {str(e)}"
        logging.error(erreur)
        return False, {"erreur": erreur}

def extraire_texte_reponse(reponse_json: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Extrait le texte de réponse du JSON retourné par l'API en tenant compte des différents formats.
    
    Args:
        reponse_json: Le JSON de réponse de l'API
        
    Returns:
        Tuple contenant (succès, texte)
        - succès: booléen indiquant si l'extraction a réussi
        - texte: le texte extrait ou un message d'erreur
    """
    try:
        # Si la réponse contient une erreur explicite
        if "erreur" in reponse_json:
            return False, reponse_json["erreur"]
            
        # Pour l'API Gemini
        if "candidates" in reponse_json:
            try:
                texte = reponse_json["candidates"][0]["content"]["parts"][0]["text"]
                return True, texte
            except (KeyError, IndexError) as e:
                logging.error(f"Structure de réponse Gemini inattendue: {e}")
        
        # Pour l'API OpenAI
        elif "choices" in reponse_json:
            try:
                texte = reponse_json["choices"][0]["message"]["content"]
                return True, texte
            except (KeyError, IndexError) as e:
                logging.error(f"Structure de réponse OpenAI inattendue: {e}")
                
        # Pour l'API Claude/Anthropic
        elif "content" in reponse_json:
            try:
                texte = reponse_json["content"][0]["text"]
                return True, texte
            except (KeyError, IndexError) as e:
                logging.error(f"Structure de réponse Claude inattendue: {e}")
                
        # Si le format n'est pas reconnu, retourner le JSON brut
        return False, f"Format de réponse non reconnu: {json.dumps(reponse_json, ensure_ascii=False)}"
        
    except Exception as e:
        erreur = f"Erreur lors de l'extraction du texte: {str(e)}"
        logging.error(erreur)
        return False, erreur