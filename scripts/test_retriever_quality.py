"""Kiểm tra chất lượng retrieval với BM25 và lọc chunk ngắn."""
import json
import math
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "starter"))
from baseline import tokenize

with open(ROOT / "data/advanced/chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

with open(ROOT / "data/advanced/questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

# Lọc các chunk rác < 40 ký tự
clean_chunks = [c for c in chunks if len(c["text"].strip()) >= 35]
print(f"Tổng chunks gốc: {len(chunks)}, Chunks sau lọc: {len(clean_chunks)}")

class BM25Retriever:
    def __init__(self, chunks, k1=1.5, b=0.75):
        self.chunks = chunks
        self.doc_tokens = [tokenize(c["text"]) for c in chunks]
        self.doc_lens = [len(toks) for toks in self.doc_tokens]
        self.avgdl = sum(self.doc_lens) / len(self.doc_lens) if self.doc_lens else 1.0
        self.k1 = k1
        self.b = b

        df = Counter()
        for toks in self.doc_tokens:
            df.update(set(toks))
        N = len(chunks)
        self.idf = {term: math.log((N - freq + 0.5) / (freq + 0.5) + 1.0) for term, freq in df.items()}

    def search(self, query: str, top_k: int = 6):
        q_tokens = tokenize(query)
        scores = []
        for idx, (chunk, toks, dlen) in enumerate(zip(self.chunks, self.doc_tokens, self.doc_lens)):
            score = 0.0
            term_counts = Counter(toks)
            for q in q_tokens:
                if q in term_counts:
                    f = term_counts[q]
                    denom = f + self.k1 * (1.0 - self.b + self.b * (dlen / self.avgdl))
                    score += self.idf.get(q, 0.0) * (f * (self.k1 + 1.0)) / denom
            if score > 0:
                scores.append((score, chunk))
        scores.sort(key=lambda x: -x[0])
        return [c for s, c in scores[:top_k]]

retriever = BM25Retriever(clean_chunks)

dev_q = [q for q in questions if q["split"] == "dev" and q["gold"]]
hits = 0
for q in dev_q:
    results = retriever.search(q["question"], top_k=6)
    gold_pages = {g["page"] for g in q["gold"]}
    res_pages = {r["page"] for r in results}
    hit = bool(gold_pages.intersection(res_pages))
    if hit:
        hits += 1
    print(f"Q: {q['id']} ({q.get('category')}): Hit={hit} (Gold pages: {gold_pages}, Found: {res_pages})")

print(f"\nBM25 Retrieval Hit@6: {hits}/{len(dev_q)} ({hits/len(dev_q)*100:.1f}%)")
