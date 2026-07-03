import os
from dotenv import load_dotenv
load_dotenv('config.env')
import google.generativeai as genai

key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=key)

try:
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    with open('models_output.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(models))
except Exception as e:
    with open('models_output.txt', 'w', encoding='utf-8') as f:
        f.write("FATAL: " + repr(e))
