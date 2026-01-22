from __future__ import annotations

import json
from typing import Iterable

import psycopg2
import numpy as np
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector

from app.config import settings


def get_pg_conn():
    conn = psycopg2.connect(settings.rag_pg_url)
    try:
        register_vector(conn)
    except psycopg2.ProgrammingError:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.commit()
        register_vector(conn)
    return conn


def ensure_schema():
    dim = settings.rag_embedding_dim
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS patient_notes_embeddings (
                    patient_id TEXT NOT NULL,
                    chunk_id INT NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    embedding vector({dim}) NOT NULL,
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    PRIMARY KEY (patient_id, chunk_id)
                )
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_patient_notes_embedding
                ON patient_notes_embeddings USING ivfflat (embedding vector_cosine_ops)
                """
            )
        conn.commit()


def upsert_embeddings(rows: Iterable[tuple[str, int, str, dict, list[float]]]):
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO patient_notes_embeddings (patient_id, chunk_id, content, metadata, embedding)
                VALUES %s
                ON CONFLICT (patient_id, chunk_id)
                DO UPDATE SET
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding,
                    updated_at = NOW()
                """,
                [(pid, chunk_id, content, json.dumps(meta), embedding) for pid, chunk_id, content, meta, embedding in rows],
            )
        conn.commit()


def similarity_search(query_embedding: list[float], k: int = 5, patient_ids: list[str] | None = None):
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            query_vec = np.array(query_embedding, dtype=float)
            if patient_ids:
                cur.execute(
                    """
                    SELECT patient_id, content, metadata, embedding
                    FROM patient_notes_embeddings
                    WHERE patient_id = ANY(%s)
                    """,
                    (patient_ids,),
                )
            else:
                cur.execute(
                    """
                    SELECT patient_id, content, metadata, embedding
                    FROM patient_notes_embeddings
                    """
                )
            rows = cur.fetchall()

    if not rows:
        return []

    # Compute cosine similarity in Python
    sims = []
    q_norm = np.linalg.norm(query_vec) + 1e-10
    for patient_id, content, metadata, embedding in rows:
        emb = np.array(embedding, dtype=float)
        sim = float(np.dot(query_vec, emb) / (q_norm * (np.linalg.norm(emb) + 1e-10)))
        sims.append({
            "patient_id": patient_id,
            "content": content,
            "metadata": metadata,
            "similarity": sim,
        })

    sims.sort(key=lambda x: x["similarity"], reverse=True)
    return sims[:k]
