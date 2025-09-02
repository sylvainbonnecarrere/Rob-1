from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="<OPENROUTER_API_KEY>",
)

completion = client.chat.completions.create(
  extra_headers={
    "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
    "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
  },
  extra_body={},
  model="qwen/qwen3-30b-a3b-instruct-2507",
  messages=[
    {
      "role": "user",
      "content": "What is the meaning of life?"
    },
        { 
      "role": 'assistant', 
      "content": "I'm not sure, but my best guess is" 
    }
  ]
)
print(completion.choices[0].message.content)