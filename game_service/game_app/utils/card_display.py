"""
ASCII Art Card Display Generator for Tri-Duel Game.

Uses PURE ASCII (basic characters only) for maximum compatibility.
Works on any device, terminal, or browser without encoding issues.
"""
#e

def get_category_emoji(category: str) -> str:
    """
    Get emoji representation for card category.
    Used only in simple text display, not in ASCII art cards.

    Args:
        category: Card category (rock, paper, scissors)

    Returns:
        str: Unicode emoji character
    """
    emoji_map = {
        "rock": "🪨",
        "paper": "📄",
        "scissors": "✂️"
    }
    return emoji_map.get(category.lower(), "❓")


def get_category_symbol(category: str) -> str:
    """
    Get Pure ASCII symbol representation for card category.

    Args:
        category: Card category

    Returns:
        str: Pure ASCII symbol
    """
    symbols = {
        "rock": "[ROCK]",
        "paper": "[PAPER]",
        "scissors": "[SCISSORS]"
    }
    return symbols.get(category.lower(), "[UNKNOWN]")


def generate_card_ascii(card_id: int, category: str, power: int) -> str:
    """
    Generate card using PURE ASCII (only basic characters: +, -, |, =, *)
    Works perfectly on ALL devices without Unicode issues.

    Args:
        card_id: Unique card identifier
        category: Card category (rock, paper, scissors)
        power: Card power level (1-9)

    Returns:
        str: Pure ASCII card representation
    """
    category_display = category.upper()

    # Determine rarity
    if power >= 7:
        rarity = "*** LEGENDARY ***"
    elif power >= 5:
        rarity = "** RARE **"
    else:
        rarity = "* COMMON *"

    # Pure ASCII card - works EVERYWHERE
    card = f"""
+---------------------+
|                     |
|   {category_display:^17}   |
|                     |
|     POWER: {power:>2}       |
|                     |
|   {rarity:^17}   |
|                     |
|     ID: {card_id:>4}        |
|                     |
+---------------------+"""

    return card.strip()


def generate_compact_card_ascii(card_id: int, category: str, power: int) -> str:
    """
    Generate compact Pure ASCII card (smaller).

    Args:
        card_id: Unique card identifier
        category: Card category (rock, paper, scissors)
        power: Card power level (1-9)

    Returns:
        str: Compact Pure ASCII card
    """
    cat_short = category.upper()[:4]

    card = f"""
+---------------+
| {cat_short:^13} |
|   PWR: {power:>2}     |
|   ID:  {card_id:>4}   |
+---------------+"""

    return card.strip()


def generate_hand_display(cards: list) -> str:
    """
    Generate ASCII art display for multiple cards (hand view).

    Args:
        cards: List of card dicts with id, category, power

    Returns:
        str: ASCII art showing all cards side by side
    """
    if not cards:
        return "[ Empty Hand ]"

    # Generate compact cards
    card_arts = [generate_compact_card_ascii(c['id'], c['category'], c['power'])
                 for c in cards]

    # Split each card into lines
    card_lines = [art.split('\n') for art in card_arts]

    # Combine cards horizontally
    max_lines = max(len(lines) for lines in card_lines)
    combined = []

    for i in range(max_lines):
        line_parts = []
        for card in card_lines:
            if i < len(card):
                line_parts.append(card[i])
            else:
                line_parts.append(" " * 17)  # Empty space
        combined.append("  ".join(line_parts))

    width = len(combined[0])
    header = f"\n{'=' * width}\n{'YOUR HAND':^{width}}\n{'=' * width}\n"
    footer = f"\n{'=' * width}\n"

    return header + "\n".join(combined) + footer


def generate_card_simple(card_id: int, category: str, power: int) -> str:
    """
    Generate simple one-line card representation.

    Args:
        card_id: Unique card identifier
        category: Card category (rock, paper, scissors)
        power: Card power level (1-9)

    Returns:
        str: Simple card representation
    """
    emoji = get_category_emoji(category)
    return f"{emoji} {category.capitalize()} (PWR: {power}, ID: {card_id})"


def generate_card_list_display(cards: list) -> str:
    """
    Generate a list view of cards using Pure ASCII.

    Args:
        cards: List of card dicts with id, category, power

    Returns:
        str: Formatted Pure ASCII list
    """
    if not cards:
        return "No cards available."

    lines = ["\n" + "=" * 70]
    lines.append(f"{'AVAILABLE CARDS':^70}")
    lines.append("=" * 70 + "\n")

    # Group by category
    by_category = {}
    for card in cards:
        cat = card['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(card)

    for category in sorted(by_category.keys()):
        emoji = get_category_emoji(category)
        lines.append(f"\n{emoji}  {category.upper()}")
        lines.append("-" * 70)

        # Table header
        lines.append(f"  {'ID':<6} | {'Power':<10} | {'Visual':<20}")
        lines.append("  " + "-" * 65)

        for card in sorted(by_category[category], key=lambda x: x['power']):
            # Power bar using only ASCII
            power_bar = "#" * card['power'] + "." * (9 - card['power'])
            lines.append(f"  {card['id']:<6} | {card['power']:<10} | [{power_bar}]")

    lines.append("\n" + "=" * 70)
    lines.append(f"{'Total: ' + str(len(cards)) + ' cards':^70}")
    lines.append("=" * 70 + "\n")

    return "\n".join(lines)
