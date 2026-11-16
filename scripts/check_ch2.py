"""Kiểm tra chunk trang 9 và trang 55."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
with open(ROOT / "data/advanced/chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

for c in chunks:
    if c["page"] in (9, 55) and ("Chương 2" in c["text"] or "CHƯƠNG 2" in c["text"]):
        print(f"ID: {c['id']}, Page: {c['page']}")
        print(c["text"][:200])
        print("---")
