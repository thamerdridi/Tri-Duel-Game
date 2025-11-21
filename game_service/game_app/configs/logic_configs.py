import os

# What beats what
BEATS = {
    "rock": "scissors",
    "scissors": "paper",
    "paper": "rock",
}

# Hand size
HAND_SIZE = os.getenv("HAND_SIZE", 5)

# Rounds count
MAX_ROUNDS = os.getenv("MAX_ROUNDS", 5)