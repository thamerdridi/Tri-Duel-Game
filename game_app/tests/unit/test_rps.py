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
