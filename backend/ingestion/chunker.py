"""
MediBot Chunker — Hierarchical chunking with Docling HybridChunker,
with fallback to regex-based section chunking.
"""

import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def chunk_document(doc, file_path: str, collection: str, access_roles: list[str]) -> list[dict]:
    """
    Chunk a parsed document into structured chunks with metadata.

    Args:
        doc: Parsed document (Docling DoclingDocument or SimpleDocument fallback)
        file_path: Path to the original file
        collection: Collection name (e.g., 'clinical', 'billing')
        access_roles: List of roles permitted to access this document

    Returns:
        List of chunk dicts with text and metadata
    """
    filename = Path(file_path).name

    # Try Docling HybridChunker first
    if not getattr(doc, "_is_fallback", False):
        try:
            return _chunk_with_docling(doc, filename, collection, access_roles)
        except Exception as e:
            logger.warning(f"Docling chunking failed: {e}. Using fallback.")
            markdown = doc.export_to_markdown()
            return _chunk_with_fallback(markdown, filename, collection, access_roles)
    else:
        return _chunk_with_fallback(doc.text, filename, collection, access_roles)


def _chunk_with_docling(doc, filename: str, collection: str, access_roles: list[str]) -> list[dict]:
    """Chunk using Docling's HybridChunker for structure-aware splitting."""
    from docling_core.transforms.chunker import HybridChunker

    chunker = HybridChunker(
        tokenizer="sentence-transformers/all-MiniLM-L6-v2",
        max_tokens=512,
        merge_peers=True,
    )

    chunks = []
    for i, chunk in enumerate(chunker.chunk(doc)):
        # Extract section heading from chunk metadata
        headings = chunk.meta.headings if chunk.meta and chunk.meta.headings else []
        section_title = " > ".join(headings) if headings else "General"

        # Determine chunk type
        chunk_type = _classify_chunk_type(chunk.text, headings)

        # Prepend section heading as context
        text_with_context = f"[Section: {section_title}]\n{chunk.text}" if section_title != "General" else chunk.text

        chunks.append({
            "text": text_with_context,
            "metadata": {
                "source_document": filename,
                "collection": collection,
                "access_roles": access_roles,
                "section_title": section_title,
                "chunk_type": chunk_type,
                "chunk_index": i,
            },
        })

    logger.info(f"  → Chunked {filename} into {len(chunks)} chunks (Docling)")
    return chunks


def _chunk_with_fallback(text: str, filename: str, collection: str, access_roles: list[str]) -> list[dict]:
    """
    Fallback chunker: split by headings (Markdown-style) then by paragraph,
    with a max token limit per chunk.
    """
    MAX_CHUNK_CHARS = 1500  # ~375 tokens

    # Split by markdown headings
    sections = re.split(r'\n(?=#{1,4}\s)', text)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract heading
        heading_match = re.match(r'^(#{1,4})\s+(.+)', section)
        if heading_match:
            section_title = heading_match.group(2).strip()
            body = section[heading_match.end():].strip()
        else:
            section_title = "General"
            body = section

        # Split into sub-chunks if too long
        paragraphs = re.split(r'\n\n+', body)
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 2 > MAX_CHUNK_CHARS and current_chunk:
                chunks.append(_make_chunk(current_chunk, filename, collection, access_roles, section_title, len(chunks)))
                current_chunk = para
            else:
                current_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para

        if current_chunk:
            chunks.append(_make_chunk(current_chunk, filename, collection, access_roles, section_title, len(chunks)))

    # If no chunks were created (e.g., plain text without headings), chunk by size
    if not chunks:
        for i in range(0, len(text), MAX_CHUNK_CHARS):
            chunk_text = text[i:i + MAX_CHUNK_CHARS].strip()
            if chunk_text:
                chunks.append(_make_chunk(chunk_text, filename, collection, access_roles, "General", len(chunks)))

    logger.info(f"  → Chunked {filename} into {len(chunks)} chunks (fallback)")
    return chunks


def _make_chunk(text: str, filename: str, collection: str, access_roles: list[str],
                section_title: str, index: int) -> dict:
    """Create a chunk dict with metadata."""
    chunk_type = _classify_chunk_type(text, [section_title])

    # Prepend section heading as context
    text_with_context = f"[Section: {section_title}]\n{text}" if section_title != "General" else text

    return {
        "text": text_with_context,
        "metadata": {
            "source_document": filename,
            "collection": collection,
            "access_roles": access_roles,
            "section_title": section_title,
            "chunk_type": chunk_type,
            "chunk_index": index,
        },
    }


def _classify_chunk_type(text: str, headings: list[str]) -> str:
    """Classify chunk type based on content analysis."""
    # Check if it's a table (has pipe characters or tab-separated columns)
    lines = text.strip().split('\n')
    pipe_lines = sum(1 for line in lines if '|' in line and line.count('|') >= 2)
    if pipe_lines >= 2:
        return "table"

    # Check if it looks like code
    if text.strip().startswith('```') or '    ' in text[:50]:
        return "code"

    # Check if it's just a heading
    if len(text.strip()) < 100 and headings:
        return "heading"

    return "text"
