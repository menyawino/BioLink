"""
Authentication routes for BioLink API.
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.core import (
    Token,
    User,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.core import limiter, RateLimits

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[User]:
    """Get current user from JWT token."""
    if token is None:
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


@router.post("/token", response_model=Token)
@limiter.limit(RateLimits.AUTH)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.

    Default test users:
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
        data={"sub": user.username, "scopes": user.scopes},
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
async def refresh_token(request: Request, token: str):
    """Refresh access token using refresh token."""
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
        data={"sub": user.username, "scopes": user.scopes},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    Logout endpoint. In a stateless JWT system, the client should discard the token.
    For token revocation, a blacklist would be needed (Redis recommended).
    """
    # TODO: Add token to blacklist in Redis if implementing token revocation
    return {"message": "Successfully logged out"}
