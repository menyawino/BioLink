from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Iterable, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from langchain_ollama import ChatOllama

logger = logging.getLogger(__name__)


@lru_cache(maxsize=8)
def _available_models(base_url: str) -> tuple[str, ...]:
    tags_url = urljoin(f"{base_url.rstrip('/')}/", "api/tags")
    request = Request(tags_url, headers={"Accept": "application/json"})

    try:
        with urlopen(request, timeout=2.5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("Unable to query Ollama model inventory at %s: %s", tags_url, exc)
        return ()

    models = tuple(
        item.get("name", "").strip()
        for item in payload.get("models", [])
        if item.get("name", "").strip()
    )
    return models


def _match_model_name(requested_model: Optional[str], available_models: Iterable[str]) -> Optional[str]:
    if not requested_model:
        return None

    available = tuple(available_models)
    if requested_model in available:
        return requested_model

    requested_lower = requested_model.lower()
    for model_name in available:
        if model_name.lower() == requested_lower:
            return model_name

    return None


def resolve_ollama_model(
    base_url: str,
    requested_model: str,
    fallback_models: Optional[Iterable[str]] = None,
) -> str:
    available = _available_models(base_url)
    matched = _match_model_name(requested_model, available)
    if matched:
        return matched

    for fallback in fallback_models or ():
        matched = _match_model_name(fallback, available)
        if matched:
            logger.warning(
                "Ollama model %s is unavailable; using configured fallback %s instead",
                requested_model,
                matched,
            )
            return matched

    if available:
        logger.warning(
            "Ollama model %s is unavailable; using first installed model %s instead",
            requested_model,
            available[0],
        )
        return available[0]

    return requested_model


def build_chat_ollama(
    base_url: str,
    requested_model: str,
    *,
    temperature: float,
    fallback_models: Optional[Iterable[str]] = None,
    **kwargs,
) -> ChatOllama:
    resolved_model = resolve_ollama_model(base_url, requested_model, fallback_models)
    return ChatOllama(
        base_url=base_url,
        model=resolved_model,
        temperature=temperature,
        **kwargs,
    )