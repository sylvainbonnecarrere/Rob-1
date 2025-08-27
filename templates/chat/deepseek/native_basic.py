import requests
import json

response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": "Bearer <OPENROUTER_API_KEY>",
    "Content-Type": "application/json",  },
  data=json.dumps({
    "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",
    "messages": [
      {
          "role": "system",
          "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "What is the meaning of life?"
      }
    ],
    
  })
)