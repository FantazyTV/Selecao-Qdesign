from openai import OpenAI
import dotenv
dotenv.load_dotenv()
import os

client = OpenAI(
  base_url=os.getenv("OPENAI_API_BASE"),
  api_key=os.getenv("OPENAI_API_KEY"),
)

completion = client.chat.completions.create(
  extra_body={},
  model=os.getenv("OPENAI_MODEL"),
  messages=[
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ]
)
print(completion.choices[0].message.content)