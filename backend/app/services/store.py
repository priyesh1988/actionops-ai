from __future__ import annotations

import json
from contextlib import contextmanager

from sqlalchemy import select

from app.db.init_db import init_db
from app.db.models import ApprovalRecordDB, AuditEventDB, ExecutionRecordDB, IncidentRecord
from app.db.session import SessionLocal
from app.schemas.models import ApprovalRecord, AuditEvent, ExecutionRecord, Incident, IncidentStatus, IncidentSummary

init_db()


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _incident_from_row(row: IncidentRecord) -> Incident:
    return Incident(
        id=row.id,
        title=row.title,
        service=row.service,
        environment=row.environment,
        source=row.source,
        category=row.category,
        signals=row.signals,
        triage_summary=row.triage_summary,
        probable_cause=row.probable_cause,
        confidence=row.confidence,
        status=row.status,
        created_at=row.created_at,
    )


def _approval_from_row(row: ApprovalRecordDB) -> ApprovalRecord:
    return ApprovalRecord(
        incident_id=row.incident_id,
        action_id=row.action_id,
        status=row.status,
        required_role=row.required_role,
        reason=row.reason,
        approver=row.approver,
        decided_at=row.decided_at,
    )


def _execution_from_row(row: ExecutionRecordDB) -> ExecutionRecord:
    return ExecutionRecord(
        incident_id=row.incident_id,
        action_id=row.action_id,
        status=row.status,
        output=row.output,
        verification_status=row.verification_status,
        executed_by=row.executed_by,
        executed_at=row.executed_at,
    )


def _audit_from_row(row: AuditEventDB) -> AuditEvent:
    return AuditEvent(
        incident_id=row.incident_id,
        event_type=row.event_type,
        actor=row.actor,
        payload=json.loads(row.payload_json or "{}"),
        created_at=row.created_at,
    )


def create_incident(incident: Incident) -> Incident:
    with session_scope() as session:
        session.add(
            IncidentRecord(
                id=incident.id,
                title=incident.title,
                service=incident.service,
                environment=incident.environment.value,
                source=incident.source,
                category=incident.category,
                signals_json=json.dumps(incident.signals),
                triage_summary=incident.triage_summary,
                probable_cause=incident.probable_cause,
                confidence=incident.confidence,
                status=incident.status.value,
                created_at=incident.created_at,
            )
        )
    return incident


def update_incident(incident: Incident) -> Incident:
    with session_scope() as session:
        row = session.get(IncidentRecord, incident.id)
        if row is None:
            raise KeyError(f"Incident {incident.id} not found")
        row.title = incident.title
        row.service = incident.service
        row.environment = incident.environment.value
        row.source = incident.source
        row.category = incident.category
        row.signals_json = json.dumps(incident.signals)
        row.triage_summary = incident.triage_summary
        row.probable_cause = incident.probable_cause
        row.confidence = incident.confidence
        row.status = incident.status.value
    return incident


def get_incident(incident_id: str) -> Incident | None:
    with session_scope() as session:
        row = session.get(IncidentRecord, incident_id)
        return _incident_from_row(row) if row else None


def list_incidents() -> list[Incident]:
    with session_scope() as session:
        rows = session.scalars(select(IncidentRecord).order_by(IncidentRecord.created_at.desc())).all()
        return [_incident_from_row(r) for r in rows]


def create_approval(record: ApprovalRecord) -> ApprovalRecord:
    with session_scope() as session:
        session.add(
            ApprovalRecordDB(
                incident_id=record.incident_id,
                action_id=record.action_id,
                status=record.status,
                required_role=record.required_role,
                reason=record.reason,
                approver=record.approver,
                decided_at=record.decided_at,
            )
        )
    return record


def get_approvals(incident_id: str) -> list[ApprovalRecord]:
    with session_scope() as session:
        rows = session.scalars(select(ApprovalRecordDB).where(ApprovalRecordDB.incident_id == incident_id)).all()
        return [_approval_from_row(r) for r in rows]


def create_execution(record: ExecutionRecord) -> ExecutionRecord:
    with session_scope() as session:
        session.add(
            ExecutionRecordDB(
                incident_id=record.incident_id,
                action_id=record.action_id,
                status=record.status,
                output=record.output,
                verification_status=record.verification_status,
                executed_by=record.executed_by,
                executed_at=record.executed_at,
            )
        )
    return record


def create_audit(event: AuditEvent) -> AuditEvent:
    with session_scope() as session:
        session.add(
            AuditEventDB(
                incident_id=event.incident_id,
                event_type=event.event_type,
                actor=event.actor,
                payload_json=json.dumps(event.payload, default=str),
                created_at=event.created_at,
            )
        )
    return event


def get_audit_events(incident_id: str) -> list[AuditEvent]:
    with session_scope() as session:
        rows = session.scalars(select(AuditEventDB).where(AuditEventDB.incident_id == incident_id).order_by(AuditEventDB.created_at.asc())).all()
        return [_audit_from_row(r) for r in rows]


def get_summary() -> IncidentSummary:
    incidents = list_incidents()
    return IncidentSummary(
        open_count=sum(1 for i in incidents if i.status == IncidentStatus.open),
        awaiting_approval_count=sum(1 for i in incidents if i.status == IncidentStatus.awaiting_approval),
        recovered_count=sum(1 for i in incidents if i.status == IncidentStatus.recovered),
        failed_count=sum(1 for i in incidents if i.status == IncidentStatus.failed),
        total_count=len(incidents),
    )
