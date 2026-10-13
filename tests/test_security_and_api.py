"""Regression tests for optional audit backend authentication and integrity."""
import os
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agents.base import AuditTrail, SecurityException
from agents.api import app
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor


def test_modified_audit_event_or_signature_is_detected():
    trail = AuditTrail(secret_key="a-long-enough-test-secret")
    trail.log("test", "auditor", "CASE", {"status": "ok"})
    trail.log("test", "auditor", "CASE", {"status": "next"})
    assert trail.verify_integrity()
    snapshot = trail.get_trail()
    snapshot[0]["actor"] = "forged"
    assert trail.verify_integrity(), "Snapshots should not mutate ledger"
    trail.logs[0]["actor"] = "forged"
    assert not trail.verify_integrity()


def test_numeric_payload_rejects_nonfinite_values():
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="X", target_identifier="KEY", primary_metric=float("nan"))
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="X", target_identifier="KEY",
                          primary_metric=20, secondary_metric=float("inf"))


def test_supervisor_checks_nested_metadata_for_phi(monkeypatch):
    monkeypatch.setenv("AUDIT_SECRET_KEY", "synthetic-audit-key-for-test-only")
    payload = SystemTaskPayload(task_id="X", target_identifier="KEY",
                                primary_metric=1.0, attributes={"note": "MRN-123456"})
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(payload)


def test_api_rejects_missing_or_incorrect_token(monkeypatch):
    monkeypatch.setenv("AUDIT_SECRET_KEY", "synthetic-audit-key-for-test-only")
    monkeypatch.setenv("API_ACCESS_TOKEN", "synthetic-api-test-token-32-characters")
    client = TestClient(app)
    body = {"task_id": "TEST", "target_identifier": "KEY", "primary_metric": 2.0}
    assert client.post("/api/audit", json=body).status_code == 401
    assert client.post("/api/audit", json=body, headers={
        "Authorization": "Bearer incorrect"}).status_code == 403
    assert client.get("/api/audit/logs").status_code == 401
    valid = client.post("/api/audit", json=body, headers={
        "Authorization": "Bearer synthetic-api-test-token-32-characters"})
    assert valid.status_code == 200
    assert valid.json()["total_alerts"] == 0


def test_api_requires_configuration(monkeypatch):
    monkeypatch.delenv("API_ACCESS_TOKEN", raising=False)
    client = TestClient(app)
    result = client.post("/api/audit", json={
        "task_id": "TEST", "target_identifier": "KEY", "primary_metric": 2.0})
    assert result.status_code == 503
