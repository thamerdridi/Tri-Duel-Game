import os

# What beats what
BEATS = {
    "rock": "scissors",
    "scissors": "paper",
    "paper": "rock",
}

# Hand size (cards per player)
HAND_SIZE = int(os.getenv("HAND_SIZE", "5"))

# Maximum rounds per match
MAX_ROUNDS = int(os.getenv("MAX_ROUNDS", "5"))


