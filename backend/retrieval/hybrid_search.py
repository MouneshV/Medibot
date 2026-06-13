"""
MediBot Hybrid Search — Dense + BM25 with RBAC metadata filtering at the Qdrant level.
Uses Reciprocal Rank Fusion (RRF) to combine dense and sparse results.
"""

import logging
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchAny,
    Prefetch,
    FusionQuery,
    Fusion,
    SparseVector,
    QueryRequest,
)

from config import (
    QDRANT_URL,
    QDRANT_COLLECTION,
    EMBEDDING_MODEL,
    HYBRID_SEARCH_TOP_K,
)

logger = logging.getLogger(__name__)

# Module-level model singletons (loaded once)
_dense_model = None
_sparse_model = None
_qdrant_client = None


def _get_dense_model():
    global _dense_model
    if _dense_model is None:
        logger.info(f"Loading dense embedding model: {EMBEDDING_MODEL}")
        _dense_model = SentenceTransformer(EMBEDDING_MODEL)
    return _dense_model


def _get_sparse_model():
    global _sparse_model
    if _sparse_model is None:
        logger.info("Loading sparse BM25 model...")
        _sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
    return _sparse_model


def _get_qdrant_client():
    global _qdrant_client
    if _qdrant_client is None:
        try:
            _qdrant_client = QdrantClient(url=QDRANT_URL)
            _qdrant_client.get_collections()
        except Exception:
            logger.warning("Qdrant server not reachable. Using persistent local storage.")
            _qdrant_client = QdrantClient(path="./qdrant_storage")
    return _qdrant_client


def hybrid_search(query: str, user_role: str, top_k: int = HYBRID_SEARCH_TOP_K) -> list[dict]:
    """
    Perform hybrid search (dense + BM25) with RBAC filtering.

    The RBAC filter is applied at the Qdrant query level — restricted documents
    are NEVER returned, not filtered after the fact. This ensures that even
    adversarial prompts cannot surface unauthorized content.

    Args:
        query: The user's natural language question
        user_role: The authenticated user's role (e.g., 'doctor', 'nurse')
        top_k: Number of results to return

    Returns:
        List of dicts with 'text' and 'metadata' keys
    """
    client = _get_qdrant_client()
    dense_model = _get_dense_model()
    sparse_model = _get_sparse_model()

    # --- Generate query embeddings ---
    dense_query = dense_model.encode(query).tolist()

    sparse_result = list(sparse_model.query_embed(query))[0]
    sparse_query = SparseVector(
        indices=sparse_result.indices.tolist(),
        values=sparse_result.values.tolist(),
    )

    # --- RBAC Filter: Only return chunks accessible to this role ---
    rbac_filter = Filter(
        must=[
            FieldCondition(
                key="access_roles",
                match=MatchAny(any=[user_role]),
            )
        ]
    )

    # --- Hybrid query with RRF fusion ---
    try:
        results = client.query_points(
            collection_name=QDRANT_COLLECTION,
            prefetch=[
                Prefetch(
                    query=sparse_query,
                    using="bm25",
                    limit=top_k * 2,
                    filter=rbac_filter,
                ),
                Prefetch(
                    query=dense_query,
                    using="dense",
                    limit=top_k * 2,
                    filter=rbac_filter,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=top_k,
            with_payload=True,
        )
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        # Fallback: try dense-only search
        logger.info("Falling back to dense-only search...")
        results = client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=dense_query,
            using="dense",
            limit=top_k,
            query_filter=rbac_filter,
            with_payload=True,
        )

    # --- Format results ---
    search_results = []
    for point in results.points:
        payload = point.payload
        search_results.append({
            "text": payload.get("text", ""),
            "score": point.score,
            "metadata": {
                "source_document": payload.get("source_document", ""),
                "collection": payload.get("collection", ""),
                "access_roles": payload.get("access_roles", []),
                "section_title": payload.get("section_title", ""),
                "chunk_type": payload.get("chunk_type", "text"),
            },
        })

    logger.info(
        f"Hybrid search returned {len(search_results)} results "
        f"for role '{user_role}' (query: '{query[:50]}...')"
    )
    return search_results
