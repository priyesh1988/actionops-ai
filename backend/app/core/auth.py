from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import jwt
import requests
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

ALLOWED_ROLES = {"viewer", "support", "sre", "senior_sre", "prod_approver", "platform_admin"}
security = HTTPBearer(auto_error=False)


@dataclass
class Principal:
    subject: str
    role: str
    email: str | None = None
    claims: dict[str, Any] | None = None


@lru_cache(maxsize=1)
def _jwks_client() -> jwt.PyJWKClient | None:
    if settings.jwt_jwks_url:
        return jwt.PyJWKClient(settings.jwt_jwks_url)
    return None


def _parse_role(claims: dict[str, Any]) -> str | None:
    candidates = [
        claims.get("role"),
        claims.get("roles", [None])[0] if isinstance(claims.get("roles"), list) and claims.get("roles") else None,
        claims.get("https://actionops.ai/role"),
    ]
    for role in candidates:
        if role in ALLOWED_ROLES:
            return role
    return None


def _decode_jwt(token: str) -> dict[str, Any]:
    algorithms = [alg.strip() for alg in settings.jwt_algorithms.split(",") if alg.strip()]
    options = {"verify_aud": bool(settings.jwt_audience), "verify_iss": bool(settings.jwt_issuer)}
    if settings.jwt_jwks_url:
        signing_key = _jwks_client().get_signing_key_from_jwt(token).key  # type: ignore[union-attr]
        return jwt.decode(token, signing_key, algorithms=algorithms, audience=settings.jwt_audience, issuer=settings.jwt_issuer, options=options)
    return jwt.decode(token, settings.jwt_shared_secret, algorithms=algorithms, audience=settings.jwt_audience, issuer=settings.jwt_issuer, options=options)


def get_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_role: str | None = Header(default=None),
    x_actor: str | None = Header(default="dev-user"),
) -> Principal:
    if settings.auth_mode == "dev":
        if not x_role:
            raise HTTPException(status_code=401, detail="Missing X-Role header")
        if x_role not in ALLOWED_ROLES:
            raise HTTPException(status_code=403, detail="Unknown role")
        return Principal(subject=x_actor or "dev-user", role=x_role, email=None, claims={"mode": "dev"})

    if not credentials:
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        claims = _decode_jwt(credentials.credentials)
    except (jwt.InvalidTokenError, requests.RequestException) as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc
    role = _parse_role(claims)
    if role is None:
        raise HTTPException(status_code=403, detail="No supported role claim found")
    return Principal(
        subject=claims.get("sub", "unknown"),
        role=role,
        email=claims.get("email"),
        claims=claims,
    )
