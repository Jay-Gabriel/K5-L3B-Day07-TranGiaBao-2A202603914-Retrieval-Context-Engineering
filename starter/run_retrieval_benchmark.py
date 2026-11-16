"""Comparable original-query ranking; separate immutable dev/test outputs."""
import argparse
import statistics
import time
from pathlib import Path
from baseline import hit, pack_context, validate
from configs import BENCHMARK_DIR, CONFIGS, ROOT, RESULTS, build_retrievers, load_data, output_dir, write_json, digest


def evaluate_retriever(retriever, questions, budget=800, strategy_name='unknown', top_k=3):
    traces = []
    for q in questions:
        start = time.perf_counter()
        try:
            results = retriever.search(q['question'], filters=q.get('filter'), top_k=max(3, top_k))
            context, ids = pack_context(results[:top_k], budget)
            marked = [{**c, 'hit': hit(c, q['gold'])} for c in results]
            traces.append({'query_id': q['id'], 'split': q['split'], 'question': q['question'],
                'status': 'ok', 'results': marked, 'context': context, 'context_ids': ids,
                'context_chars': len(context), 'elapsed_ms': round((time.perf_counter()-start)*1000, 2),
                'hit1': bool(marked and marked[0]['hit']), 'hit3': any(c['hit'] for c in marked[:3]),
                'context_hit': any(c['hit'] and c['id'] in ids for c in marked)})
        except Exception as e:
            traces.append({'query_id': q['id'], 'status': 'error', 'error': str(e),
                           'hit1': False, 'hit3': False, 'context_hit': False,
                           'context_chars': 0, 'elapsed_ms': round((time.perf_counter()-start)*1000, 2)})
    n = len(traces)
    summary = {'strategy': strategy_name, 'split': questions[0]['split'], 'n': n,
               'top_k': top_k, 'budget_chars': budget, 'provider_errors': sum(t['status']=='error' for t in traces),
               'median_ms': statistics.median(t['elapsed_ms'] for t in traces),
               'service_cost_usd': 0, 'cost_note': 'Local embedding; Qdrant account/hosting cost not estimated.'}
    for key in ('hit1', 'hit3', 'context_hit'):
        summary[key] = sum(t[key] for t in traces)
        summary[key+'_rate'] = round(100*summary[key]/n, 2)
    return summary, traces


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--split', required=True, choices=('dev', 'test'))
    parser.add_argument('--configs', nargs='+', choices=list(CONFIGS), default=list(CONFIGS))
    parser.add_argument('--output', type=Path, default=RESULTS / 'retrieval')
    args = parser.parse_args()
    if args.split == 'test':
        from run_agent_benchmark import verify_selection
        verify_selection(args.configs)
    chunks, questions, _ = load_data()
    selected = [q for q in questions if q['split'] == args.split]
    validate(chunks, selected)
    for name in args.configs:
        if output_dir(args.output, args.split, name).exists():
            parser.error('Output đã tồn tại; chọn --output mới để giữ bằng chứng.')
    retrievers = build_retrievers(chunks, [CONFIGS[n]['method'] for n in args.configs])
    for name in args.configs:
        config = CONFIGS[name]
        summary, traces = evaluate_retriever(retrievers[config['method']], selected,
            budget=config['budget'], strategy_name=config['method'], top_k=config['top_k'])
        summary['config'] = config
        summary['corpus_sha256'] = digest(ROOT / 'data/chunks.json')
        summary['questions_sha256'] = digest(BENCHMARK_DIR/'questions.json')
        out = output_dir(args.output, args.split, name)
        write_json(out / 'summary.json', summary); write_json(out / 'traces.json', traces)
        print(name, summary, flush=True)

if __name__ == '__main__': main()
