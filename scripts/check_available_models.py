"""Kiểm tra các model Gemini còn quota miễn phí trong dự án."""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

api_key = os.getenv("GEMINI_API_KEY")

candidates = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    "gemini-2.0-pro-exp-02-05"
]

print("Kiểm tra quota từng model:")
for m in candidates:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
    req = urllib.request.Request(
        url,
        data=json.dumps({"contents": [{"parts": [{"text": "1+1=?"}]}]}).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key}
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.load(resp)
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            print(f"  [OK] Model '{m}' KHẢ DỤNG! Output: {text}")
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode())
        code = body.get("error", {}).get("code")
        msg = body.get("error", {}).get("message", "")[:70]
        print(f"  [FAIL] Model '{m}': HTTP {code} - {msg}")
    except Exception as e:
        print(f"  [FAIL] Model '{m}': {e}")
