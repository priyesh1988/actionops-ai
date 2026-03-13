from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import Principal, get_principal
from app.engine.triage import triage_incident
from app.schemas.models import ApprovalRequest, ExecuteRequest, Incident, IncidentCreate, TriageResponse
from app.services import store
from app.services.audit import write_audit
from app.services.recovery import approve_action, execute_action, list_actions

router = APIRouter()


@router.get("/actions")
def actions(principal: Principal = Depends(get_principal)) -> dict:
    return {"items": list_actions(), "viewer_role": principal.role, "viewer": principal.subject}


@router.get("/incidents")
def get_incidents(principal: Principal = Depends(get_principal)) -> dict:
    return {"items": store.list_incidents(), "viewer_role": principal.role, "viewer": principal.subject}


@router.get("/summary")
def summary(principal: Principal = Depends(get_principal)) -> dict:
    return {"metrics": store.get_summary(), "viewer_role": principal.role, "viewer": principal.subject}


@router.post("/incidents", response_model=Incident)
def create_incident(payload: IncidentCreate, principal: Principal = Depends(get_principal)) -> Incident:
    incident = Incident(**payload.model_dump())
    store.create_incident(incident)
    write_audit(incident.id, "incident_created", principal.subject, incident.model_dump(mode="json"))
    return incident


@router.post("/incidents/{incident_id}/triage", response_model=TriageResponse)
def triage(incident_id: str, principal: Principal = Depends(get_principal)) -> TriageResponse:
    incident = store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    recs = triage_incident(incident)
    store.update_incident(incident)
    write_audit(incident.id, "triaged", principal.subject, {"recommendations": [r.model_dump(mode='json') for r in recs]})
    return TriageResponse(incident=incident, recommendations=recs)


@router.post("/incidents/{incident_id}/approve")
def approve(incident_id: str, request: ApprovalRequest, principal: Principal = Depends(get_principal)) -> dict:
    incident = store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    try:
        record = approve_action(incident, request.action_id, principal.subject, principal.role, request.decision, request.reason)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {"approval": record}


@router.post("/incidents/{incident_id}/execute")
def execute(incident_id: str, request: ExecuteRequest, principal: Principal = Depends(get_principal)) -> dict:
    incident = store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    try:
        record = execute_action(incident, request, principal.subject, principal.role)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {"execution": record}


@router.get("/incidents/{incident_id}/audit")
def audit(incident_id: str, principal: Principal = Depends(get_principal)) -> dict:
    return {"items": store.get_audit_events(incident_id), "viewer_role": principal.role, "viewer": principal.subject}


@router.post("/demo/seed")
def seed(principal: Principal = Depends(get_principal)) -> dict:
    incident = Incident(
        title="payment-api deploy failed",
        service="payment-api",
        environment="prod",
        source="github-actions",
        category="deployment_failure",
        signals={"error": "Secret payment-api-db-url not found", "commit_sha": "abc1234"},
    )
    store.create_incident(incident)
    write_audit(incident.id, "seeded", principal.subject, incident.model_dump(mode="json"))
    return {"incident_id": incident.id}
