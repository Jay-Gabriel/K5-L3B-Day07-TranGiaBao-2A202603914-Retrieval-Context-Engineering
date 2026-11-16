"""In chi tiết một số chunk cụ thể."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS_FILE = ROOT / "data" / "advanced" / "chunks.json"

with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

by_id = {c["id"]: c for c in chunks}

print("=== TABLE 1.1 (vn2035_p77_table_292) ===")
print(by_id.get("vn2035_p77_table_292", {}).get("text", "NOT FOUND"))

print("\n=== HÌNH 1.3 (vn2035_p61_diagram_258) ===")
print(by_id.get("vn2035_p61_diagram_258", {}).get("text", "NOT FOUND"))

print("\n=== HỘP 1.1 (vn2035_p51_diagram_244) ===")
print(by_id.get("vn2035_p51_diagram_244", {}).get("text", "NOT FOUND"))
