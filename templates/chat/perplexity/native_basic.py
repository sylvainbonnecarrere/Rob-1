import requests

url = "https://api.perplexity.ai/chat/completions"

payload = {
    "model": "{{LLM_MODEL}}",
    "messages": [
        {
            "role": "system",
            "content": "{{SYSTEM_PROMPT_ROLE}}, {{SYSTEM_PROMPT_BEHAVIOR}}"
        },
        {
            "role": "user",
            "content": "{{USER_PROMPT}}"
        }
    ]
}
headers = {
    "Authorization": "Bearer {{API_KEY}}",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())