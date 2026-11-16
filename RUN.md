# Chạy bài làm Day 7

Bài làm: **Trần Gia Bảo — 2A202603914**. Python 3.11 trở lên. Toàn bộ lệnh chạy từ thư mục gốc repo.

## Cài đặt

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Điền `GEMINI_API_KEY`, `GEMINI_MODEL`, `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION` và `EMBEDDING_MODEL` vào `.env`. Giữ model embedding tương thích với index Day 6: `sentence-transformers/all-MiniLM-L6-v2`, 384 chiều, Cosine. Model agent trong kết quả đã lưu được ghi riêng trong mỗi `run.json`; nếu chạy model khác, đó là thí nghiệm mới. Không đưa `.env` vào Git.

Dữ liệu đã xuất nằm ở `data/chunks.json`: **81 payload gốc của Qdrant Day 6**, giữ nguyên ID, text và ranh giới chunk. PDF thực tế có **52 trang**; mỗi trang chứa tối đa hai slide. Citation dùng số trang PDF, không dùng số slide in bên trong. `data/corpus_manifest.json` lưu hash và thông tin kiểm tra. `source` giữ đường dẫn gốc từ Day 6; demo chỉ hiển thị tên file.

Nguồn là bài giảng *Chẩn đoán và Điều trị Suy tim* của GS. TS. Huỳnh Văn Minh, file `cme2._suy_timgs_minh.pdf`. Sinh viên cần bổ sung nguồn truy cập hợp lệ và xác nhận quyền sử dụng/chia sẻ trước khi nộp hoặc đưa repo lên public. Mục đích học tập không tự xác lập giấy phép.

## Mở demo

```bash
python starter/web_demo/app.py
```

Mở **http://127.0.0.1:8502**. Đổi cổng nếu cần:

```bash
python starter/web_demo/app.py --port 8503
```

Demo mặc định chỉ nghe trên máy cục bộ. Không cần Node, CDN hay frontend build. TF-IDF chạy cục bộ; chỉ khởi tạo kết nối Qdrant khi chọn Dense/Hybrid. Model trả lời luôn được gọi thật, không có câu trả lời dựng sẵn hoặc cache dùng thay benchmark. Demo dùng `DEMO_GEMINI_MODEL=gemini-3.1-flash-lite`; benchmark đã lưu dùng `GEMINI_MODEL=gemini-3.5-flash-lite`. Model benchmark chạm giới hạn 500 request/ngày trong chiến dịch; các lỗi 429 được giữ nguyên trong test. Model demo khác được nêu rõ trong phần tùy chọn và mỗi câu trả lời; không dùng nó để thay kết quả test đã chạy.

Xem [kịch bản trình bày](docs/DEMO.md). Khi thiếu API key, lỗi model, timeout hoặc quota, UI báo lỗi riêng, không gọi đó là thiếu bằng chứng.

## Kiểm tra code và kết nối

```bash
python -m unittest discover -s tests -v
python starter/test_qdrant_day7.py
python starter/probe_api_key.py
python starter/test_agent_live.py --config lexical_context
```

Unit test dùng adapter giả để kiểm tra hành vi code; không đo chất lượng model. Ba lệnh cuối gọi dịch vụ thật và có thể tiêu thụ quota. Controller giãn nhịp gọi API và retry hữu hạn; lỗi vẫn được lưu, không thay bằng dữ liệu giả. Demo và CLI chạy đồng thời có thể dùng chung quota tài khoản.

Để kiểm tra UI bằng trình duyệt:

```bash
pip install -r requirements-dev.txt
python -m playwright install chromium
# Mở demo ở cổng 8503 trong terminal khác trước:
DEMO_URL=http://127.0.0.1:8503 python tests/browser_demo.py
```

Script UI này dùng response fixture có nhãn QA để kiểm tra bố cục và xử lý lỗi; không phải benchmark agent thật.

## Dữ liệu và khôi phục index

Repo kèm snapshot chunk và benchmark, không cần đường dẫn Day 6 trên máy tác giả. Để xuất lại đúng collection Day 6 của bạn:

```bash
python starter/export_day6_to_day7.py --output /tmp/day7-export/chunks.json
```

Exporter chỉ đọc Qdrant. Nó kiểm tra cấu hình vector, lấy text/payload nguyên bản, ghi hash, đếm trang từ PDF cục bộ nếu có. Danh tính embedding phải được kiểm tra từ cấu hình ingest Day 6; số chiều không chứng minh được model.

Để tái tạo trên Qdrant của riêng bạn, tạo collection **mới**:

```bash
python starter/restore_index.py --collection day7-reproduced
```

Sau đó đặt `QDRANT_COLLECTION=day7-reproduced` trong `.env`. Script từ chối ghi đè collection có sẵn. Việc tái tạo collection là chạy mới, không chỉnh metadata của kết quả đã lưu.

## Thí nghiệm và đánh giá

Kết quả chính ở `starter/results/v2/`, tách `dev` và `test`. Bản cũ không dùng cho báo cáo mới; lịch sử cục bộ được giữ ở `.local-history/` và không đưa vào Git. `dev_pilots.json` ghi các lần thăm dò/lỗi trước lần chạy cuối.

1. `data/questions.json` chứa gold cho 20 câu có đáp án; `data/cases.json` chứa 24 câu gồm cả câu thiếu bằng chứng. `starter/prepare_benchmark.py` tái tạo đúng bộ câu hỏi v2, không sinh câu hỏi bằng cách chép một đoạn gold vào query. Bộ cũ đã được xem; v2 đặt câu hỏi cụ thể mới và chia dev/test trước khi chọn cấu hình. Corpus vẫn là cùng tài liệu, nên kết quả không khái quát cho tài liệu khác.
2. Retrieval so sánh query gốc; agent có thể viết query và tìm tiếp. Mỗi bước được lưu riêng. Không đưa gold, expected answer, nhãn hoặc absence reason vào model/retriever. Không sử dụng filter `section` không tồn tại.
3. Chọn trên dev theo thứ tự: ít lỗi hệ thống, điểm câu trả lời cao, từ chối đúng câu thiếu evidence, context đầy đủ, thời gian trung vị thấp. Cần xem nội dung và nhãn trước khi chốt.
4. Chạy model không sinh điểm chất lượng. Mỗi run tạo `reviews.pending.json`; người đánh giá đọc câu trả lời/context/citation và PDF, rồi tạo `reviews.json`. Nhãn hiện có được AI hỗ trợ đối chiếu, có lý do từng câu và ghi `student_verified: false`; sinh viên cần duyệt, không được mô tả là đã chấm thủ công bởi sinh viên.
5. Sau khi chốt, chỉ chạy baseline và cấu hình chọn trên test. `selection.json` khóa hash code/dữ liệu, model, collection, embedding và các artifact dev đã chấm. Không thay pipeline để tối ưu từ test; nếu làm vậy cần test mới.

Các lệnh dưới đây dành cho một lần tái lập mới. Output cùng đường dẫn đã tồn tại sẽ bị từ chối để giữ bằng chứng. Không xóa hoặc sửa các kết quả đã công bố để chạy đè. Khi thực hiện một chiến dịch thí nghiệm mới, sao chép repo sang thư mục làm việc riêng, giữ nguyên bộ kết quả gốc, rồi chọn output khác và tạo benchmark test mới nếu đã dùng test cũ để chỉnh.

```bash
# Query gốc, cả 5 cấu hình trên dev:
python starter/run_retrieval_benchmark.py --split dev --output /tmp/day7-retrieval
# Agent: baseline và 2 cấu hình cải thiện trên dev:
python starter/run_agent_benchmark.py --split dev --configs baseline hybrid_context lexical_context --output /tmp/day7-agent
# Sau khi tạo reviews.json bằng đánh giá nội dung từng câu:
python starter/summarize_reviews.py --run /tmp/day7-agent/dev/baseline
```

Bản đánh giá đã công bố dùng output mặc định và `python starter/select_config.py` để chốt, sau đó:

```bash
python starter/run_retrieval_benchmark.py --split test --configs baseline lexical_context
python starter/run_agent_benchmark.py --split test --configs baseline lexical_context
```

Lệnh này minh họa cấu hình đã chọn trong lần chạy được lưu; xem `selection.json` làm nguồn chính xác. Nếu chạy lại trên repo đã có kết quả, runner sẽ báo output tồn tại. Việc xem test để tái lập không cho phép dùng chính bộ test đó để chọn lại cấu hình.

## Giới hạn

- Dense dùng MiniLM với tài liệu tiếng Việt có lỗi trích xuất/font; chất lượng cần đo thay vì giả định tốt hơn lexical.
- Context budget đo bằng **ký tự**, gồm header nguồn, không phải token. Chunk không vừa bị bỏ nguyên khối, không tự tóm tắt hoặc cắt sửa bằng chứng.
- Hybrid dùng RRF k=60; mỗi nhánh lấy `max(10, top_k*3)` candidate: 10 khi top-k=3, 18 khi top-k=6. Vì số candidate thay đổi, ranking top-3 của hai cấu hình Hybrid có thể khác nhau.
- Model có thể tìm tối đa 3 lần. Context tích lũy ưu tiên chunk đã lấy trước; đây vẫn là hạn chế khi cần đổi hướng tìm.
- Citation có trong context chưa chứng minh mọi khẳng định đúng. Nhãn nội dung và citation được lưu riêng để kiểm tra lại.
- Lưu usage token thực; chưa truy vấn hóa đơn tài khoản. Chi phí agent ghi `null`/chưa đo, không bịa tổng chi phí bằng $0.
- Không thực hiện bonus: tài liệu dưới 100 trang và chưa có benchmark multimodal nâng cao.
