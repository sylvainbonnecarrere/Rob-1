from openai import OpenAI

client = OpenAI(base_url="http://localhost:1234/v1", api_key="{{API_KEY}}")  # La clé est souvent "lm-studio" par défaut, ou vide si non configurée

response = client.chat.completions.create(
    model="{{LLM_MODEL}}",  # Remplacez par le nom exact de votre modèle chargé
    messages=[
        {"role": "system", "content": "{{SYSTEM_PROMPT_ROLE}}, {{SYSTEM_PROMPT_BEHAVIOR}}"},
        {"role": "user", "content": "{{USER_PROMPT}}"}
    ],
    temperature=0.7,
)

print(response.choices[0].message.content)