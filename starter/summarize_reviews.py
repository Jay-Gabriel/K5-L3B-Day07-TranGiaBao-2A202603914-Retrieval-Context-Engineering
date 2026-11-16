"""Aggregate explicit audit labels. Never infer answer quality from gold/citation IDs."""
import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from agent_metrics import aggregate
from configs import ROOT, write_json


def summarize(cases,traces,reviews):
    for review in reviews:
        if not review.get('reason') or not review.get('context_reason'):
            raise ValueError(f"{review['query_id']}: cần lý do chấm answer và context")
        if review.get('review_type') not in ('ai_assisted','human'):
            raise ValueError('Nêu rõ nguồn nhãn, không dùng nhãn tự sinh từ gold.')
        if type(review.get('student_verified')) is not bool:
            raise ValueError('Ghi rõ sinh viên đã duyệt nhãn hay chưa.')
    summary=aggregate(cases,traces,reviews)
    by_id={r['query_id']:r for r in reviews}
    answerable={c['id'] for c in cases if c['answerable']}
    counts=Counter()
    for t in traces:
        if t['query_id'] in answerable and t['status']!='error':
            grade=by_id[t['query_id']]['context_grade']
            if type(grade) is not int or grade not in (0,1,2):raise ValueError('context_grade must be 0..2')
            counts[str(grade)]+=1
    summary['context_review']={'0':counts['0'],'1':counts['1'],'2':counts['2'],'N':len(answerable)}
    summary['pipeline_context_evidence']={'n':counts['2'],'N':len(answerable)}
    dist=Counter(sum(e['event']=='search' for e in t['events']) for t in traces)
    summary['search_count_distribution']={str(k):v for k,v in sorted(dist.items())}
    summary['mean_model_calls']=statistics.mean(len(t['model_calls']) for t in traces)
    summary['median_ms']=statistics.median(t['elapsed_ms'] for t in traces)
    summary['tokens']={key:sum(t['usage'].get(key,0) for t in traces)
                      for key in ('promptTokenCount','candidatesTokenCount','totalTokenCount')}
    summary['cost_usd']=None
    summary['cost_note']='Token usage recorded. Account billing was not queried; no invented $0 total.'
    summary['review_note']='AI-assisted content and original-PDF audit; student verification pending.'
    summary['student_verified']=all(r['student_verified'] for r in reviews)
    return summary


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=Path);args=p.parse_args()
    load=lambda path:json.loads(path.read_text())
    traces=load(args.run/'traces.json');reviews=load(args.run/'reviews.json')
    run=load(args.run/'run.json')
    if not traces:raise ValueError('Trace rỗng')
    split=traces[0]['split']
    cases=[c for c in load(ROOT/'data/cases.json') if c['split']==split]
    expected={c['id'] for c in cases}
    if {t['query_id'] for t in traces}!=expected or len(traces)!=len(expected):
        raise ValueError('Run chưa đủ toàn bộ câu hỏi của split; không thu nhỏ mẫu số.')
    if {r['query_id'] for r in reviews}!=expected or len(reviews)!=len(expected):
        raise ValueError('Nhãn thiếu/trùng/thừa câu hỏi.')
    write_json(args.run/'summary.json',summarize(cases,traces,reviews))
    print(args.run)

if __name__=='__main__':main()
