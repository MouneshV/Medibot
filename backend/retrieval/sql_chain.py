"""
MediBot SQL RAG — Answer analytical questions using SQL queries over relational database.
NL → SQL → Execute → NL Answer pipeline.
"""

import sqlite3
import logging
from groq import Groq

from config import GROQ_API_KEY, LLM_MODEL, DATABASE_PATH

logger = logging.getLogger(__name__)

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)


def get_db_schema() -> str:
    """Fetch database schema (CREATE TABLE statements) for prompt context."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    schema_info = ""
    for (table_name,) in tables:
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        schema_info += f"\nTable: {table_name}\n"
        for col_id, col_name, col_type, notnull, default, pk in columns:
            schema_info += f"  - {col_name}: {col_type}\n"

    conn.close()
    return schema_info


def sql_rag_chain(question: str, user_role: str) -> dict:
    """
    SQL RAG pipeline for analytical questions.

    Steps:
    1. Generate SQL query from natural language question
    2. Clean and extract SQL from LLM output
    3. Execute SQL against database
    4. Generate natural language answer from results

    Args:
        question: User's analytical question (e.g., "How many claims were escalated last month?")
        user_role: Authenticated user's role (must be admin or billing_executive)

    Returns:
        Dict with 'answer' and 'sources' (empty for SQL RAG)
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"SQL RAG Chain: Question from {user_role}")
    logger.info(f"  Q: {question}")

    # --- 1. Get database schema ---
    db_schema = get_db_schema()

    # --- 2. Generate SQL Query ---
    system_prompt = f"""You are an SQL expert. Generate a SQL query to answer the following question.

Database Schema:
{db_schema}

Important:
- Write ONLY the SQL query, nothing else.
- Use standard SQLite syntax.
- Make sure the query is safe and efficient.
- Return ONLY the SELECT statement, no explanations."""

    logger.info("  → Generating SQL query...")
    sql_response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {question}"},
        ],
        temperature=0.1,
        max_tokens=256,
    )

    sql_query = sql_response.choices[0].message.content.strip()

    # --- 3. Extract SQL from response ---
    # LLM might include markdown code blocks, remove them
    if "```" in sql_query:
        sql_query = sql_query.split("```")[1]
        if sql_query.startswith("sql"):
            sql_query = sql_query[3:]
    sql_query = sql_query.strip()

    logger.info(f"  → Generated SQL: {sql_query[:100]}...")

    # --- 4. Execute SQL ---
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        conn.close()
        logger.info(f"  → Query executed successfully, got {len(results)} rows")
    except Exception as e:
        logger.error(f"  → SQL execution failed: {e}")
        return {
            "answer": f"I encountered an error executing the database query: {str(e)}. "
                     f"Please rephrase your question or try a different query.",
            "sources": [],
            "retrieval_type": "sql_rag",
        }

    # --- 5. Generate Natural Language Answer ---
    logger.info("  → Generating natural language answer...")

    # Format results as text
    results_text = f"Columns: {', '.join(col_names)}\n"
    for row in results[:10]:  # Limit to first 10 rows for context
        results_text += f"  {row}\n"
    if len(results) > 10:
        results_text += f"  ... ({len(results) - 10} more rows)\n"

    answer_prompt = f"""Based on the database query results, provide a clear and concise answer to the question.

Question: {question}

Database Results:
{results_text}

Provide a natural language summary of the results. Be specific with numbers and metrics."""

    answer_response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful analyst. Summarize database query results clearly."},
            {"role": "user", "content": answer_prompt},
        ],
        temperature=0.3,
        max_tokens=512,
    )

    answer = answer_response.choices[0].message.content

    logger.info(f"  → Answer: {answer[:100]}...")
    logger.info(f"{'='*60}\n")

    return {
        "answer": answer,
        "sources": [],
        "retrieval_type": "sql_rag",
    }
