from game_app.services.match_service import MatchService
from game_app.configs.logic_configs import HAND_SIZE
import pytest


def test_create_match(db_session):
    service = MatchService(db_session)

    match = service.create_match("alice", "bob")

    assert match.id is not None
    assert match.player1_id == "alice"
    assert match.player2_id == "bob"
    assert match.current_round == 1
    assert match.status == "in_progress"
    assert match.points_p1 == 0
    assert match.points_p2 == 0

    # Check that players received HAND_SIZE cards each
    cards_p1 = service.get_player_hand(match.id, "alice")
    cards_p2 = service.get_player_hand(match.id, "bob")

    assert len(cards_p1) == HAND_SIZE
    assert len(cards_p2) == HAND_SIZE

def test_submit_move_waits_for_opponent(db_session):
    service = MatchService(db_session)
    match = service.create_match("alice", "bob")

    hand = service.get_player_hand(match.id, "alice")

    response = service.submit_move(match.id, "alice", hand[0]['match_card_id'])
    assert response["status"] == "waiting_for_opponent"

def test_submit_move_resolves_round(db_session):
    service = MatchService(db_session)
    match = service.create_match("alice", "bob")

    hand_a = service.get_player_hand(match.id, "alice")
    hand_b = service.get_player_hand(match.id, "bob")

    # Alice plays
    r1 = service.submit_move(match.id, "alice", hand_a[0]['match_card_id'])
    assert r1["status"] == "waiting_for_opponent"

    # Bob plays -> round resolved
    r2 = service.submit_move(match.id, "bob", hand_b[0]['match_card_id'])
    assert r2["round"] == 1
    assert "winner" in r2
    assert "reason" in r2

def test_match_finishes_after_five_rounds(db_session):
    service = MatchService(db_session)
    match = service.create_match("alice", "bob")

    for _ in range(5):
        hand_a = service.get_player_hand(match.id, "alice")
        hand_b = service.get_player_hand(match.id, "bob")

        service.submit_move(match.id, "alice", hand_a[0]['match_card_id'])
        #assert hand_a[0]['card']['id'] == hand_a[0]['match_card_id']
        result = service.submit_move(match.id, "bob", hand_b[0]['match_card_id'])

    assert result["match_finished"] is True
    assert match.status == "finished"
    assert match.winner in ["alice", "bob", None]


def test_card_cannot_be_used_twice(db_session):
    service = MatchService(db_session)
    match = service.create_match("alice", "bob")

    hand = service.get_player_hand(match.id, "alice")
    card_id = hand[0]['match_card_id']

    service.submit_move(match.id, "alice", card_id)

    with pytest.raises(ValueError):
        service.submit_move(match.id, "alice", card_id)
