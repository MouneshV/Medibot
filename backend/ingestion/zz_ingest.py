"""
MediBot Ingestion Pipeline — Parse, chunk, embed, and store documents in Qdrant.
Supports both dense (sentence-transformers) and sparse (BM25) vectors for hybrid search.
"""

import os
import sys
import logging
from pathlib import Path
from uuid import uuid4

# *** CRITICAL: Disable HuggingFace symlinks BEFORE importing Docling ***
os.environ['HF_HUB_DISABLE_SYMLINK_WARNING'] = '1'
os.environ['HF_HUB_SYMLINK_MODE'] = 'hardlink'  # Windows-safe: use hardlinks
os.environ['DOCLING_DISABLE_CUDA'] = '1'  # Disable GPU to reduce complexity

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    SparseIndexParams,
    PointStruct,
    SparseVector,
)
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding

from config import (
    QDRANT_URL,
    QDRANT_COLLECTION,
    EMBEDDING_MODEL,
    DATA_DIR,
    COLLECTION_ACCESS_ROLES,
)
from ingestion.parser import parse_document
from ingestion.chunker import chunk_document

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def get_all_documents(data_dir: str) -> list[dict]:
    """
    Scan the data directory and return a list of documents with metadata.
    Each entry: {path, collection, access_roles}
    """
    documents = []
    data_path = Path(data_dir)

    for collection_dir in sorted(data_path.iterdir()):
        if not collection_dir.is_dir():
            continue

        collection_name = collection_dir.name

        # Skip the db folder (that's for SQL RAG)
        if collection_name == "db":
            continue

        access_roles = COLLECTION_ACCESS_ROLES.get(collection_name, [])
        if not access_roles:
            logger.warning(f"Unknown collection '{collection_name}', skipping.")
            continue

        for file_path in sorted(collection_dir.iterdir()):
            if file_path.suffix.lower() in (".pdf", ".md", ".markdown"):
                documents.append({
                    "path": str(file_path),
                    "collection": collection_name,
                    "access_roles": access_roles,
                })

    return documents


def run_ingestion():
    """
    Main ingestion pipeline:
    1. Scan data directory for documents
    2. Parse each document with Docling
    3. Chunk with HybridChunker
    4. Generate dense + sparse embeddings
    5. Store in Qdrant with metadata
    """
    logger.info("=" * 60)
    logger.info("MediBot Ingestion Pipeline — Starting")
    logger.info("=" * 60)

    # --- 1. Initialize models ---
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
    dense_model = SentenceTransformer(EMBEDDING_MODEL)
    embedding_dim = dense_model.get_sentence_embedding_dimension()
    logger.info(f"  Dense embedding dimension: {embedding_dim}")

    logger.info("Loading sparse BM25 model...")
    sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
    logger.info("  Sparse model loaded.")

    # --- 2. Initialize Qdrant ---
    logger.info(f"Connecting to Qdrant at {QDRANT_URL}")
    try:
        client = QdrantClient(url=QDRANT_URL)
        client.get_collections()  # Test connection
        logger.info("  Connected to Qdrant server.")
    except Exception:
        logger.warning("  Qdrant server not reachable. Using persistent local storage.")
        client = QdrantClient(path="./qdrant_storage")

    # Recreate collection (fresh ingestion)
    if client.collection_exists(QDRANT_COLLECTION):
        logger.info(f"  Deleting existing collection '{QDRANT_COLLECTION}'...")
        client.delete_collection(QDRANT_COLLECTION)

    logger.info(f"  Creating collection '{QDRANT_COLLECTION}' with hybrid vectors...")
    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config={
            "dense": VectorParams(
                size=embedding_dim,
                distance=Distance.COSINE,
            ),
        },
        sparse_vectors_config={
            "bm25": SparseVectorParams(
                index=SparseIndexParams(on_disk=False),
            ),
        },
    )

    # --- 3. Scan documents ---
    documents = get_all_documents(DATA_DIR)
    logger.info(f"\nFound {len(documents)} documents to ingest:")
    for doc in documents:
        logger.info(f"  [{doc['collection']}] {Path(doc['path']).name}")

    # --- 4. Process each document ---
    all_chunks = []
    for doc_info in documents:
        logger.info(f"\nProcessing: {Path(doc_info['path']).name}")

        # Parse
        parsed_doc = parse_document(doc_info["path"])

        # Chunk
        chunks = chunk_document(
            parsed_doc,
            doc_info["path"],
            doc_info["collection"],
            doc_info["access_roles"],
        )
        all_chunks.extend(chunks)

    logger.info(f"\nTotal chunks generated: {len(all_chunks)}")

    # --- 5. Generate embeddings and upload ---
    logger.info("Generating dense embeddings...")
    texts = [c["text"] for c in all_chunks]
    dense_embeddings = dense_model.encode(texts, show_progress_bar=True, batch_size=32)

    logger.info("Generating sparse BM25 embeddings...")
    sparse_embeddings_list = list(sparse_model.embed(texts, batch_size=32))

    logger.info("Uploading to Qdrant...")
    points = []
    for i, (chunk, dense_emb, sparse_emb) in enumerate(
        zip(all_chunks, dense_embeddings, sparse_embeddings_list)
    ):
        point_id = str(uuid4())
        points.append(
            PointStruct(
                id=point_id,
                vector={
                    "dense": dense_emb.tolist(),
                    "bm25": SparseVector(
                        indices=sparse_emb.indices.tolist(),
                        values=sparse_emb.values.tolist(),
                    ),
                },
                payload={
                    "text": chunk["text"],
                    **chunk["metadata"],
                },
            )
        )

    # Upload in batches
    BATCH_SIZE = 64
    for i in range(0, len(points), BATCH_SIZE):
        batch = points[i : i + BATCH_SIZE]
        client.upsert(collection_name=QDRANT_COLLECTION, points=batch)
        logger.info(f"  Uploaded batch {i // BATCH_SIZE + 1}/{(len(points) + BATCH_SIZE - 1) // BATCH_SIZE}")

    logger.info(f"\n{'=' * 60}")
    logger.info(f"Ingestion complete! {len(points)} chunks stored in '{QDRANT_COLLECTION}'")
    logger.info(f"{'=' * 60}")

    return len(points)


if __name__ == "__main__":
    run_ingestion()
