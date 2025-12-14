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
    if os.getenv("TESTING"):
        return
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


app.include_router(players.router)
app.include_router(matches.router)
