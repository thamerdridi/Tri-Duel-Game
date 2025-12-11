"""
Card Service - handles card retrieval and image generation logic with caching.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from io import BytesIO
from functools import lru_cache

from game_app.database.models import CardDefinition
from game_app.utils.card_image import generate_card_image, generate_card_thumbnail


# Module-level cached functions (shared across all CardService instances)
@lru_cache(maxsize=128)
def _cached_generate_card_image(card_id: int, category: str, power: int) -> bytes:
    """
    Generate and cache card image as bytes.

    This function is cached at module level so all CardService instances
    share the same cache. Caches up to 128 unique cards.

    Args:
        card_id: Card definition ID
        category: Card category (rock, paper, scissors)
        power: Card power level

    Returns:
        bytes: PNG image data
    """
    img_io = generate_card_image(card_id, category, power)
    return img_io.read()


@lru_cache(maxsize=128)
def _cached_generate_card_thumbnail(card_id: int, category: str, power: int) -> bytes:
    """
    Generate and cache card thumbnail as bytes.

    This function is cached at module level so all CardService instances
    share the same cache. Caches up to 128 unique thumbnails.

    Args:
        card_id: Card definition ID
        category: Card category (rock, paper, scissors)
        power: Card power level

    Returns:
        bytes: PNG thumbnail data
    """
    img_io = generate_card_thumbnail(card_id, category, power)
    return img_io.read()


class CardService:
    """Service for managing card retrieval and image generation with caching."""

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
        Generate PNG image for a card with caching.

        First call: generates image and caches it (~50-100ms)
        Subsequent calls: returns cached image (~0.1ms) - 500-1000x faster!

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

        # Get cached bytes (uses lru_cache)
        cached_bytes = _cached_generate_card_image(card.id, card.category, card.power)

        # Return new BytesIO with cached data
        return BytesIO(cached_bytes)

    def generate_card_thumbnail(self, card_id: int) -> Optional[BytesIO]:
        """
        Generate PNG thumbnail for a card with caching.

        First call: generates thumbnail and caches it (~20-50ms)
        Subsequent calls: returns cached thumbnail (~0.1ms) - 200-500x faster!

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

        # Get cached bytes (uses lru_cache)
        cached_bytes = _cached_generate_card_thumbnail(card.id, card.category, card.power)

        # Return new BytesIO with cached data
        return BytesIO(cached_bytes)

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

    @staticmethod
    def clear_cache():
        """
        Clear the image cache.

        Useful for testing or when card designs change.
        """
        _cached_generate_card_image.cache_clear()
        _cached_generate_card_thumbnail.cache_clear()

    @staticmethod
    def get_cache_info():
        """
        Get cache statistics for monitoring.

        Returns:
            Dict with cache hits, misses, size, maxsize
        """
        return {
            "images": {
                "hits": _cached_generate_card_image.cache_info().hits,
                "misses": _cached_generate_card_image.cache_info().misses,
                "size": _cached_generate_card_image.cache_info().currsize,
                "maxsize": _cached_generate_card_image.cache_info().maxsize,
            },
            "thumbnails": {
                "hits": _cached_generate_card_thumbnail.cache_info().hits,
                "misses": _cached_generate_card_thumbnail.cache_info().misses,
                "size": _cached_generate_card_thumbnail.cache_info().currsize,
                "maxsize": _cached_generate_card_thumbnail.cache_info().maxsize,
            }
        }
