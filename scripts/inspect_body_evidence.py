"""Tìm kiếm các bảng và biểu đồ trong phần thân báo cáo (trang 40-500)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS_FILE = ROOT / "data" / "advanced" / "chunks.json"

with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

# Lọc các chunk nằm ở các trang nội dung (page >= 35) có chứa số liệu cụ thể
body_tables = [c for c in chunks if c["page"] >= 35 and ("Bảng " in c["text"] or "bảng " in c["text"].lower()) and len(c["text"]) > 150]
body_charts = [c for c in chunks if c["page"] >= 35 and ("Hình " in c["text"] or "Biểu đồ " in c["text"]) and ("%" in c["text"] or "tỷ" in c["text"].lower()) and len(c["text"]) > 150]
body_diagrams = [c for c in chunks if c["page"] >= 35 and ("Hộp " in c["text"] or "Sơ đồ " in c["text"]) and len(c["text"]) > 150]

print(f"Body Tables: {len(body_tables)}, Body Charts: {len(body_charts)}, Body Diagrams: {len(body_diagrams)}")

print("\n--- 3 BẢNG NỘI DUNG MẪU ---")
for t in body_tables[:3]:
    print(f"ID: {t['id']}, Page: {t['page']}")
    print(t["text"][:300] + "\n...")

print("\n--- 3 BIỂU ĐỒ NỘI DUNG MẪU ---")
for c in body_charts[:3]:
    print(f"ID: {c['id']}, Page: {c['page']}")
    print(c["text"][:300] + "\n...")

print("\n--- 3 SƠ ĐỒ/HỘP NỘI DUNG MẪU ---")
for d in body_diagrams[:3]:
    print(f"ID: {d['id']}, Page: {d['page']}")
    print(d["text"][:300] + "\n...")
