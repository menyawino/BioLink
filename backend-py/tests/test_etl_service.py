import app.services.etl_service as etl_service
import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    yield


class DummyResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.text or f"HTTP {self.status_code}")


def test_resolve_pipeline_processor_id_discovers_scripted_processor(monkeypatch):
    etl_service.NIFI_SCRIPTED_PIPELINE_PROCESSOR_ID = "proc-registry-scripted-pipeline"

    def fake_get(url, headers, timeout, verify):
        return DummyResponse(
            payload={
                "processGroupFlow": {
                    "flow": {
                        "processors": [
                            {
                                "component": {
                                    "id": "processor-123",
                                    "name": "Run Scripted Registry Pipeline",
                                }
                            }
                        ]
                    }
                }
            }
        )

    monkeypatch.setattr(etl_service.requests, "get", fake_get)

    assert etl_service._resolve_pipeline_processor_id({}) == "processor-123"


def test_trigger_etl_pipeline_uses_script_aligned_mode(monkeypatch):
    monkeypatch.setattr(etl_service, "_get_auth_headers", lambda: {"Authorization": "Bearer token"})
    monkeypatch.setattr(etl_service, "_resolve_pipeline_processor_id", lambda headers: "processor-abc")
    monkeypatch.setattr(etl_service, "_run_once_processor", lambda processor_id, headers: {"ok": True, "status_code": 202})
    monkeypatch.setattr(etl_service, "_stage_csv_for_nifi", lambda csv_path, dataset: None)

    result = etl_service.trigger_etl_pipeline(etl_service.ETLParams(dataset_name="bhs"))

    assert result["ok"] is True
    assert result["engine"] == "nifi"
    assert result["mode"] == "script-aligned"
    assert result["processor_id"] == "processor-abc"
