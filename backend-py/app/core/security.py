"""
Security utilities for authentication and authorization.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from app.config import settings

logger = logging.getLogger(__name__)

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
    role: str = "viewer"
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
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
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


def get_user(username: str) -> Optional[UserInDB]:
    """Get user from PostgreSQL database."""
    from app.database import SessionLocal
    from app.models.user import UserModel

    db = SessionLocal()
    try:
        user_row = db.query(UserModel).filter(UserModel.username == username).first()
        if user_row is None:
            return None
        return UserInDB(
            username=user_row.username,
            email=user_row.email,
            full_name=user_row.full_name,
            role=user_row.role,
            disabled=user_row.disabled,
            scopes=user_row.scopes or [],
            hashed_password=user_row.hashed_password,
        )
    except Exception as e:
        logger.error(f"Error fetching user '{username}': {e}")
        return None
    finally:
        db.close()


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user credentials and update last_login."""
    from app.database import SessionLocal
    from app.models.user import UserModel

    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None

    # Update last_login timestamp
    db = SessionLocal()
    try:
        db.query(UserModel).filter(UserModel.username == username).update(
            {"last_login": datetime.now(UTC)}
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    return user
