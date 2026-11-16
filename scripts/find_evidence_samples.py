"""Tìm và trích xuất các bảng, biểu đồ, sơ đồ cụ thể từ chunks.json để xây dựng benchmark."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS_FILE = ROOT / "data" / "advanced" / "chunks.json"

with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Tổng chunks: {len(chunks)}")
tables = [c for c in chunks if c["metadata"].get("type") == "table"]
charts = [c for c in chunks if c["metadata"].get("type") == "chart"]
diagrams = [c for c in chunks if c["metadata"].get("type") == "diagram"]

print(f"Tables: {len(tables)}, Charts: {len(charts)}, Diagrams: {len(diagrams)}")

print("\n--- SAMPLE TABLES ---")
for t in tables[10:18]:
    title = t["metadata"].get("title", "")
    print(f"ID: {t['id']}, Page: {t['page']}, Title: {title[:70]}")
    lines = t["text"].splitlines()[:5]
    print("   " + "\n   ".join(lines))

print("\n--- SAMPLE CHARTS ---")
for c in charts[5:13]:
    title = c["metadata"].get("title", "")
    print(f"ID: {c['id']}, Page: {c['page']}, Title: {title[:70]}")
    lines = c["text"].splitlines()[:4]
    print("   " + "\n   ".join(lines))

print("\n--- SAMPLE DIAGRAMS/BOXES ---")
for d in diagrams[10:18]:
    title = d["metadata"].get("title", "")
    print(f"ID: {d['id']}, Page: {d['page']}, Title: {title[:70]}")
    lines = d["text"].splitlines()[:4]
    print("   " + "\n   ".join(lines))
