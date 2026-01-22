from __future__ import annotations

import re
from typing import Iterable, List

from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


def redact_phi(text: str) -> str:
    text = re.sub(r"\b\d{7,}\b", "[REDACTED_ID]", text)
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)
    return text


def chunk_text(text: str) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
    )
    return splitter.split_text(text)


def embed_texts(texts: Iterable[str]) -> List[List[float]]:
    embeddings = OllamaEmbeddings(
        base_url=settings.ollama_base_url,
        model=settings.rag_embedding_model,
    )
    return embeddings.embed_documents(list(texts))


def embed_query(text: str) -> List[float]:
    embeddings = OllamaEmbeddings(
        base_url=settings.ollama_base_url,
        model=settings.rag_embedding_model,
    )
    return embeddings.embed_query(text)
