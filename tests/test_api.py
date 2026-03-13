from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_triage_recommends_rollback_for_missing_secret() -> None:
    response = client.post(
        "/api/v1/incidents",
        headers={"X-Role": "sre"},
        json={
            "title": "deploy failed",
            "service": "checkout",
            "environment": "prod",
            "source": "github-actions",
            "category": "deployment_failure",
            "signals": {"error": "Secret DB_URL not found"},
        },
    )
    incident_id = response.json()["id"]

    triage = client.post(f"/api/v1/incidents/{incident_id}/triage", headers={"X-Role": "sre"})
    assert triage.status_code == 200
    actions = [x["action_id"] for x in triage.json()["recommendations"]]
    assert "rollback_release" in actions


def test_prod_execution_requires_approval() -> None:
    response = client.post(
        "/api/v1/incidents",
        headers={"X-Role": "sre"},
        json={
            "title": "deploy failed",
            "service": "payment-api",
            "environment": "prod",
            "source": "github-actions",
            "category": "deployment_failure",
            "signals": {"error": "Secret not found"},
        },
    )
    incident_id = response.json()["id"]
    client.post(f"/api/v1/incidents/{incident_id}/triage", headers={"X-Role": "sre"})

    execute = client.post(
        f"/api/v1/incidents/{incident_id}/execute",
        headers={"X-Role": "sre"},
        json={"action_id": "rollback_release"},
    )
    assert execute.status_code == 403
