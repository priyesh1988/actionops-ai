from app.adapters.executor import ExecutorAdapter
from app.engine.playbooks import PLAYBOOKS
from app.engine.policy import can_execute, requires_approval
from app.integrations.notifiers import NotificationFanout
from app.schemas.models import ApprovalRecord, ExecuteRequest, ExecutionRecord, Incident, IncidentStatus
from app.services import store
from app.services.audit import write_audit


executor = ExecutorAdapter()
notifier = NotificationFanout()


def approve_action(incident: Incident, action_id: str, actor: str, role: str, decision: str, reason: str) -> ApprovalRecord:
    _, required_role = requires_approval(incident, action_id, incident.confidence or 0.0)
    if not can_execute(role, required_role):
        raise PermissionError(f"Role {role} cannot approve action requiring {required_role}")

    record = ApprovalRecord(
        incident_id=incident.id,
        action_id=action_id,
        status=decision,
        required_role=required_role,
        reason=reason,
        approver=actor,
    )
    store.create_approval(record)
    incident.status = IncidentStatus.approved if decision == "approved" else IncidentStatus.escalated
    store.update_incident(incident)
    write_audit(incident.id, "approval", actor, record.model_dump(mode="json"))
    return record


def execute_action(incident: Incident, request: ExecuteRequest, actor: str, role: str) -> ExecutionRecord:
    approval_needed, required_role = requires_approval(incident, request.action_id, incident.confidence or 0.0)
    approved = any(
        a.incident_id == incident.id and a.action_id == request.action_id and a.status == "approved"
        for a in store.get_approvals(incident.id)
    )
    if approval_needed and not approved:
        raise PermissionError("Approval required before execution")
    if not can_execute(role, required_role):
        raise PermissionError(f"Role {role} cannot execute action requiring {required_role}")

    output = executor.run(incident, request.action_id)
    verification_status = "passed" if incident.probable_cause != "unknown" else "manual-check-required"
    status = "completed" if verification_status == "passed" else "needs-escalation"
    incident.status = IncidentStatus.recovered if verification_status == "passed" else IncidentStatus.failed
    store.update_incident(incident)
    record = ExecutionRecord(
        incident_id=incident.id,
        action_id=request.action_id,
        status=status,
        output=output,
        verification_status=verification_status,
        executed_by=actor,
    )
    store.create_execution(record)
    channels = notifier.send_recovery_event(incident, request.action_id, status, actor)
    write_audit(
        incident.id,
        "execution",
        actor,
        {**record.model_dump(mode="json"), "notifications": channels, "playbook": PLAYBOOKS.get(request.action_id, {})},
    )
    return record


def list_actions() -> dict:
    return PLAYBOOKS
