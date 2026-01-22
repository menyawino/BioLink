import time
import requests


def run():
    start = time.time()
    question = "Low EF males"

    resp = requests.post("http://localhost:3001/api/rag", json={"question": question}, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    elapsed = time.time() - start
    assert elapsed < 15, f"Stage 6 latency too high: {elapsed:.2f}s"
    assert "answer" in data.get("data", {}), "No answer returned"
    assert "No matching" not in data["data"]["answer"], "No contextual answer returned"

    print("Stage 6 OK:")
    print(data["data"]["answer"])


if __name__ == "__main__":
    run()
