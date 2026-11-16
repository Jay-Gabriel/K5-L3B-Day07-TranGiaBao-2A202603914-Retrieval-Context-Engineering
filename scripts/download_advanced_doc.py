"""Tải tài liệu Việt Nam 2035 từ World Bank Open Knowledge Repository (398 trang)."""
import os
import sys
import urllib.request
from pathlib import Path
from pypdf import PdfReader

DEST_DIR = Path(__file__).resolve().parents[1] / "data" / "advanced"
DEST_FILE = DEST_DIR / "vietnam_2035.pdf"
URL = "https://openknowledge.worldbank.org/server/api/core/bitstreams/c35a60f4-8e65-55b2-bd08-286fe21c15b8/content"

def main():
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    if DEST_FILE.exists() and DEST_FILE.stat().st_size > 5_000_000:
        print(f"[OK] File đã tồn tại: {DEST_FILE} ({DEST_FILE.stat().st_size / 1024 / 1024:.2f} MB)")
    else:
        print(f"[DOWNLOADING] Đang tải tài liệu từ: {URL}")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        req = urllib.request.Request(URL, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as resp, open(DEST_FILE, "wb") as f:
            chunk_size = 1024 * 1024
            downloaded = 0
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                print(f"  -> Đã tải {downloaded / 1024 / 1024:.2f} MB...")
        print(f"[DOWNLOAD COMPLETED] Lưu thành công: {DEST_FILE}")

    reader = PdfReader(DEST_FILE)
    num_pages = len(reader.pages)
    print(f"[VERIFIED] Số trang PDF: {num_pages} trang (yêu cầu tối thiểu >= 100 trang)")
    if num_pages < 100:
        raise ValueError(f"Số trang {num_pages} không đạt ngưỡng >= 100 trang!")

if __name__ == "__main__":
    main()
