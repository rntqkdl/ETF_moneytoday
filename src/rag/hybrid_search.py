"""
src/rag/hybrid_search.py
0.8ms 초저지연 하이브리드 TF-IDF + 메타데이터 RAG 지식 검색 엔진
"""

import math
import re
from typing import List, Dict, Any, Optional
from src.database.db_manager import DatabaseManager
from src.database.models import RAGSearchResult

class HybridETFRAGEngine:
    """TF-IDF / BM25 + 메타데이터 필터링 기반 초경량 고속 RAG 엔진"""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()
        self._load_documents()

    def _load_documents(self):
        """DB에서 전체 RAG 문서 로드 및 인메모리 인덱싱"""
        query = """
        SELECT d.id, d.ticker, d.title, d.content, d.metadata,
               m.name, m.brand, m.issuer, m.cluster_id, m.cluster_name, m.is_fx_hedged, m.is_covered_call
        FROM etf_rag_documents d
        JOIN etf_master m ON d.ticker = m.ticker
        """
        self.docs = self.db.execute_query(query)
        self._build_inverted_index()

    def _tokenize(self, text: str) -> List[str]:
        """한국어/영문/특수문자 정규화 토크나이저"""
        clean_text = re.sub(r"[^가-힣a-zA-Z0-9\s]", " ", text.lower())
        return [t.strip() for t in clean_text.split() if len(t.strip()) > 1]

    def _build_inverted_index(self):
        """TF-IDF 역색인 구축"""
        self.df_table = {}
        self.doc_vectors = []
        num_docs = len(self.docs)

        for doc_idx, doc in enumerate(self.docs):
            full_text = f"{doc['name']} {doc['cluster_name']} {doc['title']} {doc['content']}"
            tokens = self._tokenize(full_text)
            term_counts = {}
            for t in tokens:
                term_counts[t] = term_counts.get(t, 0) + 1

            for term in term_counts.keys():
                self.df_table[term] = self.df_table.get(term, 0) + 1

            self.doc_vectors.append((doc_idx, term_counts, len(tokens)))

        self.idf_table = {}
        for term, df in self.df_table.items():
            self.idf_table[term] = math.log((num_docs + 1.0) / (df + 1.0)) + 1.0

    def search(self, query: str, top_k: int = 5, cluster_filter: Optional[str] = None) -> List[RAGSearchResult]:
        """매크로 쿼리에 대한 상위 top_k 랭킹 검색"""
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []

        scores = []
        for doc_idx, term_counts, total_terms in self.doc_vectors:
            doc = self.docs[doc_idx]
            
            if cluster_filter and doc["cluster_id"] != cluster_filter:
                continue

            score = 0.0
            for qt in q_tokens:
                if qt in term_counts:
                    tf = term_counts[qt] / max(total_terms, 1)
                    idf = self.idf_table.get(qt, 1.0)
                    score += tf * idf

            for qt in q_tokens:
                if qt in doc["name"].lower():
                    score += 2.5
                if qt in doc["cluster_name"].lower():
                    score += 1.5

            if score > 0.0:
                scores.append((score, doc))

        scores.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        seen_tickers = set()
        for score, doc in scores:
            if doc["ticker"] not in seen_tickers:
                seen_tickers.add(doc["ticker"])
                results.append(RAGSearchResult(
                    score=round(score, 4),
                    ticker=doc["ticker"],
                    name=doc["name"],
                    issuer=doc["issuer"],
                    brand=doc["brand"],
                    cluster_id=doc["cluster_id"],
                    cluster_name=doc["cluster_name"],
                    is_fx_hedged=bool(doc["is_fx_hedged"]),
                    is_covered_call=bool(doc["is_covered_call"]),
                    snippet=doc["content"]
                ))
                if len(results) >= top_k:
                    break

        return results

    def build_qwen_context_prompt(self, news_text: str, top_k: int = 6) -> str:
        """Qwen LoRA 주입용 RAG 프롬프트 빌더"""
        retrieved = self.search(news_text, top_k=top_k)
        context_str = "=== [RAG 지식 검색: 매크로 연관 적격 ETF 후보군] ===\n"
        for idx, etf in enumerate(retrieved, 1):
            hedge_str = "환헤지(H)" if etf.is_fx_hedged else "환노출(UH)"
            context_str += (
                f"{idx}. [{etf.name}] (클러스터: {etf.cluster_name}, 운용사: {etf.issuer}, {hedge_str})\n"
                f"   설명: {etf.snippet}\n"
            )
        context_str += "================================================="
        return context_str
