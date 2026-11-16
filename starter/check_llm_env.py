import urllib.request
import json

try:
    req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
    data = json.loads(req.read().decode())
    print("Ollama is RUNNING! Available models:")
    for m in data.get("models", []):
        print(f" - {m.get('name')}")
except Exception as e:
    print(f"Ollama is not running: {e}")
