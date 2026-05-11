from __future__ import annotations
import json
import logging
import re
import time
from datetime import UTC, datetime
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.config import settings
from app.core.security import User, get_password_hash
from app.database import SessionLocal
from app.models.user import UserModel

logger = logging.getLogger(__name__)

_OPENID_CACHE_TTL_SECONDS = 3600
_openid_cache: dict[str, dict[str, Any]] = {}

_ROLE_SCOPES: dict[str, list[str]] = {
    "admin": ["admin", "read", "write", "delete"],
    "researcher": ["read", "write"],
    "viewer": ["read"],
}


def _fetch_json(url: str) -> dict[str, Any]:
    try:
        with urlopen(url, timeout=5) as response:
            return json.load(response)
    except (OSError, URLError, json.JSONDecodeError) as exc:
        logger.warning("Failed to load Azure Entra metadata from %s: %s", url, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Azure Entra metadata is unavailable",
        ) from exc


def _openid_metadata_urls() -> list[str]:
    tenant_id = settings.azure_entra_tenant_id.strip()
    return [
        f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration",
        f"https://login.microsoftonline.com/{tenant_id}/.well-known/openid-configuration",
    ]


def _load_openid_metadata(openid_url: str) -> tuple[dict[str, Any], dict[str, Any]]:
    now = time.time()
    cached_entry = _openid_cache.get(openid_url)
    if cached_entry and now < float(cached_entry.get("expires_at", 0.0)):
        return cached_entry["config"], cached_entry["jwks"]

    config = _fetch_json(openid_url)
    jwks = _fetch_json(config["jwks_uri"])
    _openid_cache[openid_url] = {
        "expires_at": now + _OPENID_CACHE_TTL_SECONDS,
        "config": config,
        "jwks": jwks,
    }
    return config, jwks


def _load_openid_metadata_variants() -> list[tuple[dict[str, Any], dict[str, Any]]]:
    variants: list[tuple[dict[str, Any], dict[str, Any]]] = []
    last_error: HTTPException | None = None

    for openid_url in _openid_metadata_urls():
        try:
            variants.append(_load_openid_metadata(openid_url))
        except HTTPException as exc:
            last_error = exc

    if variants:
        return variants

    raise last_error or HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Azure Entra metadata is unavailable",
    )


def _select_signing_keys(token: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    key_id = header.get("kid")
    candidate_keys: list[tuple[dict[str, Any], dict[str, Any]]] = []

    for openid_config, jwks in _load_openid_metadata_variants():
        for key in jwks.get("keys", []):
            if key.get("kid") == key_id:
                candidate_keys.append((key, openid_config))

    if candidate_keys:
        return candidate_keys

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unknown Azure Entra signing key",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _decode_entra_token(token: str) -> dict[str, Any]:
    signing_key_candidates = _select_signing_keys(token)
    audiences = settings.azure_entra_expected_audiences
    decode_error: JWTError | None = None

    for signing_key, openid_config in signing_key_candidates:
        for audience in audiences:
            try:
                return jwt.decode(
                    token,
                    signing_key,
                    algorithms=["RS256"],
                    audience=audience,
                    issuer=openid_config.get("issuer"),
                    options={"verify_at_hash": False},
                )
            except JWTError as exc:
                decode_error = exc

    try:
        unverified_claims = jwt.get_unverified_claims(token)
    except JWTError:
        unverified_claims = {}

    expected_issuers = [
        openid_config.get("issuer")
        for _, openid_config in signing_key_candidates
        if openid_config.get("issuer")
    ]
    logger.info(
        "Azure Entra token validation failed: %s; aud=%s iss=%s ver=%s azp=%s scp=%s expected_audiences=%s expected_issuers=%s",
        decode_error,
        unverified_claims.get("aud"),
        unverified_claims.get("iss"),
        unverified_claims.get("ver"),
        unverified_claims.get("azp"),
        unverified_claims.get("scp"),
        audiences,
        expected_issuers,
    )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Azure Entra token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _normalize_email(value: str | None) -> str:
    return (value or "").strip().lower()


def _extract_email(payload: dict[str, Any]) -> str:
    email = _normalize_email(
        payload.get("preferred_username")
        or payload.get("email")
        or payload.get("upn")
    )
    if not email or "@" not in email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Azure Entra token is missing an email identity claim",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return email


def _default_role_for_email(email: str) -> str:
    if email in settings.azure_entra_admin_emails_list:
        return "admin"
    return "viewer"


def _sanitize_username(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9_-]+", "-", value.strip().lower())
    normalized = normalized.strip("-_")
    return normalized[:150]


def _candidate_username(payload: dict[str, Any], email: str) -> str:
    raw_candidates = [
        payload.get("preferred_username"),
        payload.get("unique_name"),
        email.split("@", 1)[0],
        payload.get("name"),
        payload.get("oid"),
    ]
    for raw_value in raw_candidates:
        if not raw_value:
            continue
        base_value = str(raw_value).split("@", 1)[0]
        username = _sanitize_username(base_value)
        if username:
            return username
    return "user"


def _ensure_allowed_email(email: str):
    allowed_emails = settings.azure_entra_allowed_emails_list
    if allowed_emails and email not in allowed_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This Azure Entra account is not allowed to access the preview",
        )


def _resolve_or_create_user(payload: dict[str, Any]) -> User:
    email = _extract_email(payload)
    _ensure_allowed_email(email)

    full_name = str(payload.get("name") or "").strip() or None
    object_id = str(payload.get("oid") or payload.get("sub") or email)

    db = SessionLocal()
    try:
        user_row = db.query(UserModel).filter(UserModel.email == email).first()
        if user_row is None:
            username = _candidate_username(payload, email)
            suffix = 1
            while db.query(UserModel).filter(UserModel.username == username).first():
                username = f"{_candidate_username(payload, email)}-{suffix}"
                suffix += 1

            role = _default_role_for_email(email)
            user_row = UserModel(
                username=username,
                email=email,
                full_name=full_name,
                role=role,
                scopes=_ROLE_SCOPES[role],
                hashed_password=get_password_hash(
                    f"entra::{object_id}::{settings.secret_key}"
                ),
            )
            db.add(user_row)
        else:
            if full_name:
                user_row.full_name = full_name
            if email in settings.azure_entra_admin_emails_list and user_row.role != "admin":
                user_row.role = "admin"
                user_row.scopes = _ROLE_SCOPES["admin"]

        user_row.last_login = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user_row)
        return User(
            username=user_row.username,
            email=user_row.email,
            full_name=user_row.full_name,
            role=user_row.role,
            disabled=user_row.disabled,
            scopes=user_row.scopes or [],
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Failed to resolve Azure Entra user: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve Azure Entra user",
        ) from exc
    finally:
        db.close()


def get_entra_user_from_token(token: str) -> User:
    payload = _decode_entra_token(token)
    return _resolve_or_create_user(payload)