"""
MediBot RAG Chain — Full pipeline: retrieve → rerank → generate with LLM.
"""

import logging
from groq import Groq

from config import GROQ_API_KEY, LLM_MODEL
from retrieval.hybrid_search import hybrid_search
from retrieval.reranker import rerank

logger = logging.getLogger(__name__)

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)


def rag_chain(question: str, user_role: str) -> dict:
    """
    Full RAG pipeline for document-based question answering.

    Steps:
    1. Hybrid retrieval with RBAC filtering
    2. Reranking to surface top-k most relevant chunks
    3. LLM generation with context

    Args:
        question: User's natural language question
        user_role: Authenticated user's role (for RBAC filtering)

    Returns:
        Dict with 'answer', 'sources', and 'retrieval_type'
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"RAG Chain: Question from {user_role}")
    logger.info(f"  Q: {question[:80]}...")

    # --- 1. Hybrid Search ---
    candidates = hybrid_search(question, user_role, top_k=10)

    if not candidates:
        logger.warning("No documents found for this query.")
        return {
            "answer": f"Sorry, I couldn't find any relevant information in the available documents for your role ({user_role}). "
                     f"This might be because: 1) The answer isn't in the knowledge base, or 2) You don't have access to the relevant documents.",
            "sources": [],
            "retrieval_type": "hybrid_rag",
        }

    logger.info(f"  → Retrieved {len(candidates)} candidates")

    # --- 2. Reranking ---
    reranked = rerank(question, candidates, top_k=3)
    logger.info(f"  → Reranked to {len(reranked)} top chunks")

    # --- 3. Prepare context ---
    context = "\n\n".join([
        f"[Document: {chunk['metadata']['source_document']} | Section: {chunk['metadata']['section_title']}]\n{chunk['text']}"
        for chunk in reranked
    ])

    # --- 4. Generate LLM Response ---
    system_prompt = """You are MediBot, an intelligent medical assistant for MediAssist Health Network.
You have access to a curated knowledge base of clinical protocols, nursing procedures, billing guides, and equipment manuals.

Guidelines:
- Answer questions based ONLY on the provided context.
- If the answer is not in the context, say "I don't have information about that in the knowledge base."
- Always cite the source document and section for your answer.
- Be concise and clinically accurate.
- For medical questions, prioritize safety and clarity."""

    user_message = f"""Question: {question}

Context from knowledge base:
{context}

Please answer the question based on the context provided above. Be concise and cite your sources."""

    logger.info("  → Calling LLM...")
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        max_tokens=1024,
    )

    answer = response.choices[0].message.content

    # --- 5. Format sources ---
    sources = [
        {
            "source_document": chunk["metadata"]["source_document"],
            "section_title": chunk["metadata"]["section_title"],
            "collection": chunk["metadata"]["collection"],
        }
        for chunk in reranked
    ]

    logger.info(f"  → LLM response: {answer[:100]}...")
    logger.info(f"{'='*60}\n")

    return {
        "answer": answer,
        "sources": sources,
        "retrieval_type": "hybrid_rag",
    }
