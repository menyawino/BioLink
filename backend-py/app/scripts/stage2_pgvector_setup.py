import time
from app.rag.vector_store import ensure_schema, similarity_search
from app.config import settings


def run():
    start = time.time()
    ensure_schema()

    # basic query should run even if table empty
    test_embedding = [0.0] * settings.rag_embedding_dim
    results = similarity_search(test_embedding, k=1)
    elapsed = time.time() - start

    assert elapsed < 5, f"Stage 2 latency too high: {elapsed:.2f}s"
    print("Stage 2 OK: pgvector schema ready, query latency", f"{elapsed:.2f}s")
    print("Sample results:", results)


if __name__ == "__main__":
    run()
