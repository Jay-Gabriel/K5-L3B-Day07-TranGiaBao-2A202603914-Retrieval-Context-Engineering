"""Render the report from reviewed results; no answer grading is performed here."""
import json
import sys
from pathlib import Path
from configs import ROOT,RESULTS,CONFIGS


def load(path):return json.loads(path.read_text())
def cell(value):return str(value).replace('|','\\|').replace('\n','<br>')
def ratio(n,N):return f'{n}/{N} ({100*n/N:.1f}%)' if N else '0/0 (không áp dụng)'
def frac(value):return ratio(value['n'],value['N'])


def main():
    selection=load(RESULTS/'selection.json');chosen=selection['selected']
    corp=load(ROOT/'data/corpus_manifest.json')
    names={'baseline':'TF-IDF baseline','dense':'Dense Qdrant','hybrid':'Hybrid RRF',
           'hybrid_context':'Hybrid mở rộng','lexical_context':'TF-IDF mở rộng'}
    lines=[
'# Báo cáo Day 7 — Agentic RAG',
'', '**Trần Gia Bảo — 2A202603914 — L3 — K5 VinUni AI20k**',
'', '> Trạng thái nhãn: AI hỗ trợ đọc trace, câu trả lời và đối chiếu PDF gốc; sinh viên chưa xác nhận (`student_verified: false`). Các điểm dưới đây là kết quả theo bộ nhãn này, không phải điểm chấm của giảng viên.',
'', '## Dữ liệu và benchmark',
'', f'- Bài giảng *Chẩn đoán và Điều trị Suy tim*, GS. TS. Huỳnh Văn Minh, file `data/cme2._suy_timgs_minh.pdf`: **{corp["pdf_pages"]} trang PDF, {corp["chunks"]} chunk**. Mỗi trang có tối đa hai slide; citation dùng trang PDF. Con số 46 trang trong báo cáo cũ là sai và đã được sửa.',
'- Nguồn file được dùng từ Day 6. URL gốc ứng viên được ghi ở `data/source_reference.json`; không truy cập được tại thời điểm kiểm tra nên chưa xác minh byte với nguồn web. Sinh viên cần xác nhận nguồn truy cập và quyền dùng/chia sẻ. Không khẳng định mục đích học tập tự cho phép phân phối.',
'- Qdrant Day 6: collection `rag_strategy_b`, 81 điểm, Cosine, 384 chiều; model `sentence-transformers/all-MiniLM-L6-v2` chạy bằng FastEmbed/ONNX. Đã đối chiếu cấu hình embedding trong code Day 6. Qdrant chỉ xác nhận kích thước và khoảng cách, không chứng minh danh tính embedding.',
'- `data/chunks.json` xuất trực tiếp payload Day 6. Bản trích lại trước đó có 5 chunk khác ranh giới/text; đã thay bằng payload gốc để không gán vector của nội dung này cho nội dung khác. Manifest lưu hash corpus và PDF. Không thay đổi index gốc.',
'- Benchmark **v2: 24 câu**, gồm dev 15 có đáp án + 2 thiếu bằng chứng; test 5 có đáp án + 2 thiếu bằng chứng. Bộ cũ có câu chứa nội dung công việc lẫn vào query và đã được xem, nên không dùng kết quả cũ làm đánh giá độc lập mới.',
'- V2 đặt câu hỏi cụ thể theo tài liệu, chia split trước khi chọn pipeline. Dev/test không hỏi lại cùng một đáp án; cùng corpus lịch sử vẫn được dùng. `questions.json` lưu đáp án/evidence; `cases.json` lưu cả câu thiếu evidence và lý do kiểm tra toàn văn. Không dùng filter section không có trong metadata.',
'- Evidence định lượng dùng source ID + trang + đoạn trích nguyên văn. Hit@1/Hit@3 và CER retrieval chấm khớp đoạn evidence trong chunk đúng trang. Chấm nội dung/context bằng đọc đối chiếu, không suy ra đáp án đúng chỉ từ ID citation.',
'', '## Retrieval và thử nghiệm',
'', 'So sánh trên cùng corpus, cùng câu hỏi và nhãn. Bảng dưới dùng **query gốc**, không trộn kết quả nhiều lượt tìm của agent. CER là tỷ lệ câu có đủ gold evidence trong context được đóng gói. Mẫu số chỉ gồm câu có đáp án.',
'', '| Cấu hình | Split | top-k / budget ký tự / candidate mỗi nhánh | Hit@1 | Evidence Hit@3 | CER retrieval | Trung vị retrieval |',
'|---|---|---|---|---|---|---|']
    for split,configs in [('dev',list(CONFIGS)),('test',['baseline',chosen])]:
        for name in configs:
            m=load(RESULTS/'retrieval'/split/name/'summary.json');config=CONFIGS[name]
            candidates=max(10,config['top_k']*3) if config['method']=='hybrid' else 'theo index'
            lines.append(f'| {names[name]} | {split} | {config["top_k"]} / {config["budget"]} / {candidates} | {ratio(m["hit1"],m["n"])} | {ratio(m["hit3"],m["n"])} | {ratio(m["context_hit"],m["n"])} | {m["median_ms"]:.2f} ms |')
    lines += [
'', 'TF-IDF dùng token Unicode NFC/casefold và cosine. Dense tạo query embedding tương thích Day 6 rồi gọi Qdrant. Hybrid hợp nhất ranking bằng RRF k=60, không cộng trực tiếp các score khác thang đo. Với top-k=3, mỗi nhánh Hybrid lấy 10 candidate; top-k=6 lấy 18, nên thứ hạng top-3 có thể khác giữa hai cấu hình Hybrid.',
'', 'Các giả thuyết được thử trên dev:',
'', '1. **Hybrid**: kết hợp dense và lexical có thể bổ sung ngữ nghĩa/từ khóa. Cấu hình 800 ký tự không vượt TF-IDF trên dev; không kết luận Hybrid luôn tốt hơn.',
'2. **Hybrid mở rộng**: top-k=6, context 6000 ký tự thay vì top-k=3/800 giúp giữ đoạn bị bỏ do budget; agent thật được chạy và chấm riêng. Có 1 lỗi Qdrant timeout, được báo riêng.',
'3. **TF-IDF mở rộng**: dùng lexical tốt hơn trên dev, tăng top-k/context để giảm mất evidence. Agent thật được chạy và chấm riêng; đây là cấu hình được chốt nếu thắng theo tiêu chí đã khai báo.',
'', '## Agent, context và đánh giá',
'', f'Model thật: **{selection["runtime_settings"]["model"]}**, temperature=0, native function calling `search`/`answer`. Model chọn query từ lượt đầu và có thể tìm tiếp, tối đa 3 lần. Runtime chỉ đưa question và history/context không chứa gold. Prompt không nêu đích danh các chủ đề dùng làm nhãn abstention trong benchmark.',
'', 'Context được tích lũy, loại ID trùng và giữ nguyên văn chunk; budget tính cả header nguồn. Chunk không vừa bị bỏ nguyên khối. Citation phải thuộc context; thiếu dấu citation trong câu được thêm đúng ID model đã chọn để chuẩn hóa định dạng, không tự tạo nguồn. ID ngoài corpus/context hoặc output sai giao thức là lỗi. Citation có ID hợp lệ vẫn cần kiểm tra hỗ trợ từng khẳng định.',
'', '| Cấu hình | Split | Tool use | Grounded 0/1/2; TB /2 | Citation hỗ trợ | Câu có citation | Abstention đúng | Từ chối nhầm | CER pipeline | Lỗi | Trung vị agent |',
'|---|---|---|---|---|---|---|---|---|---|---|']
    summaries={}
    for split,configs in [('dev',['baseline','hybrid_context','lexical_context']),('test',['baseline',chosen])]:
        for name in configs:
            m=load(RESULTS/'agent'/split/name/'summary.json');summaries[(split,name)]=m;g=m['grounded_answer']
            lines.append(f'| {names[name]} | {split} | {frac(m["tool_use"])} | {g["0"]}/{g["1"]}/{g["2"]}; {g["mean"]:.3f}/2 (N={g["N"]}) | {frac(m["citation_validity"])} | {frac(m["answer_citation_coverage"])} | {ratio(m["abstention"]["n"],2)} | {frac(m["false_abstention"])} | {frac(m["pipeline_context_evidence"])} | {m["provider_errors"]} | {m["median_ms"]/1000:.2f} s |')
    lines += ['', 'Abstention trong bảng dùng toàn bộ 2 câu thiếu bằng chứng của mỗi split, kể cả khi có lỗi. Tool use và mean grounded dùng các lần chạy thành công theo script cơ bản; số lỗi được báo riêng. CER pipeline dựa trên context cuối sau tất cả lượt tìm, khác CER của một lượt retrieval ở bảng trước. Lỗi provider được tách khỏi mean câu trả lời theo script cơ bản; CER pipeline vẫn dùng toàn bộ số câu có đáp án. Không loại lỗi khỏi báo cáo. Phân bố context 0/1/2 dưới đây không bao gồm lỗi hệ thống; N ghi toàn bộ câu có đáp án.',
'', '| Cấu hình / split | Context 0 / 1 / 2; N | Phân bố số lượt search (lượt:số câu) | Số lần gọi model TB | Token input / output / tổng |',
'|---|---|---|---|---|']
    for (split,name),m in summaries.items():
        c=m['context_review'];u=m['tokens']
        lines.append(f'| {names[name]} / {split} | {c["0"]} / {c["1"]} / {c["2"]}; N={c["N"]} | {cell(m["search_count_distribution"])} | {m["mean_model_calls"]:.2f} | {u["promptTokenCount"]} / {u["candidatesTokenCount"]} / {u["totalTokenCount"]} |')
    lines += [
'', 'Latency agent bao gồm model, retrieval, giãn nhịp 4,5 giây giữa request và retry hữu hạn; không đại diện thuần tốc độ inference. Lưu token usage thực của phản hồi nhận được. **Chi phí agent chưa được đo bằng hóa đơn: `null`, không khẳng định tổng $0.** Retrieval dùng embedding cục bộ; chi phí tài khoản/hosting Qdrant chưa được phân bổ.',
'', '## Chọn cấu hình trên dev và phân tích lỗi',
'', f'Đã chọn **{names[chosen]}** lúc `{selection["created_at"]}`, trước khi chạy test. Tiêu chí thứ tự: ít lỗi, grounded answer cao, abstention đúng cao, context đủ cao, latency thấp. `selection.json` lưu hash code/dữ liệu/runtime và run/trace/review/summary dev; runner từ chối test khi các bằng chứng này thay đổi. Không chọn Hybrid chỉ vì tên phương pháp phức tạp hơn.',
'', '- **Lỗi dev d01 — tìm đúng nhưng mất context:** TF-IDF đưa trang 2 lên đầu, nhưng chunk cùng header vượt budget 800 nên bị bỏ; context cuối chỉ còn trang 3, agent từ chối. TF-IDF mở rộng giữ được trang 2 và trả đúng 550.000/năm. Đây là lỗi đóng gói context, không phải lỗi thiếu tài liệu.',
'- **Lỗi dev d13 — bỏ đoạn chứa điều kiện:** baseline chỉ giữ para_1 trang 32, thiếu ô mục tiêu 8–12 tuần trong para_0. TF-IDF mở rộng giữ cả para_0 và trả đúng thời gian. Không coi đoạn cùng trang là evidence đủ nếu thiếu đúng điều kiện được hỏi.',
'- **Lỗi còn lại d15:** TF-IDF mở rộng vẫn không đưa ba tên chẹn beta giai đoạn C ở trang 43 vào context sau ba lượt; agent từ chối câu có đáp án. Không dùng test để sửa lỗi này. Hybrid mở rộng tìm được câu này, nhưng tổng chất lượng/thời gian/lỗi trên dev chưa thắng cấu hình chọn.',
'- **Giới hạn nhãn evidence:** t01 có một nguồn thay thế hợp lệ ở PDF trang 5 (HFpEF/Preserved EF ≥50%) dù gold ban đầu ở trang 4. Đã đối chiếu trang gốc và chấp nhận citation/context đó khi chấm nội dung. Giữ nguyên gold đã chốt; không sửa test để nâng metric khớp nguyên văn. Vì vậy CER định lượng có thể thấp hơn CER chấm nội dung.',
'- **Lỗi hệ thống:** Hybrid mở rộng d04 gặp `ResponseHandlingException` timeout của vector store. Trace còn giữ các bước đã chạy; không chuyển lỗi thành một câu từ chối đúng. Các thăm dò dev trước đó còn gặp 429 và lỗi định dạng citation; tóm tắt ở `dev_pilots.json`, không trộn vào lần chạy cuối.',
'', '**Giới hạn test do quota:** model benchmark chạm giới hạn 500 request/ngày/project/model của free tier. Baseline lỗi 1/7 case; cấu hình chọn lỗi 5/7 case. Mean của cấu hình chọn chỉ dựa trên 2 câu có đáp án chạy thành công, không thể coi là kết quả tốt trên toàn bộ test. Chưa có bằng chứng test ổn định để kết luận cấu hình chọn thắng baseline. Giữ nguyên toàn bộ lỗi, không chạy lại rồi chỉ chọn lần tốt.',
'', '## Từng câu test: baseline và cấu hình đã chọn',
'', 'Đã đọc cả 5 câu có đáp án và 2 câu thiếu bằng chứng cho mỗi cấu hình, chấm context, nội dung và citation với PDF. Bảng lấy **nguyên câu trả lời lưu trong trace**, không viết lại thành một câu trả lời đẹp hơn.',
'', '| Cấu hình | ID / câu hỏi | Câu trả lời thực tế | Nhãn và lý do |',
'|---|---|---|---|']
    for name in ['baseline',chosen]:
        path=RESULTS/'agent/test'/name
        reviews={r['query_id']:r for r in load(path/'reviews.json')}
        for t in load(path/'traces.json'):
            r=reviews[t['query_id']];grade='lỗi hệ thống' if t['status']=='error' else r.get('answer_grade','abstention: '+str(r.get('abstention_correct')))
            lines.append(f'| {names[name]} | {t["query_id"]}<br>{cell(t["question"])} | {cell(t['status']+': '+(t['answer'] or t.get('error','')))} | {grade}; context {r["context_grade"]}. {cell(r["reason"])} |')
    lines += [
'', '## Tái lập, trace và demo',
'', f'- Môi trường chạy ghi nhận: Python `{sys.version.split()[0]}`, Linux, dependencies pin trong `requirements.txt`. Cách cài/chạy: [RUN.md](../../RUN.md).',
'- Dữ liệu/nhãn: `data/chunks.json`, `questions.json`, `cases.json`, `benchmark_manifest.json`, `corpus_manifest.json`.',
'- Retrieval: `starter/results/v2/retrieval/{dev,test}/{config}/traces.json` và `summary.json`.',
'- Agent: `starter/results/v2/agent/{dev,test}/{config}/run.json`, `traces.json`, `reviews.pending.json`, `reviews.json`, `summary.json`. Mỗi citation có nhãn hỗ trợ và mỗi câu có lý do; nhãn AI không thay xác nhận của sinh viên.',
'- `starter/build_report.py` chỉ dựng báo cáo từ artifact đã chấm, không tự chấm điểm. Nếu sinh viên duyệt nhãn, lưu bản xác nhận riêng để không sửa các bằng chứng dev đã khóa; nếu thay đổi tiêu chí/lựa chọn từ test thì cần test mới.',
'- Demo: `python starter/web_demo/app.py`, http://127.0.0.1:8502. UI hiện câu hỏi nguyên bản, query thực mỗi lượt, đoạn nguyên văn ngay khi retrieval trả về, nhãn chỉ tìm được/đã gửi model/được trích dẫn và link đúng trang PDF. Không hardcode câu trả lời, nguồn hay điểm benchmark. Lỗi kết nối tách khỏi thiếu bằng chứng.',
'- Model demo riêng: `gemini-3.1-flash-lite`, hiển thị rõ trên UI; benchmark giữ `gemini-3.5-flash-lite`. Không trộn kết quả model demo vào test đã chốt.',
'- Kịch bản trình bày: [docs/DEMO.md](../../docs/DEMO.md). Unit test mock chỉ xác minh code. UI fixtures chỉ kiểm tra giao diện; live smoke được ghi riêng, không đưa vào điểm test.',
'', '## Giới hạn và phần nâng cao',
'', 'Bộ test nhỏ, một tài liệu lịch sử và có lỗi font/trích xuất; chưa chứng minh tổng quát hóa, chưa đánh giá đối kháng rộng và không thể bảo đảm không hallucination trên mọi câu hỏi. Context tích lũy ưu tiên chunk cũ có thể giữ nhiễu. Dense MiniLM thể hiện yếu hơn lexical trên dev tiếng Việt này; kết quả không chứng minh dense kém trên mọi corpus. Sinh viên còn cần duyệt nhãn và xác nhận nguồn/quyền tài liệu trước khi nộp/public.',
'', '**Không thực hiện bonus 15 điểm:** tài liệu 52 trang, chưa có index/benchmark multimodal 100 trang và bộ test nâng cao. Không dùng kết quả phần cơ bản để tuyên bố đạt ngưỡng bonus.',
'']
    output=ROOT/'report/individual/2A202603914_TranGiaBao.md'
    output.write_text('\n'.join(lines));print(output)

if __name__=='__main__':main()
