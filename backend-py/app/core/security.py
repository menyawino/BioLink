"""
Security utilities for authentication and authorization.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# JWT Configuration
SECRET_KEY = getattr(settings, "secret_key", "your-secret-key-change-in-production")
ALGORITHM = getattr(settings, "jwt_algorithm", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, "access_token_expire_minutes", 30)
REFRESH_TOKEN_EXPIRE_DAYS = getattr(settings, "refresh_token_expire_days", 7)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: list[str] = []


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    scopes: list[str] = []


class UserInDB(User):
    hashed_password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# Mock user database - Replace with actual database in production
# This is for demonstration purposes
USERS_DB = {
    "admin": {
        "username": "admin",
        "full_name": "Administrator",
        "email": "admin@biolink.local",
        "hashed_password": get_password_hash("admin"),
        "disabled": False,
        "scopes": ["admin", "read", "write", "delete"],
    },
    "researcher": {
        "username": "researcher",
        "full_name": "Research User",
        "email": "researcher@biolink.local",
        "hashed_password": get_password_hash("researcher"),
        "disabled": False,
        "scopes": ["read", "write"],
    },
    "viewer": {
        "username": "viewer",
        "full_name": "View Only User",
        "email": "viewer@biolink.local",
        "hashed_password": get_password_hash("viewer"),
        "disabled": False,
        "scopes": ["read"],
    },
}


def get_user(username: str) -> Optional[UserInDB]:
    """Get user from database."""
    if username in USERS_DB:
        user_dict = USERS_DB[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user credentials."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
