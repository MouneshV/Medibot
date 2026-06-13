"""
MediBot Collections Router — Returns accessible collections for a role.
"""

import logging
from fastapi import APIRouter, Security
from fastapi.security import HTTPBearer

from auth import get_current_user
from models import CollectionsResponse
from config import ROLE_COLLECTIONS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["collections"])
security = HTTPBearer()


@router.get("/collections/{role}", response_model=CollectionsResponse)
async def get_collections(role: str, credentials=Security(security)):
    """
    Get the list of document collections accessible to a given role.

    Args:
        role: Role name (e.g., 'doctor', 'nurse', 'billing_executive')
        credentials: JWT token

    Returns:
        List of accessible collections
    """
    # Verify user is authenticated
    try:
        payload = get_current_user(credentials.credentials)
        authenticated_role = payload.get("role")
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise

    # Get collections for the requested role
    collections = ROLE_COLLECTIONS.get(role, [])

    logger.info(f"Collections for role '{role}': {collections}")

    return CollectionsResponse(role=role, collections=collections)
