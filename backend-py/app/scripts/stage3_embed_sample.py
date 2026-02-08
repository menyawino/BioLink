import os
import time
import json
from pathlib import Path

from app.rag.sqlserver import fetch_patients
from app.rag.embedding import chunk_text, embed_texts, redact_phi
from app.rag.vector_store import ensure_schema, upsert_embeddings
from app.services.extractor import default_wrapper
from app.database import engine
from sqlalchemy import text


def run():
    start = time.time()
    ensure_schema()

    limit = int(os.getenv("RAG_EMBED_LIMIT", "1000"))
    rows = fetch_patients(limit=limit)
    assert rows, "No rows fetched from SQL Server"

    to_upsert = []
    extractor = default_wrapper()
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "extractions"))
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    for row in rows:
        patient_id = str(row[0])
        notes = row[5] or ""
        notes = redact_phi(notes)
        # Run LangExtract on the raw notes (if available) and persist JSONL
        try:
            extractions = extractor.extract_notes(
                [notes],
                prompt_description=(
                    "Extract structured entities and attributes from this clinical note. "
                    "Return extractions with exact text spans, classes, and attributes."
                ),
                examples=[],
            )
        except Exception:
            extractions = []

        # Save one JSONL line per patient with the extraction result
        try:
            out_path = os.path.join(out_dir, f"patient_{patient_id}_extractions.jsonl")
            with open(out_path, "a", encoding="utf-8") as fh:
                line = json.dumps({"patient_id": patient_id, "extractions": extractions}, ensure_ascii=False)
                fh.write(line + "\n")
        except Exception:
            # non-fatal: continue to embedding step
            pass
        # Persist extraction to DB (non-fatal)
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO patient_note_extractions (patient_id, chunk_id, extraction, source, stage) VALUES (:patient_id, :chunk_id, :extraction::jsonb, :source, :stage)"
                    ),
                    {
                        "patient_id": int(patient_id),
                        "chunk_id": None,
                        "extraction": json.dumps(extractions, ensure_ascii=False),
                        "source": "langextract",
                        "stage": 3,
                    },
                )
        except Exception:
            # non-fatal: keep processing embeddings even if DB write fails
            pass
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
