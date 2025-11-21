from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Card
from ..schemas import CardOut


router = APIRouter(
    prefix="/cards",
    tags=["cards"],
)


@router.get("", response_model=List[CardOut])
def list_cards(db: Session = Depends(get_db)):
    cards = db.query(Card).order_by(Card.category, Card.power).all()
    return cards


@router.get("/{card_id}", response_model=CardOut)
def get_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return card
