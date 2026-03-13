from app.engine.playbooks import PLAYBOOKS
from app.schemas.models import Environment, Incident


def requires_approval(incident: Incident, action_id: str, confidence: float) -> tuple[bool, str]:
    playbook = PLAYBOOKS[action_id]
    required_role = playbook["required_role"]

    if incident.environment == Environment.prod and action_id == "rollback_release":
        return True, "prod_approver"
    if incident.environment == Environment.prod and confidence < 0.80:
        return True, "senior_sre"
    if incident.environment != Environment.prod and playbook["risk_level"] == "low":
        return False, required_role
    return incident.environment == Environment.prod, required_role


def can_execute(role: str, required_role: str) -> bool:
    hierarchy = {
        "viewer": 0,
        "support": 1,
        "sre": 2,
        "senior_sre": 3,
        "prod_approver": 4,
        "platform_admin": 5,
    }
    return hierarchy[role] >= hierarchy[required_role]
