from fastapi import FastAPI

from game_app.api.router import router
from game_app.database.database import Base, engine, SessionLocal

# Import models so Base.metadata knows about them
from game_app.database.models import *
from game_app.database.init.initialize_cards import init_cards

app = FastAPI()

@app.on_event("startup")
def startup_event():
    # Create tables if not exist
    Base.metadata.create_all(bind=engine)

    # Initialize card definitions (dev only)
    db = SessionLocal()
    try:
        init_cards(db, reset=False)  # reset=False to avoid wiping DB each restart
    finally:
        db.close()


# ============================================================
# ROUTERS
# ============================================================
app.include_router(router)


# ============================================================
# HEALTH CHECK
# ============================================================
@app.get("/")
def root():
    return {"status": "ok"}
