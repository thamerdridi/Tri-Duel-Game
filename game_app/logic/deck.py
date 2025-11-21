import random
from game_app.logic.models import Card
from game_app.configs.logic_configs import HAND_SIZE

def build_deck(card_definitions) -> list[Card]:
    """
    card_definitions: list of card definitions from database, ex. CardDefinition
    :returns list of Card objects to use in game.
    """
    deck = [
        Card(id=cd.id, category=cd.category, power=cd.power)
        for cd in card_definitions
        if cd.active
    ]
    random.shuffle(deck)
    return deck

def deal_two_hands(full_deck: list[Card], hand_size: int = HAND_SIZE):
    """
    Deals two hands from the full deck.
    :returns (hand_p1, hand_p2)
    """
    if len(full_deck) <= hand_size * 2:
        raise Exception(f"Too few cards in deck - deck contains {len(full_deck)} and each hand has {hand_size}")

    hand_p1 = full_deck[:hand_size]
    hand_p2 = full_deck[hand_size : hand_size * 2]
    leftover = full_deck[hand_size * 2 :]

    return hand_p1, hand_p2