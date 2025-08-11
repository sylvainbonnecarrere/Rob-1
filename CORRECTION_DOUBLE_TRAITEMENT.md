🔧 CORRECTION CRITIQUE - DOUBLE TRAITEMENT PROMPT
=======================================================

❌ PROBLÈME IDENTIFIÉ:
----------------------
- Erreur: "curl: (6) Could not resolve host: application"
- Double traitement du prompt causant des conflits JSON
- Template moderne + ancienne fonction generer_prompt() = chaos

🔍 ANALYSE TECHNIQUE:
--------------------
1. **Template curl_basic.txt** utilise:
   - {{SYSTEM_PROMPT_ROLE}} → "alien rigolo" 
   - {{SYSTEM_PROMPT_BEHAVIOR}} → "réponses courtes et de moins de 5 phrases"
   - {{USER_PROMPT}} → Question utilisateur

2. **generer_prompt()** ajoutait ENCORE:
   - "Tu es alien rigolo. Tu dois être réponses courtes et de moins de 5 phrases.. Question: [user input]"

3. **Résultat = Double instruction**:
   ```json
   {
     "system_instruction": {"text": "alien rigolo réponses courtes..."},
     "contents": [{"text": "Tu es alien rigolo. Tu dois être... Question: Salut"}]
   }
   ```

🔧 SOLUTION APPLIQUÉE:
----------------------
✅ **SUPPRIMÉ:** `prompt_concatene = generer_prompt(question_finale, profil)`
✅ **REMPLACÉ PAR:** `requete_curl = preparer_requete_curl(question_finale)`
✅ **LOGIQUE:** Le système de templates moderne gère déjà rôle/comportement via placeholders

📍 **CHANGEMENT LIGNE 783:**
```python
# ANCIEN (causait double traitement):
prompt_concatene = generer_prompt(question_finale, profil)
requete_curl = preparer_requete_curl(prompt_concatene)

# NOUVEAU (template system pur):
requete_curl = preparer_requete_curl(question_finale)
```

✅ RÉSULTAT ATTENDU:
-------------------
- ✅ Fin du double traitement des instructions système
- ✅ Template JSON propre et valide
- ✅ Headers curl correctement formés
- ✅ Pas d'erreur "Could not resolve host"
- ✅ API Gemini fonctionne normalement

⚠️ NOTE IMPORTANTE:
------------------
La fonction generer_prompt() était pour l'ANCIEN système sans templates.
Le NOUVEAU système utilise les templates avec placeholders automatiques.
Mélanger les deux = dysfonctionnement garanti.

🎯 STATUT: CORRECTION APPLIQUÉE - TEST IMMÉDIAT RECOMMANDÉ
=======================================================
