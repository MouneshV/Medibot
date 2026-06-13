"""
MediBot Configuration — RBAC matrix, user credentials, settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- API & Model Settings ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "medibot_docs")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
JWT_SECRET = os.getenv("JWT_SECRET", "medibot-secret-key")
DATABASE_PATH = os.getenv("DATABASE_PATH", "../mediassist_data/db/mediassist.db")
DATA_DIR = os.getenv("DATA_DIR", "../mediassist_data")

# --- RBAC: Role-Based Access Control ---
# Maps each role to the document collections they can access.
ROLE_COLLECTIONS = {
    "doctor": ["clinical", "nursing", "general"],
    "nurse": ["nursing", "general"],
    "billing_executive": ["billing", "general"],
    "technician": ["equipment", "general"],
    "admin": ["clinical", "nursing", "billing", "equipment", "general"],
}

# Maps each collection to the roles that can access it.
# Used during ingestion to stamp access_roles metadata on each chunk.
COLLECTION_ACCESS_ROLES = {
    "general": ["doctor", "nurse", "billing_executive", "technician", "admin"],
    "clinical": ["doctor", "admin"],
    "nursing": ["nurse", "doctor", "admin"],
    "billing": ["billing_executive", "admin"],
    "equipment": ["technician", "admin"],
}

# Roles permitted to use SQL RAG for analytical queries.
SQL_RAG_PERMITTED_ROLES = ["billing_executive", "admin"]

# --- Demo User Credentials ---
USERS = {
    "dr.mehta": {"password": "doctor123", "role": "doctor", "display_name": "Dr. Mehta"},
    "nurse.priya": {"password": "nurse123", "role": "nurse", "display_name": "Nurse Priya"},
    "billing.ravi": {"password": "billing123", "role": "billing_executive", "display_name": "Ravi (Billing)"},
    "tech.anand": {"password": "tech123", "role": "technician", "display_name": "Anand (Technician)"},
    "admin.sys": {"password": "admin123", "role": "admin", "display_name": "System Admin"},
}

# --- Retrieval Settings ---
HYBRID_SEARCH_TOP_K = 10  # Number of candidates from hybrid search
RERANK_TOP_K = 3          # Number of chunks after reranking
CHUNK_MAX_TOKENS = 512    # Max tokens per chunk during ingestion

# Role display info for frontend
ROLE_DISPLAY = {
    "doctor": {"label": "Doctor", "color": "#3b82f6"},
    "nurse": {"label": "Nurse", "color": "#22c55e"},
    "billing_executive": {"label": "Billing Executive", "color": "#a855f7"},
    "technician": {"label": "Technician", "color": "#f97316"},
    "admin": {"label": "Administrator", "color": "#ef4444"},
}
