from __future__ import annotations

import json

import requests

from app.core.config import settings
from app.schemas.models import Incident


class NotificationFanout:
    def send_recovery_event(self, incident: Incident, action_id: str, status: str, actor: str) -> list[str]:
        sent: list[str] = []
        text = f"[{status}] {incident.service} {incident.environment.value}: {action_id} by {actor} for incident {incident.id}"
        if settings.slack_webhook_url:
            requests.post(settings.slack_webhook_url, json={"text": text}, timeout=5)
            sent.append("slack")
        if settings.pagerduty_routing_key:
            payload = {
                "routing_key": settings.pagerduty_routing_key,
                "event_action": "trigger" if status != "completed" else "resolve",
                "payload": {
                    "summary": text,
                    "source": "actionops-ai",
                    "severity": "warning" if incident.environment.value != "prod" else "error",
                    "custom_details": {
                        "incident_id": incident.id,
                        "service": incident.service,
                        "environment": incident.environment.value,
                        "action_id": action_id,
                        "actor": actor,
                    },
                },
            }
            requests.post(settings.pagerduty_event_url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=5)
            sent.append("pagerduty")
        return sent
