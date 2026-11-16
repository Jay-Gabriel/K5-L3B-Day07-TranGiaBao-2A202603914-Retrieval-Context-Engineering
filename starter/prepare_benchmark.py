"""Rebuild the versioned, authored benchmark; never derives questions from gold snippets."""
import argparse
from configs import ROOT, write_json, digest
from baseline import validate
import json
import re

# Each question asks a specific fact. Evidence boundaries retain verbatim PDF extraction.
DEV = [
('d01',2,0,'Theo phần dịch tễ học trong bài giảng, có bao nhiêu trường hợp suy tim mới xuất hiện mỗi năm?', '550.000 trường hợp mỗi năm.', '550,000', 'mỗi năm.'),
('d02',3,0,'Hai biểu hiện lâm sàng chính của suy tim được bài giảng nêu là gì?', 'Mệt và khó thở.', 'Biểu hiện lâm sàng chính', 'khó \nthở.'),
('d03',6,0,'Trong nhóm bệnh cơ tim do độc chất, tài liệu nêu hai chất gây nghiện nào?', 'Rượu và cocaine.', 'BCT do rượu', 'BCT do cocaine'),
('d04',7,0,'Bệnh cơ tim do stress còn được gọi bằng tên gì trong tài liệu?', 'Takotsubo.', 'Bệnh cơ tim do stress', '(Takotsubo)'),
('d05',8,0,'Hai thuốc ức chế calci nào được nêu trong danh sách thuốc có thể làm nặng suy tim?', 'Verapamil và diltiazen (cách viết trong tài liệu).', 'Ức chế calci', '(verapamil, diltiazen)'),
('d06',12,1,'Tài liệu yêu cầu những điều kiện nào để chẩn đoán suy tim tâm trương?', 'Triệu chứng cơ năng, triệu chứng thực thể, PXTM bảo tồn và chứng cứ bệnh cấu trúc cơ tim và/hoặc rối loạn chức năng tâm trương.', 'Chẩn đóan suy tim tâm trương', 'chức năng tâm trương'),
('d07',16,1,'Theo phân độ NYHA trong bài giảng, mức III được mô tả thế nào về vận động và triệu chứng khi nghỉ?', 'Hạn chế nhiều vận động; khỏe khi nghỉ nhưng chỉ vận động nhẹ đã có triệu chứng cơ năng.', 'III Hạn chế nhiều', 'triệu chứng cơ năng.'),
('d08',20,0,'Hai chất chỉ điểm sinh học mới giúp khảo sát tình trạng sợi hóa cơ tim được nêu là gì?', 'Soluble ST2 và galectin-3.', 'Chất chỉ điểm sinh học mới', 'tim \n•\u202fHiệu quả:'),
('d09',21,0,'Ngoài giảm tử vong, tài liệu nêu các mục tiêu điều trị suy tim nào?', 'Cải thiện triệu chứng, chất lượng cuộc sống, gắng sức; giảm nhập viện; phòng tăng tổn thương và giảm tái cấu trúc cơ tim.', 'Cải thiện triệu chứng', 'cấu trúc cơ tim'),
('d10',22,0,'Phần điều trị không thuốc liệt kê những thay đổi lối sống nào?', 'Giảm cân, ngưng thuốc lá, không uống rượu, bớt natri, tập thể dục và hạn chế nước khi suy tim nặng.', 'Thay đổi lối sống:', '(suy tim nặng)'),
('d11',23,0,'Trong mục tác dụng thuốc, ba loại giúp cải thiện triệu chứng được liệt kê là gì?', 'Lợi tiểu, digoxin liều thấp, nitrates.', 'Các thuốc cải thiện được triệu chứng:', 'Nitrates'),
('d12',24,0,'Theo slide ức chế men chuyển, creatinine được thử lại sau khoảng thời gian nào?', 'Sau 2 tuần.', 'Liều từ thấp đến cao-', '2 tuần sau'),
('d13',32,0,'Theo hướng dẫn cách dùng chẹn beta trong bài giảng, mục tiêu đạt liều đích trong bao nhiêu tuần?', '8–12 tuần.', 'Mục tiêu đạt liều đích', '8-12 tuần'),
('d14',40,0,'Trong chiến lược tối ưu điều trị nội, hai nhóm bệnh nhân nào được ví dụ là cần thăm khám thường xuyên và tăng liều chậm?', 'Người cao tuổi và bệnh nhân bệnh thận mạn.', 'Một số bệnh nhân', 'thường xuyên, tăng liều chậm'),
('d15',43,0,'Tại phần điều trị giai đoạn C, ba chẹn beta được nêu đích danh là gì?', 'Bisoprolol, carvedilol hoặc metoprolol succinate.', 'Một trong 3 chẹn bêta', 'succinate)'),
]
TEST = [
('t01',4,0,'Theo bảng phân loại EF trong bài giảng, HFpEF có EF từ bao nhiêu phần trăm trở lên?', 'EF ≥50%.', 'II. Suy  Tim với EF', '≥50%'),
('t02',19,1,'Đối với bệnh nhân ngoại trú, BNP hoặc NT-proBNP dùng lượng định độ nặng và tiên lượng được xếp loại khuyến cáo và mức chứng cứ nào?', 'Loại I, mức chứng cứ A.', 'Loại I:', '(MCC: A) \nLoại IIa'),
('t03',26,0,'Trong slide các chẹn thụ thể AG II, ba hoạt chất nào có khoảng liều lượng được liệt kê?', 'Candesartan, valsartan và losartan.', 'Candesartan', '100mg-150mg/ngày)'),
('t04',30,0,'Theo bảng lợi tiểu vòng, thời gian tác dụng của furosemide là bao nhiêu giờ?', '4–6 giờ.', 'Furosemide', '4-6 giờ'),
('t05',44,0,'Theo bài giảng, CHARM-Preserved có bao nhiêu bệnh nhân và candesartan có giảm có ý nghĩa tiêu chí chính không?', '3023 bệnh nhân; không giảm có ý nghĩa tiêu chí chính (tử vong tim mạch, suy tim).', 'Nghiên cứu CHARM-', 'vong tim mạch, suy tim)'),
]
ABSENT = [
('du01','dev','Tài liệu báo cáo kết quả thử nghiệm EMPEROR-Reduced với empagliflozin như thế nào?', 'Không có tên thử nghiệm EMPEROR-Reduced hoặc empagliflozin trong toàn văn; không suy luận kết quả thử nghiệm từ các thuốc cũ.'),
('du02','dev','Theo tài liệu, một lần tái khám suy tim ở Bệnh viện Đại học Y Dược Huế có giá bao nhiêu đồng?', 'Không có bảng viện phí, giá tái khám hay đơn vị tiền tệ cho dịch vụ này; kiểm tra toàn văn, không chỉ top-k.'),
('tu01','test','Trong tài liệu, DAPA-HF ghi nhận dapagliflozin giảm bao nhiêu phần trăm biến cố chính?', 'Toàn văn không có DAPA-HF hoặc dapagliflozin; không lấy số liệu thử nghiệm từ kiến thức ngoài.'),
('tu02','test','Tài liệu cho biết tỷ lệ suy tim toàn quốc Việt Nam năm 2025 là bao nhiêu?', 'Không có thống kê năm 2025. Các tỷ lệ dịch tễ cũ trong tài liệu không trả lời được câu hỏi có điều kiện thời gian này.'),
]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output', default=str(ROOT/'data'))
    args=parser.parse_args()
    chunks=json.loads((ROOT/'data/chunks.json').read_text())
    by_id={c['id']:c for c in chunks}; questions=[];cases=[]
    for split,rows in [('dev',DEV),('test',TEST)]:
        for cid,page,part,question,expected,start,end in rows:
            chunk=by_id[f'cme2._suy_timgs_minh_p{page}_para_{part}']
            text=chunk['text']
            pattern=lambda value: r'\s+'.join(re.escape(part) for part in value.split())
            first=re.search(pattern(start),text)
            if not first:raise ValueError(f'{cid}: missing evidence start')
            last=re.search(pattern(end),text[first.start():])
            if not last:raise ValueError(f'{cid}: missing evidence end')
            a=first.start();b=a+last.end()
            evidence=text[a:b]
            questions.append({'id':cid,'split':split,'question':question,'expected_answer':expected,
                'gold':[{'source_id':chunk['source_id'],'page':page,'evidence':evidence}]})
            cases.append({'id':cid,'split':split,'question':question,'answerable':True,'expected_behavior':'search_and_answer'})
    for cid,split,question,reason in ABSENT:
        cases.append({'id':cid,'split':split,'question':question,'answerable':False,
                      'expected_behavior':'search_and_abstain','absence_reason':reason})
    validate(chunks,questions)
    from pathlib import Path
    out=Path(args.output)
    write_json(out/'questions.json',questions);write_json(out/'cases.json',cases)
    write_json(out/'benchmark_manifest.json',{
        'version':'v2','created_at':'2026-11-16','source_pages':52,'chunks':len(chunks),
        'split_counts':{'dev':{'answerable':15,'unanswerable':2},'test':{'answerable':5,'unanswerable':2}},
        'history':'v1 test was inspected. v2 uses authored specific questions, separate answers by split, no metadata filters; test evaluated after dev freeze. Same source PDF reused.',
        'limitations':'Small benchmark, single historical document; prepared with AI assistance. Student must confirm labels and source permissions.',
        'questions_sha256':digest(out/'questions.json'),'cases_sha256':digest(out/'cases.json')})
    print('Prepared v2: 20 answerable, 4 unanswerable; evidence validates.')

if __name__=='__main__': main()
