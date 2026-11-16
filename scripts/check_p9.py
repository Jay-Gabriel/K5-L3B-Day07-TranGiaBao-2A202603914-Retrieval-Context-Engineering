"""Kiểm tra đoạn 1.1. Tiến trình trong vn2035_p9_text_5."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS_FILE = ROOT / "data" / "advanced" / "chunks.json"

with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

by_id = {c["id"]: c for c in chunks}
text = by_id["vn2035_p9_text_5"]["text"]
lines = [l for l in text.splitlines() if "1.1" in l or "1.2" in l or "1.3" in l or "1.4" in l]
for l in lines:
    print(repr(l))
