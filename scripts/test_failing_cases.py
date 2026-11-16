"""Kiểm tra thử nghiệm 5 câu multi-hop và chart bị miss trước đó với budget=15000."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_advanced_pipeline import AdvancedRetriever, AdvancedGeminiController, chunks, benchmark
from agentic import run_agent

target_ids = ["adv_test_15", "adv_test_17", "adv_test_18", "adv_test_19", "adv_test_21"]
test_cases = [q for q in benchmark if q["id"] in target_ids]

retriever = AdvancedRetriever(chunks)
controller = AdvancedGeminiController(model="gemini-3.1-flash-lite", max_searches=3)

for c in test_cases:
    print(f"\nTesting {c['id']} ({c['category']}): {c['question'][:70]}...")
    trace_events = []
    res = run_agent(
        question=c["question"],
        controller=controller,
        retriever=retriever,
        max_searches=3,
        top_k=6,
        budget=15000,
        trace_sink=trace_events
    )
    print(f"Status: {res['status']}")
    print(f"Answer: {res['answer'][:150]}")
    print(f"Citations: {res['citations']}")
