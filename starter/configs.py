"""Shared experiment settings for CLI and demo."""
import hashlib
import os
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = os.getenv('DAY7_CAMPAIGN', 'v3')
if CAMPAIGN not in ('v2','v3'):raise ValueError('Unsupported campaign')
BENCHMARK_DIR = ROOT / 'data/benchmark_v3' if CAMPAIGN == 'v3' else ROOT / 'data'
RESULTS = ROOT / 'starter/results' / CAMPAIGN
CONFIGS = {
    'baseline': {'method': 'tfidf', 'top_k': 3, 'budget': 800, 'max_searches': 3},
    'dense': {'method': 'dense', 'top_k': 3, 'budget': 800, 'max_searches': 3},
    'hybrid': {'method': 'hybrid', 'top_k': 3, 'budget': 800, 'max_searches': 3},
    'hybrid_context': {'method': 'hybrid', 'top_k': 6, 'budget': 6000, 'max_searches': 3},
    'lexical_context': {'method': 'tfidf', 'top_k': 6, 'budget': 6000, 'max_searches': 3},
}

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_data():
    return (json.loads((ROOT/'data/chunks.json').read_text()),
            json.loads((BENCHMARK_DIR/'questions.json').read_text()),
            json.loads((BENCHMARK_DIR/'cases.json').read_text()))

def build_retrievers(chunks, methods):
    from retrievers import TfidfRetriever, QdrantDenseRetriever, HybridRrfRetriever
    out = {'tfidf': TfidfRetriever(chunks)}
    if set(methods) & {'dense', 'hybrid'}:
        out['dense'] = QdrantDenseRetriever(chunks)
    if 'hybrid' in methods:
        out['hybrid'] = HybridRrfRetriever(out['dense'], out['tfidf'])
    return out

def output_dir(root, split, config):
    if split not in ('dev', 'test') or config not in CONFIGS and config != 'tfidf':
        raise ValueError('split/config không hợp lệ')
    return Path(root) / split / config

def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
