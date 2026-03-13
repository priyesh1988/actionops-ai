# ActionOps AI

**AI issue triage and permissioned recovery platform for end-to-end product deployment.**

ActionOps AI ingests deployment failures, application incidents, and workflow errors; explains probable root cause; calculates blast radius and confidence; enforces policy and approvals; executes approved recovery actions; persists the full timeline in PostgreSQL; and emits metrics/traces for enterprise operations.

## Core workflow

```text
Detect -> Correlate -> Diagnose -> Recommend -> Check policy -> Request approval -> Execute -> Verify -> Notify -> Audit
```

## Architecture highlights

### Control plane
FastAPI API for incident intake, triage, approval, execution, audit, and summary reporting.

### Policy and permissions
Role hierarchy and environment-aware controls determine whether an action can run directly, needs approval, or must escalate.

### Persistence layer
All incidents, approvals, executions, and audit events are stored in PostgreSQL-compatible schema through SQLAlchemy.

### Recovery adapters
Playbooks route to execution adapters. Argo Rollouts-backed actions are modeled for rollback, pause, and restart flows.

### Notifications
Slack and PagerDuty hooks can be emitted after approvals or recovery execution.

### Observability
Prometheus scrapes `/metrics`; OpenTelemetry instruments FastAPI and SQLAlchemy and can export spans through OTLP.

## Quickstart

```bash
cp .env.example .env
make up
make seed
make test
```

Backend API: `http://localhost:8080/docs`

Frontend UI: `http://localhost:5173`

Prometheus: `http://localhost:9090`

Jaeger: `http://localhost:16686`

## Local auth modes

### Dev mode
Default local mode. Requests use headers:

```bash
-H 'X-Role: sre' -H 'X-Actor: priyesh'
```

### JWT mode
Set in `.env`:

```bash
AUTH_MODE=jwt
JWT_ISSUER=https://issuer.example.com/
JWT_AUDIENCE=actionops-api
JWT_JWKS_URL=https://issuer.example.com/.well-known/jwks.json
```

Or use shared-secret validation for local signing:

```bash
AUTH_MODE=jwt
JWT_SHARED_SECRET=change-me
```

Accepted role claims:
- `role`
- first value in `roles`
- `https://actionops.ai/role`

Supported roles:
- `viewer`
- `support`
- `sre`
- `senior_sre`
- `prod_approver`
- `platform_admin`

## Example API flow

### Create an incident

```bash
curl -s http://localhost:8080/api/v1/incidents \
  -H 'Content-Type: application/json' \
  -H 'X-Role: sre' \
  -H 'X-Actor: oncall-sre' \
  -d '{
    "title": "payment-api deploy failed",
    "service": "payment-api",
    "environment": "prod",
    "source": "github-actions",
    "category": "deployment_failure",
    "signals": {
      "error": "Secret payment-api-db-url not found",
      "commit_sha": "abc1234",
      "region": "us-west-2"
    }
  }'
```

### Triage the incident

```bash
curl -s http://localhost:8080/api/v1/incidents/<incident_id>/triage \
  -X POST -H 'X-Role: sre' -H 'X-Actor: oncall-sre'
```

### Approve rollback in production

```bash
curl -s http://localhost:8080/api/v1/incidents/<incident_id>/approve \
  -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Role: prod_approver' \
  -H 'X-Actor: prod-approver-1' \
  -d '{"action_id":"rollback_release","decision":"approved","reason":"Healthy last release available"}'
```

### Execute recovery

```bash
curl -s http://localhost:8080/api/v1/incidents/<incident_id>/execute \
  -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Role: sre' \
  -H 'X-Actor: oncall-sre' \
  -d '{"action_id":"rollback_release"}'
```

### View metrics summary

```bash
curl -s http://localhost:8080/api/v1/summary -H 'X-Role: viewer'
```

## Repo layout

```text
actionops-ai/
├── backend/                 # FastAPI control plane
│   ├── app/api              # REST endpoints
│   ├── app/core             # config, auth, observability
│   ├── app/db               # SQLAlchemy models and session
│   ├── app/engine           # triage, policy, playbooks
│   ├── app/integrations     # Argo, Slack, PagerDuty adapters
│   └── app/services         # persistence, audit, recovery
├── frontend/                # React/Vite ops console
├── deploy/helm/actionops/   # Helm chart
├── deploy/observability/    # Prometheus config
├── k8s/                     # Raw Kubernetes manifests
├── docs/                    # Architecture notes
└── tests/                   # API tests
```

## Production deployment notes

- Point `DATABASE_URL` to managed PostgreSQL
- Set `AUTH_MODE=jwt` and configure issuer/audience/JWKS
- Wire `SLACK_WEBHOOK_URL` and/or `PAGERDUTY_ROUTING_KEY`
- Set `ARGO_ROLLOUTS_BASE_URL` and token for real rollout control
- Export traces to your collector with `OTEL_EXPORTER_OTLP_ENDPOINT`
- Scrape `/metrics` with Prometheus or a compatible collector

## Example success scenario

1. `payment-api` rollout fails because a secret reference is missing.
2. Triage classifies `missing_secret` with high confidence.
3. Recommendations include `rollback_release` and `pause_rollout_and_notify`.
4. Policy requires production approval for rollback.
5. A `prod_approver` approves.
6. ActionOps executes the Argo-backed rollback, emits audit + notification events, and marks the incident recovered.

## Example escalation scenario

1. `checkout` enters repeated crash loops after config rollout.
2. Confidence is moderate, so the system will not self-heal in production.
3. Policy requires elevated approval.
4. After execution, verification remains inconclusive.
5. ActionOps records the failed recovery and escalates with the incident timeline intact.

## License

All Rights Reserved.
