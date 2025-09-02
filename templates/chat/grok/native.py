# In your terminal, first run:
# pip install xai-sdk

import os

from xai_sdk import Client
from xai_sdk.chat import user, system

client = Client(
    api_key=os.getenv("XAI_API_KEY"),
    timeout=3600,  # Override default timeout with longer timeout for reasoning models
)

chat = client.chat.create(model="grok-4")
chat.append(system("You are Grok, a highly intelligent and helpful AI assistant."))
chat.append(user("What is the best French Cheese?"))

response = chat.sample()
print(response.content)