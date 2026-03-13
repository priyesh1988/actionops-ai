from app.integrations.argo_rollouts import ArgoRolloutsClient
from app.schemas.models import Incident


class ExecutorAdapter:
    def __init__(self) -> None:
        self.argo = ArgoRolloutsClient()

    def run(self, incident: Incident, action_id: str) -> str:
        if action_id in {"rollback_release", "pause_rollout_and_notify", "restart_deployment"}:
            return self.argo.run_action(incident.service, incident.environment.value, action_id)
        mapping = {
            "retry_job": f"Retried failed workflow for {incident.service}",
            "enable_safe_mode": f"Enabled safe mode for {incident.service}",
        }
        return mapping.get(action_id, f"Executed {action_id} for {incident.service}")
