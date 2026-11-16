"""Tìm thêm các bảng, biểu đồ, hộp thể chế trong các chương 1 đến 7."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS_FILE = ROOT / "data" / "advanced" / "chunks.json"

with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

# Tìm các Bảng có nhiều số liệu
tables = [c for c in chunks if c["page"] >= 35 and "BẢNG" in c["text"].upper() and len(c["text"]) > 200]
print(f"Tổng số bảng tìm được: {len(tables)}")
for i, t in enumerate(tables[:15]):
    first_line = t["text"].splitlines()[0]
    second_line = t["text"].splitlines()[1] if len(t["text"].splitlines()) > 1 else ""
    print(f"[{i+1}] ID: {t['id']}, Page: {t['page']}, Header: {first_line[:60]} | {second_line[:50]}")

# Tìm các Hộp thông tin / Sơ đồ thể chế
boxes = [c for c in chunks if c["page"] >= 35 and ("HỘP " in c["text"].upper() or "SƠ ĐỒ " in c["text"].upper()) and len(c["text"]) > 200]
print(f"\nTổng số hộp/sơ đồ tìm được: {len(boxes)}")
for i, b in enumerate(boxes[:15]):
    first_line = b["text"].splitlines()[0]
    second_line = b["text"].splitlines()[1] if len(b["text"].splitlines()) > 1 else ""
    print(f"[{i+1}] ID: {b['id']}, Page: {b['page']}, Header: {first_line[:60]} | {second_line[:50]}")

# Tìm các Biểu đồ / Hình ảnh
charts = [c for c in chunks if c["page"] >= 35 and ("HÌNH " in c["text"].upper() or "BIỂU ĐỒ " in c["text"].upper()) and len(c["text"]) > 200]
print(f"\nTổng số hình/biểu đồ tìm được: {len(charts)}")
for i, ch in enumerate(charts[:15]):
    first_line = ch["text"].splitlines()[0]
    second_line = ch["text"].splitlines()[1] if len(ch["text"].splitlines()) > 1 else ""
    print(f"[{i+1}] ID: {ch['id']}, Page: {ch['page']}, Header: {first_line[:60]} | {second_line[:50]}")
