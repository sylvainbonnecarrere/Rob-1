from openai import OpenAI

client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")  # La clé est souvent "lm-studio" par défaut, ou vide si non configurée

response = client.chat.completions.create(
    model="google/gemma-3-1b",  # Remplacez par le nom exact de votre modèle chargé
    messages=[
        {"role": "system", "content": "Tu es un expert,  architecte et développeur."},
        {"role": "user", "content": "Écris un script simple pour calculer la factorielle d'un nombre."}
    ],
    temperature=0.7,
)

print(response.choices[0].message.content)