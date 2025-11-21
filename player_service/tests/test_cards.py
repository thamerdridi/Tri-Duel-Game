"""Unit tests for card endpoints."""


def test_get_all_cards(client):
    """Test retrieving all cards."""
    response = client.get("/cards")
    assert response.status_code == 200
    
    cards = response.json()
    assert len(cards) == 18  # Should have 18 cards
    
    # Check structure of first card
    assert "id" in cards[0]
    assert "category" in cards[0]
    assert "power" in cards[0]
    assert "name" in cards[0]


def test_get_single_card(client):
    """Test retrieving a single card by ID."""
    response = client.get("/cards/1")
    assert response.status_code == 200
    
    card = response.json()
    assert card["id"] == 1
    assert card["category"] in ["rock", "paper", "scissors"]
    assert isinstance(card["power"], int)
    assert card["name"] is not None


def test_get_nonexistent_card(client):
    """Test retrieving a card that doesn't exist."""
    response = client.get("/cards/999")
    assert response.status_code == 404


def test_cards_have_correct_categories(client):
    """Test that cards have valid categories."""
    response = client.get("/cards")
    cards = response.json()
    
    valid_categories = {"rock", "paper", "scissors"}
    for card in cards:
        assert card["category"] in valid_categories


def test_cards_have_valid_powers(client):
    """Test that cards have valid power values."""
    response = client.get("/cards")
    cards = response.json()
    
    valid_powers = {10, 20, 30, 40, 50, 60}
    for card in cards:
        assert card["power"] in valid_powers


def test_each_category_has_six_cards(client):
    """Test that each category has exactly 6 cards."""
    response = client.get("/cards")
    cards = response.json()
    
    rock_count = sum(1 for c in cards if c["category"] == "rock")
    paper_count = sum(1 for c in cards if c["category"] == "paper")
    scissors_count = sum(1 for c in cards if c["category"] == "scissors")
    
    assert rock_count == 6
    assert paper_count == 6
    assert scissors_count == 6
