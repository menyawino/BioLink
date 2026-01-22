import os
import time

from app.rag.sqlserver import fetch_patients
from app.rag.embedding import chunk_text, embed_texts, redact_phi
from app.rag.vector_store import ensure_schema, upsert_embeddings


def run():
    start = time.time()
    ensure_schema()

    limit = int(os.getenv("RAG_EMBED_LIMIT", "1000"))
    rows = fetch_patients(limit=limit)
    assert rows, "No rows fetched from SQL Server"

    to_upsert = []
    for row in rows:
        patient_id = str(row[0])
        notes = row[5] or ""
        notes = redact_phi(notes)
        chunks = chunk_text(notes) or [""]
        embeddings = embed_texts(chunks)

        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            meta = {"source": "sqlserver", "stage": 3}
            to_upsert.append((patient_id, idx, chunk, meta, emb))

    upsert_embeddings(to_upsert)
    elapsed = time.time() - start
    assert elapsed < 120, f"Stage 3 latency too high: {elapsed:.2f}s"

    print("Stage 3 OK: embedded and stored notes", f"{elapsed:.2f}s")


if __name__ == "__main__":
    run()
