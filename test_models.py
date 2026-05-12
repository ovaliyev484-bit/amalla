import os
import asyncio
from google import genai

import json
from pathlib import Path

def _get_api_key() -> str:
    path = Path("config/api_keys.json")
    if path.exists():
        with open(path, "r") as f:
            return json.load(f).get("gemini_api_key", "")
    return os.getenv("GEMINI_API_KEY", "").strip()

async def test_models():
    api_key = _get_api_key()
    if not api_key:
        print("API KEY NOT FOUND")
        return
    
    client = genai.Client(api_key=api_key, http_options={"api_version": "v1alpha"})
    models = [
        "models/gemini-3.1-flash-live-preview",
        "gemini-2.0-flash-exp", 
        "models/gemini-2.0-flash-exp"
    ]
    
    for m in models:
        try:
            print(f"Testing {m}...")
            async with client.aio.live.connect(model=m, config={"generation_config": {"response_modalities": ["AUDIO"]}}) as session:
                print(f"SUCCESS: {m} works!")
                return m
        except Exception as e:
            print(f"FAILED: {m} -> {e}")

if __name__ == "__main__":
    asyncio.run(test_models())
