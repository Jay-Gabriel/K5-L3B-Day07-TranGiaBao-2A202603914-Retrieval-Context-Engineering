"""Freeze complete, current and reviewed dev runs before test."""
import json
from datetime import datetime,timezone
from configs import RESULTS,ROOT,CONFIGS,load_data,write_json,digest
from run_agent_benchmark import fingerprints,runtime_settings
from summarize_reviews import summarize


def validate_dev_run(path):
    load=lambda name:json.loads((path/name).read_text())
    run=load('run.json');traces=load('traces.json');reviews=load('reviews.json');summary=load('summary.json')
    if run['fingerprints']!=fingerprints() or run.get('runtime_settings')!=runtime_settings():
        raise ValueError(f'{path.name}: stale pipeline/runtime')
    if run['config_name']!=path.name or run.get('config')!=CONFIGS[path.name] or run['model']!=runtime_settings()['model']:
        raise ValueError('Run model/config mismatch')
    _,_,cases=load_data();cases=[c for c in cases if c['split']=='dev'];expected={c['id']:c for c in cases}
    if len(traces)!=len(expected) or {t['query_id'] for t in traces}!=set(expected):
        raise ValueError('Incomplete/duplicate/extra dev traces')
    if len(reviews)!=len(expected) or {r['query_id'] for r in reviews}!=set(expected):
        raise ValueError('Incomplete/duplicate/extra dev reviews')
    for t in traces:
        if t['split']!='dev' or t['question']!=expected[t['query_id']]['question'] or t['config']!=CONFIGS[path.name] or t['model']!=run['model']:
            raise ValueError('Trace metadata differs from declared run')
    if summarize(cases,traces,reviews)!=summary:raise ValueError('Summary does not match reviewed labels')
    return summary


def main():
    if (RESULTS/'selection.json').exists():raise ValueError('Selection already frozen.')
    if (RESULTS/'agent/test').exists():raise ValueError('Test already exists; cannot choose a configuration now.')
    scores=[];artifacts={}
    for p in sorted((RESULTS/'agent/dev').glob('*/summary.json')):
        m=validate_dev_run(p.parent)
        key=(m['provider_errors'],-(m['grounded_answer']['mean'] or 0),
             -m['abstention']['n'],-m['pipeline_context_evidence']['n'],m['median_ms'])
        scores.append((key,p.parent.name,m))
        for filename in ('run.json','traces.json','reviews.json','summary.json'):
            artifact=p.parent/filename;artifacts[str(artifact.relative_to(ROOT))]=digest(artifact)
    if len(scores)<3:raise ValueError('Review baseline and at least two improvement configs on dev.')
    scores.sort();selected=scores[0][1]
    write_json(RESULTS/'selection.json',{'selected':selected,'config':CONFIGS[selected],
        'created_at':datetime.now(timezone.utc).isoformat(), 'split_used':'dev',
        'criterion':'Min errors; max audited grounded answer; max correct abstention; max sufficient context; min median latency.',
        'review_status':'Completed AI-assisted original-PDF/trace audit; reviewer provenance retained',
        'dev_ranking':[{'config':name,'sort_key':key} for key,name,_ in scores],
        'fingerprints':fingerprints(),'runtime_settings':runtime_settings(),'reviewed_artifacts':artifacts})
    print('Frozen from dev:',selected)

if __name__=='__main__':main()
