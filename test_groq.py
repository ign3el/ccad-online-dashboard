
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_groq():
    api_key = os.getenv('GROQ_API_KEY')
    print(f"Testing with API Key: {api_key[:10]}...")
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "Test system prompt"},
            {"role": "user", "content": "Say hello"}
        ],
        "temperature": 0.2,
        "max_tokens": 10
    }
    
    try:
        res = requests.post(url, json=payload, headers=headers)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_groq()
