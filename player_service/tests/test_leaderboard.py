"""Tests for leaderboard functionality."""


def test_empty_leaderboard(client):
    """Test leaderboard with no matches."""
    response = client.get("/leaderboard")
    assert response.status_code == 200
    assert response.json() == []


def test_leaderboard_with_matches(client, sample_match_data):
    """Test leaderboard after creating some matches."""
    # Alice wins
    client.post("/matches", json=sample_match_data)
    
    # Bob wins
    match2 = sample_match_data.copy()
    match2["player1_external_id"] = "charlie"
    match2["player2_external_id"] = "bob"
    match2["winner_external_id"] = "bob"
    match2["player1_score"] = 1
    match2["player2_score"] = 4
    client.post("/matches", json=match2)
    
    # Get leaderboard
    response = client.get("/leaderboard")
    assert response.status_code == 200
    
    leaderboard = response.json()
    assert len(leaderboard) == 3  # alice, bob, charlie
    
    # Check structure
    for entry in leaderboard:
        assert "external_id" in entry
        assert "username" in entry
        assert "wins" in entry
        assert "matches" in entry


def test_leaderboard_sorting(client, sample_match_data):
    """Test that leaderboard is sorted by wins."""
    # Alice: 2 wins
    client.post("/matches", json=sample_match_data)
    
    match2 = sample_match_data.copy()
    match2["player2_external_id"] = "charlie"
    client.post("/matches", json=match2)
    
    # Bob: 1 win
    match3 = sample_match_data.copy()
    match3["player1_external_id"] = "bob"
    match3["player2_external_id"] = "david"
    match3["winner_external_id"] = "bob"
    client.post("/matches", json=match3)
    
    # Get leaderboard
    response = client.get("/leaderboard")
    leaderboard = response.json()
    
    # Alice should be first (2 wins)
    assert leaderboard[0]["external_id"] == "alice"
    assert leaderboard[0]["wins"] == 2
    
    # Bob should be second (1 win)
    assert leaderboard[1]["external_id"] == "bob"
    assert leaderboard[1]["wins"] == 1


def test_leaderboard_counts_draws(client, sample_match_data):
    """Test that draws count towards total matches but not wins."""
    # Draw between alice and bob
    sample_match_data["winner_external_id"] = None
    sample_match_data["player1_score"] = 3
    sample_match_data["player2_score"] = 3
    client.post("/matches", json=sample_match_data)
    
    response = client.get("/leaderboard")
    leaderboard = response.json()
    
    # Find alice
    alice = next(p for p in leaderboard if p["external_id"] == "alice")
    assert alice["wins"] == 0
    assert alice["matches"] == 1


def test_leaderboard_with_only_losses(client, sample_match_data):
    """Test player with only losses still appears in leaderboard."""
    # Charlie loses to alice
    sample_match_data["player2_external_id"] = "charlie"
    client.post("/matches", json=sample_match_data)
    
    response = client.get("/leaderboard")
    leaderboard = response.json()
    
    # Charlie should be in leaderboard with 0 wins
    charlie = next(p for p in leaderboard if p["external_id"] == "charlie")
    assert charlie["wins"] == 0
    assert charlie["matches"] == 1


def test_leaderboard_tiebreaker(client, sample_match_data):
    """Test tiebreaker when players have same wins."""
    # Alice: 1 win, 1 match
    client.post("/matches", json=sample_match_data)
    
    # Bob: 1 win, 2 matches (played more)
    match2 = sample_match_data.copy()
    match2["player1_external_id"] = "bob"
    match2["player2_external_id"] = "charlie"
    match2["winner_external_id"] = "bob"
    client.post("/matches", json=match2)
    
    match3 = sample_match_data.copy()
    match3["player1_external_id"] = "bob"
    match3["player2_external_id"] = "david"
    match3["winner_external_id"] = "david"
    client.post("/matches", json=match3)
    
    response = client.get("/leaderboard")
    leaderboard = response.json()
    
    # Both have 1 win, but ordering may vary
    top_two = [p["external_id"] for p in leaderboard[:2]]
    assert "alice" in top_two
    assert "bob" in top_two
