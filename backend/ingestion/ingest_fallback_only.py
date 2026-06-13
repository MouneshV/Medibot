"""
MediBot Ingestion Pipeline — FALLBACK MODE (No Docling)
Uses only PyMuPDF and pdfplumber for faster, simpler parsing.
Run this if Docling keeps failing due to Windows permissions.
"""

import os
import sys
import logging
from pathlib import Path
from uuid import uuid4

# Add parent dir to path
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
from ingestion.chunker import chunk_document

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def parse_pdf_fallback_only(file_path: Path) -> str:
    """Parse PDF using ONLY PyMuPDF, no Docling."""
    try:
        import fitz
        logger.info(f"  Parsing {file_path.name} with PyMuPDF...")
        doc = fitz.open(str(file_path))
        text = ""
        for page_num, page in enumerate(doc, 1):
            page_text = page.get_text()
            if page_text:
                text += f"--- PAGE {page_num} ---\n{page_text}\n\n"
        doc.close()
        return text
    except ImportError:
        logger.error("PyMuPDF not installed. Run: pip install PyMuPDF")
        raise


def parse_document_fallback(file_path: Path) -> str:
    """Parse document (PDF or Markdown)."""
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        return parse_pdf_fallback_only(file_path)
    elif ext in (".md", ".markdown"):
        return file_path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Unsupported format: {ext}")


def get_all_documents(data_dir: str) -> list[dict]:
    """Scan data directory for documents."""
    documents = []
    data_path = Path(data_dir)

    for collection_dir in sorted(data_path.iterdir()):
        if not collection_dir.is_dir():
            continue

        collection_name = collection_dir.name
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
    """Main ingestion pipeline (fallback mode)."""
    logger.info("=" * 60)
    logger.info("MediBot Ingestion Pipeline — FALLBACK MODE (No Docling)")
    logger.info("=" * 60)

    # Initialize models
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
    dense_model = SentenceTransformer(EMBEDDING_MODEL)
    embedding_dim = dense_model.get_sentence_embedding_dimension()
    logger.info(f"  Dense embedding dimension: {embedding_dim}")

    logger.info("Loading sparse BM25 model...")
    sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
    logger.info("  Sparse model loaded.")

    # Initialize Qdrant
    logger.info(f"Connecting to Qdrant at {QDRANT_URL}")
    try:
        client = QdrantClient(url=QDRANT_URL)
        client.get_collections()
        logger.info("  Connected to Qdrant server.")
    except Exception:
        logger.warning("  Qdrant server not reachable. Using persistent local storage.")
        client = QdrantClient(path="./qdrant_storage")

    # Recreate collection
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

    # Scan documents
    documents = get_all_documents(DATA_DIR)
    logger.info(f"\nFound {len(documents)} documents to ingest:")
    for doc in documents:
        logger.info(f"  [{doc['collection']}] {Path(doc['path']).name}")

    # Process documents
    all_chunks = []
    for i, doc_info in enumerate(documents, 1):
        logger.info(f"\n[{i}/{len(documents)}] Processing: {Path(doc_info['path']).name}")

        try:
            # Parse
            text = parse_document_fallback(Path(doc_info["path"]))

            # Chunk using fallback
            chunks = chunk_document(
                type('SimpleDoc', (), {'text': text, 'export_to_markdown': lambda: text, '_is_fallback': True})(),
                doc_info["path"],
                doc_info["collection"],
                doc_info["access_roles"],
            )
            all_chunks.extend(chunks)
            logger.info(f"  ✓ {len(chunks)} chunks generated")
        except Exception as e:
            logger.error(f"  ✗ Failed: {e}")
            continue

    logger.info(f"\nTotal chunks: {len(all_chunks)}")

    # Generate embeddings
    logger.info("Generating dense embeddings...")
    texts = [c["text"] for c in all_chunks]
    dense_embeddings = dense_model.encode(texts, show_progress_bar=True, batch_size=32)

    logger.info("Generating sparse BM25 embeddings...")
    sparse_embeddings_list = list(sparse_model.embed(texts, batch_size=32))

    # Upload to Qdrant
    logger.info("Uploading to Qdrant...")
    points = []
    for chunk, dense_emb, sparse_emb in zip(all_chunks, dense_embeddings, sparse_embeddings_list):
        points.append(
            PointStruct(
                id=str(uuid4()),
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
    logger.info(f"✓ Ingestion complete! {len(points)} chunks stored")
    logger.info(f"{'=' * 60}")

    return len(points)


if __name__ == "__main__":
    run_ingestion()
