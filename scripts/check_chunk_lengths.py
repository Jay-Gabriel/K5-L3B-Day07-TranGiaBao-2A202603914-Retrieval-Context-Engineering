"""Kiểm tra phân bố độ dài các chunk."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
with open(ROOT / "data/advanced/chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

long_chunks = [c for c in chunks if len(c["text"]) > 2000]
print(f"Tổng chunks: {len(chunks)}, Chunks > 2000 chars: {len(long_chunks)}")
for c in long_chunks[:10]:
    print(f"ID: {c['id']}, Page: {c['page']}, Length: {len(c['text'])}, Preview: {c['text'][:60]}")
