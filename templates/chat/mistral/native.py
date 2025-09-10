import os
from mistralai import Mistral

model = "mistral-large-latest"

client = Mistral(api_key=api_key)

chat_response = client.chat.complete(
    model= model,
    messages = [
        {
            "role": "user",
            "content": "You are mouse, very smart.What is the best French cheese?",
        }
    ]
)
print(chat_response.choices[0].message.content)