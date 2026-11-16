"""Shared experiment settings for CLI and demo."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'starter/results/v2'
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
    return tuple(json.loads((ROOT / 'data' / name).read_text())
                 for name in ('chunks.json', 'questions.json', 'cases.json'))

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
