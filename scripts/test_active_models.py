"""Kiểm tra hoạt động của gemini-3.1-flash-lite và gemini-3.8-flash."""
import json
import os
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

api_key = os.getenv("GEMINI_API_KEY")

for m in ["gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-flash-lite-latest", "gemini-3.7-flash"]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": "Hello world"}]}]}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            print(f"[OK] Model '{m}' HOẠT ĐỘNG HOÀN HẢO! Trả về: {text[:50]}")
    except Exception as e:
        print(f"[FAIL] Model '{m}': {e}")
