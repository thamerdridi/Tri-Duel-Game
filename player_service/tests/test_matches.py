"""Integration tests for match creation and retrieval."""


def test_create_match(client, sample_match_data):
    """Test creating a new match."""
    response = client.post("/matches", json=sample_match_data)
    assert response.status_code == 201
    
    data = response.json()
    assert "id" in data
    assert isinstance(data["id"], int)


def test_create_match_with_draw(client, sample_match_data):
    """Test creating a match that ended in a draw."""
    sample_match_data["winner_external_id"] = None
    sample_match_data["player1_score"] = 3
    sample_match_data["player2_score"] = 3
    
    response = client.post("/matches", json=sample_match_data)
    assert response.status_code == 201


def test_create_match_auto_creates_players(client, sample_match_data):
    """Test that creating a match automatically creates player profiles."""
    # First match should create both players
    response = client.post("/matches", json=sample_match_data)
    assert response.status_code == 201
    
    # Verify players were created
    response1 = client.get("/players/alice/matches")
    assert response1.status_code == 200
    
    response2 = client.get("/players/bob/matches")
    assert response2.status_code == 200


def test_create_match_missing_required_fields(client):
    """Test creating a match with missing required fields."""
    incomplete_data = {
        "player1_external_id": "alice",
        # Missing player2_external_id and other required fields
    }
    
    response = client.post("/matches", json=incomplete_data)
    assert response.status_code == 422  # Validation error


def test_create_match_ignores_rounds_field(client, sample_match_data):
    """Test that legacy/extra 'rounds' field does not break match creation."""
    payload = {
        **sample_match_data,
        "rounds": None,
    }

    response = client.post("/matches", json=payload)
    assert response.status_code == 201


def test_get_player_matches(client, sample_match_data):
    """Test retrieving all matches for a player."""
    # Create a match
    client.post("/matches", json=sample_match_data)
    
    # Get matches for player1
    response = client.get("/players/alice/matches")
    assert response.status_code == 200
    
    matches = response.json()
    assert len(matches) == 1
    assert matches[0]["player1_external_id"] == "alice"
    assert matches[0]["player2_external_id"] == "bob"
    assert matches[0]["winner_external_id"] == "alice"


def test_get_player_matches_empty(client):
    """Test getting matches for a player with no matches."""
    response = client.get("/players/nonexistent/matches")
    # Returns 404 when player profile doesn't exist
    assert response.status_code == 404


def test_get_match_detail(client, sample_match_data):
    """Test retrieving match information by ID."""
    # Create a match
    create_response = client.post("/matches", json=sample_match_data)
    match_id = create_response.json()["id"]
    
    # Get match details
    response = client.get(f"/players/alice/matches/{match_id}")
    assert response.status_code == 200
    
    match = response.json()
    assert match["id"] == match_id
    assert match["player1_external_id"] == "alice"


def test_get_match_detail_not_found(client):
    """Test getting details for non-existent match."""
    response = client.get("/players/alice/matches/999")
    assert response.status_code == 404


def test_get_match_detail_wrong_player(client, sample_match_data):
    """Test getting match details with wrong player ID."""
    # Create a match between alice and bob
    create_response = client.post("/matches", json=sample_match_data)
    match_id = create_response.json()["id"]
    
    # Try to access with different player
    response = client.get(f"/players/charlie/matches/{match_id}")
    assert response.status_code == 404


def test_multiple_matches_same_players(client, sample_match_data):
    """Test creating multiple matches between same players."""
    # Create first match
    client.post("/matches", json=sample_match_data)
    
    # Create second match (alice loses this time)
    sample_match_data["winner_external_id"] = "bob"
    sample_match_data["player1_score"] = 2
    sample_match_data["player2_score"] = 3
    client.post("/matches", json=sample_match_data)
    
    # Check alice has 2 matches
    response = client.get("/players/alice/matches")
    assert response.status_code == 200
    assert len(response.json()) == 2
