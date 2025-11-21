from game_app.logic.models import Card, RoundResult

from game_app.configs.logic_configs import BEATS

def rps_outcome(card_p1: Card, card_p2: Card) -> RoundResult:
    # Same category -> compare power
    if card_p1.category == card_p2.category:
        if card_p1.power > card_p2.power:
            return RoundResult("p1", card_p1, card_p2, "higher power")
        elif card_p1.power < card_p2.power:
            return RoundResult("p2", card_p1, card_p2, "higher power")
        else:
            return RoundResult(None, card_p1, card_p2, "equal power")

    # Different categories -> RPS rules
    if BEATS[card_p1.category] == card_p2.category:
        return RoundResult("p1", card_p1, card_p2, f"{card_p1.category} beats {card_p2.category}")
    else:
        return RoundResult("p2", card_p1, card_p2, f"{card_p2.category} beats {card_p1.category}")
