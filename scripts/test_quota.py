"""Test Gemini API request directly to inspect HTTP 429 response body."""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "models/gemini-3.5-flash-lite").removeprefix("models/")

url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
req = urllib.request.Request(
    url,
    data=json.dumps({"contents": [{"parts": [{"text": "Hello"}]}]}).encode(),
    headers={"Content-Type": "application/json", "x-goog-api-key": api_key}
)

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print("[SUCCESS]:", resp.status, json.load(resp))
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"[HTTP {e.code}]: {body}")
except Exception as e:
    print(f"[ERROR]: {e}")
