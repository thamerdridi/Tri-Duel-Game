"""
==========================================
CARD DISPLAY API TESTS (SVG Endpoints)
==========================================

PURPOSE:
--------
Tests for card SVG visualization endpoints.
Verifies that cards can be rendered as SVG graphics without authentication.

WHAT IS TESTED:
---------------
1. List all cards (GET /cards):
   - Returns SVG gallery of all cards
   - Public endpoint (no auth required)

2. Get single card (GET /cards/{id}):
   - Returns specific card as SVG
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

NOTES:
------
- Cards endpoints return SVG images, not JSON
- All endpoints are public (no authentication required)
- SVG can be viewed directly in browsers
"""


def test_list_all_cards(client):
    """Test listing all cards as SVG gallery."""
    response = client.get("/cards")

    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["content-type"]

    # Check that response contains SVG content
    content = response.text
    assert content.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert '<svg' in content
    assert '</svg>' in content

    # Should contain card-related text (Rock, Paper, Scissors)
    assert ('Rock' in content or 'Paper' in content or 'Scissors' in content)


def test_list_cards_without_auth(client_no_auth):
    """Test that cards endpoint is public (no auth required)."""
    response = client_no_auth.get("/cards")

    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["content-type"]
    assert '<svg' in response.text


def test_get_single_card(client):
    """Test getting single card detail as SVG."""
    # Test with card ID 1 (should exist after seeding)
    card_id = 1
    response = client.get(f"/cards/{card_id}")

    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["content-type"]

    # Check SVG content
    content = response.text
    assert '<svg' in content
    assert '</svg>' in content
    # Should have visual elements (text or shapes)
    assert '<text' in content or '<rect' in content


def test_get_card_not_found(client):
    """Test getting non-existent card returns 404."""
    response = client.get("/cards/99999")

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "not found" in detail.lower()


def test_get_card_svg_structure(client):
    """Test that SVG has proper structure."""
    response = client.get("/cards/1")

    assert response.status_code == 200
    content = response.text

    # Check basic SVG structure
    assert '<?xml version="1.0" encoding="UTF-8"?>' in content
    assert '<svg' in content
    assert 'xmlns="http://www.w3.org/2000/svg"' in content
    assert '</svg>' in content

    # Should have visual elements
    assert '<rect' in content or '<circle' in content or '<path' in content
    assert '<text' in content


def test_cards_gallery_contains_multiple_cards(client):
    """Test that gallery SVG contains representations of multiple cards."""
    response = client.get("/cards")

    assert response.status_code == 200
    content = response.text

    # Gallery should have multiple visual elements (more than a single card)
    # Count SVG groups or rectangles
    rect_count = content.count('<rect')
    assert rect_count > 5, "Gallery should contain multiple card representations"


def test_single_card_caching_headers(client):
    """Test that single card SVG has caching headers."""
    response = client.get("/cards/1")

    assert response.status_code == 200
    # Should have cache control header for optimization
    assert "cache-control" in [k.lower() for k in response.headers.keys()]


def test_multiple_cards_render_correctly(client):
    """Test that multiple different cards can be rendered."""
    # Test first few card IDs
    for card_id in [1, 2, 3]:
        response = client.get(f"/cards/{card_id}")

        assert response.status_code == 200
        assert "image/svg+xml" in response.headers["content-type"]
        assert '<svg' in response.text
        assert '</svg>' in response.text


def test_gallery_response_size(client):
    """Test that gallery SVG is reasonably sized."""
    response = client.get("/cards")

    assert response.status_code == 200
    content_length = len(response.text)

    # SVG should be substantial but not enormous
    assert content_length > 1000, "Gallery SVG should contain meaningful content"
    assert content_length < 1000000, "Gallery SVG should not be excessively large"


def test_single_card_response_size(client):
    """Test that single card SVG is reasonably sized."""
    response = client.get("/cards/1")

    assert response.status_code == 200
    content_length = len(response.text)

    # Single card should be smaller than gallery
    assert content_length > 200, "Card SVG should contain meaningful content"
    assert content_length < 100000, "Card SVG should not be excessively large"

