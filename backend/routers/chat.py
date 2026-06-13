"""
MediBot Chat Router — Main RAG endpoint with routing to hybrid or SQL RAG.
"""

import logging
import re
from fastapi import APIRouter, HTTPException, Security
from fastapi.security import HTTPBearer

from auth import get_current_user
from models import ChatRequest, ChatResponse
from retrieval.rag_chain import rag_chain
from retrieval.sql_chain import sql_rag_chain
from config import SQL_RAG_PERMITTED_ROLES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["chat"])
security = HTTPBearer()


def _is_analytical_question(question: str) -> bool:
    """
    Heuristic to detect if a question is analytical/SQL-driven.
    Looks for keywords like count, total, statistics, how many, percentage, etc.
    """
    analytical_keywords = [
        r'\bhow many\b',
        r'\bcount\b',
        r'\btotal\b',
        r'\baverage\b',
        r'\bmax\b',
        r'\bmin\b',
        r'\bstatistic',
        r'\breport',
        r'\banalysis',
        r'\bpercentage\b',
        r'\btrend\b',
        r'\bsummary\b',
        r'\bcomparison\b',
        r'\bsince\b',
        r'\blast\b',
        r'\bmonth\b',
        r'\byear\b',
    ]
    question_lower = question.lower()
    return any(re.search(kw, question_lower) for kw in analytical_keywords)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, credentials=Security(security)):
    """
    Main RAG endpoint.

    Routes to either:
    - Hybrid RAG (dense + BM25 retrieval + reranking) for general questions
    - SQL RAG (NL→SQL→Execute) for analytical questions

    All queries are RBAC-filtered at the Qdrant level based on user role.

    Args:
        question: User's question
        credentials: JWT token (via HTTPBearer)

    Returns:
        Answer, sources, retrieval_type, and user role
    """
    try:
        payload = get_current_user(credentials.credentials)
        user_role = payload.get("role")
        username = payload.get("sub")
    except HTTPException as e:
        logger.error(f"Authentication failed: {e.detail}")
        raise

    logger.info(f"\n[CHAT] User '{username}' ({user_role}): {request.question[:80]}...")

    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # --- Route to SQL RAG or Hybrid RAG ---
    is_analytical = _is_analytical_question(question)
    logger.info(f"  Analytical question: {is_analytical}")

    if is_analytical and user_role in SQL_RAG_PERMITTED_ROLES:
        logger.info(f"  → Routing to SQL RAG (role: {user_role})")
        try:
            result = sql_rag_chain(question, user_role)
        except Exception as e:
            logger.error(f"SQL RAG failed: {e}")
            # Fallback to hybrid RAG
            logger.info("  → Falling back to Hybrid RAG")
            result = rag_chain(question, user_role)
    else:
        if is_analytical and user_role not in SQL_RAG_PERMITTED_ROLES:
            logger.info(f"  → Analytical question but role '{user_role}' not permitted for SQL RAG, using Hybrid RAG")
        else:
            logger.info("  → Routing to Hybrid RAG")
        result = rag_chain(question, user_role)

    logger.info(f"  ✓ Response: {result['retrieval_type']} with {len(result['sources'])} sources")

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        retrieval_type=result["retrieval_type"],
        role=user_role,
    )
