from fastapi import FastAPI

from game_app.api.router import router
from game_app.database.database import Base, engine, SessionLocal

# Import models so Base.metadata knows about them
from game_app.database.models import *
from game_app.database.init.initialize_cards import init_cards

app = FastAPI(
    title="Tri-Duel Game Service",
    description="""
    🎮 **Tri-Duel Game Service** - Match logic and card game engine
    
    ## Features
    * 🃏 Create and manage matches
    * 🎯 Submit moves and resolve rounds
    * 🪨📄✂️ Rock-Paper-Scissors card mechanics
    * 🎨 Beautiful SVG card display
    
    ## Card Display
    Use `/cards` endpoints to view all available cards with SVG visualization.
    No authentication required for viewing cards!
    
    ## Authentication
    Protected endpoints require JWT Bearer token from Auth Service.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

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
@app.get("/health")
def health_check():
    return {"status": "ok"}
