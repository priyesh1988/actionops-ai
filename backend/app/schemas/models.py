from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Environment(str, Enum):
    dev = "dev"
    staging = "staging"
    prod = "prod"


class IncidentStatus(str, Enum):
    open = "open"
    triaged = "triaged"
    awaiting_approval = "awaiting_approval"
    approved = "approved"
    recovered = "recovered"
    escalated = "escalated"
    failed = "failed"


class IncidentCreate(BaseModel):
    title: str
    service: str
    environment: Environment
    source: str
    category: str
    signals: dict[str, Any] = Field(default_factory=dict)


class Incident(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    service: str
    environment: Environment
    source: str
    category: str
    signals: dict[str, Any] = Field(default_factory=dict)
    triage_summary: str | None = None
    probable_cause: str | None = None
    confidence: float | None = None
    status: IncidentStatus = IncidentStatus.open
    created_at: datetime = Field(default_factory=utc_now)


class Recommendation(BaseModel):
    action_id: str
    probable_cause: str
    confidence: float
    risk_level: str
    blast_radius: str
    requires_approval: bool
    explanation: str


class TriageResponse(BaseModel):
    incident: Incident
    recommendations: list[Recommendation]


class ApprovalRequest(BaseModel):
    action_id: str
    decision: str
    reason: str


class ApprovalRecord(BaseModel):
    incident_id: str
    action_id: str
    status: str
    required_role: str
    reason: str
    approver: str
    decided_at: datetime = Field(default_factory=utc_now)


class ExecuteRequest(BaseModel):
    action_id: str


class ExecutionRecord(BaseModel):
    incident_id: str
    action_id: str
    status: str
    output: str
    verification_status: str
    executed_by: str
    executed_at: datetime = Field(default_factory=utc_now)


class AuditEvent(BaseModel):
    incident_id: str
    event_type: str
    actor: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class IncidentSummary(BaseModel):
    open_count: int
    awaiting_approval_count: int
    recovered_count: int
    failed_count: int
    total_count: int
