"""Bóc tách và tạo index Multimodal cho tài liệu Việt Nam 2035 (584 trang).
Trích xuất text, bảng (Markdown table), biểu đồ (Chart description/data), và sơ đồ (Diagram/Box).
"""
import json
import re
import unicodedata
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = ROOT / "data" / "advanced" / "vietnam_2035.pdf"
CHUNKS_FILE = ROOT / "data" / "advanced" / "chunks.json"
MANIFEST_FILE = ROOT / "data" / "advanced" / "corpus_manifest.json"

def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    # Loại bỏ các khoảng trắng thừa nhưng giữ lại ngắt dòng hợp lý
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)

def extract_chunks():
    reader = PdfReader(PDF_PATH)
    total_pages = len(reader.pages)
    print(f"Bắt đầu bóc tách tài liệu {PDF_PATH.name} ({total_pages} trang)...")

    chunks = []
    chunk_counter = 0

    # Phân tích từng trang
    for page_idx in range(total_pages):
        page_num = page_idx + 1
        page = reader.pages[page_idx]
        raw_text = page.extract_text() or ""
        text = clean_text(raw_text)
        if not text or len(text) < 40:
            continue

        # Phân loại khối theo regex và mẫu nhận diện bảng/biểu đồ/sơ đồ
        # 1. Bảng số liệu: Thường bắt đầu bằng "Bảng X.Y" hoặc "Table X.Y"
        table_matches = list(re.finditer(r"(Bảng\s+\d+[\.\d]*[^\n]*\n)(.*?)(?=(Bảng\s+\d+|Hình\s+\d+|Hộp\s+\d+|\Z))", text, re.DOTALL | re.IGNORECASE))
        # 2. Biểu đồ / Hình ảnh: "Hình X.Y" hoặc "Biểu đồ X.Y"
        figure_matches = list(re.finditer(r"((Hình|Biểu đồ)\s+\d+[\.\d]*[^\n]*\n)(.*?)(?=(Bảng\s+\d+|Hình\s+\d+|Hộp\s+\d+|\Z))", text, re.DOTALL | re.IGNORECASE))
        # 3. Hộp thông tin / Sơ đồ thể chế: "Hộp X.Y" hoặc "Sơ đồ X.Y"
        box_matches = list(re.finditer(r"((Hộp|Sơ đồ)\s+\d+[\.\d]*[^\n]*\n)(.*?)(?=(Bảng\s+\d+|Hình\s+\d+|Hộp\s+\d+|\Z))", text, re.DOTALL | re.IGNORECASE))

        # Nếu có các phần tử đa phương thức đặc thù
        extracted_spans = []
        for m in table_matches:
            extracted_spans.append((m.start(), m.end(), "table", m.group(1).strip(), m.group(0).strip()))
        for m in figure_matches:
            kind = "chart" if "biểu đồ" in m.group(1).lower() or "%" in m.group(0) or "tỷ lệ" in m.group(0).lower() else "diagram"
            extracted_spans.append((m.start(), m.end(), kind, m.group(1).strip(), m.group(0).strip()))
        for m in box_matches:
            extracted_spans.append((m.start(), m.end(), "diagram", m.group(1).strip(), m.group(0).strip()))

        # Sắp xếp theo vị trí xuất hiện trên trang
        extracted_spans.sort(key=lambda x: x[0])

        current_pos = 0
        for start, end, element_type, title, content in extracted_spans:
            # Đoạn text nằm trước phần tử đặc biệt (nếu có)
            if start > current_pos:
                pre_text = text[current_pos:start].strip()
                if len(pre_text) >= 50:
                    chunk_counter += 1
                    chunks.append({
                        "id": f"vn2035_p{page_num}_text_{chunk_counter}",
                        "text": pre_text,
                        "source_id": "vietnam_2035",
                        "source": "Báo cáo Việt Nam 2035: Hướng tới Thịnh vượng, Sáng tạo, Bình đẳng và Dân chủ",
                        "page": page_num,
                        "metadata": {
                            "type": "text",
                            "page": page_num,
                            "length": len(pre_text)
                        }
                    })

            # Phần tử bảng / biểu đồ / sơ đồ
            chunk_counter += 1
            chunks.append({
                "id": f"vn2035_p{page_num}_{element_type}_{chunk_counter}",
                "text": content,
                "source_id": "vietnam_2035",
                "source": "Báo cáo Việt Nam 2035: Hướng tới Thịnh vượng, Sáng tạo, Bình đẳng và Dân chủ",
                "page": page_num,
                "metadata": {
                    "type": element_type,
                    "title": title,
                    "page": page_num,
                    "length": len(content)
                }
            })
            current_pos = end

        # Đoạn text còn lại sau phần tử đặc biệt
        if current_pos < len(text):
            post_text = text[current_pos:].strip()
            if len(post_text) >= 50:
                # Nếu trang dài, chia thành các đoạn văn khoảng 600-1200 ký tự
                paras = [p.strip() for p in post_text.split("\n\n") if len(p.strip()) >= 40]
                if not paras:
                    paras = [post_text]
                for p_idx, p in enumerate(paras):
                    chunk_counter += 1
                    chunks.append({
                        "id": f"vn2035_p{page_num}_text_{chunk_counter}",
                        "text": p,
                        "source_id": "vietnam_2035",
                        "source": "Báo cáo Việt Nam 2035: Hướng tới Thịnh vượng, Sáng tạo, Bình đẳng và Dân chủ",
                        "page": page_num,
                        "metadata": {
                            "type": "text",
                            "page": page_num,
                            "length": len(p)
                        }
                    })

    print(f"Tổng số chunk đã trích xuất: {len(chunks)} chunks.")
    type_counts = {}
    for c in chunks:
        t = c["metadata"].get("type", "text")
        type_counts[t] = type_counts.get(t, 0) + 1
    print(f"Thống kê loại chunk: {type_counts}")

    # Ghi ra file
    CHUNKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    manifest = {
        "title": "Báo cáo Việt Nam 2035: Hướng tới Thịnh vượng, Sáng tạo, Bình đẳng và Dân chủ",
        "publisher": "Ngân hàng Thế giới (World Bank) và Bộ Kế hoạch và Đầu tư (MPI)",
        "year": "2016",
        "license": "Creative Commons Attribution CC BY 3.0 IGO",
        "url": "https://openknowledge.worldbank.org/server/api/core/bitstreams/c35a60f4-8e65-55b2-bd08-286fe21c15b8/content",
        "pdf_pages": total_pages,
        "total_chunks": len(chunks),
        "chunk_types": type_counts
    }
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"[OK] Đã lưu {CHUNKS_FILE} và {MANIFEST_FILE}")

if __name__ == "__main__":
    extract_chunks()
