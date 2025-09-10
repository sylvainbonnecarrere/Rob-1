import os
from mistralai import Mistral


model = "{{LLM_MODEL}}"

client = Mistral(api_key="{{API_KEY}}")

chat_response = client.chat.complete(
    model= model,
    messages = [
        {
            "role": "user",
            "content": "{{SYSTEM_PROMPT_ROLE}}, {{SYSTEM_PROMPT_BEHAVIOR}}. {{USER_PROMPT}}",
        }
    ]
)
print(chat_response.choices[0].message.content)