
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def list_models():
    api_key = os.getenv('GROQ_API_KEY')
    url = "https://api.groq.com/openai/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            models = res.json().get('data', [])
            print("Available Models:")
            for m in models:
                print(f"- {m['id']}")
        else:
            print(f"Error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    list_models()
