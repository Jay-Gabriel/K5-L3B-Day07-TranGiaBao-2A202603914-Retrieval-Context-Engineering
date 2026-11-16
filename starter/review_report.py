"""Load local billing configuration, then aggregate explicitly completed review labels."""
import argparse,json
from pathlib import Path
from dotenv import load_dotenv
ROOT=Path(__file__).resolve().parents[1]
load_dotenv(ROOT/'.env')
from configs import load_data,write_json,digest
from summarize_reviews import summarize


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=Path);args=p.parse_args()
    load=lambda name:json.loads((args.run/name).read_text())
    traces=load('traces.json');reviews=load('reviews.json');run=load('run.json')
    _,_,all_cases=load_data();split=traces[0]['split'];cases=[c for c in all_cases if c['split']==split]
    expected={c['id'] for c in cases}
    if len(traces)!=len(expected) or {t['query_id'] for t in traces}!=expected:raise ValueError('Incomplete traces')
    if len(reviews)!=len(expected) or {r['query_id'] for r in reviews}!=expected:raise ValueError('Incomplete reviews')
    if run['cases']!=len(cases):raise ValueError('Incomplete run')
    write_json(args.run/'summary.json',summarize(cases,traces,reviews))
    answerable={c['id'] for c in cases if c['answerable']}
    relevant=[r for r in reviews if r['query_id'] in answerable]
    if any(type(r.get('answer_refused')) is not bool for r in relevant):raise ValueError('Need semantic refusal labels')
    write_json(args.run/'audit.json',{'reviews_sha256':digest(args.run/'reviews.json'),
        'semantic_false_abstention':{'n':sum(r['answer_refused'] for r in relevant),'N':len(answerable)},
        'note':'Semantic refusals read from answer content, including false document-wide absence with a citation; status-based false_abstention is retained separately in summary.json.'})
    print(args.run)

if __name__=='__main__':main()
