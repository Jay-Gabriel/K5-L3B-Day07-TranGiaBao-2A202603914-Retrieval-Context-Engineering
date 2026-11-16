"""Liệt kê danh sách tất cả các models đang được hỗ trợ cho API key này."""
import json
import os
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

api_key = os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.load(resp)
    print("Danh sách model khả dụng:")
    for m in data.get("models", []):
        name = m.get("name")
        methods = m.get("supportedGenerationMethods", [])
        if "generateContent" in methods:
            print(f"  - {name} ({m.get('displayName')})")
