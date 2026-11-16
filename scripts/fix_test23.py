"""Sửa evidence của adv_test_23."""
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "scripts" / "generate_advanced_benchmark.py"
text = FILE.read_text(encoding="utf-8")

old_text = '''"evidence": "1.1. Tiến trình ...................................................................................................................................................................................................................................................................\\n1.2. Áp lực thay đổi và những cải cách chủ yếu ...................................................................................................................................."'''
new_text = '''"evidence": "1.3. Đổi mới – đạt được những thành tựu kỷ lục song đang xuất hiện"'''

assert old_text in text, "Không tìm thấy old_text"
text = text.replace(old_text, new_text)
FILE.write_text(text, encoding="utf-8")
print("Đã cập nhật adv_test_23")
