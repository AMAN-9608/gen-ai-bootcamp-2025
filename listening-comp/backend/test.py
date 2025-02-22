from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# response = client.models.generate_content(
#     # model="gemini-2.0-flash",\
#     model="gemini-2.0-flash-lite-preview-02-05",
#     contents="""what is the translation of 'this car is fast' to Japanese?""",
#     config=types.GenerateContentConfig(
#         system_instruction="You are a Japanese tutor. The user will ask your help with translating english to japanese, but do NOT provide them with the direct answer. Only provide hints!!!",
#     )
# )

# print(response.text)

response = client.models.embed_content(
            model="text-embedding-004",
            contents="this car is fast",
            )

print(response.embeddings[0].values)