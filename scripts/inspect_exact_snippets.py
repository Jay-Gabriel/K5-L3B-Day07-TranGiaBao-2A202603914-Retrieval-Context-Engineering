"""Lấy chính xác các đoạn text/ô/hàng trong các chunk để làm gold evidence."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS_FILE = ROOT / "data" / "advanced" / "chunks.json"

with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

by_id = {c["id"]: c for c in chunks}

targets = [
    ("vn2035_p77_table_292", "Table 1.1"),
    ("vn2035_p81_table_302", "Table 1.2"),
    ("vn2035_p128_table_401", "Table 2.1"),
    ("vn2035_p129_table_403", "Table 2.2"),
    ("vn2035_p131_table_408", "Table 2.3"),
    ("vn2035_p132_table_416", "Table 2.4"),
    ("vn2035_p144_table_445", "Table 2.5"),
    ("vn2035_p51_diagram_245", "Box 1.1"),
    ("vn2035_p61_diagram_259", "Box 1.2"),
    ("vn2035_p62_diagram_262", "Box 1.3"),
    ("vn2035_p72_diagram_280", "Box 1.4"),
    ("vn2035_p80_diagram_300", "Box 1.5"),
    ("vn2035_p89_diagram_315", "Box 1.6"),
    ("vn2035_p119_diagram_381", "Box 2.1"),
    ("vn2035_p64_chart_268", "Chart 1.3"),
    ("vn2035_p66_chart_271", "Chart 1.4"),
    ("vn2035_p67_chart_273", "Chart 1.5"),
    ("vn2035_p73_chart_282", "Chart 1.6"),
    ("vn2035_p74_chart_286", "Chart 1.7"),
    ("vn2035_p54_diagram_249", "Figure 1.1"),
]

for cid, label in targets:
    c = by_id.get(cid)
    if c:
        print(f"=== {label} [{cid}] (Page {c['page']}) ===")
        lines = [line.strip() for line in c['text'].splitlines() if line.strip()]
        for l in lines[:6]:
            print("  ", l)
    else:
        print(f"=== {label} [{cid}] NOT FOUND ===")
