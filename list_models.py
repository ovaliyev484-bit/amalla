import os
from google import genai
import json
from pathlib import Path

def _get_api_key() -> str:
    path = Path("config/api_keys.json")
    if path.exists():
        with open(path, "r") as f:
            return json.load(f).get("gemini_api_key", "")
    return os.getenv("GEMINI_API_KEY", "").strip()

def list_all_models():
    api_key = _get_api_key()
    client = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})
    
    print("Available Models:")
    for m in client.models.list():
        print(f"- {m.name} ({m.supported_actions})")

if __name__ == "__main__":
    list_all_models()
