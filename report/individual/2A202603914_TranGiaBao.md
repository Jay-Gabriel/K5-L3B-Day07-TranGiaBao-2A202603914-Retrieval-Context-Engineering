# Báo cáo Day 7 — Agentic RAG

**Trần Gia Bảo — 2A202603914 — L3B — K5 VinUni AI20k**

> Nhãn có nguồn gốc rõ: AI hỗ trợ đọc từng câu trả lời/context/citation và đối chiếu tài liệu gốc. Không tự suy ra chất lượng từ ID citation, không tự nhận sinh viên đã chấm hoặc giảng viên đã xác nhận điểm.

## Dữ liệu, nguồn và benchmark

Bài giảng **Chẩn đoán và Điều trị Suy tim**, GS. TS. Huỳnh Văn Minh: 52 trang PDF, 81 chunk, hash PDF `8eb4ee61d23aa478a20ed3c126beb5cc5a23f965b48e12fe06ae1f9ba96f13a1`. Citation dùng trang PDF, không nhầm số slide in bên trong. Dữ liệu do người dùng cung cấp từ bài Day 6; tác giả/cơ quan được đối chiếu trên trang đầu. `data/source_review.json` ghi quá trình kiểm tra nguồn và quyền, không gán giấy phép Creative Commons/public domain khi chưa có bằng chứng.
Nguồn lịch sử ở Sở Y tế Thừa Thiên Huế hiện không phân giải DNS. URL theo miền Huế mới trả HTML, không được coi là PDF thay thế. Giữ bản gốc có hash để người chấm đối chiếu; không khẳng định việc từng truy cập công khai đồng nghĩa được cấp phép phân phối.

Qdrant Day 6: collection `rag_strategy_b`, 81 điểm, 384 chiều, Cosine. Embedding `sentence-transformers/all-MiniLM-L6-v2` chạy FastEmbed/ONNX; danh tính model đối chiếu từ cấu hình ingest Day 6, không suy ra chỉ từ số chiều. Snapshot chunk giữ chính xác payload/ID/text của index, tránh lỗi đổi ranh giới chunk dưới vector cũ. Đường dẫn `source` lịch sử được giữ để tái lập; UI hiển thị tên file.

Campaign **v3** có **24 câu**: dev 15 có đáp án +2 thiếu bằng chứng; test mới 5 có đáp án +2 thiếu bằng chứng. Dùng dev để chọn model/cấu hình và tiêu chí trước khi chạy test. Câu test v3 hỏi các facts khác v2/dev; dữ liệu/evidence được khóa bằng hash. Không đưa gold, expected answer, absence reason hoặc nhãn vào model/retriever. Không dùng filter từ gold.

Kết quả v2 model Gemini 3.5 gặp quota vẫn nằm nguyên ở `starter/results/v2/` và báo cáo `archive/2A202603914_TranGiaBao_v2.md`; đó là lịch sử thực nghiệm, không thay lỗi bằng kết quả model khác. Campaign v3 bắt đầu lại trên dev với model mới rồi dùng test mới, không chọn cấu hình bằng test cũ.

## So sánh retrieval trên query gốc

| Cấu hình | Split | top-k / budget ký tự / candidate mỗi nhánh | Hit@1 | Evidence Hit@3 | CER retrieval | Trung vị |
|---|---|---|---|---|---|---|
| TF-IDF baseline | dev | 3 / 800 / toàn index | 11/15 (73.3%) | 14/15 (93.3%) | 7/15 (46.7%) | 0.19 ms |
| Dense Qdrant | dev | 3 / 800 / toàn index | 2/15 (13.3%) | 3/15 (20.0%) | 2/15 (13.3%) | 786.31 ms |
| Hybrid RRF | dev | 3 / 800 / 10 | 3/15 (20.0%) | 9/15 (60.0%) | 3/15 (20.0%) | 1008.01 ms |
| Hybrid mở rộng | dev | 6 / 6000 / 18 | 3/15 (20.0%) | 5/15 (33.3%) | 9/15 (60.0%) | 717.06 ms |
| TF-IDF mở rộng | dev | 6 / 6000 / toàn index | 11/15 (73.3%) | 14/15 (93.3%) | 14/15 (93.3%) | 0.20 ms |
| TF-IDF baseline | test | 3 / 800 / toàn index | 4/5 (80.0%) | 5/5 (100.0%) | 0/5 (0.0%) | 0.20 ms |
| TF-IDF mở rộng | test | 6 / 6000 / toàn index | 4/5 (80.0%) | 5/5 (100.0%) | 5/5 (100.0%) | 0.22 ms |

Hit định lượng yêu cầu source ID/trang/evidence nguyên văn trong một chunk. Mẫu số chỉ gồm câu có đáp án. Nguồn thay thế hợp lệ vẫn được chấm theo nội dung: ví dụ t32 baseline trích trang 16 trong khi gold ban đầu ở trang 15; giữ nguyên gold đã khóa, không sửa nhãn retrieval sau test để nâng điểm. TF-IDF dùng NFC/casefold và cosine; dense truy vấn vector tương thích Day 6; Hybrid dùng RRF k=60, không cộng score khác thang đo. Hybrid lấy 10 candidate mỗi nhánh khi top-k=3, 18 khi top-k=6, nên ranking top-3 có thể thay đổi theo tập candidate. CER retrieval đo context sau một lượt query gốc; không trộn với pipeline nhiều lượt của agent.

## Agent và các thí nghiệm cải thiện

Model thật **gemini-3.1-flash-lite**, temperature=0, native function calling `search`/`answer`. Model chọn query từ đầu và có thể tìm tiếp tối đa 3 lượt. Context tích lũy, deduplicate ID, giữ nguyên văn chunk và nguồn; budget là ký tự gồm header, chunk không vừa bị bỏ nguyên khối. Runtime kiểm tra citation thuộc context; định dạng thiếu [ID] được bổ sung đúng ID model đã chọn, không tạo nguồn mới. Output sai/citation lạ/provider timeout là lỗi riêng.

Ba cấu hình agent trên dev: baseline TF-IDF top-3/800; Hybrid top-6/6000 (giả thuyết fusion và mở rộng context giúp giữ evidence); TF-IDF top-6/6000 (giả thuyết lexical phù hợp corpus tiếng Việt này và budget lớn khắc phục bỏ chunk). Đây là hai cấu hình nhằm cải thiện baseline, mỗi cấu hình có kết quả riêng. Retrieval dev còn so sánh dense và Hybrid 800; không khẳng định mọi thử nghiệm đều cải thiện.

| Cấu hình | Split | Tool use | Grounded 0/1/2; TB /2 | Citation hỗ trợ | Câu có citation | Abstention đúng | Từ chối nhầm | CER pipeline | Lỗi | Trung vị |
|---|---|---|---|---|---|---|---|---|---|---|
| TF-IDF baseline | dev | 17/17 (100.0%) | 8/0/7; 0.933/2 (N=15) | 7/9 (77.8%) | 9/9 (100.0%) | 2/2 (100.0%) | 8/15 (53.3%) | 7/15 (46.7%) | 0 | 12.06s |
| Hybrid mở rộng | dev | 17/17 (100.0%) | 4/0/11; 1.467/2 (N=15) | 11/12 (91.7%) | 12/12 (100.0%) | 2/2 (100.0%) | 4/15 (26.7%) | 11/15 (73.3%) | 0 | 12.43s |
| TF-IDF mở rộng | dev | 17/17 (100.0%) | 1/0/14; 1.867/2 (N=15) | 14/14 (100.0%) | 14/14 (100.0%) | 2/2 (100.0%) | 1/15 (6.7%) | 14/15 (93.3%) | 0 | 9.19s |
| TF-IDF baseline | test | 7/7 (100.0%) | 4/0/1; 0.400/2 (N=5) | 1/1 (100.0%) | 1/1 (100.0%) | 2/2 (100.0%) | 4/5 (80.0%) | 1/5 (20.0%) | 0 | 18.13s |
| TF-IDF mở rộng | test | 7/7 (100.0%) | 0/0/5; 2.000/2 (N=5) | 6/6 (100.0%) | 5/5 (100.0%) | 2/2 (100.0%) | 0/5 (0.0%) | 5/5 (100.0%) | 0 | 8.95s |

Từ chối nhầm được đọc theo nội dung nhãn `answer_refused`, gồm cả câu trả lời tuyên bố sai rằng tài liệu không có thông tin nhưng vẫn gắn citation. `summary.json` giữ thêm bộ đếm dựa trên runtime status để phân biệt. CER pipeline chấm đủ evidence trong context cuối đã gửi model, kể cả khi bước answer sau đó lỗi. Context 0=không có evidence, 1=có nhưng thiếu điều kiện/nguồn, 2=đủ evidence và nguồn. Câu lỗi trước retrieval có context 0. Lỗi được báo riêng; mean grounded/tool use theo các lần chạy thành công của script cơ bản, còn abstention ở bảng dùng toàn bộ câu thiếu bằng chứng.

## Lượt gọi, context, token và chi phí

| Cấu hình / split | Context 0/1/2 | Search lượt:số câu | Gọi model TB | Input / output / thoughts token | API ước tính FreeTier | Tương đương trả phí |
|---|---|---|---|---|---|---|
| TF-IDF baseline / dev | 6/2/7 | {'1': 8, '2': 2, '3': 7} | 2.94 | 33793/2072/0 | $0.000000 | $0.011556 |
| Hybrid mở rộng / dev | 3/1/11 | {'1': 11, '2': 2, '3': 4} | 2.59 | 78825/2085/0 | $0.000000 | $0.022834 |
| TF-IDF mở rộng / dev | 1/0/14 | {'1': 16, '3': 1} | 2.12 | 59688/2023/0 | $0.000000 | $0.017957 |
| TF-IDF baseline / test | 4/0/1 | {'1': 1, '3': 6} | 3.71 | 17243/844/0 | $0.000000 | $0.005577 |
| TF-IDF mở rộng / test | 0/0/5 | {'1': 7} | 2.00 | 22619/793/0 | $0.000000 | $0.006844 |

Nguồn: [Google Gemini API pricing — Gemini 3.1 Flash-Lite](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-flash-lite), kiểm tra 16/11/2026. Standard text input $0.25/triệu token, output gồm thinking $1.50/triệu; FreeTier miễn phí trong quota. `paid_equivalent_usd=(input×0.25+(output+thoughts)×1.50)/1e6`. Ước tính API theo cấu hình FreeTier dựa trên quota response của cùng project đã lưu, **không phải hóa đơn đã đối soát**. Không dùng Search grounding, caching hay batch có phụ phí. Chi phí máy cục bộ/Qdrant hosting chưa được phân bổ, không gán tổng hạ tầng là $0. Latency gồm API, retrieval, giãn nhịp 4.5 giây và retry.

## Chốt trên dev và phân tích lỗi

Chốt **TF-IDF mở rộng** lúc `2026-11-16T05:03:33.192426+00:00`. Thứ tự tiêu chí công bố: ít lỗi, grounded cao, abstention đúng cao, context đủ cao, latency thấp. `selection.json` khóa code, benchmark, model, collection, billing assumption và hash trace/review/summary dev. Test chỉ chạy baseline và cấu hình chọn sau chốt, không chỉnh pipeline từ test.

Các lỗi dev được đọc theo trace và nguồn:
- **d01 — ranking đúng nhưng context sai:** trang 2 có số trường hợp mới/năm; baseline budget 800 bỏ chunk vì header + text không vừa. So sánh trace cấu hình mở rộng để đo việc giữ evidence thay vì chỉ báo Hit@3.
- **d13 — thiếu đúng điều kiện:** mục tiêu 8–12 tuần nằm trong para_0 trang 32; chỉ giữ para_1 cùng trang vẫn không đủ. So sánh context và điểm trả lời trước/sau mở budget.
- **d15 — giới hạn lexical/context tích lũy:** query về ba chẹn beta giai đoạn C có thể xếp đoạn mô tả giai đoạn lên trước danh sách thuốc trang 43. Đánh giá theo trace v3 thực tế; không sửa query từ gold hoặc dùng câu test để chữa lỗi.

| Dev ID | Cấu hình | Trạng thái / điểm | Nhận xét đối chiếu |
|---|---|---|---|
| d01 | TF-IDF baseline | abstain / 0 | Incorrect abstention: original PDF p2 states 550,000 new cases each year. Final context is p3 definition/symptoms and contains no incidence count. |
| d01 | Hybrid mở rộng | answered / 2 | Correct: 550,000 new cases per year exactly matches original PDF p2 and the cited final-context incidence bullet. |
| d01 | TF-IDF mở rộng | answered / 2 | Correct: 550,000 new cases per year exactly matches original PDF p2 and the cited final-context incidence bullet. |
| d13 | TF-IDF baseline | answered / 0 | Incorrect document-wide absence claim: original PDF p32, visually inspected, explicitly gives a target-dose goal of 8–12 weeks. The cited fragment supports resuming titration after symptoms normalize, but does not support saying the document lacks a week count. |
| d13 | Hybrid mở rộng | answered / 2 | Correct: target dose within 8–12 weeks matches the original PDF p32 table, visually inspected, and the cited final-context row. |
| d13 | TF-IDF mở rộng | answered / 2 | Correct: target dose within 8–12 weeks matches the original PDF p32 table, visually inspected, and the cited final-context row. |
| d15 | TF-IDF baseline | abstain / 0 | Incorrect abstention: original PDF p43 stage-C slide names bisoprolol, carvedilol, and metoprolol succinate. |
| d15 | Hybrid mở rộng | answered / 2 | Correct: bisoprolol, carvedilol, and metoprolol succinate match original PDF p43 stage-C slide and cited passage. |
| d15 | TF-IDF mở rộng | abstain / 0 | Incorrect abstention: original PDF p43 stage-C slide names bisoprolol, carvedilol, and metoprolol succinate. |

## Đối chiếu từng câu test

Bảng lấy nguyên câu trả lời và nhãn đã đọc, gồm đủ 5 câu có đáp án và 2 câu thiếu bằng chứng cho mỗi cấu hình. Chấm citation theo nội dung nó hỗ trợ trong context/PDF, không chỉ theo ID. Với câu thiếu bằng chứng, kiểm tra toàn tài liệu và hành vi trả lời, không kết luận chỉ từ top-k.

| Cấu hình | ID / câu hỏi | Trạng thái / câu trả lời thật | Nhãn / lý do |
|---|---|---|---|
| TF-IDF baseline | t31<br>Theo phần dịch tễ học, tỷ lệ tử vong sau 5 năm của bệnh nhân suy tim được nêu là bao nhiêu? | abstain: Không đủ bằng chứng để trả lời. | 0; context 0. Incorrect abstention: original PDF p2 explicitly states five-year mortality reaches 50%. |
| TF-IDF baseline | t32<br>Theo sơ đồ ACC/AHA trong bài giảng, giai đoạn A được định nghĩa thế nào về nguy cơ, bệnh tim thực thể và triệu chứng? | answered: Theo sơ đồ ACC/AHA, giai đoạn A được định nghĩa là có nguy cơ cao suy tim, không có bệnh tim thực thể hoặc triệu chứng cơ năng suy tim [cme2._suy_timgs_minh_p16_para_0]. | 2; context 2. Correct: high risk of heart failure without structural heart disease or heart-failure symptoms matches original PDF p15/p16. The p16 alternative citation substantively supports all three elements; no unsupported added conditions. |
| TF-IDF baseline | t33<br>Trong bảng thuốc UCMC, tên biệt dược của captopril là gì? | abstain: Không đủ bằng chứng để trả lời. | 0; context 0. Incorrect abstention: original PDF p25 table identifies captopril as Capoten. |
| TF-IDF baseline | t34<br>Theo bảng lợi tiểu giữ kali, amiloride thải trừ qua cơ quan nào và có thời gian tác dụng bao nhiêu giờ? | abstain: Không đủ bằng chứng để trả lời. | 0; context 0. Incorrect abstention: original PDF p31 table gives amiloride renal elimination and 24-hour duration. |
| TF-IDF baseline | t35<br>Theo slide ghép tim, tỷ lệ sống còn sau 1 năm và sau 5 năm lần lượt là bao nhiêu? | abstain: Không đủ bằng chứng để trả lời. | 0; context 0. Incorrect abstention: original PDF p50 gives survival of 80–90% at one year and 70% at five years. |
| TF-IDF baseline | t3u1<br>Trong tài liệu, thử nghiệm VICTORIA cho thấy vericiguat cải thiện kết cục suy tim như thế nào? | abstain: Không đủ bằng chứng để trả lời. | abstention True; context not_applicable. Correct abstention. Independent all-52-page original-PDF text scan found zero VICTORIA or vericiguat mentions, consistent with the stored absence audit and document-scope review. Final drug/classification passages contain no trial result; do not infer modern trial outcomes from older treatments. |
| TF-IDF baseline | t3u2<br>Theo tài liệu, phối hợp warfarin với ginkgo biloba làm thay đổi INR bao nhiêu? | abstain: Không đủ bằng chứng để trả lời. | abstention True; context not_applicable. Correct abstention. Independent all-52-page original-PDF text scan found zero warfarin, ginkgo, biloba or INR mentions, consistent with stored absence audit and document-scope review. Final context gives no quantitative interaction evidence; an INR change cannot be derived from unrelated drug passages. |
| TF-IDF mở rộng | t31<br>Theo phần dịch tễ học, tỷ lệ tử vong sau 5 năm của bệnh nhân suy tim được nêu là bao nhiêu? | answered: Theo phần dịch tễ học, tỷ lệ tử vong sau 5 năm của bệnh nhân suy tim chiếm đến 50% [cme2._suy_timgs_minh_p2_para_0]. | 2; context 2. Correct: the answer preserves the original p2 wording that five-year mortality reaches 50%; cited final context explicitly gives this statistic. |
| TF-IDF mở rộng | t32<br>Theo sơ đồ ACC/AHA trong bài giảng, giai đoạn A được định nghĩa thế nào về nguy cơ, bệnh tim thực thể và triệu chứng? | answered: Theo sơ đồ ACC/AHA, giai đoạn A được định nghĩa là nhóm có nguy cơ cao suy tim, không có bệnh tim thực thể hoặc triệu chứng cơ năng suy tim [cme2._suy_timgs_minh_p15_para_1, cme2._suy_timgs_minh_p16_para_0]. [cme2._suy_timgs_minh_p15_para_1] [cme2._suy_timgs_minh_p16_para_0] | 2; context 2. Correct: high risk of heart failure without structural heart disease or heart-failure symptoms matches original PDF p15/p16. The p16 alternative citation substantively supports all three elements; no unsupported added conditions. Both p15 and p16 citations independently support this definition. |
| TF-IDF mở rộng | t33<br>Trong bảng thuốc UCMC, tên biệt dược của captopril là gì? | answered: Trong bảng thuốc UCMC, tên biệt dược của captopril là Capoten [cme2._suy_timgs_minh_p25_para_1]. | 2; context 2. Correct: Capoten is aligned with captopril in the original p25 ACE-inhibitor table, visually verified, and the cited final-context table. |
| TF-IDF mở rộng | t34<br>Theo bảng lợi tiểu giữ kali, amiloride thải trừ qua cơ quan nào và có thời gian tác dụng bao nhiêu giờ? | answered: Theo bảng lợi tiểu giữ kali, amiloride thải trừ qua thận và có thời gian tác dụng là 24 giờ [cme2._suy_timgs_minh_p31_para_0]. | 2; context 2. Correct: renal elimination and 24-hour duration both match the amiloride row in original PDF p31, visually verified, and cited final context. |
| TF-IDF mở rộng | t35<br>Theo slide ghép tim, tỷ lệ sống còn sau 1 năm và sau 5 năm lần lượt là bao nhiêu? | answered: Theo slide ghép tim, tỷ lệ sống còn sau 1 năm là 80% - 90% và sau 5 năm là 70% [cme2._suy_timgs_minh_p50_para_0]. | 2; context 2. Correct: one-year survival 80–90% and five-year survival 70% match original PDF p50 and cited context; both horizons and the range are preserved. |
| TF-IDF mở rộng | t3u1<br>Trong tài liệu, thử nghiệm VICTORIA cho thấy vericiguat cải thiện kết cục suy tim như thế nào? | abstain: Không đủ bằng chứng để trả lời. | abstention True; context not_applicable. Correct abstention. Independent all-52-page original-PDF text scan found zero VICTORIA or vericiguat mentions, consistent with the stored absence audit and document-scope review. Final drug/classification passages contain no trial result; do not infer modern trial outcomes from older treatments. |
| TF-IDF mở rộng | t3u2<br>Theo tài liệu, phối hợp warfarin với ginkgo biloba làm thay đổi INR bao nhiêu? | abstain: Không đủ bằng chứng để trả lời. | abstention True; context not_applicable. Correct abstention. Independent all-52-page original-PDF text scan found zero warfarin, ginkgo, biloba or INR mentions, consistent with stored absence audit and document-scope review. Final context gives no quantitative interaction evidence; an INR change cannot be derived from unrelated drug passages. |

## Tái lập và trình bày

- Python 3.14.3, dependencies pin trong `requirements.txt`. [Cách chạy](../../RUN.md), [kịch bản demo](../../docs/DEMO.md).
- Corpus và metadata: `data/chunks.json`, `corpus_manifest.json`, `source_review.json`. Benchmark v3: `data/benchmark_v3/{questions,cases,manifest}.json`.
- Kết quả: `starter/results/v3/{retrieval,agent}/{dev,test}/{config}/`. Agent có run/trace/nhãn pending/nhãn đã chấm/summary; retrieval có ranking/context/metrics. `selection.json` là bằng chứng chọn trên dev. Code report chỉ tổng hợp nhãn, không tự chấm.
- Demo cho thấy câu hỏi, query model chọn, đoạn lấy thật, đoạn đã gửi model và nguồn được citation; mở đúng trang PDF. Có câu được hỗ trợ, câu thiếu evidence và lỗi API riêng. Không hiển thị câu trả lời/citation giả khi API lỗi.
- Unit/HTTP/UI tests kiểm tra code bằng fixtures, tách khỏi benchmark model thật. Không lấy điểm dev/demo thay test. GitHub repo cá nhân public cho phép người chấm đọc code/report.

## Giới hạn và phạm vi hoàn thành

Bộ test nhỏ và một tài liệu lịch sử, có lỗi font/trích xuất; kết quả không chứng minh không hallucination trên mọi câu. Reranker/vision/OCR bảng chưa được đánh giá, context giữ chunk cũ có thể giữ nhiễu. Nhãn AI có lý do và nguồn để người khác kiểm tra; không tự nhận đánh giá độc lập bởi con người. Quyền tài liệu được ghi theo thông tin xác minh thực, không tự cấp giấy phép mới.

**Phạm vi:** hoàn tất phần bắt buộc (rubric tối đa 85 điểm). Bonus 15 điểm cần tài liệu ≥100 trang, index multimodal và benchmark nâng cao riêng; không dùng số liệu phần cơ bản để tuyên bố đạt bonus hoặc bảo đảm giảng viên chấm 100/100.
