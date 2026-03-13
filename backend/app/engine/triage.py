from __future__ import annotations

from app.engine.playbooks import PLAYBOOKS
from app.engine.policy import requires_approval
from app.schemas.models import Incident, Recommendation


def _infer_cause(incident: Incident) -> tuple[str, float, list[str]]:
    error_blob = str(incident.signals).lower()
    if "secret" in error_blob:
        return "missing_secret", 0.91, ["rollback_release", "pause_rollout_and_notify"]
    if "crashloop" in error_blob or "crash loop" in error_blob:
        return "runtime_crash_loop", 0.72, ["restart_deployment", "rollback_release"]
    if "timeout" in error_blob or "queue" in error_blob:
        return "stuck_async_job", 0.83, ["retry_job", "enable_safe_mode"]
    return "unknown", 0.52, ["pause_rollout_and_notify"]


def triage_incident(incident: Incident) -> list[Recommendation]:
    probable_cause, confidence, action_ids = _infer_cause(incident)
    incident.probable_cause = probable_cause
    incident.confidence = confidence
    incident.triage_summary = f"Likely cause: {probable_cause}; confidence={confidence:.2f}"

    recs: list[Recommendation] = []
    for action_id in action_ids:
        approval_needed, _ = requires_approval(incident, action_id, confidence)
        playbook = PLAYBOOKS[action_id]
        recs.append(
            Recommendation(
                action_id=action_id,
                probable_cause=probable_cause,
                confidence=confidence,
                risk_level=playbook["risk_level"],
                blast_radius=playbook["blast_radius"],
                requires_approval=approval_needed,
                explanation=f"{action_id} recommended because the issue resembles {probable_cause}",
            )
        )
    return recs
