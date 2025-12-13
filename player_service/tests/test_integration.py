"""End-to-end integration tests simulating full workflows."""


def test_full_match_workflow(client, sample_match_data):
    """Test complete workflow: create match, retrieve history, check leaderboard."""
    # Step 1: Verify cards exist
    cards_response = client.get("/cards")
    assert cards_response.status_code == 200
    assert len(cards_response.json()) == 18
    
    # Step 2: Create a match (this creates players automatically)
    match_response = client.post("/matches", json=sample_match_data)
    assert match_response.status_code == 201
    match_id = match_response.json()["id"]
    
    # Step 3: Check player1's match history
    history_response = client.get("/players/alice/matches")
    assert history_response.status_code == 200
    matches = history_response.json()
    assert len(matches) == 1
    assert matches[0]["winner_external_id"] == "alice"
    
    # Step 4: Check detailed match info
    detail_response = client.get(f"/players/alice/matches/{match_id}")
    assert detail_response.status_code == 200
    match_detail = detail_response.json()
    assert match_detail["id"] == match_id
    
    # Step 5: Check leaderboard
    leaderboard_response = client.get("/leaderboard")
    assert leaderboard_response.status_code == 200
    leaderboard = leaderboard_response.json()
    assert len(leaderboard) == 2  # alice and bob
    
    # Alice should be top (1 win)
    assert leaderboard[0]["external_id"] == "alice"
    assert leaderboard[0]["wins"] == 1


def test_multiple_players_multiple_matches(client, sample_match_data):
    """Test system with multiple players and multiple matches."""
    # Match 1: Alice vs Bob (Alice wins)
    client.post("/matches", json=sample_match_data)
    
    # Match 2: Alice vs Charlie (Alice wins)
    match2 = sample_match_data.copy()
    match2["player2_external_id"] = "charlie"
    client.post("/matches", json=match2)
    
    # Match 3: Bob vs Charlie (Charlie wins)
    match3 = sample_match_data.copy()
    match3["player1_external_id"] = "bob"
    match3["player2_external_id"] = "charlie"
    match3["winner_external_id"] = "charlie"
    match3["player1_score"] = 2
    match3["player2_score"] = 4
    client.post("/matches", json=match3)
    
    # Check leaderboard
    leaderboard = client.get("/leaderboard").json()
    
    # Alice: 2 wins, 2 matches
    alice = next(p for p in leaderboard if p["external_id"] == "alice")
    assert alice["wins"] == 2
    assert alice["matches"] == 2
    
    # Charlie: 1 win, 2 matches
    charlie = next(p for p in leaderboard if p["external_id"] == "charlie")
    assert charlie["wins"] == 1
    assert charlie["matches"] == 2
    
    # Bob: 0 wins, 2 matches
    bob = next(p for p in leaderboard if p["external_id"] == "bob")
    assert bob["wins"] == 0
    assert bob["matches"] == 2


def test_player_history_shows_all_matches(client, sample_match_data):
    """Test that player history includes matches as both player1 and player2."""
    # Alice as player1
    client.post("/matches", json=sample_match_data)
    
    # Alice as player2 (loses to Charlie)
    match2 = sample_match_data.copy()
    match2["player1_external_id"] = "charlie"
    match2["player2_external_id"] = "alice"
    match2["winner_external_id"] = "charlie"
    match2["player1_score"] = 4
    match2["player2_score"] = 1
    client.post("/matches", json=match2)
    
    # Get Alice's history
    history = client.get("/players/alice/matches").json()
    assert len(history) == 2
    
    # Should include both matches
    player_positions = [
        (m["player1_external_id"], m["player2_external_id"]) 
        for m in history
    ]
    assert ("alice", "bob") in player_positions
    assert ("charlie", "alice") in player_positions


def test_health_check_always_works(client):
    """Test that health check works regardless of database state."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
