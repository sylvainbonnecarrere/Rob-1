from openai import OpenAI

client = OpenAI()

response = client.responses.create(
  model="{{LLM_MODEL}}",
  input="{{SYSTEM_PROMPT_ROLE}}, {{SYSTEM_PROMPT_BEHAVIOR}}. {{USER_PROMPT}} "
)

print(response)