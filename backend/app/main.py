from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings
from app.core.observability import setup_observability

app = FastAPI(title=settings.app_name, version=settings.app_version)
setup_observability(app)
app.include_router(router, prefix=settings.api_prefix)


@app.get("/health")
def health() -> dict[str, bool | str]:
    return {"ok": True, "env": settings.app_env}
