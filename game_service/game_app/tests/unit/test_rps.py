"""
==========================================
RPS (ROCK-PAPER-SCISSORS) LOGIC UNIT TESTS
==========================================

PURPOSE:
--------
Pure unit tests for the core game logic - Rock-Paper-Scissors with power values.
Tests the rps.py module that determines round winners.

WHAT IS TESTED:
---------------
1. Basic RPS Rules:
   - Rock beats Scissors (regardless of power)
   - Scissors beats Paper (regardless of power)
   - Paper beats Rock (regardless of power)

2. Same Category Resolution:
   - Higher power wins when categories match
   - Equal power results in draw when categories match

3. Winner Determination:
   - Correct winner ("p1", "p2", or None for draw)
   - Reason string explains why (e.g., "rock beats scissors")

GAME RULES:
-----------
The game uses Rock-Paper-Scissors rules with a twist:
1. Different categories: Category rules apply (rock > scissors > paper > rock)
2. Same category: Higher power value wins
3. Same category AND power: Draw (no winner)

HOW TO RUN:
-----------
These are PURE UNIT TESTS - no dependencies required.

Run all unit tests:
    $ cd game_service
    $ pytest game_app/tests/unit/ -v

Run RPS tests only:
    $ pytest game_app/tests/unit/test_rps.py -v

Run specific test:
    $ pytest game_app/tests/unit/test_rps.py::test_rock_beats_scissors -v

Run with verbose output:
    $ pytest game_app/tests/unit/test_rps.py -v -s

FIXTURES USED:
--------------
None - these tests create Card objects directly (no database needed).

NOTES:
------
- These are TRUE UNIT TESTS - fastest to run
- No external dependencies (no DB, no services)
- Test pure game logic
- Use Card domain models directly
- Critical for game correctness
"""

import pytest
from game_app.logic.models import Card
from game_app.logic.rps import rps_outcome

def test_rock_beats_scissors():
    c1 = Card(id=1, category="rock", power=1)
    c2 = Card(id=2, category="scissors", power=9)
    result = rps_outcome(c1, c2)
    assert result.winner == "p1"
    assert "rock" in result.reason

def test_scissors_beats_paper():
    c1 = Card(id=1, category="scissors", power=3)
    c2 = Card(id=2, category="paper", power=5)
    result = rps_outcome(c1, c2)
    assert result.winner == "p1"

def test_paper_beats_rock():
    c1 = Card(id=1, category="paper", power=2)
    c2 = Card(id=3, category="rock", power=7)
    result = rps_outcome(c1, c2)
    assert result.winner == "p1"

def test_same_category_higher_power_wins():
    c1 = Card(id=1, category="rock", power=4)
    c2 = Card(id=4, category="rock", power=2)
    result = rps_outcome(c1, c2)
    assert result.winner == "p1"

def test_same_category_equal_power_draw():
    c1 = Card(id=8, category="paper", power=3)
    c2 = Card(id=3, category="paper", power=3)
    result = rps_outcome(c1, c2)
    assert result.winner is None
