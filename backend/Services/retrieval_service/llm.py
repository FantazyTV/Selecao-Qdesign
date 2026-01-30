from openai import OpenAI
import dotenv
dotenv.load_dotenv()
import os

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENAI_API_KEY")
)

completion = client.chat.completions.create(

  extra_body={},
  model="google/gemma-3-27b-it:free",
  messages=[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What is the meaning of life"
        }
      ]
    }
  ]
)
print(completion.choices[0].message.content)