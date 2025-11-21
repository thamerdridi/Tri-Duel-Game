from game_app.logic.models import Card
from game_app.logic.rps import rps_outcome
from game_app.configs.logic_configs import *

class MatchEngine:
    """
    Obsolete - used only in development.

    Logic of the Match.
    """

    def __init__(self, deck_p1: list[Card], deck_p2: list[Card]):
        assert len(deck_p1) == len(deck_p2)
        self.deck_p1 = deck_p1
        self.deck_p2 = deck_p2
        self.points_p1 = 0
        self.points_p2 = 0
        self.current_round = 1
        self.max_rounds = MAX_ROUNDS

    def play_round(self, card_idx_p1: int, card_idx_p2: int):
        """
        Players choose index of cards the want to play.
        """
        card_p1 = self.deck_p1.pop(card_idx_p1)
        card_p2 = self.deck_p2.pop(card_idx_p2)

        result = rps_outcome(card_p1, card_p2)

        if result.winner == "p1":
            self.points_p1 += 1
        elif result.winner == "p2":
            self.points_p2 += 1

        self.current_round += 1
        return result

    def is_finished(self) -> bool:
        return self.current_round > self.max_rounds

    def winner(self):
        if self.points_p1 > self.points_p2:
            return "p1"
        elif self.points_p2 > self.points_p1:
            return "p2"
        else:
            return None  # draw
