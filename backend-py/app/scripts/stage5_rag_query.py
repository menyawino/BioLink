import time
from app.rag.embedding import embed_query
from app.rag.vector_store import similarity_search
from app.rag.sqlserver import fetch_patient_ids_by_filters
from app.config import settings


def run():
    start = time.time()

    question = "low EF cadio male"  # sample query
    query_embedding = embed_query(question)

    patient_ids = fetch_patient_ids_by_filters(age_min=None, age_max=None, gender="male", limit=200)
    results = similarity_search(query_embedding, k=settings.rag_top_k, patient_ids=patient_ids)

    elapsed = time.time() - start
    assert elapsed < 5, f"Stage 5 latency too high: {elapsed:.2f}s"
    assert results is not None, "No results returned"

    print("Stage 5 OK: RAG query", f"{elapsed:.2f}s")
    for r in results:
        print(r)


if __name__ == "__main__":
    run()
