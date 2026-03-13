# ActionOps AI Architecture

## Control plane
FastAPI exposes incident lifecycle APIs for create, triage, approve, execute, audit, and summary.

## Auth
- `dev` mode for local workflows using `X-Role` and `X-Actor`
- `jwt` mode for enterprise environments using issuer/audience/JWKS or shared-secret validation
- role claims map into a fixed operational hierarchy

## Data model
PostgreSQL-compatible schema persists:
- incidents
- approvals
- executions
- audit events

## Policy flow
1. classify probable cause
2. rank recommended actions
3. derive required role based on environment + confidence + playbook risk
4. require approval where policy says so
5. execute only when authorization and approvals satisfy policy

## Recovery adapters
- Argo Rollouts-backed adapter for rollback, pause, and restart paths
- internal adapter path for retry-job and safe-mode operations
- notification fanout to Slack and PagerDuty

## Observability
- `/metrics` for Prometheus scraping
- OpenTelemetry spans for FastAPI and SQLAlchemy
- OTLP export to Jaeger or another collector

## Future hardening
- Alembic migrations
- service-to-service mTLS
- tenant isolation and policy packs
- signed runbook bundles and change windows
- evidence bundle storage in object storage
