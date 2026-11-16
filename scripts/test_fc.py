"""Kiểm tra Function Calling với gemini-3.1-flash-lite."""
import json
import os
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

api_key = os.getenv("GEMINI_API_KEY")
model = "gemini-3.1-flash-lite"
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

tools = [{'functionDeclarations': [
    {'name': 'search', 'description': 'Tìm kiếm', 'parameters': {'type': 'OBJECT', 'properties': {'query': {'type': 'STRING'}}, 'required': ['query']}},
    {'name': 'answer', 'description': 'Trả lời', 'parameters': {'type': 'OBJECT', 'properties': {'answer': {'type': 'STRING'}, 'citations': {'type': 'ARRAY', 'items': {'type': 'STRING'}}}, 'required': ['answer', 'citations']}}
]}]

payload = {
    'contents': [{'role': 'user', 'parts': [{'text': 'Theo Bảng 1.1, tốc độ tăng trưởng của Việt Nam là bao nhiêu?'}]}],
    'tools': tools,
    'toolConfig': {'functionCallingConfig': {'mode': 'ANY', 'allowedFunctionNames': ['search']}}
}

req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.load(resp)
    print("[SUCCESS FC]:", json.dumps(data, indent=2, ensure_ascii=False))
