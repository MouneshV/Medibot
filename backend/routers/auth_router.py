"""
MediBot Auth Router — Login endpoint.
"""

import logging
from fastapi import APIRouter, HTTPException

from auth import authenticate_user, create_token
from models import LoginRequest, LoginResponse
from config import ROLE_COLLECTIONS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.

    Args:
        username: Demo username (e.g., 'dr.mehta', 'nurse.priya')
        password: Demo password (e.g., 'doctor123')

    Returns:
        Token, role, and accessible collections
    """
    user = authenticate_user(request.username, request.password)
    if not user:
        logger.warning(f"Failed login attempt for username: {request.username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_token(user["username"], user["role"])
    collections = ROLE_COLLECTIONS.get(user["role"], [])

    logger.info(f"User {request.username} ({user['role']}) logged in successfully")

    return LoginResponse(
        token=token,
        role=user["role"],
        username=request.username,
        display_name=user["display_name"],
        collections=collections,
    )
