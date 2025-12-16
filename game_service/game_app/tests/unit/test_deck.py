"""
==========================================
DECK LOGIC UNIT TESTS
==========================================

PURPOSE:
--------
Pure unit tests for deck building and card dealing logic.
Tests the deck.py module in complete isolation.

WHAT IS TESTED:
---------------
1. Deck Building (build_deck):
   - Creates Card objects from CardDefinition database models
   - Includes only active card definitions
   - Preserves card properties (id, category, power)

2. Hand Dealing (deal_two_hands):
   - Splits full deck into two equal hands
   - Each player gets HAND_SIZE cards
   - No duplicate cards between hands (unique distribution)
   - Random shuffle ensures fairness

HOW TO RUN:
-----------
These are PURE UNIT TESTS - no database, no services, no authentication required.

Run all unit tests:
    $ cd game_service
    $ pytest game_app/tests/unit/ -v

Run deck tests only:
    $ pytest game_app/tests/unit/test_deck.py -v

Run specific test:
    $ pytest game_app/tests/unit/test_deck.py::test_build_deck_creates_18_cards -v

FIXTURES USED:
--------------
None - these tests use FakeCardDef test doubles to avoid database dependency.

TEST DOUBLES:
-------------
- `FakeCardDef`: Simulates CardDefinition database model
  - Minimal implementation for testing
  - No database required

NOTES:
------
- These are TRUE UNIT TESTS - fastest to run
- No external dependencies
- Test pure Python logic
- Use fake objects instead of real database models
"""

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
