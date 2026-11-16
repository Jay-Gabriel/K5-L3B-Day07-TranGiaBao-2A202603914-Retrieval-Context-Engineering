"""Kiểm tra BM25 trên 24 câu có đáp án của tập TEST."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from test_retriever_quality import BM25Retriever, clean_chunks

with open(ROOT / "data/advanced/questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

retriever = BM25Retriever(clean_chunks)
test_q = [q for q in questions if q["split"] == "test" and q["gold"]]

hits = 0
for q in test_q:
    results = retriever.search(q["question"], top_k=6)
    gold_pages = {g["page"] for g in q["gold"]}
    res_pages = {r["page"] for r in results}
    hit = bool(gold_pages.intersection(res_pages))
    if hit:
        hits += 1
    print(f"Test Q: {q['id']} ({q.get('category')}): Hit={hit} (Gold: {gold_pages}, Found: {res_pages})")

print(f"\nTest BM25 Retrieval Hit@6: {hits}/{len(test_q)} ({hits/len(test_q)*100:.1f}%)")
