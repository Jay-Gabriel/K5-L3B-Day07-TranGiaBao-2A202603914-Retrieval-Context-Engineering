"""In toàn văn chunk vn2035_p72_diagram_280 để lấy chính xác substring."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS_FILE = ROOT / "data" / "advanced" / "chunks.json"

with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

by_id = {c["id"]: c for c in chunks}
print(repr(by_id["vn2035_p72_diagram_280"]["text"]))
