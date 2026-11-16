"""Authored v3 test; reuse dev and corpus, never reuse old test answers as new ones."""
import json,re
from datetime import datetime,timezone
from pathlib import Path
from baseline import validate
from configs import ROOT,write_json,digest

TEST=[
('t31',2,0,'Theo phần dịch tễ học, tỷ lệ tử vong sau 5 năm của bệnh nhân suy tim được nêu là bao nhiêu?', 'Đến 50%.', 'Tử vong 5 năm', '50%'),
('t32',15,1,'Theo sơ đồ ACC/AHA trong bài giảng, giai đoạn A được định nghĩa thế nào về nguy cơ, bệnh tim thực thể và triệu chứng?', 'Nguy cơ cao suy tim, không có bệnh tim thực thể hoặc triệu chứng cơ năng suy tim.', 'Giai đoạn A','cơ năng suy tim'),
('t33',25,1,'Trong bảng thuốc UCMC, tên biệt dược của captopril là gì?', 'Capoten.', 'Captopril','Capoten'),
('t34',31,0,'Theo bảng lợi tiểu giữ kali, amiloride thải trừ qua cơ quan nào và có thời gian tác dụng bao nhiêu giờ?', 'Thận; 24 giờ.', 'Amiloride','24 giờ'),
('t35',50,0,'Theo slide ghép tim, tỷ lệ sống còn sau 1 năm và sau 5 năm lần lượt là bao nhiêu?', 'Sau 1 năm 80–90%; sau 5 năm 70%.', 'Tỉ lệ sống còn:','70%'),
]
ABSENT=[
('t3u1','Trong tài liệu, thử nghiệm VICTORIA cho thấy vericiguat cải thiện kết cục suy tim như thế nào?', 'Đã kiểm tra toàn bộ text/PDF: không có VICTORIA hoặc vericiguat; không dùng kiến thức về thử nghiệm ngoài tài liệu.'),
('t3u2','Theo tài liệu, phối hợp warfarin với ginkgo biloba làm thay đổi INR bao nhiêu?', 'Không có ginkgo, biloba hoặc dữ liệu định lượng tương tác warfarin–ginkgo/INR trong toàn tài liệu; không suy đoán từ các thuốc được nhắc tới.')]


def main():
    out=ROOT/'data/benchmark_v3'
    if (out/'questions.json').exists():raise ValueError('v3 exists; never overwrite a published benchmark.')
    chunks=json.loads((ROOT/'data/chunks.json').read_text());by_id={c['id']:c for c in chunks}
    questions=[q for q in json.loads((ROOT/'data/questions.json').read_text()) if q['split']=='dev']
    cases=[c for c in json.loads((ROOT/'data/cases.json').read_text()) if c['split']=='dev']
    for cid,page,part,question,answer,start,end in TEST:
        chunk=by_id[f'cme2._suy_timgs_minh_p{page}_para_{part}'];text=chunk['text']
        pattern=lambda s:r'\s+'.join(re.escape(v) for v in s.split())
        a=re.search(pattern(start),text).start();b=a+re.search(pattern(end),text[a:]).end()
        questions.append({'id':cid,'split':'test','question':question,'expected_answer':answer,
            'gold':[{'source_id':chunk['source_id'],'page':page,'evidence':text[a:b]}]})
        cases.append({'id':cid,'split':'test','question':question,'answerable':True,'expected_behavior':'search_and_answer'})
    for cid,question,reason in ABSENT:
        cases.append({'id':cid,'split':'test','question':question,'answerable':False,'expected_behavior':'search_and_abstain','absence_reason':reason})
    validate(chunks,questions)
    write_json(out/'questions.json',questions);write_json(out/'cases.json',cases)
    write_json(out/'manifest.json',{'version':'v3','created_at':datetime.now(timezone.utc).isoformat(),
        'history':'v2 retained unmodified at starter/results/v2 and commit 74ff068. New model gemini-3.1-flash-lite will be selected on dev before v3 test. New test facts and questions differ from v2 and dev. No v3 test run before freeze.',
        'split_counts':{'dev':{'answerable':15,'unanswerable':2},'test':{'answerable':5,'unanswerable':2}},
        'questions_sha256':digest(out/'questions.json'),'cases_sha256':digest(out/'cases.json'),
        'corpus_sha256':digest(ROOT/'data/chunks.json'),'authorship':'AI-assisted question authoring and original-PDF evidence review.'})
    print('v3 prepared: unchanged 17 dev cases, 7 new test cases.')

if __name__=='__main__':main()
