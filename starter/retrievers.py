"""Các bộ truy xuất dữ liệu (Retrievers) cho Day 07:
1. TfidfRetriever (Lexical BM25/TF-IDF)
2. QdrantDenseRetriever (Dense Vector Store từ Day 06)
3. HybridRrfRetriever (Kết hợp Dense + Lexical qua Reciprocal Rank Fusion)
"""
import math
import os
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

# Nạp .env
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", unicodedata.normalize("NFC", text).casefold())


class TfidfRetriever:
    """Lexical Retrieval sử dụng TF-IDF chạy offline."""

    def __init__(self, chunks: list[dict[str, Any]]):
        self.chunks = chunks
        self.chunk_by_id = {c["id"]: c for c in chunks}
        counts = [Counter(tokenize(c["text"])) for c in chunks]
        df = Counter(term for row in counts for term in row)
        self.idf = {term: math.log((1 + len(chunks)) / (1 + count)) + 1 for term, count in df.items()}
        self.vectors = [self._vector(row) for row in counts]

    def _vector(self, counts: Counter) -> dict[str, float]:
        vector = {term: count * self.idf[term] for term, count in counts.items() if term in self.idf}
        norm = math.sqrt(sum(value * value for value in vector.values())) or 1.0
        return {term: value / norm for term, value in vector.items()}

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        query_vec = self._vector(Counter(tokenize(query)))
        results = []
        for chunk, vector in zip(self.chunks, self.vectors):
            if filters:
                meta = chunk.get("metadata", {})
                if not all(meta.get(k) == v for k, v in filters.items()):
                    continue
            score = sum(value * vector.get(term, 0.0) for term, value in query_vec.items())
            if score > 0:
                results.append({
                    "id": chunk["id"],
                    "text": chunk["text"],
                    "source_id": chunk["source_id"],
                    "source": chunk["source"],
                    "page": chunk["page"],
                    "metadata": chunk.get("metadata", {}),
                    "score": float(score),
                    "strategy": "tfidf"
                })
        return sorted(results, key=lambda c: (-c["score"], c["id"]))[:top_k]


class QdrantDenseRetriever:
    """Dense Retrieval kết nối trực tiếp với Qdrant Cloud từ Day 06."""

    def __init__(self, chunks: list[dict[str, Any]], collection_name: str | None = None, model_name: str | None = None):
        self.chunks = chunks
        self.chunk_by_id = {c["id"]: c for c in chunks}
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION", "rag_strategy_b")
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

        url = os.getenv("QDRANT_URL", "https://qdrant.vectorium.space")
        api_key = os.getenv("QDRANT_API_KEY")

        from qdrant_client import QdrantClient
        self.client = QdrantClient(
            url=url,
            port=443,
            api_key=api_key,
            prefer_grpc=False,
            https=True,
            timeout=10
        )

        from fastembed import TextEmbedding
        self.embed_model = TextEmbedding(model_name=self.model_name)

    def embed_query(self, query: str) -> list[float]:
        return list(self.embed_model.embed([query]))[0].tolist()

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        query_vector = self.embed_query(query)

        query_filter = None
        if filters:
            from qdrant_client.http import models as qmodels
            conditions = []
            for k, v in filters.items():
                conditions.append(qmodels.FieldCondition(key=k, match=qmodels.MatchValue(value=v)))
            if conditions:
                query_filter = qmodels.Filter(must=conditions)

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k
        )

        results = []
        for p in response.points:
            payload = p.payload or {}
            cid = payload.get("chunk_id", str(p.id))
            base = self.chunk_by_id.get(cid)
            if base:
                results.append({
                    **base,
                    "score": float(p.score),
                    "strategy": "qdrant_dense"
                })
            else:
                raise ValueError('Qdrant trả chunk không có trong corpus đã chốt; không gán nguồn hoặc trang mặc định.')
        return results[:top_k]


class HybridRrfRetriever:
    """Hybrid Retrieval kết hợp Dense + Lexical qua thuật toán Reciprocal Rank Fusion (RRF)."""

    def __init__(self, dense_retriever: QdrantDenseRetriever, tfidf_retriever: TfidfRetriever, rrf_k: int = 60):
        self.dense = dense_retriever
        self.tfidf = tfidf_retriever
        self.rrf_k = rrf_k

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        fetch_k = max(10, top_k * 3)
        dense_results = self.dense.search(query, filters=filters, top_k=fetch_k)
        tfidf_results = self.tfidf.search(query, filters=filters, top_k=fetch_k)

        all_candidates: dict[str, dict[str, Any]] = {}
        rrf_scores: Counter = Counter()

        # Tính rank dense
        for rank, item in enumerate(dense_results, start=1):
            cid = item["id"]
            all_candidates[cid] = item
            rrf_scores[cid] += 1.0 / (self.rrf_k + rank)

        # Tính rank tfidf
        for rank, item in enumerate(tfidf_results, start=1):
            cid = item["id"]
            if cid not in all_candidates:
                all_candidates[cid] = item
            rrf_scores[cid] += 1.0 / (self.rrf_k + rank)

        # Xếp hạng tổng hợp
        fused = []
        for cid, score in rrf_scores.most_common():
            cand = dict(all_candidates[cid])
            cand["score"] = float(score)
            cand["strategy"] = "hybrid_rrf"
            fused.append(cand)

        return fused[:top_k]
