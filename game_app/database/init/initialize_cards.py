from sqlalchemy.orm import Session
from game_app.database.models import CardDefinition
from game_app.configs.cards_config import CARDS


def init_cards(db: Session, reset: bool = False):
    """
    Initialize the cards in database.

    :param reset: if true, reset all cards before initializing.
    """

    if reset:
        deleted = db.query(CardDefinition).delete()
        print(f"[init_cards] Reset enabled — deleted {deleted} existing card definitions.")
        db.commit()

    existing = db.query(CardDefinition).count()

    if existing > 0:
        print(f"[init_cards] Cards already initialized ({existing} found). Use reset=True to overwrite. -> skipping")
        return

    # initialization
    for category, powers in CARDS.items():
        for p in powers:
            card = CardDefinition(category=category, power=p, active=True)
            db.add(card)

    db.commit()
    print(f"[init_cards] Inserted {sum(len(p) for p in CARDS.values())} cards.")
