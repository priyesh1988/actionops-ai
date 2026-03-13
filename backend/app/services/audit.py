from app.schemas.models import AuditEvent
from app.services import store


def write_audit(incident_id: str, event_type: str, actor: str, payload: dict) -> None:
    store.create_audit(AuditEvent(incident_id=incident_id, event_type=event_type, actor=actor, payload=payload))
