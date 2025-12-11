"""
Card Service - handles card retrieval and image generation logic.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from io import BytesIO

from game_app.database.models import CardDefinition
from game_app.utils.card_image import generate_card_image, generate_card_thumbnail


class CardService:
    """Service for managing card retrieval and image generation."""

    def __init__(self, db: Session):
        self.db = db

    def get_all_cards(self) -> List[Dict]:
        """
        Get all active cards with image URLs.

        Returns:
            List of card dicts with basic info and image URLs
        """
        cards = (
            self.db.query(CardDefinition)
            .filter(CardDefinition.active == True)
            .order_by(CardDefinition.category, CardDefinition.power)
            .all()
        )

        return [
            {
                "id": card.id,
                "category": card.category,
                "power": card.power,
                "image_url": f"/cards/{card.id}/image",
                "thumbnail_url": f"/cards/{card.id}/thumbnail"
            }
            for card in cards
        ]

    def get_card_by_id(self, card_id: int) -> Optional[Dict]:
        """
        Get single card by ID with full details.

        Args:
            card_id: Card definition ID

        Returns:
            Card dict with details and image URLs, or None if not found
        """
        card = (
            self.db.query(CardDefinition)
            .filter(CardDefinition.id == card_id, CardDefinition.active == True)
            .first()
        )

        if not card:
            return None

        # Game rules
        rules = {
            "rock": {"beats": "scissors", "loses_to": "paper"},
            "paper": {"beats": "rock", "loses_to": "scissors"},
            "scissors": {"beats": "paper", "loses_to": "rock"}
        }

        rule = rules.get(card.category, {})

        return {
            "id": card.id,
            "category": card.category,
            "power": card.power,
            "image_url": f"/cards/{card.id}/image",
            "thumbnail_url": f"/cards/{card.id}/thumbnail",
            "beats": rule.get("beats", "unknown"),
            "loses_to": rule.get("loses_to", "unknown"),
            "rarity": self._get_rarity(card.power)
        }

    def generate_card_image(self, card_id: int) -> Optional[BytesIO]:
        """
        Generate PNG image for a card.

        Args:
            card_id: Card definition ID

        Returns:
            BytesIO with PNG image, or None if card not found
        """
        card = (
            self.db.query(CardDefinition)
            .filter(CardDefinition.id == card_id, CardDefinition.active == True)
            .first()
        )

        if not card:
            return None

        return generate_card_image(card.id, card.category, card.power)

    def generate_card_thumbnail(self, card_id: int) -> Optional[BytesIO]:
        """
        Generate PNG thumbnail for a card.

        Args:
            card_id: Card definition ID

        Returns:
            BytesIO with PNG thumbnail, or None if card not found
        """
        card = (
            self.db.query(CardDefinition)
            .filter(CardDefinition.id == card_id, CardDefinition.active == True)
            .first()
        )

        if not card:
            return None

        return generate_card_thumbnail(card.id, card.category, card.power)

    def _get_rarity(self, power: int) -> str:
        """
        Determine card rarity based on power level.

        Args:
            power: Card power level

        Returns:
            Rarity string
        """
        if power >= 7:
            return "legendary"
        elif power >= 5:
            return "rare"
        else:
            return "common"
