# Chạy và kiểm tra bài làm Day 7

**Trần Gia Bảo — 2A202603914 — L3B.** Chạy lệnh từ thư mục gốc repo; Python 3.11 trở lên.

## Cài và mở demo

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Điền API key và thông tin Qdrant vào .env bằng trình soạn thảo.
python starter/web_demo/app.py
```

Mở **http://127.0.0.1:8502**. `--port 8503` nếu cần đổi cổng. Demo chỉ nghe trên localhost mặc định, không cần Node/CDN/frontend build. Câu trả lời luôn gọi model thật. Chọn câu gợi ý chỉ điền vào ô, chưa gửi; bấm “Tìm câu trả lời” để bắt đầu.

UI hiển thị nguyên câu hỏi, query model chọn và các đoạn retrieval trả về ngay trong quá trình chạy. Nhãn phân biệt đoạn chỉ tìm được, đoạn đã gửi model và đoạn được trích dẫn. Bấm nguồn để xem nguyên văn/mở đúng trang PDF. Timeout/quota/output sai là lỗi riêng, không được thay bằng một câu trả lời giả hoặc gọi là abstention đúng. [Kịch bản demo](docs/DEMO.md).

Model mặc định của campaign v3 và demo: **gemini-3.1-flash-lite**. `.env` chứa `GEMINI_MODEL`, `DEMO_GEMINI_MODEL`, `GEMINI_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION`, `EMBEDDING_MODEL`. Không đưa `.env` vào Git. Controller giãn nhịp gọi để giảm lỗi quota và retry hữu hạn; không có cache dựng kết quả benchmark.

## Dữ liệu và nguồn

`data/chunks.json` chứa **81 payload nguyên bản Day 6**, cùng ID/text/ranh giới với Qdrant. PDF có **52 trang**, thường hai slide/trang; citation dùng số trang PDF. Embedding **sentence-transformers/all-MiniLM-L6-v2**, 384 chiều, Cosine; collection mặc định `rag_strategy_b`. Thay embedding phải tạo index tương thích, không chỉ đổi tên trong cấu hình.

Nguồn là bài giảng *Chẩn đoán và Điều trị Suy tim* của **GS. TS. Huỳnh Văn Minh**, do người dùng cung cấp từ bài Day 6. `data/corpus_manifest.json` lưu hash/cấu hình; `source_review.json` ghi tác giả, trang đầu và việc kiểm tra URL. URL lịch sử không còn phân giải DNS, đường dẫn tương tự trên miền mới trả HTML và không được coi là nguồn PDF mới. Không gán giấy phép mở cho tài liệu khi chưa có bằng chứng; quyền tác giả không được chuyển giao bởi repo code. Chỉ dùng/chia sẻ dữ liệu trong phạm vi được phép.

Xuất lại collection gốc (chỉ đọc, không thay index):

```bash
python starter/export_day6_to_day7.py --output /tmp/day7-export/chunks.json
```

Tái tạo trên Qdrant riêng bằng snapshot được phép sử dụng:

```bash
python starter/restore_index.py --collection day7-reproduced
# Sau đó đặt QDRANT_COLLECTION=day7-reproduced trong .env.
```

Script từ chối ghi đè collection tồn tại. Số chiều của Qdrant không tự chứng minh danh tính model; kiểm tra cấu hình ingest Day 6.

## Campaign v3 và lịch sử v2

Kết quả hiện tại: `starter/results/v3/`. Benchmark hiện tại: `data/benchmark_v3/`, dev **15+2**, test **5+2**. Dev được tái dùng; test hỏi các facts mới, tách trước chọn cấu hình. Runtime chỉ nhận câu hỏi/context, không nhận gold/expected answer/absence reason/nhãn.

V2 với model 3.5 đã chạm quota vẫn được giữ nguyên ở `starter/results/v2/` và báo cáo archive. Không lấy model demo để điền lại câu lỗi cũ. Code v2 tương ứng commit `74ff068`; v3 là campaign mới, chọn trên dev rồi mới chạy test mới.

Các cấu hình: TF-IDF, dense Qdrant, Hybrid RRF và hai cấu hình context mở rộng. Budget tính **ký tự gồm header**, chunk không vừa bị bỏ nguyên khối. Hybrid RRF k=60; mỗi nhánh lấy `max(10,top_k*3)` candidate. Context tích lũy giữ chunk cũ trước, nên vẫn có thể giữ nhiễu. Agent tối đa 3 lượt tìm; query gốc và query viết lại được lưu riêng.

## Kiểm thử và đọc kết quả

```bash
python -m unittest discover -s tests -v
```

Unit/HTTP tests dùng fixtures để kiểm tra hành vi code, không đo chất lượng model. Kiểm tra UI (demo đang chạy trước):

```bash
pip install -r requirements-dev.txt
python -m playwright install chromium
DEMO_URL=http://127.0.0.1:8502 python tests/browser_demo.py
```

Smoke test live riêng, có tiêu thụ quota:

```bash
python starter/test_agent_live.py --config lexical_context
python starter/test_qdrant_day7.py
```

Mỗi run agent có `run.json`, `traces.json`, `reviews.pending.json`, `reviews.json`, `summary.json`, `audit.json`. Nhãn hiện tại được AI hỗ trợ đọc nội dung và đối chiếu PDF gốc, có lý do/citation support từng câu; không tự nhận đã được con người chấm. Một ID citation hợp lệ không tự tạo ra điểm đúng. `audit.json` còn đếm từ chối theo nội dung, kể cả câu “tài liệu không nêu” có citation nhưng thực tế sai.

## Tái lập thí nghiệm

Các lệnh ghi output đã tồn tại sẽ bị từ chối. Giữ nguyên artifact công bố. Nếu muốn tái chạy, dùng bản sao làm việc riêng và chuyển `starter/results/v3` của bản sao vào thư mục lưu trữ cục bộ trước; không dùng kết quả test để chỉnh rồi tiếp tục coi chính test đó là độc lập.

```bash
python starter/run_retrieval_benchmark.py --split dev
python starter/run_agent_benchmark.py --split dev --configs baseline hybrid_context lexical_context
# Đọc từng câu trả lời/context/citation với PDF, ghi reviews.json có lý do.
python starter/review_report.py --run starter/results/v3/agent/dev/baseline
python starter/review_report.py --run starter/results/v3/agent/dev/hybrid_context
python starter/review_report.py --run starter/results/v3/agent/dev/lexical_context
python starter/select_config.py
# Ví dụ nếu selection.json đã chọn lexical_context:
python starter/run_retrieval_benchmark.py --split test --configs baseline lexical_context
python starter/run_agent_benchmark.py --split test --configs baseline lexical_context
# Đọc/chấm cả hai cấu hình test rồi tổng hợp:
python starter/review_report.py --run starter/results/v3/agent/test/baseline
python starter/review_report.py --run starter/results/v3/agent/test/lexical_context
python starter/build_report.py
```

`review_report.py` nạp `.env` cho cơ sở chi phí, kiểm tra đủ toàn bộ case, không tự chấm nội dung. `selection.json` khóa code/dữ liệu/model/collection/giả định billing và artifact dev, từ chối test nếu thay đổi. Tiêu chí: ít lỗi, điểm trả lời cao, abstention đúng, context đầy đủ, latency thấp. Nếu chỉnh pipeline bằng test thì tạo test mới.

## Chi phí và giới hạn

Lưu usage thực của mỗi phản hồi: input, output, thinking và tổng token. `GEMINI_BILLING_TIER=free|paid|unknown` là **giả định dùng để ước tính**, không xác minh hóa đơn. Với model 3.1 Flash-Lite, [pricing chính thức](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-flash-lite) có FreeTier miễn phí trong quota; standard tương đương input $0.25/M và output gồm thoughts $1.50/M. Summary báo cả chi phí biên theo tier và giá trị tương đương trả phí; không gán tổng máy/Qdrant hosting bằng $0. Tier unknown giữ chi phí null. Tài khoản của lần chạy có cơ sở FreeTier từ quota response đã lưu ở v2.

CER đánh giá context đã gửi, độc lập với việc answer API sau đó thành công hay lỗi. Lỗi hệ thống luôn báo riêng. Không tuyên bố kết quả một bộ test nhỏ bảo đảm đúng mọi câu hỏi hoặc tuyệt đối không hallucination. Phần bắt buộc tối đa 85 điểm; bonus 15 điểm có yêu cầu ≥100 trang/multimodal/benchmark riêng, không được tự cộng từ kết quả này.
