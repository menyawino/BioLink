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


def test_resolve_pipeline_processor_id_discovers_scripted_processor_in_child_group(monkeypatch):
    etl_service.NIFI_SCRIPTED_PIPELINE_PROCESSOR_ID = "proc-registry-scripted-pipeline"

    def fake_get(url, headers, timeout, verify):
        if url.endswith("/flow/process-groups/root"):
            return DummyResponse(
                payload={
                    "processGroupFlow": {
                        "flow": {
                            "processors": [],
                            "processGroups": [
                                {"component": {"id": "group-123", "name": "Registry Pipeline"}}
                            ],
                        }
                    }
                }
            )

        if url.endswith("/flow/process-groups/group-123"):
            return DummyResponse(
                payload={
                    "processGroupFlow": {
                        "flow": {
                            "processors": [
                                {
                                    "component": {
                                        "id": "processor-nested",
                                        "name": "Run Scripted Registry Pipeline",
                                    }
                                }
                            ],
                            "processGroups": [],
                        }
                    }
                }
            )

        raise AssertionError(f"Unexpected URL {url}")

    monkeypatch.setattr(etl_service.requests, "get", fake_get)

    assert etl_service._resolve_pipeline_processor_id({}) == "processor-nested"


def test_trigger_etl_pipeline_uses_script_aligned_mode(monkeypatch):
    monkeypatch.setattr(etl_service, "_get_auth_headers", lambda: {"Authorization": "Bearer token"})
    monkeypatch.setattr(etl_service, "_resolve_pipeline_processor_id", lambda headers: "processor-abc")
    monkeypatch.setattr(etl_service, "_run_once_processor", lambda processor_id, headers: {"ok": True, "status_code": 202})
    configured_context = {}

    def fake_configure_processor(processor_id, headers, *, trigger_token, requested_datasets):
        configured_context["processor_id"] = processor_id
        configured_context["trigger_token"] = trigger_token
        configured_context["requested_datasets"] = requested_datasets
        return {"ok": True, "trigger_token": trigger_token}

    monkeypatch.setattr(etl_service, "_configure_processor_run_context", fake_configure_processor)
    monkeypatch.setattr(etl_service, "_stage_csv_for_nifi", lambda csv_path, dataset: None)
    monkeypatch.setattr(etl_service.registry_loader, "get_registry_counts", lambda engine: {"unified_registry": 0, "bhs_participants": 0, "ehvol_participants": 0})
    monkeypatch.setattr(etl_service.registry_loader, "get_latest_registry_run_id", lambda engine: 3)

    def fake_wait(engine, **kwargs):
        assert kwargs["trigger_token"] == configured_context["trigger_token"]
        assert kwargs["expected_tables"] == ["unified_registry", "bhs_participants"]
        return {
            "verified": True,
            "counts": {"unified_registry": 4943, "bhs_participants": 3500, "ehvol_participants": 1442},
            "run_id": 4,
            "manifest": {"status": "succeeded", "trigger_token": kwargs["trigger_token"]},
        }

    monkeypatch.setattr(
        etl_service.registry_loader,
        "wait_for_registry_repopulation",
        fake_wait,
    )

    result = etl_service.trigger_etl_pipeline(etl_service.ETLParams(dataset_name="bhs"))

    assert result["ok"] is True
    assert result["engine"] == "nifi"
    assert result["mode"] == "script-aligned"
    assert result["processor_id"] == "processor-abc"
    assert result["verified"] is True
    assert result["verification_method"] == "nifi"
    assert result["trigger_token"] == configured_context["trigger_token"]


def test_trigger_etl_pipeline_falls_back_to_snapshot_loader(monkeypatch):
    monkeypatch.setattr(etl_service, "_get_auth_headers", lambda: {"Authorization": "Bearer token"})
    monkeypatch.setattr(etl_service, "_resolve_pipeline_processor_id", lambda headers: "processor-abc")
    monkeypatch.setattr(etl_service, "_run_once_processor", lambda processor_id, headers: {"ok": True, "status_code": 202})
    monkeypatch.setattr(
        etl_service,
        "_configure_processor_run_context",
        lambda processor_id, headers, **kwargs: {"ok": True, "trigger_token": kwargs["trigger_token"]},
    )
    monkeypatch.setattr(etl_service, "_stage_csv_for_nifi", lambda csv_path, dataset: None)
    monkeypatch.setattr(etl_service.registry_loader, "get_registry_counts", lambda engine: {"unified_registry": 0, "bhs_participants": 0, "ehvol_participants": 0})
    monkeypatch.setattr(etl_service.registry_loader, "get_latest_registry_run_id", lambda engine: None)
    monkeypatch.setattr(
        etl_service.registry_loader,
        "wait_for_registry_repopulation",
        lambda engine, **kwargs: {
            "verified": False,
            "counts": {"unified_registry": 0, "bhs_participants": 0, "ehvol_participants": 0},
            "run_id": None,
            "manifest": {"status": "running", "trigger_token": kwargs["trigger_token"]},
        },
    )
    monkeypatch.setattr(
        etl_service.registry_loader,
        "ensure_registry_snapshot_loaded",
        lambda engine, **kwargs: {
            "ok": True,
            "loaded": True,
            "counts": {"unified_registry": 4943, "bhs_participants": 3500, "ehvol_participants": 1442},
            "run_id": 5,
        },
    )

    result = etl_service.trigger_etl_pipeline(
        etl_service.ETLParams(dataset_name="bhs", datasets=["bhs", "ehvol"])
    )

    assert result["ok"] is True
    assert result["verified"] is True
    assert result["verification_method"] == "snapshot-fallback"


def test_configure_processor_run_context_updates_processor_properties(monkeypatch):
    captured = {}

    def fake_get(url, headers, timeout, verify):
        assert url.endswith("/processors/processor-abc")
        return DummyResponse(
            payload={
                "revision": {"version": 7},
                "component": {
                    "id": "processor-abc",
                    "config": {
                        "properties": {
                            "Existing": "value",
                        }
                    },
                },
            }
        )

    def fake_put(url, json, headers, timeout, verify):
        captured["url"] = url
        captured["json"] = json
        return DummyResponse(status_code=200, payload={})

    monkeypatch.setattr(etl_service.requests, "get", fake_get)
    monkeypatch.setattr(etl_service.requests, "put", fake_put)

    result = etl_service._configure_processor_run_context(
        "processor-abc",
        {"Authorization": "Bearer token"},
        trigger_token="run-token-123",
        requested_datasets=["ehvol", "bhs"],
    )

    assert result == {"ok": True, "trigger_token": "run-token-123"}
    properties = captured["json"]["component"]["config"]["properties"]
    assert properties["Existing"] == "value"
    assert properties[etl_service.NIFI_TRIGGER_RUN_TOKEN_PROPERTY] == "run-token-123"
    assert properties[etl_service.NIFI_TRIGGER_DATASETS_PROPERTY] == "ehvol,bhs"
