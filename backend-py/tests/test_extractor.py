import json

import pytest

from app.services import extractor


def test_extract_notes_no_langextract(monkeypatch):
    # Simulate langextract missing
    monkeypatch.setattr(extractor, "lx", None)
    w = extractor.default_wrapper()
    res = w.extract_notes(["some text"], prompt_description="test")
    assert res == []


class FakeResult:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return json.dumps(self._payload)


class FakeLX:
    def extract(self, text_or_documents, prompt_description, examples, model_id, model_url, fence_output):
        return FakeResult({"extractions": [{"class": "entity", "text": text_or_documents}]})


def test_extract_notes_success(monkeypatch):
    monkeypatch.setattr(extractor, "lx", FakeLX())
    w = extractor.default_wrapper()
    res = w.extract_notes(["note content"], prompt_description="extract stuff")
    assert isinstance(res, list)
    assert res and res[0]["text_index"] == 0
    assert "result" in res[0]