from fastapi import FastAPI

from .db import Base, engine
from .routers import players, matches


app = FastAPI(
    title="Tri-Duel Player Service",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    import os
    import time
    from sqlalchemy.exc import OperationalError

    if os.getenv("TESTING"):
        return

    # Docker/Postgres can be "healthy" but still not immediately reachable from other containers.
    # Retry a few times instead of crashing the container.
    last_error: Exception | None = None
    for _ in range(30):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError as e:
            last_error = e
            time.sleep(1)

    raise last_error or RuntimeError("Database not reachable")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


app.include_router(players.router)
app.include_router(matches.router)
