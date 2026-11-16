"""Kiểm tra và sửa lỗi exact matching cho toàn bộ 48 câu hỏi benchmark."""
import re
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "scripts" / "generate_advanced_benchmark.py"
text = FILE.read_text(encoding="utf-8")

# Sửa lỗi adv_dev_06
old_06 = '''"evidence": "Quan điểm\\nđang thay đổi của người dân về thị trường và nhà nước do Phòng Thương mại và Công\\nnghiệp Việt Nam (VCCI) và Ngân hàng Thế giới tiến hành"'''
new_06 = '''"evidence": "do Phòng Thương mại và Công\\nnghiệp (VCCI) Việt Nam, với sự hỗ trợ của Ngân hàng Thế giới, thực hiện."'''

if old_06 in text:
    text = text.replace(old_06, new_06)
    print("Đã thay thế evidence adv_dev_06 thành công!")
else:
    print("Không tìm thấy đoạn old_06 nguyên văn, đang dùng regex...")
    text = re.sub(
        r'"chunk_id":\s*"vn2035_p72_diagram_280",\s*"evidence":\s*".*?"',
        r'"chunk_id": "vn2035_p72_diagram_280",\n                "evidence": "do Phòng Thương mại và Công\\nnghiệp (VCCI) Việt Nam, với sự hỗ trợ của Ngân hàng Thế giới, thực hiện."',
        text,
        flags=re.DOTALL
    )

FILE.write_text(text, encoding="utf-8")
print("Đã cập nhật generate_advanced_benchmark.py")
