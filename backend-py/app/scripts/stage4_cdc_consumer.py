import json
import os
import time
from kafka import KafkaConsumer
from dotenv import load_dotenv

from app.rag.embedding import chunk_text, embed_texts, redact_phi
from app.rag.vector_store import ensure_schema, upsert_embeddings

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


def run():
    bootstrap = os.getenv("DEBEZIUM_BOOTSTRAP", "localhost:9092")
    topic = os.getenv("DEBEZIUM_TOPIC", "EHVol.dbo.patients")

    ensure_schema()

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="biolink-rag-cdc",
    )

    print(f"Stage 4 CDC consumer started on {topic}")

    for message in consumer:
        payload = message.value.get("payload")
        if not payload:
            continue

        op = payload.get("op")
        if op not in {"c", "u", "r"}:
            continue

        after = payload.get("after") or {}
        patient_id = str(after.get("id"))
        notes = after.get("notes") or ""
        if not patient_id or not notes:
            continue

        notes = redact_phi(notes)
        chunks = chunk_text(notes) or [""]
        embeddings = embed_texts(chunks)

        rows = []
        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            meta = {"source": "debezium", "op": op, "ts": payload.get("ts_ms")}
            rows.append((patient_id, idx, chunk, meta, emb))

        upsert_embeddings(rows)
        print(f"Upserted embeddings for patient {patient_id} ({len(rows)} chunks)")
        time.sleep(0.1)


if __name__ == "__main__":
    run()
