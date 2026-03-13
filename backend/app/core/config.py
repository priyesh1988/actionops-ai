from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "dev"
    app_name: str = "ActionOps AI"
    app_version: str = "0.2.0"
    api_prefix: str = "/api/v1"

    default_automation_level: str = "advisory"

    auth_mode: str = "dev"  # dev|jwt
    jwt_issuer: str | None = None
    jwt_audience: str | None = None
    jwt_jwks_url: str | None = None
    jwt_shared_secret: str = "change-me"
    jwt_algorithms: str = "HS256,RS256"

    database_url: str = "sqlite:///./actionops.db"

    slack_webhook_url: str | None = None
    pagerduty_routing_key: str | None = None
    pagerduty_event_url: str = "https://events.pagerduty.com/v2/enqueue"

    argo_rollouts_base_url: str | None = None
    argo_rollouts_token: str | None = None
    argo_namespace: str = "default"

    otel_enabled: bool = True
    otel_service_name: str = "actionops-backend"
    otel_exporter_otlp_endpoint: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
