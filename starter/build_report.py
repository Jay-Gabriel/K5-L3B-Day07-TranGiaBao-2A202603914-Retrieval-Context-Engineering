"""Build a report from explicit reviewed artifacts; never grade answers here."""
import json,sys
from pathlib import Path
from configs import ROOT,RESULTS,CONFIGS,BENCHMARK_DIR,CAMPAIGN


def load(path):return json.loads(path.read_text())
def cell(value):return str(value).replace('|','\\|').replace('\n','<br>')
def ratio(n,N):return f'{n}/{N} ({100*n/N:.1f}%)' if N else '0/0 (không áp dụng)'
def frac(value):return ratio(value['n'],value['N'])
LABELS={'baseline':'TF-IDF baseline','dense':'Dense Qdrant','hybrid':'Hybrid RRF','hybrid_context':'Hybrid mở rộng','lexical_context':'TF-IDF mở rộng'}


def main():
    selection=load(RESULTS/'selection.json');chosen=selection['selected'];corp=load(ROOT/'data/corpus_manifest.json')
    cases=load(BENCHMARK_DIR/'cases.json');model=selection['runtime_settings']['model']
    lines=['# Báo cáo Day 7 — Agentic RAG','', '**Trần Gia Bảo — 2A202603914 — L3B — K5 VinUni AI20k**','',
      '> Nhãn có nguồn gốc rõ: AI hỗ trợ đọc từng câu trả lời/context/citation và đối chiếu tài liệu gốc. Không tự suy ra chất lượng từ ID citation, không tự nhận sinh viên đã chấm hoặc giảng viên đã xác nhận điểm.',
      '', '## Dữ liệu, nguồn và benchmark','',
      f'Bài giảng **Chẩn đoán và Điều trị Suy tim**, GS. TS. Huỳnh Văn Minh: {corp["pdf_pages"]} trang PDF, {corp["chunks"]} chunk, hash PDF `{corp["pdf_sha256"]}`. Citation dùng trang PDF, không nhầm số slide in bên trong. Dữ liệu do người dùng cung cấp từ bài Day 6; tác giả/cơ quan được đối chiếu trên trang đầu. `data/source_review.json` ghi quá trình kiểm tra nguồn và quyền, không gán giấy phép Creative Commons/public domain khi chưa có bằng chứng.',
      'Nguồn lịch sử ở Sở Y tế Thừa Thiên Huế hiện không phân giải DNS. URL theo miền Huế mới trả HTML, không được coi là PDF thay thế. Giữ bản gốc có hash để người chấm đối chiếu; không khẳng định việc từng truy cập công khai đồng nghĩa được cấp phép phân phối.',
      '', 'Qdrant Day 6: collection `rag_strategy_b`, 81 điểm, 384 chiều, Cosine. Embedding `sentence-transformers/all-MiniLM-L6-v2` chạy FastEmbed/ONNX; danh tính model đối chiếu từ cấu hình ingest Day 6, không suy ra chỉ từ số chiều. Snapshot chunk giữ chính xác payload/ID/text của index, tránh lỗi đổi ranh giới chunk dưới vector cũ. Đường dẫn `source` lịch sử được giữ để tái lập; UI hiển thị tên file.',
      '', f'Campaign **{CAMPAIGN}** có **24 câu**: dev 15 có đáp án +2 thiếu bằng chứng; test mới 5 có đáp án +2 thiếu bằng chứng. Dùng dev để chọn model/cấu hình và tiêu chí trước khi chạy test. Câu test v3 hỏi các facts khác v2/dev; dữ liệu/evidence được khóa bằng hash. Không đưa gold, expected answer, absence reason hoặc nhãn vào model/retriever. Không dùng filter từ gold.',
      '', 'Kết quả v2 model Gemini 3.5 gặp quota vẫn nằm nguyên ở `starter/results/v2/` và báo cáo `archive/2A202603914_TranGiaBao_v2.md`; đó là lịch sử thực nghiệm, không thay lỗi bằng kết quả model khác. Campaign v3 bắt đầu lại trên dev với model mới rồi dùng test mới, không chọn cấu hình bằng test cũ.',
      '', '## So sánh retrieval trên query gốc','',
      '| Cấu hình | Split | top-k / budget ký tự / candidate mỗi nhánh | Hit@1 | Evidence Hit@3 | CER retrieval | Trung vị |',
      '|---|---|---|---|---|---|---|']
    for split,names in [('dev',list(CONFIGS)),('test',['baseline',chosen])]:
        for name in names:
            m=load(RESULTS/'retrieval'/split/name/'summary.json');c=CONFIGS[name]
            k=max(10,c['top_k']*3) if c['method']=='hybrid' else 'toàn index'
            lines.append(f'| {LABELS[name]} | {split} | {c["top_k"]} / {c["budget"]} / {k} | {ratio(m["hit1"],m["n"])} | {ratio(m["hit3"],m["n"])} | {ratio(m["context_hit"],m["n"])} | {m["median_ms"]:.2f} ms |')
    lines += ['', 'Hit định lượng yêu cầu source ID/trang/evidence nguyên văn trong một chunk. Mẫu số chỉ gồm câu có đáp án. Nguồn thay thế hợp lệ vẫn được chấm theo nội dung: ví dụ t32 baseline trích trang 16 trong khi gold ban đầu ở trang 15; giữ nguyên gold đã khóa, không sửa nhãn retrieval sau test để nâng điểm. TF-IDF dùng NFC/casefold và cosine; dense truy vấn vector tương thích Day 6; Hybrid dùng RRF k=60, không cộng score khác thang đo. Hybrid lấy 10 candidate mỗi nhánh khi top-k=3, 18 khi top-k=6, nên ranking top-3 có thể thay đổi theo tập candidate. CER retrieval đo context sau một lượt query gốc; không trộn với pipeline nhiều lượt của agent.',
      '', '## Agent và các thí nghiệm cải thiện','',
      f'Model thật **{model}**, temperature=0, native function calling `search`/`answer`. Model chọn query từ đầu và có thể tìm tiếp tối đa 3 lượt. Context tích lũy, deduplicate ID, giữ nguyên văn chunk và nguồn; budget là ký tự gồm header, chunk không vừa bị bỏ nguyên khối. Runtime kiểm tra citation thuộc context; định dạng thiếu [ID] được bổ sung đúng ID model đã chọn, không tạo nguồn mới. Output sai/citation lạ/provider timeout là lỗi riêng.',
      '', 'Ba cấu hình agent trên dev: baseline TF-IDF top-3/800; Hybrid top-6/6000 (giả thuyết fusion và mở rộng context giúp giữ evidence); TF-IDF top-6/6000 (giả thuyết lexical phù hợp corpus tiếng Việt này và budget lớn khắc phục bỏ chunk). Đây là hai cấu hình nhằm cải thiện baseline, mỗi cấu hình có kết quả riêng. Retrieval dev còn so sánh dense và Hybrid 800; không khẳng định mọi thử nghiệm đều cải thiện.',
      '', '| Cấu hình | Split | Tool use | Grounded 0/1/2; TB /2 | Citation hỗ trợ | Câu có citation | Abstention đúng | Từ chối nhầm | CER pipeline | Lỗi | Trung vị |',
      '|---|---|---|---|---|---|---|---|---|---|---|']
    summaries={}
    for split,names in [('dev',['baseline','hybrid_context','lexical_context']),('test',['baseline',chosen])]:
        for name in names:
            m=load(RESULTS/'agent'/split/name/'summary.json');summaries[(split,name)]=m;g=m['grounded_answer']
            audit=load(RESULTS/'agent'/split/name/'audit.json')
            unans=sum(c['split']==split and not c['answerable'] for c in cases)
            mean=f'{g["mean"]:.3f}' if g['mean'] is not None else 'N/A'
            lines.append(f'| {LABELS[name]} | {split} | {frac(m["tool_use"])} | {g["0"]}/{g["1"]}/{g["2"]}; {mean}/2 (N={g["N"]}) | {frac(m["citation_validity"])} | {frac(m["answer_citation_coverage"])} | {ratio(m["abstention"]["n"],unans)} | {frac(audit["semantic_false_abstention"])} | {frac(m["pipeline_context_evidence"])} | {m["provider_errors"]} | {m["median_ms"]/1000:.2f}s |')
    lines += ['', 'Từ chối nhầm được đọc theo nội dung nhãn `answer_refused`, gồm cả câu trả lời tuyên bố sai rằng tài liệu không có thông tin nhưng vẫn gắn citation. `summary.json` giữ thêm bộ đếm dựa trên runtime status để phân biệt. CER pipeline chấm đủ evidence trong context cuối đã gửi model, kể cả khi bước answer sau đó lỗi. Context 0=không có evidence, 1=có nhưng thiếu điều kiện/nguồn, 2=đủ evidence và nguồn. Câu lỗi trước retrieval có context 0. Lỗi được báo riêng; mean grounded/tool use theo các lần chạy thành công của script cơ bản, còn abstention ở bảng dùng toàn bộ câu thiếu bằng chứng.',
      '', '## Lượt gọi, context, token và chi phí','',
      '| Cấu hình / split | Context 0/1/2 | Search lượt:số câu | Gọi model TB | Input / output / thoughts token | API ước tính FreeTier | Tương đương trả phí |',
      '|---|---|---|---|---|---|---|']
    for (split,name),m in summaries.items():
        c=m['context_review'];u=m['tokens']
        lines.append(f'| {LABELS[name]} / {split} | {c["0"]}/{c["1"]}/{c["2"]} | {cell(m["search_count_distribution"])} | {m["mean_model_calls"]:.2f} | {u["promptTokenCount"]}/{u["candidatesTokenCount"]}/{u.get("thoughtsTokenCount",0)} | ${m["cost_usd"]:.6f} | ${m["paid_equivalent_usd"]:.6f} |')
    lines += ['', 'Nguồn: [Google Gemini API pricing — Gemini 3.1 Flash-Lite](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-flash-lite), kiểm tra 16/11/2026. Standard text input $0.25/triệu token, output gồm thinking $1.50/triệu; FreeTier miễn phí trong quota. `paid_equivalent_usd=(input×0.25+(output+thoughts)×1.50)/1e6`. Ước tính API theo cấu hình FreeTier dựa trên quota response của cùng project đã lưu, **không phải hóa đơn đã đối soát**. Không dùng Search grounding, caching hay batch có phụ phí. Chi phí máy cục bộ/Qdrant hosting chưa được phân bổ, không gán tổng hạ tầng là $0. Latency gồm API, retrieval, giãn nhịp 4.5 giây và retry.',
      '', '## Chốt trên dev và phân tích lỗi','',
      f'Chốt **{LABELS[chosen]}** lúc `{selection["created_at"]}`. Thứ tự tiêu chí công bố: ít lỗi, grounded cao, abstention đúng cao, context đủ cao, latency thấp. `selection.json` khóa code, benchmark, model, collection, billing assumption và hash trace/review/summary dev. Test chỉ chạy baseline và cấu hình chọn sau chốt, không chỉnh pipeline từ test.',
      '', 'Các lỗi dev được đọc theo trace và nguồn:',
      '- **d01 — ranking đúng nhưng context sai:** trang 2 có số trường hợp mới/năm; baseline budget 800 bỏ chunk vì header + text không vừa. So sánh trace cấu hình mở rộng để đo việc giữ evidence thay vì chỉ báo Hit@3.',
      '- **d13 — thiếu đúng điều kiện:** mục tiêu 8–12 tuần nằm trong para_0 trang 32; chỉ giữ para_1 cùng trang vẫn không đủ. So sánh context và điểm trả lời trước/sau mở budget.',
      '- **d15 — giới hạn lexical/context tích lũy:** query về ba chẹn beta giai đoạn C có thể xếp đoạn mô tả giai đoạn lên trước danh sách thuốc trang 43. Đánh giá theo trace v3 thực tế; không sửa query từ gold hoặc dùng câu test để chữa lỗi.',
      '', '| Dev ID | Cấu hình | Trạng thái / điểm | Nhận xét đối chiếu |', '|---|---|---|---|']
    for cid in ['d01','d13','d15']:
        for name in ['baseline','hybrid_context','lexical_context']:
            p=RESULTS/'agent/dev'/name;t=next(t for t in load(p/'traces.json') if t['query_id']==cid);r=next(r for r in load(p/'reviews.json') if r['query_id']==cid)
            lines.append(f'| {cid} | {LABELS[name]} | {t["status"]} / {r.get("answer_grade","N/A")} | {cell(r["reason"])} |')
    lines += ['', '## Đối chiếu từng câu test','', 'Bảng lấy nguyên câu trả lời và nhãn đã đọc, gồm đủ 5 câu có đáp án và 2 câu thiếu bằng chứng cho mỗi cấu hình. Chấm citation theo nội dung nó hỗ trợ trong context/PDF, không chỉ theo ID. Với câu thiếu bằng chứng, kiểm tra toàn tài liệu và hành vi trả lời, không kết luận chỉ từ top-k.',
      '', '| Cấu hình | ID / câu hỏi | Trạng thái / câu trả lời thật | Nhãn / lý do |', '|---|---|---|---|']
    for name in ['baseline',chosen]:
        p=RESULTS/'agent/test'/name;rs={r['query_id']:r for r in load(p/'reviews.json')}
        for t in load(p/'traces.json'):
            r=rs[t['query_id']];grade=r.get('answer_grade','abstention '+str(r.get('abstention_correct')))
            lines.append(f'| {LABELS[name]} | {t["query_id"]}<br>{cell(t["question"])} | {cell(t["status"]+": "+(t["answer"] or t.get("error","")))} | {grade}; context {r["context_grade"]}. {cell(r["reason"])} |')
    lines += ['', '## Tái lập và trình bày','',
      f'- Python {sys.version.split()[0]}, dependencies pin trong `requirements.txt`. [Cách chạy](../../RUN.md), [kịch bản demo](../../docs/DEMO.md).',
      '- Corpus và metadata: `data/chunks.json`, `corpus_manifest.json`, `source_review.json`. Benchmark v3: `data/benchmark_v3/{questions,cases,manifest}.json`.',
      '- Kết quả: `starter/results/v3/{retrieval,agent}/{dev,test}/{config}/`. Agent có run/trace/nhãn pending/nhãn đã chấm/summary; retrieval có ranking/context/metrics. `selection.json` là bằng chứng chọn trên dev. Code report chỉ tổng hợp nhãn, không tự chấm.',
      '- Demo cho thấy câu hỏi, query model chọn, đoạn lấy thật, đoạn đã gửi model và nguồn được citation; mở đúng trang PDF. Có câu được hỗ trợ, câu thiếu evidence và lỗi API riêng. Không hiển thị câu trả lời/citation giả khi API lỗi.',
      '- Unit/HTTP/UI tests kiểm tra code bằng fixtures, tách khỏi benchmark model thật. Không lấy điểm dev/demo thay test. GitHub repo cá nhân public cho phép người chấm đọc code/report.',
      '', '## Giới hạn và phạm vi hoàn thành','',
      'Bộ test nhỏ và một tài liệu lịch sử, có lỗi font/trích xuất; kết quả không chứng minh không hallucination trên mọi câu. Reranker/vision/OCR bảng chưa được đánh giá, context giữ chunk cũ có thể giữ nhiễu. Nhãn AI có lý do và nguồn để người khác kiểm tra; không tự nhận đánh giá độc lập bởi con người. Quyền tài liệu được ghi theo thông tin xác minh thực, không tự cấp giấy phép mới.',
      '', '**Phạm vi:** hoàn tất phần bắt buộc (rubric tối đa 85 điểm). Bonus 15 điểm cần tài liệu ≥100 trang, index multimodal và benchmark nâng cao riêng; không dùng số liệu phần cơ bản để tuyên bố đạt bonus hoặc bảo đảm giảng viên chấm 100/100.', '']
    out=ROOT/'report/individual/2A202603914_TranGiaBao.md';out.write_text('\n'.join(lines));print(out)

if __name__=='__main__':main()
