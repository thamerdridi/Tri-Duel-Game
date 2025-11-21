from dataclasses import dataclass

@dataclass
class Card:
    id: int             # id from db
    category: str       # "rock", "paper", "scissors"
    power: int          # ex. 1,2,3,4,5,6,9

@dataclass
class RoundResult:
    winner: str | None  # "p1", "p2", None (draw)
    card_p1: Card
    card_p2: Card
    reason: str         # ex "rock beats scissors" "higher power"
