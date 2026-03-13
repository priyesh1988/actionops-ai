from __future__ import annotations

from app.core.config import settings


class ArgoRolloutsClient:
    def run_action(self, service: str, environment: str, action_id: str) -> str:
        base = settings.argo_rollouts_base_url
        ns = settings.argo_namespace
        if action_id == "rollback_release":
            return f"Argo rollout undo requested for {service} in namespace {ns} ({environment}) via {base or 'simulated adapter'}"
        if action_id == "pause_rollout_and_notify":
            return f"Argo rollout paused for {service} in namespace {ns} ({environment}) via {base or 'simulated adapter'}"
        if action_id == "restart_deployment":
            return f"Deployment restart requested for {service} in namespace {ns} ({environment}) via {base or 'simulated adapter'}"
        return f"No direct Argo mapping for {action_id}; simulated action recorded for {service}"
