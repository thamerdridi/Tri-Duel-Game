"""
Card Service - handles card retrieval and SVG generation.
"""
from sqlalchemy.orm import Session
from typing import Optional

from game_app.database.models import CardDefinition
from game_app.utils.card_svg import generate_card_svg


class CardService:
    """Service for managing card SVG generation."""

    def __init__(self, db: Session):
        self.db = db

    def generate_card_svg(self, card_id: int) -> Optional[str]:
        """
        Generate SVG visualization for a single card.

        Args:
            card_id: Card definition ID

        Returns:
            str: SVG XML string, or None if card not found
        """
        card = (
            self.db.query(CardDefinition)
            .filter(CardDefinition.id == card_id, CardDefinition.active == True)
            .first()
        )

        if not card:
            return None

        return generate_card_svg(card.id, card.category, card.power)


    def generate_deck_gallery_svg(self) -> str:
        """
        Generate SVG showing all available cards in a grid.

        Returns:
            str: SVG with all cards in grid layout
        """
        from game_app.utils.card_deck_svg import generate_deck_grid_svg

        # Get all cards
        cards = (
            self.db.query(CardDefinition)
            .filter(CardDefinition.active == True)
            .order_by(CardDefinition.category, CardDefinition.power)
            .all()
        )

        # Convert to dicts for SVG generator
        card_dicts = [
            {
                "id": card.id,
                "category": card.category,
                "power": card.power,
            }
            for card in cards
        ]

        return generate_deck_grid_svg(card_dicts)

