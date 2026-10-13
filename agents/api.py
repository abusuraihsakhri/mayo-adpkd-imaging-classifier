"""FastAPI endpoints for the optional local audit demonstration.

This backend is distinct from the clinical Mayo Imaging Classification module.
Configure API_ACCESS_TOKEN and AUDIT_SECRET_KEY before serving externally.
"""
import os
import secrets
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel
from .base import AuditLogger, SecurityException
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")
app = FastAPI(
    title="Mayo ADPKD repository audit demo API",
    description="Nonclinical demonstration of the existing worker/audit machinery",
    version="3.0.1",
)


def require_token(authorization: str | None = Header(default=None)):
    token = os.getenv("API_ACCESS_TOKEN", "")
    if len(token) < 32:
        raise HTTPException(503, "API_ACCESS_TOKEN must be configured (minimum 32 characters)")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Bearer token required")
    if not secrets.compare_digest(authorization[7:], token):
        raise HTTPException(403, "Invalid bearer token")


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "mayo-adpkd-imaging-classifier",
            "component": "nonclinical audit demo"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()) if os.getenv("AUDIT_SECRET_KEY") else 0,
    }


@app.post("/api/audit", dependencies=[Depends(require_token)])
def api_audit(payload: SystemTaskPayload):
    try:
        return supervisor.process_task(payload).to_dict()
    except SecurityException as exc:
        raise HTTPException(400, "Sensitive identifier rejected") from exc


@app.post("/api/chat", dependencies=[Depends(require_token)])
def api_chat(req: ChatRequest):
    try:
        return {"response": supervisor.query_supervisory_chat(req.query)}
    except SecurityException as exc:
        raise HTTPException(400, "Sensitive identifier rejected") from exc


@app.get("/api/audit/logs", dependencies=[Depends(require_token)])
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(),
            "verified": AuditLogger.verify_integrity()}
