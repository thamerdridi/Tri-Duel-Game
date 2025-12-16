from contextlib import asynccontextmanager
from fastapi import FastAPI

from .db import Base, engine
from .routers import players, matches


@asynccontextmanager
async def lifespan(app: FastAPI):
    import os
    import time
    from sqlalchemy.exc import OperationalError

    if not os.getenv("TESTING"):
        # Docker/Postgres can be "healthy" but still not immediately reachable from other containers.
        # Retry a few times instead of crashing the container.
        last_error: Exception | None = None
        for _ in range(30):
            try:
                Base.metadata.create_all(bind=engine)
                break
            except OperationalError as e:
                last_error = e
                time.sleep(1)
        else:
            raise last_error or RuntimeError("Database not reachable")

    yield


app = FastAPI(
    title="Tri-Duel Player Service",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


app.include_router(players.router)
app.include_router(matches.router)
