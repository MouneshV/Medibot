"""
MediBot Authentication — JWT token generation and validation.
"""

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import JWT_SECRET, USERS

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

security_scheme = HTTPBearer()


def authenticate_user(username: str, password: str) -> dict | None:
    """Validate username/password against demo credentials."""
    user = USERS.get(username)
    if user and user["password"] == password:
        return {
            "username": username,
            "role": user["role"],
            "display_name": user["display_name"],
        }
    return None


def create_token(username: str, role: str) -> str:
    """Create a JWT token containing username, role, and expiration."""
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Returns the payload."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_user(token: str) -> dict:
    """Extract user info from Bearer token."""
    payload = decode_token(token)
    username = payload.get("sub")
    role = payload.get("role")
    if not username or not role:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return {"username": username, "role": role, "sub": username}
