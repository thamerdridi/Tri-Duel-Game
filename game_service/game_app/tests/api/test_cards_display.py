"""
==========================================
CARD DISPLAY API TESTS
==========================================

PURPOSE:
--------
Tests for card display endpoints with ASCII art visualization.
Verifies that cards can be browsed without authentication.

WHAT IS TESTED:
---------------
1. List all cards (GET /cards):
   - Returns all active cards
   - Includes ASCII art display
   - Public endpoint (no auth required)

2. Get single card (GET /cards/{id}):
   - Returns specific card details
   - Includes full ASCII art
   - Shows card relationships (beats/loses to)
   - Public endpoint (no auth required)

3. Error cases:
   - Card not found (404)
   - Invalid card ID

HOW TO RUN:
-----------
Run all card display tests:
    $ cd game_service
    $ pytest game_app/tests/api/test_cards_display.py -v

Run specific test:
    $ pytest game_app/tests/api/test_cards_display.py::test_list_all_cards -v

Run with output (see ASCII art):
    $ pytest game_app/tests/api/test_cards_display.py -v -s
"""


def test_list_all_cards(client):
    """Test listing all cards with ASCII art."""
    response = client.get("/cards/")

    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert "total" in data
    assert "cards" in data
    assert "ascii_list" in data

    # Should have 18 cards
    assert data["total"] > 0
    assert len(data["cards"]) == data["total"]

    # Check card structure
    first_card = data["cards"][0]
    assert "id" in first_card
    assert "category" in first_card
    assert "power" in first_card
    assert "emoji" in first_card
    assert "ascii_art" in first_card
    assert "ascii_compact" in first_card
    assert "display_text" in first_card

    # ASCII list should be non-empty string
    assert isinstance(data["ascii_list"], str)
    assert len(data["ascii_list"]) > 0


def test_list_cards_without_auth(client_no_auth):
    """Test that cards endpoint is public (no auth required)."""
    response = client_no_auth.get("/cards/")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0


def test_get_single_card(client):
    """Test getting single card detail with ASCII art."""
    # First get list to find a valid card ID
    list_response = client.get("/cards/")
    cards = list_response.json()["cards"]
    card_id = cards[0]["id"]

    # Get specific card
    response = client.get(f"/cards/{card_id}")

    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert "card" in data
    assert "description" in data
    assert "beats" in data
    assert "loses_to" in data

    # Check card details
    card = data["card"]
    assert card["id"] == card_id
    assert "ascii_art" in card
    assert len(card["ascii_art"]) > 50  # ASCII art should be substantial

    # Check relationships
    assert data["beats"] in ["rock", "paper", "scissors"]
    assert data["loses_to"] in ["rock", "paper", "scissors"]


def test_get_card_not_found(client):
    """Test getting non-existent card returns 404."""
    response = client.get("/cards/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_card_categories(client):
    """Test that cards have valid categories."""
    response = client.get("/cards/")
    cards = response.json()["cards"]

    valid_categories = {"rock", "paper", "scissors"}

    for card in cards:
        assert card["category"] in valid_categories


def test_card_emojis(client):
    """Test that cards have proper emoji representations."""
    response = client.get("/cards/")
    cards = response.json()["cards"]

    emoji_map = {
        "rock": "🪨",
        "paper": "📄",
        "scissors": "✂️"
    }

    for card in cards:
        expected_emoji = emoji_map[card["category"]]
        assert card["emoji"] == expected_emoji


def test_ascii_art_format(client):
    """Test that ASCII art is properly formatted."""
    response = client.get("/cards/1")

    assert response.status_code == 200
    card = response.json()["card"]

    # Check ASCII art contains borders
    assert "╔" in card["ascii_art"] or "┌" in card["ascii_art"]
    assert "║" in card["ascii_art"] or "│" in card["ascii_art"]

    # Check compact version
    assert len(card["ascii_compact"]) < len(card["ascii_art"])


def test_cards_sorted_by_category_and_power(client):
    """Test that cards are sorted by category then power."""
    response = client.get("/cards/")
    cards = response.json()["cards"]

    # Group by category
    by_category = {}
    for card in cards:
        cat = card["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(card["power"])

    # Check each category is sorted by power
    for category, powers in by_category.items():
        assert powers == sorted(powers), f"{category} cards not sorted by power"


def test_rock_paper_scissors_relationships(client):
    """Test that card relationships are correct."""
    response = client.get("/cards/")
    cards = response.json()["cards"]

    # Get one card of each type
    rock_card = next(c for c in cards if c["category"] == "rock")
    paper_card = next(c for c in cards if c["category"] == "paper")
    scissors_card = next(c for c in cards if c["category"] == "scissors")

    # Test rock
    rock_detail = client.get(f"/cards/{rock_card['id']}").json()
    assert rock_detail["beats"] == "scissors"
    assert rock_detail["loses_to"] == "paper"

    # Test paper
    paper_detail = client.get(f"/cards/{paper_card['id']}").json()
    assert paper_detail["beats"] == "rock"
    assert paper_detail["loses_to"] == "scissors"

    # Test scissors
    scissors_detail = client.get(f"/cards/{scissors_card['id']}").json()
    assert scissors_detail["beats"] == "paper"
    assert scissors_detail["loses_to"] == "rock"


def test_display_text_format(client):
    """Test that display_text is human-readable."""
    response = client.get("/cards/")
    cards = response.json()["cards"]

    for card in cards:
        display = card["display_text"]

        # Should contain emoji, category, and power
        assert card["emoji"] in display
        assert card["category"].lower() in display.lower()
        assert str(card["power"]) in display

