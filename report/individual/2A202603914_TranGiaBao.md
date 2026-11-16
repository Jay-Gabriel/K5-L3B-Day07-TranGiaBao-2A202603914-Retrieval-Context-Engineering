# Báo cáo Day 7 — Agentic RAG

**Trần Gia Bảo — 2A202603914 — L3B — K5 VinUni AI20k**

> Trạng thái nhãn: AI hỗ trợ đọc trace, câu trả lời và đối chiếu PDF gốc; sinh viên chưa xác nhận (`student_verified: false`). Các điểm dưới đây là kết quả theo bộ nhãn này, không phải điểm chấm của giảng viên.

## Dữ liệu và benchmark

- Bài giảng *Chẩn đoán và Điều trị Suy tim*, GS. TS. Huỳnh Văn Minh, file `data/cme2._suy_timgs_minh.pdf`: **52 trang PDF, 81 chunk**. Mỗi trang có tối đa hai slide; citation dùng trang PDF. Con số 46 trang trong báo cáo cũ là sai và đã được sửa.
- Nguồn file được dùng từ Day 6. URL gốc ứng viên được ghi ở `data/source_reference.json`; không truy cập được tại thời điểm kiểm tra nên chưa xác minh byte với nguồn web. Sinh viên cần xác nhận nguồn truy cập và quyền dùng/chia sẻ. Không khẳng định mục đích học tập tự cho phép phân phối.
- Qdrant Day 6: collection `rag_strategy_b`, 81 điểm, Cosine, 384 chiều; model `sentence-transformers/all-MiniLM-L6-v2` chạy bằng FastEmbed/ONNX. Đã đối chiếu cấu hình embedding trong code Day 6. Qdrant chỉ xác nhận kích thước và khoảng cách, không chứng minh danh tính embedding.
- `data/chunks.json` xuất trực tiếp payload Day 6. Bản trích lại trước đó có 5 chunk khác ranh giới/text; đã thay bằng payload gốc để không gán vector của nội dung này cho nội dung khác. Manifest lưu hash corpus và PDF. Không thay đổi index gốc.
- Benchmark **v2: 24 câu**, gồm dev 15 có đáp án + 2 thiếu bằng chứng; test 5 có đáp án + 2 thiếu bằng chứng. Bộ cũ có câu chứa nội dung công việc lẫn vào query và đã được xem, nên không dùng kết quả cũ làm đánh giá độc lập mới.
- V2 đặt câu hỏi cụ thể theo tài liệu, chia split trước khi chọn pipeline. Dev/test không hỏi lại cùng một đáp án; cùng corpus lịch sử vẫn được dùng. `questions.json` lưu đáp án/evidence; `cases.json` lưu cả câu thiếu evidence và lý do kiểm tra toàn văn. Không dùng filter section không có trong metadata.
- Evidence định lượng dùng source ID + trang + đoạn trích nguyên văn. Hit@1/Hit@3 và CER retrieval chấm khớp đoạn evidence trong chunk đúng trang. Chấm nội dung/context bằng đọc đối chiếu, không suy ra đáp án đúng chỉ từ ID citation.

## Retrieval và thử nghiệm

So sánh trên cùng corpus, cùng câu hỏi và nhãn. Bảng dưới dùng **query gốc**, không trộn kết quả nhiều lượt tìm của agent. CER là tỷ lệ câu có đủ gold evidence trong context được đóng gói. Mẫu số chỉ gồm câu có đáp án.

| Cấu hình | Split | top-k / budget ký tự / candidate mỗi nhánh | Hit@1 | Evidence Hit@3 | CER retrieval | Trung vị retrieval |
|---|---|---|---|---|---|---|
| TF-IDF baseline | dev | 3 / 800 / theo index | 11/15 (73.3%) | 14/15 (93.3%) | 7/15 (46.7%) | 0.49 ms |
| Dense Qdrant | dev | 3 / 800 / theo index | 2/15 (13.3%) | 3/15 (20.0%) | 2/15 (13.3%) | 204.24 ms |
| Hybrid RRF | dev | 3 / 800 / 10 | 3/15 (20.0%) | 9/15 (60.0%) | 3/15 (20.0%) | 220.10 ms |
| Hybrid mở rộng | dev | 6 / 6000 / 18 | 3/15 (20.0%) | 5/15 (33.3%) | 9/15 (60.0%) | 210.12 ms |
| TF-IDF mở rộng | dev | 6 / 6000 / theo index | 11/15 (73.3%) | 14/15 (93.3%) | 14/15 (93.3%) | 0.62 ms |
| TF-IDF baseline | test | 3 / 800 / theo index | 4/5 (80.0%) | 5/5 (100.0%) | 2/5 (40.0%) | 0.26 ms |
| TF-IDF mở rộng | test | 6 / 6000 / theo index | 4/5 (80.0%) | 5/5 (100.0%) | 5/5 (100.0%) | 0.35 ms |

TF-IDF dùng token Unicode NFC/casefold và cosine. Dense tạo query embedding tương thích Day 6 rồi gọi Qdrant. Hybrid hợp nhất ranking bằng RRF k=60, không cộng trực tiếp các score khác thang đo. Với top-k=3, mỗi nhánh Hybrid lấy 10 candidate; top-k=6 lấy 18, nên thứ hạng top-3 có thể khác giữa hai cấu hình Hybrid.

Các giả thuyết được thử trên dev:

1. **Hybrid**: kết hợp dense và lexical có thể bổ sung ngữ nghĩa/từ khóa. Cấu hình 800 ký tự không vượt TF-IDF trên dev; không kết luận Hybrid luôn tốt hơn.
2. **Hybrid mở rộng**: top-k=6, context 6000 ký tự thay vì top-k=3/800 giúp giữ đoạn bị bỏ do budget; agent thật được chạy và chấm riêng. Có 1 lỗi Qdrant timeout, được báo riêng.
3. **TF-IDF mở rộng**: dùng lexical tốt hơn trên dev, tăng top-k/context để giảm mất evidence. Agent thật được chạy và chấm riêng; đây là cấu hình được chốt nếu thắng theo tiêu chí đã khai báo.

## Agent, context và đánh giá

Model thật: **gemini-3.5-flash-lite**, temperature=0, native function calling `search`/`answer`. Model chọn query từ lượt đầu và có thể tìm tiếp, tối đa 3 lần. Runtime chỉ đưa question và history/context không chứa gold. Prompt không nêu đích danh các chủ đề dùng làm nhãn abstention trong benchmark.

Context được tích lũy, loại ID trùng và giữ nguyên văn chunk; budget tính cả header nguồn. Chunk không vừa bị bỏ nguyên khối. Citation phải thuộc context; thiếu dấu citation trong câu được thêm đúng ID model đã chọn để chuẩn hóa định dạng, không tự tạo nguồn. ID ngoài corpus/context hoặc output sai giao thức là lỗi. Citation có ID hợp lệ vẫn cần kiểm tra hỗ trợ từng khẳng định.

| Cấu hình | Split | Tool use | Grounded 0/1/2; TB /2 | Citation hỗ trợ | Câu có citation | Abstention đúng | Từ chối nhầm | CER pipeline | Lỗi | Trung vị agent |
|---|---|---|---|---|---|---|---|---|---|---|
| TF-IDF baseline | dev | 17/17 (100.0%) | 8/0/7; 0.933/2 (N=15) | 7/7 (100.0%) | 7/7 (100.0%) | 2/2 (100.0%) | 8/15 (53.3%) | 7/15 (46.7%) | 0 | 17.61 s |
| Hybrid mở rộng | dev | 16/16 (100.0%) | 3/0/11; 1.571/2 (N=14) | 11/11 (100.0%) | 11/11 (100.0%) | 2/2 (100.0%) | 3/14 (21.4%) | 11/15 (73.3%) | 1 | 18.14 s |
| TF-IDF mở rộng | dev | 17/17 (100.0%) | 1/0/14; 1.867/2 (N=15) | 14/14 (100.0%) | 14/14 (100.0%) | 2/2 (100.0%) | 1/15 (6.7%) | 14/15 (93.3%) | 0 | 9.32 s |
| TF-IDF baseline | test | 6/6 (100.0%) | 2/0/3; 1.200/2 (N=5) | 3/3 (100.0%) | 3/3 (100.0%) | 1/2 (50.0%) | 2/5 (40.0%) | 3/5 (60.0%) | 1 | 17.56 s |
| TF-IDF mở rộng | test | 2/2 (100.0%) | 0/0/2; 2.000/2 (N=2) | 2/2 (100.0%) | 2/2 (100.0%) | 0/2 (0.0%) | 0/2 (0.0%) | 2/5 (40.0%) | 5 | 35.95 s |

Abstention trong bảng dùng toàn bộ 2 câu thiếu bằng chứng của mỗi split, kể cả khi có lỗi. Tool use và mean grounded dùng các lần chạy thành công theo script cơ bản; số lỗi được báo riêng. CER pipeline dựa trên context cuối sau tất cả lượt tìm, khác CER của một lượt retrieval ở bảng trước. Lỗi provider được tách khỏi mean câu trả lời theo script cơ bản; CER pipeline vẫn dùng toàn bộ số câu có đáp án. Không loại lỗi khỏi báo cáo. Phân bố context 0/1/2 dưới đây không bao gồm lỗi hệ thống; N ghi toàn bộ câu có đáp án.

| Cấu hình / split | Context 0 / 1 / 2; N | Phân bố số lượt search (lượt:số câu) | Số lần gọi model TB | Token input / output / tổng |
|---|---|---|---|---|
| TF-IDF baseline / dev | 4 / 4 / 7; N=15 | {'1': 6, '2': 1, '3': 10} | 3.24 | 36722 / 1965 / 38687 |
| Hybrid mở rộng / dev | 2 / 1 / 11; N=15 | {'1': 9, '2': 2, '3': 6} | 2.82 | 91415 / 2004 / 93419 |
| TF-IDF mở rộng / dev | 0 / 1 / 14; N=15 | {'1': 13, '2': 1, '3': 3} | 2.41 | 75882 / 2094 / 77976 |
| TF-IDF baseline / test | 2 / 0 / 3; N=5 | {'1': 3, '2': 1, '3': 3} | 2.86 | 12011 / 815 / 12826 |
| TF-IDF mở rộng / test | 0 / 0 / 2; N=5 | {'0': 4, '1': 3} | 0.71 | 6819 / 305 / 7124 |

Latency agent bao gồm model, retrieval, giãn nhịp 4,5 giây giữa request và retry hữu hạn; không đại diện thuần tốc độ inference. Lưu token usage thực của phản hồi nhận được. **Chi phí agent chưa được đo bằng hóa đơn: `null`, không khẳng định tổng $0.** Retrieval dùng embedding cục bộ; chi phí tài khoản/hosting Qdrant chưa được phân bổ.

## Chọn cấu hình trên dev và phân tích lỗi

Đã chọn **TF-IDF mở rộng** lúc `2026-11-16T03:50:18.019009+00:00`, trước khi chạy test. Tiêu chí thứ tự: ít lỗi, grounded answer cao, abstention đúng cao, context đủ cao, latency thấp. `selection.json` lưu hash code/dữ liệu/runtime và run/trace/review/summary dev; runner từ chối test khi các bằng chứng này thay đổi. Không chọn Hybrid chỉ vì tên phương pháp phức tạp hơn.

- **Lỗi dev d01 — tìm đúng nhưng mất context:** TF-IDF đưa trang 2 lên đầu, nhưng chunk cùng header vượt budget 800 nên bị bỏ; context cuối chỉ còn trang 3, agent từ chối. TF-IDF mở rộng giữ được trang 2 và trả đúng 550.000/năm. Đây là lỗi đóng gói context, không phải lỗi thiếu tài liệu.
- **Lỗi dev d13 — bỏ đoạn chứa điều kiện:** baseline chỉ giữ para_1 trang 32, thiếu ô mục tiêu 8–12 tuần trong para_0. TF-IDF mở rộng giữ cả para_0 và trả đúng thời gian. Không coi đoạn cùng trang là evidence đủ nếu thiếu đúng điều kiện được hỏi.
- **Lỗi còn lại d15:** TF-IDF mở rộng vẫn không đưa ba tên chẹn beta giai đoạn C ở trang 43 vào context sau ba lượt; agent từ chối câu có đáp án. Không dùng test để sửa lỗi này. Hybrid mở rộng tìm được câu này, nhưng tổng chất lượng/thời gian/lỗi trên dev chưa thắng cấu hình chọn.
- **Giới hạn nhãn evidence:** t01 có một nguồn thay thế hợp lệ ở PDF trang 5 (HFpEF/Preserved EF ≥50%) dù gold ban đầu ở trang 4. Đã đối chiếu trang gốc và chấp nhận citation/context đó khi chấm nội dung. Giữ nguyên gold đã chốt; không sửa test để nâng metric khớp nguyên văn. Vì vậy CER định lượng có thể thấp hơn CER chấm nội dung.
- **Lỗi hệ thống:** Hybrid mở rộng d04 gặp `ResponseHandlingException` timeout của vector store. Trace còn giữ các bước đã chạy; không chuyển lỗi thành một câu từ chối đúng. Các thăm dò dev trước đó còn gặp 429 và lỗi định dạng citation; tóm tắt ở `dev_pilots.json`, không trộn vào lần chạy cuối.

**Giới hạn test do quota:** model benchmark chạm giới hạn 500 request/ngày/project/model của free tier. Baseline lỗi 1/7 case; cấu hình chọn lỗi 5/7 case. Mean của cấu hình chọn chỉ dựa trên 2 câu có đáp án chạy thành công, không thể coi là kết quả tốt trên toàn bộ test. Chưa có bằng chứng test ổn định để kết luận cấu hình chọn thắng baseline. Giữ nguyên toàn bộ lỗi, không chạy lại rồi chỉ chọn lần tốt.

## Từng câu test: baseline và cấu hình đã chọn

Đã đọc cả 5 câu có đáp án và 2 câu thiếu bằng chứng cho mỗi cấu hình, chấm context, nội dung và citation với PDF. Bảng lấy **nguyên câu trả lời lưu trong trace**, không viết lại thành một câu trả lời đẹp hơn.

| Cấu hình | ID / câu hỏi | Câu trả lời thực tế | Nhãn và lý do |
|---|---|---|---|
| TF-IDF baseline | t01<br>Theo bảng phân loại EF trong bài giảng, HFpEF có EF từ bao nhiêu phần trăm trở lên? | answered: Theo bảng phân loại EF trong bài giảng, HFpEF (Preserved EF) có EF từ 50% trở lên [cme2._suy_timgs_minh_p5_para_0]. | 2; context 2. Đúng EF ≥50%. Citation trang 5 là evidence thay thế hợp lệ: bảng Preserved EF và bảng HFpEF gốc đã được kiểm tra; có trong context. Gold trang 4 không liệt kê nguồn thay thế này nên không sửa metric sau test. |
| TF-IDF baseline | t02<br>Đối với bệnh nhân ngoại trú, BNP hoặc NT-proBNP dùng lượng định độ nặng và tiên lượng được xếp loại khuyến cáo và mức chứng cứ nào? | answered: Đối với bệnh nhân ngoại trú, BNP hoặc NT-proBNP dùng lượng định độ nặng và tiên lượng được xếp loại khuyến cáo là Loại I, mức chứng cứ là A. [cme2._suy_timgs_minh_p19_para_1] | 2; context 2. Đúng Loại I và mức chứng cứ A cho BNP/NT-proBNP lượng định độ nặng/tiên lượng ở bệnh nhân NGOẠI TRÚ. Context và PDF trang 19 hỗ trợ đủ điều kiện. |
| TF-IDF baseline | t03<br>Trong slide các chẹn thụ thể AG II, ba hoạt chất nào có khoảng liều lượng được liệt kê? | answered: Trong slide các chẹn thụ thể AG II, ba hoạt chất có khoảng liều lượng được liệt kê là Candesartan (8mg-32 mg/ngày), Valsartan (80mg-320mg/ngày) và Losartan (100mg-150mg/ngày) [cme2._suy_timgs_minh_p26_para_0]. | 2; context 2. Đủ Candesartan/Valsartan/Losartan; các khoảng liều bổ sung cũng khớp nguyên bản và đúng mg/ngày. Citation/context trang 26 hỗ trợ toàn bộ. |
| TF-IDF baseline | t04<br>Theo bảng lợi tiểu vòng, thời gian tác dụng của furosemide là bao nhiêu giờ? | abstain: Không đủ bằng chứng để trả lời. | 0; context 0. Từ chối câu có đáp án. Context cuối trống, không có hàng Furosemide 4–6 giờ ở PDF trang 30. |
| TF-IDF baseline | t05<br>Theo bài giảng, CHARM-Preserved có bao nhiêu bệnh nhân và candesartan có giảm có ý nghĩa tiêu chí chính không? | abstain: Không đủ bằng chứng để trả lời. | 0; context 0. Từ chối câu có đáp án. Context chỉ có khuyến cáo trang 41, thiếu CHARM-Preserved 3023 bệnh nhân và kết quả tiêu chí chính ở trang 44. |
| TF-IDF baseline | tu01<br>Trong tài liệu, DAPA-HF ghi nhận dapagliflozin giảm bao nhiêu phần trăm biến cố chính? | abstain: Không đủ bằng chứng để trả lời. | abstention: True; context not_applicable. Từ chối không thêm số liệu DAPA-HF. Đã kiểm tra toàn văn của tài liệu lịch sử: không có DAPA-HF hoặc dapagliflozin. |
| TF-IDF baseline | tu02<br>Tài liệu cho biết tỷ lệ suy tim toàn quốc Việt Nam năm 2025 là bao nhiêu? | error: ConnectionError: Gemini HTTP 429; kiểm tra model, quota và API key. | lỗi hệ thống; context not_applicable. Lỗi Gemini HTTP 429 sau các bước tìm, không có câu trả lời. Không chấm là từ chối đúng; không thay lỗi bằng kết quả giả. |
| TF-IDF mở rộng | t01<br>Theo bảng phân loại EF trong bài giảng, HFpEF có EF từ bao nhiêu phần trăm trở lên? | error: ConnectionError: Gemini HTTP 429; kiểm tra model, quota và API key. | lỗi hệ thống; context 2. Lỗi Gemini HTTP 429 tại bước trả lời. Context đã chứa bảng HFpEF ≥50% trang 4 và trang 5 nhưng chưa có câu trả lời; không cho điểm nội dung. |
| TF-IDF mở rộng | t02<br>Đối với bệnh nhân ngoại trú, BNP hoặc NT-proBNP dùng lượng định độ nặng và tiên lượng được xếp loại khuyến cáo và mức chứng cứ nào? | error: ConnectionError: Gemini HTTP 429; kiểm tra model, quota và API key. | lỗi hệ thống; context 0. Lỗi Gemini HTTP 429 ngay lượt đầu, chưa gọi retrieval và không có context/answer. Ghi lỗi hệ thống, không diễn giải là câu hỏi thiếu bằng chứng. |
| TF-IDF mở rộng | t03<br>Trong slide các chẹn thụ thể AG II, ba hoạt chất nào có khoảng liều lượng được liệt kê? | answered: Ba hoạt chất được liệt kê khoảng liều lượng trong slide các chẹn thụ thể AG II là: Candesartan (8mg-32 mg/ngày), Valsartan (80mg-320mg/ngày) và Losartan (100mg-150mg/ngày). [cme2._suy_timgs_minh_p26_para_0] | 2; context 2. Đủ ba hoạt chất; mọi khoảng liều ghi thêm đúng nguyên bản. Citation trang 26 nằm trong context và hỗ trợ toàn câu trả lời. |
| TF-IDF mở rộng | t04<br>Theo bảng lợi tiểu vòng, thời gian tác dụng của furosemide là bao nhiêu giờ? | answered: Theo bảng lợi tiểu vòng, thời gian tác dụng của furosemide là 4-6 giờ [cme2._suy_timgs_minh_p30_para_0]. | 2; context 2. Đúng 4–6 giờ. Đối chiếu đúng hàng Furosemide và cột thời gian tác dụng ở bảng PDF trang 30, có trong context. |
| TF-IDF mở rộng | t05<br>Theo bài giảng, CHARM-Preserved có bao nhiêu bệnh nhân và candesartan có giảm có ý nghĩa tiêu chí chính không? | error: ConnectionError: Gemini HTTP 429; kiểm tra model, quota và API key. | lỗi hệ thống; context 0. Lỗi Gemini HTTP 429 ngay lượt đầu; chưa có retrieval/context/answer. Không loại case khỏi tổng test đã chạy. |
| TF-IDF mở rộng | tu01<br>Trong tài liệu, DAPA-HF ghi nhận dapagliflozin giảm bao nhiêu phần trăm biến cố chính? | error: ConnectionError: Gemini HTTP 429; kiểm tra model, quota và API key. | lỗi hệ thống; context not_applicable. Lỗi Gemini HTTP 429 ngay lượt đầu; không có hành vi từ chối để chấm đúng. |
| TF-IDF mở rộng | tu02<br>Tài liệu cho biết tỷ lệ suy tim toàn quốc Việt Nam năm 2025 là bao nhiêu? | error: ConnectionError: Gemini HTTP 429; kiểm tra model, quota và API key. | lỗi hệ thống; context not_applicable. Lỗi Gemini HTTP 429 ngay lượt đầu; không có hành vi từ chối để chấm đúng. |

## Tái lập, trace và demo

- Môi trường chạy ghi nhận: Python `3.14.3`, Linux, dependencies pin trong `requirements.txt`. Cách cài/chạy: [RUN.md](../../RUN.md).
- Dữ liệu/nhãn: `data/chunks.json`, `questions.json`, `cases.json`, `benchmark_manifest.json`, `corpus_manifest.json`.
- Retrieval: `starter/results/v2/retrieval/{dev,test}/{config}/traces.json` và `summary.json`.
- Agent: `starter/results/v2/agent/{dev,test}/{config}/run.json`, `traces.json`, `reviews.pending.json`, `reviews.json`, `summary.json`. Mỗi citation có nhãn hỗ trợ và mỗi câu có lý do; nhãn AI không thay xác nhận của sinh viên.
- `starter/build_report.py` chỉ dựng báo cáo từ artifact đã chấm, không tự chấm điểm. Nếu sinh viên duyệt nhãn, lưu bản xác nhận riêng để không sửa các bằng chứng dev đã khóa; nếu thay đổi tiêu chí/lựa chọn từ test thì cần test mới.
- Demo: `python starter/web_demo/app.py`, http://127.0.0.1:8502. UI hiện câu hỏi nguyên bản, query thực mỗi lượt, đoạn nguyên văn ngay khi retrieval trả về, nhãn chỉ tìm được/đã gửi model/được trích dẫn và link đúng trang PDF. Không hardcode câu trả lời, nguồn hay điểm benchmark. Lỗi kết nối tách khỏi thiếu bằng chứng.
- Model demo riêng: `gemini-3.1-flash-lite`, hiển thị rõ trên UI; benchmark giữ `gemini-3.5-flash-lite`. Không trộn kết quả model demo vào test đã chốt.
- Kịch bản trình bày: [docs/DEMO.md](../../docs/DEMO.md). Unit test mock chỉ xác minh code. UI fixtures chỉ kiểm tra giao diện; live smoke được ghi riêng, không đưa vào điểm test.

## Giới hạn và phần nâng cao

Bộ test nhỏ, một tài liệu lịch sử và có lỗi font/trích xuất; chưa chứng minh tổng quát hóa, chưa đánh giá đối kháng rộng và không thể bảo đảm không hallucination trên mọi câu hỏi. Context tích lũy ưu tiên chunk cũ có thể giữ nhiễu. Dense MiniLM thể hiện yếu hơn lexical trên dev tiếng Việt này; kết quả không chứng minh dense kém trên mọi corpus. Sinh viên còn cần duyệt nhãn và xác nhận nguồn/quyền tài liệu trước khi nộp/public.

**Không thực hiện bonus 15 điểm:** tài liệu 52 trang, chưa có index/benchmark multimodal 100 trang và bộ test nâng cao. Không dùng kết quả phần cơ bản để tuyên bố đạt ngưỡng bonus.
