"""
MediBot Pydantic Models — Request/Response schemas for all API endpoints.
"""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    username: str
    display_name: str
    collections: list[str]


class Source(BaseModel):
    source_document: str
    section_title: str
    collection: str


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    retrieval_type: str  # "hybrid_rag" or "sql_rag"
    role: str


class CollectionsResponse(BaseModel):
    role: str
    collections: list[str]


class HealthResponse(BaseModel):
    status: str
    service: str
