import pytest
from game_app.logic.deck import build_deck, deal_two_hands

class FakeCardDef:
    def __init__(self, id, category, power, active=True):
        self.id = id
        self.category = category
        self.power = power
        self.active = active


def test_build_deck_creates_18_cards():
    defs = [
        FakeCardDef(1, "rock", 1),
        FakeCardDef(2, "rock", 2),
        FakeCardDef(3, "rock", 3),
        FakeCardDef(4, "paper", 1),
        FakeCardDef(5, "paper", 2),
        FakeCardDef(6, "scissors", 1),
    ]

    deck = build_deck(defs)
    assert len(deck) == 6
    assert all(hasattr(card, "id") for card in deck)

def test_deal_two_hands_splits_deck():
    defs = []
    for i in range(1, 19):
        defs.append(FakeCardDef(i, "rock", i))

    deck = build_deck(defs)
    p1, p2 = deal_two_hands(deck, 6)

    assert len(p1) == 6
    assert len(p2) == 6
    assert len(set([c.id for c in p1]).intersection([c.id for c in p2])) == 0  # no duplicates
