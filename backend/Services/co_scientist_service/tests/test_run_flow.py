from fastapi.testclient import TestClient

from src.main import app
from src.providers import factory


client = TestClient(app)


class DummyProvider:
    async def generate(self, messages: list[dict]) -> dict:
        return {"choices": [{"message": {"content": "{}"}}]}

    async def stream(self, messages: list[dict]):
        yield "{}"


def test_run_flow(monkeypatch):
    monkeypatch.setattr(factory, "get_provider", lambda: DummyProvider())
    payload = {
        "project_description": "Test project",
        "concept_a": "GeneA",
        "concept_b": "DiseaseB",
    }
    run_resp = client.post("/run", json=payload)
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run_id"]

    status_resp = client.get(f"/status/{run_id}")
    assert status_resp.json()["status"] == "COMPLETED"

    hypo_resp = client.get(f"/hypothesis/{run_id}")
    assert hypo_resp.json()["hypothesis"] is not None

    feedback_resp = client.post(
        "/human/feedback",
        json={"run_id": run_id, "stage": "post-critic", "action": "APPROVE"},
    )
    assert feedback_resp.json() == {"ok": True}
