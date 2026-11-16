"""Run the live agent without gold, then emit empty review forms for separate audit."""
import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from agentic import run_agent
from controller import GeminiController
from configs import BENCHMARK_DIR, CAMPAIGN, CONFIGS, ROOT, RESULTS, build_retrievers, load_data, output_dir, write_json, digest

FROZEN_FILES = ['starter/controller.py', 'starter/agentic.py', 'starter/retrievers.py',
                'starter/configs.py', 'starter/baseline.py', 'data/chunks.json',
                str((BENCHMARK_DIR/'questions.json').relative_to(ROOT)), str((BENCHMARK_DIR/'cases.json').relative_to(ROOT)), 'starter/costs.py', 'starter/run_agent_benchmark.py',
                'starter/run_retrieval_benchmark.py', 'starter/summarize_reviews.py', 'starter/select_config.py']


def runtime_settings():
    return {'campaign': CAMPAIGN, 'billing_tier_assumption':os.getenv('GEMINI_BILLING_TIER','unknown'), 'model': os.getenv('GEMINI_MODEL', 'gemini-3.1-flash-lite').removeprefix('models/'),
            'collection': os.getenv('QDRANT_COLLECTION', 'rag_strategy_b'),
            'embedding': os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')}


def fingerprints():
    return {name: digest(ROOT / name) for name in FROZEN_FILES}


def verify_selection(names):
    path = RESULTS / 'selection.json'
    if not path.exists():
        raise ValueError('Chốt selection.json trên dev trước khi chạy test.')
    selection = json.loads(path.read_text())
    if not set(names) <= {'baseline', selection['selected']}:
        raise ValueError('Test chỉ chạy baseline và cấu hình đã chốt.')
    if selection['fingerprints'] != fingerprints() or selection['runtime_settings'] != runtime_settings():
        raise ValueError('Pipeline/dữ liệu đã đổi sau khi chốt; cần bộ test mới nếu đã chạy test.')
    for path, expected in selection['reviewed_artifacts'].items():
        if digest(ROOT / path) != expected:
            raise ValueError('Dev artifact đã đổi sau khi chốt cấu hình.')
    return selection


def review_template(case, trace):
    review = {'query_id': case['id'], 'reviewer': None, 'review_type': 'pending',
              'reason': None, 'citation_support': [None for _ in trace['citations']],
              'context_grade': None if case['answerable'] else 'not_applicable', 'context_reason': None}
    if case['answerable']: review['answer_grade'] = None
    else: review['abstention_correct'] = None
    return review


def run_config(name, retriever, cases, out):
    config = CONFIGS[name]
    initial_fingerprints = fingerprints()
    initial_settings = runtime_settings()
    traces = []
    reviews = []
    for case in cases:
        controller = GeminiController(max_searches=config['max_searches'])
        start = time.perf_counter()
        trace = {'query_id': case['id'], 'question': case['question'], 'split': case['split'],
                 'model': controller.model, 'config_name': name, 'config': config, 'events': []}
        try:
            result = run_agent(case['question'], controller, retriever, filters=None,
                top_k=config['top_k'], budget=config['budget'], max_searches=config['max_searches'],
                trace_sink=trace['events'])
            trace.update(result)
        except Exception as e:
            trace.update(status='error', answer='', citations=[], error=f'{type(e).__name__}: {e}')
        trace['model_calls'] = controller.calls
        trace['elapsed_ms'] = round((time.perf_counter()-start)*1000, 2)
        trace['usage'] = {key: sum(call['usage'].get(key, 0) for call in controller.calls)
                          for key in ('promptTokenCount', 'candidatesTokenCount', 'thoughtsTokenCount', 'totalTokenCount')}
        from costs import estimate_cost
        trace.update(estimate_cost(trace['usage'], controller.model))
        traces.append(trace)
        reviews.append(review_template(case, trace))
        write_json(out / 'traces.json', traces)
        write_json(out / 'reviews.pending.json', reviews)
        print(name, case['id'], trace['status'], trace['elapsed_ms'], flush=True)
    if initial_fingerprints != fingerprints() or initial_settings != runtime_settings():
        raise ValueError('Pipeline đã thay đổi trong khi chạy; không dùng run này để chọn cấu hình.')
    write_json(out / 'run.json', {'created_at': datetime.now(timezone.utc).isoformat(),
        'config_name': name, 'config': config, 'cases': len(cases),
        'fingerprints': initial_fingerprints, 'runtime_settings': initial_settings, 'model': controller.model,
        'evaluation': 'pending separate content/citation/context review', 'cache': False})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--split', required=True, choices=('dev', 'test'))
    parser.add_argument('--configs', nargs='+', choices=list(CONFIGS), default=['baseline', 'hybrid', 'hybrid_context'])
    parser.add_argument('--output', type=Path, default=RESULTS / 'agent')
    args = parser.parse_args()
    if args.split == 'test': verify_selection(args.configs)
    chunks, _, cases = load_data()
    cases = [c for c in cases if c['split'] == args.split]
    for name in args.configs:
        if output_dir(args.output, args.split, name).exists():
            parser.error('Output đã tồn tại; chọn --output mới. Không ghi đè test.')
    retrievers = build_retrievers(chunks, [CONFIGS[n]['method'] for n in args.configs])
    for name in args.configs:
        run_config(name, retrievers[CONFIGS[name]['method']], cases, output_dir(args.output, args.split, name))

if __name__ == '__main__': main()
