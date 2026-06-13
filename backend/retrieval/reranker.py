"""
MediBot Reranker — Cross-encoder reranking to surface the most relevant chunks.
Uses cross-encoder/ms-marco-MiniLM-L-6-v2 to jointly score (query, chunk) pairs.
"""

import logging
from sentence_transformers import CrossEncoder

from config import RERANKER_MODEL, RERANK_TOP_K

logger = logging.getLogger(__name__)

_reranker = None


def _get_reranker():
    global _reranker
    if _reranker is None:
        logger.info(f"Loading cross-encoder reranker: {RERANKER_MODEL}")
        _reranker = CrossEncoder(RERANKER_MODEL)
    return _reranker


def rerank(query: str, candidates: list[dict], top_k: int = RERANK_TOP_K) -> list[dict]:
    """
    Rerank candidate chunks using a cross-encoder model.

    The cross-encoder reads the query and each candidate chunk TOGETHER
    and assigns a joint relevance score. This is more accurate than
    independent embedding similarity.

    Args:
        query: The user's question
        candidates: List of dicts with 'text' and 'metadata' from hybrid search
        top_k: Number of top results to return after reranking

    Returns:
        Top-k reranked chunks sorted by relevance score
    """
    if not candidates:
        return []

    reranker = _get_reranker()

    # Create (query, chunk_text) pairs for the cross-encoder
    pairs = [(query, c["text"]) for c in candidates]

    # Score all pairs jointly
    scores = reranker.predict(pairs)

    # Attach scores to candidates
    for i, score in enumerate(scores):
        candidates[i]["rerank_score"] = float(score)

    # Sort by rerank score (descending) and take top-k
    ranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
    top_results = ranked[:top_k]

    logger.info(
        f"Reranked {len(candidates)} candidates → top-{top_k} "
        f"(best score: {top_results[0]['rerank_score']:.4f})"
    )

    return top_results
