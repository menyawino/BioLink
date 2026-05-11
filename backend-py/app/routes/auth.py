"""
Authentication routes for BioLink API.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session

from app.core import (
    Token,
    User,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user,
    get_password_hash,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.core import limiter, RateLimits
from app.database import get_db
from app.models.user import UserModel

logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token", auto_error=False)

# ── Redis token blacklist ───────────────────────────────────────────


def _get_redis():
    try:
        from app.core.cache import get_redis_client

        return get_redis_client()
    except Exception:
        return None


def _blacklist_token(token: str, ttl_seconds: int = 86400 * 8):
    """Add a token to the Redis blacklist."""
    r = _get_redis()
    if r:
        r.setex(f"bl:{token}", ttl_seconds, "1")


def _is_blacklisted(token: str) -> bool:
    r = _get_redis()
    if r:
        return r.get(f"bl:{token}") is not None
    return False


# ── Dependencies ────────────────────────────────────────────────────


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[User]:
    """Get current user from JWT token."""
    if token is None:
        return None

    if _is_blacklisted(token):
        return None

    payload = decode_token(token)
    if payload is None:
        return None

    username: str = payload.get("sub")
    if username is None:
        return None

    user = get_user(username)
    if user is None:
        return None

    return User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        disabled=user.disabled,
        scopes=user.scopes,
    )


async def get_current_active_user(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """Get current active user, raise exception if not authenticated."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


def require_scopes(*required: str):
    """Dependency factory: require the current user to have ALL listed scopes."""

    async def _check(user: User = Depends(get_current_active_user)) -> User:
        missing = set(required) - set(user.scopes)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scopes: {', '.join(missing)}",
            )
        return user

    return _check


def require_role(*roles: str):
    """Dependency factory: require the current user to have one of the listed roles."""

    async def _check(user: User = Depends(get_current_active_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not authorized. Required: {', '.join(roles)}",
            )
        return user

    return _check


# ── Request / Response schemas ──────────────────────────────────────


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def username_alphanum(cls, v: str) -> str:
        v = v.strip().lower()
        if len(v) < 3 or len(v) > 150:
            raise ValueError("Username must be 3-150 characters")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must be alphanumeric (underscores/hyphens allowed)")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None


class AdminUpdateUserRequest(BaseModel):
    role: Optional[str] = None
    scopes: Optional[list[str]] = None
    disabled: Optional[bool] = None
    full_name: Optional[str] = None
    email: Optional[str] = None


class AdminCreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    role: str = "viewer"
    scopes: Optional[list[str]] = None
    disabled: bool = False

    @field_validator("username")
    @classmethod
    def username_alphanum(cls, v: str) -> str:
        v = v.strip().lower()
        if len(v) < 3 or len(v) > 150:
            raise ValueError("Username must be 3-150 characters")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must be alphanumeric (underscores/hyphens allowed)")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("role")
    @classmethod
    def role_valid(cls, v: str) -> str:
        if v not in ("admin", "researcher", "viewer"):
            raise ValueError("Invalid role")
        return v

    @field_validator("email")
    @classmethod
    def email_basic_validation(cls, v: str) -> str:
        value = v.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Invalid email")
        return value


class UserResponse(BaseModel):
    username: str
    email: Optional[str]
    full_name: Optional[str]
    role: str
    scopes: list[str]
    disabled: bool
    created_at: Optional[str] = None
    last_login: Optional[str] = None


def serialize_user(user_row: UserModel) -> UserResponse:
    return UserResponse(
        username=user_row.username,
        email=user_row.email,
        full_name=user_row.full_name,
        role=user_row.role,
        scopes=user_row.scopes,
        disabled=user_row.disabled,
        created_at=user_row.created_at.isoformat() if user_row.created_at else None,
        last_login=user_row.last_login.isoformat() if user_row.last_login else None,
    )


# ── Endpoints ───────────────────────────────────────────────────────


@router.post("/token", response_model=Token)
@limiter.limit(RateLimits.AUTH)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login.

    Default users (dev only):
    - admin / admin (full access)
    - researcher / researcher (read + write)
    - viewer / viewer (read only)
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": user.scopes, "role": user.role},
        expires_delta=access_token_expires,
    )
    refresh_token = create_refresh_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
@limiter.limit(RateLimits.AUTH)
async def refresh_token(request: Request, token: str = Body(..., embed=True)):
    """Refresh access token using refresh token."""
    if _is_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    payload = decode_token(token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str = payload.get("sub")
    user = get_user(username)
    if user is None or user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": user.scopes, "role": user.role},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get current authenticated user information."""
    user_row = db.query(UserModel).filter(UserModel.username == current_user.username).first()
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")
    return serialize_user(user_row)


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    token: str = Depends(oauth2_scheme),
):
    """Logout: blacklist the current access token in Redis."""
    if token:
        _blacklist_token(token)
    return {"message": "Successfully logged out"}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RateLimits.AUTH)
async def register(request: Request, body: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user. New users get 'viewer' role by default."""
    normalized_username = body.username.strip().lower()
    normalized_email = body.email.strip().lower()

    # Check duplicate username
    if db.query(UserModel).filter(UserModel.username == normalized_username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already exists"
        )
    # Check duplicate email
    if db.query(UserModel).filter(UserModel.email == normalized_email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    new_user = UserModel(
        username=normalized_username,
        email=normalized_email,
        full_name=body.full_name,
        hashed_password=get_password_hash(body.password),
        role="viewer",
        scopes=["read"],
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"New user registered: {normalized_username}")

    return serialize_user(new_user)


@router.put("/me", response_model=UserResponse)
async def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update own profile (full_name, email)."""
    user_row = db.query(UserModel).filter(UserModel.username == current_user.username).first()
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")

    if body.email is not None:
        existing = db.query(UserModel).filter(
            UserModel.email == body.email, UserModel.username != current_user.username
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")
        user_row.email = body.email

    if body.full_name is not None:
        user_row.full_name = body.full_name

    user_row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user_row)

    return serialize_user(user_row)


@router.post("/change-password")
@limiter.limit(RateLimits.AUTH)
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Change own password. Requires current password verification."""
    user_row = db.query(UserModel).filter(UserModel.username == current_user.username).first()
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(body.current_password, user_row.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    user_row.hashed_password = get_password_hash(body.new_password)
    user_row.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Password changed successfully"}


# ── Admin endpoints ─────────────────────────────────────────────────


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Admin: list all users."""
    rows = db.query(UserModel).order_by(UserModel.created_at).all()
    return [serialize_user(r) for r in rows]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RateLimits.ADMIN)
async def admin_create_user(
    request: Request,
    body: AdminCreateUserRequest,
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Admin: create a new user with explicit role/scopes/disabled status."""
    normalized_username = body.username.strip().lower()
    normalized_email = body.email.strip().lower()

    if db.query(UserModel).filter(UserModel.username == normalized_username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already exists"
        )

    if db.query(UserModel).filter(UserModel.email == normalized_email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    valid_scopes = {"admin", "read", "write", "delete"}
    default_scopes_by_role = {
        "admin": ["admin", "read", "write", "delete"],
        "researcher": ["read", "write"],
        "viewer": ["read"],
    }
    scopes = body.scopes if body.scopes is not None else default_scopes_by_role[body.role]
    invalid_scopes = set(scopes) - valid_scopes
    if invalid_scopes:
        raise HTTPException(status_code=400, detail=f"Invalid scopes: {invalid_scopes}")

    user_row = UserModel(
        username=normalized_username,
        email=normalized_email,
        full_name=body.full_name,
        hashed_password=get_password_hash(body.password),
        role=body.role,
        scopes=scopes,
        disabled=body.disabled,
    )
    db.add(user_row)
    db.commit()
    db.refresh(user_row)
    return serialize_user(user_row)


@router.put("/users/{username}", response_model=UserResponse)
async def admin_update_user(
    username: str,
    body: AdminUpdateUserRequest,
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Admin: update a user's role, scopes, disabled status, etc."""
    user_row = db.query(UserModel).filter(UserModel.username == username).first()
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")

    if body.role is not None:
        if body.role not in ("admin", "researcher", "viewer"):
            raise HTTPException(status_code=400, detail="Invalid role")
        user_row.role = body.role

    if body.scopes is not None:
        valid_scopes = {"admin", "read", "write", "delete"}
        invalid = set(body.scopes) - valid_scopes
        if invalid:
            raise HTTPException(status_code=400, detail=f"Invalid scopes: {invalid}")
        user_row.scopes = body.scopes

    if body.disabled is not None:
        user_row.disabled = body.disabled

    if body.full_name is not None:
        user_row.full_name = body.full_name

    if body.email is not None:
        existing = db.query(UserModel).filter(
            UserModel.email == body.email, UserModel.username != username
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")
        user_row.email = body.email

    user_row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user_row)

    return serialize_user(user_row)


@router.delete("/users/{username}")
async def admin_delete_user(
    username: str,
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Admin: delete a user."""
    user_row = db.query(UserModel).filter(UserModel.username == username).first()
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")
    if user_row.username == _admin.username:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    db.delete(user_row)
    db.commit()

    return {"message": f"User '{username}' deleted"}

