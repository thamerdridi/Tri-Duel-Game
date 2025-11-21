from fastapi import FastAPI

from .db import Base, engine, SessionLocal
from . import models
from .routers import card, players, matches


app = FastAPI(
    title="Tri-Duel Player Service",
    version="0.1.0",
)


def seed_cards() -> None:
    """
    Seed the 18 Tri-Duel cards if the cards table is empty.
    """
    db = SessionLocal()
    try:
        count = db.query(models.Card).count()
        if count > 0:
            return

        deck = {
            "rock":     [1, 2, 3, 4, 6, 9],
            "paper":    [1, 2, 3, 5, 7, 9],
            "scissors": [1, 2, 4, 5, 7, 8],
        }

        for category, powers in deck.items():
            for power in powers:
                card = models.Card(
                    category=category,
                    power=power,
                    name=f"{category.capitalize()} {power}",
                    description=None,
                )
                db.add(card)

        db.commit()
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    # Create tables
    Base.metadata.create_all(bind=engine)
    # Seed deck
    seed_cards()


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


# Attach feature routers explicitly
app.include_router(card.router)
app.include_router(players.router)
app.include_router(matches.router)
