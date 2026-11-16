"""Khảo sát và trích xuất các đoạn evidence chuẩn từ chunks.json cho 48 câu hỏi benchmark."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS_FILE = ROOT / "data" / "advanced" / "chunks.json"

with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

chunk_by_id = {c["id"]: c for c in chunks}

def search_text(keyword, limit=5, element_type=None):
    results = []
    kw_lower = keyword.lower()
    for c in chunks:
        if element_type and c["metadata"].get("type") != element_type:
            continue
        if kw_lower in c["text"].lower():
            results.append(c)
            if len(results) >= limit:
                break
    return results

print("--- 1. BẢNG 1.1 ---")
for c in search_text("BẢNG 1.1", 2, "table"):
    print(c["id"], "Page:", c["page"], "\n", c["text"][:250])

print("\n--- 2. BẢNG 2.1 ---")
for c in search_text("BẢNG 2.1", 2, "table"):
    print(c["id"], "Page:", c["page"], "\n", c["text"][:250])

print("\n--- 3. BẢNG 3.1 ---")
for c in search_text("BẢNG 3.1", 2, "table"):
    print(c["id"], "Page:", c["page"], "\n", c["text"][:250])

print("\n--- 4. HÌNH 1.1 ---")
for c in search_text("HÌNH 1.1", 2):
    print(c["id"], "Page:", c["page"], "\n", c["text"][:250])

print("\n--- 5. HÌNH 1.3 ---")
for c in search_text("HÌNH 1.3", 2):
    print(c["id"], "Page:", c["page"], "\n", c["text"][:250])

print("\n--- 6. HỘP 1.1 ---")
for c in search_text("HỘP 1.1", 2):
    print(c["id"], "Page:", c["page"], "\n", c["text"][:250])

print("\n--- 7. HỘP 2.1 ---")
for c in search_text("HỘP 2.1", 2):
    print(c["id"], "Page:", c["page"], "\n", c["text"][:250])
