"""
SVG Deck/Gallery Generator - generates composite SVG showing multiple cards.

Creates three main views:
1. Deck Gallery - grid view of all available cards
2. Player Hand - visual representation of player's cards in a match
3. Card comparison views
"""
from typing import List, Dict
from game_app.configs.card_display_config import (
    CATEGORY_COLORS,
    CATEGORY_SYMBOLS,
    TEXT_COLOR,
    POWER_BAR_BACKGROUND,
    POWER_BAR_FILL,
    FONT_FAMILY,
    FONT_WEIGHT_BOLD,
    MAX_POWER,
    get_rarity_color,
)


def generate_mini_card_svg(card: Dict, x: int, y: int, size: int = 80, grayscale: bool = False) -> str:
    """
    Generate a mini card for use in deck/gallery views.

    Args:
        card: Card dict with id, category, power
        x: X position in parent SVG
        y: Y position in parent SVG
        size: Card size (default 80x112, maintains 3:4.2 ratio)
        grayscale: If True, render card in grayscale (for used cards)

    Returns:
        str: SVG group element for the mini card
    """
    card_id = card['id']
    category = card['category']
    power = card['power']

    # Colors
    bg_color = CATEGORY_COLORS.get(category.lower(), CATEGORY_COLORS["rock"])
    border_color = get_rarity_color(power)
    symbol = CATEGORY_SYMBOLS.get(category.lower(), "[?]")

    # Apply grayscale if card is used
    if grayscale:
        bg_color = "#777777"
        border_color = "#555555"
        text_color = "#AAAAAA"
        bar_fill = "#888888"
        opacity = "0.5"
    else:
        text_color = TEXT_COLOR
        bar_fill = POWER_BAR_FILL
        opacity = "1.0"

    # Dimensions
    width = size
    height = int(size * 1.4)  # 3:4.2 ratio

    # Power bar
    power_bar_width = int((power / MAX_POWER) * (width - 20))

    # Used indicator
    used_overlay = ""
    if grayscale:
        used_overlay = f"""
        <line x1="0" y1="0" x2="{width}" y2="{height}" 
              stroke="#FF0000" stroke-width="3" opacity="0.7"/>
        <line x1="{width}" y1="0" x2="0" y2="{height}" 
              stroke="#FF0000" stroke-width="3" opacity="0.7"/>
        <text x="{width // 2}" y="{height // 2}" 
              font-family="{FONT_FAMILY}" font-size="14" 
              font-weight="{FONT_WEIGHT_BOLD}"
              fill="#FF0000" text-anchor="middle">
            USED
        </text>
        """

    mini_card = f"""
    <g transform="translate({x}, {y})" opacity="{opacity}">
        <!-- Border (rarity) -->
        <rect width="{width}" height="{height}" fill="{border_color}" rx="4" ry="4"/>
        
        <!-- Background -->
        <rect x="3" y="3" width="{width - 6}" height="{height - 6}" fill="{bg_color}" rx="3" ry="3"/>
        
        <!-- Symbol -->
        <text x="{width - 8}" y="16" 
              font-family="{FONT_FAMILY}" 
              font-size="12" 
              font-weight="{FONT_WEIGHT_BOLD}"
              fill="{text_color}" 
              text-anchor="end">
            {symbol}
        </text>
        
        <!-- Category name -->
        <text x="{width // 2}" y="30" 
              font-family="{FONT_FAMILY}" 
              font-size="11" 
              font-weight="{FONT_WEIGHT_BOLD}"
              fill="{text_color}" 
              text-anchor="middle">
            {category[:4].upper()}
        </text>
        
        <!-- Power -->
        <text x="{width // 2}" y="{height // 2 + 5}" 
              font-family="{FONT_FAMILY}" 
              font-size="16" 
              font-weight="{FONT_WEIGHT_BOLD}"
              fill="{text_color}" 
              text-anchor="middle">
            {power}
        </text>
        
        <!-- Power bar -->
        <rect x="10" y="{height - 25}" width="{width - 20}" height="8" 
              fill="{POWER_BAR_BACKGROUND}" 
              rx="2" ry="2"/>
        <rect x="10" y="{height - 25}" width="{power_bar_width}" height="8" 
              fill="{bar_fill}" 
              rx="2" ry="2"/>
        
        <!-- ID -->
        <text x="{width // 2}" y="{height - 6}" 
              font-family="{FONT_FAMILY}" 
              font-size="9" 
              fill="{text_color}" 
              text-anchor="middle"
              opacity="0.8">
            #{card_id}
        </text>
        
        {used_overlay}
    </g>"""

    return mini_card


def generate_deck_grid_svg(cards: List[Dict], cards_per_row: int = 5) -> str:
    """
    Generate SVG showing all cards in a grid layout (VIEW 1: Deck Gallery).

    Args:
        cards: List of card dicts with id, category, power
        cards_per_row: Number of cards per row (default 5)

    Returns:
        str: Complete SVG with all cards in grid
    """
    if not cards:
        return '<svg width="400" height="200"><text x="200" y="100" text-anchor="middle" font-family="Arial">No cards available</text></svg>'

    # Card dimensions
    card_width = 80
    card_height = 112
    spacing = 15

    # Calculate grid dimensions
    num_rows = (len(cards) + cards_per_row - 1) // cards_per_row

    # SVG dimensions (with padding)
    padding = 30
    svg_width = (card_width + spacing) * cards_per_row + padding * 2 - spacing
    svg_height = (card_height + spacing) * num_rows + padding * 2 - spacing + 60  # +60 for title

    # Generate title
    title = f"""
    <text x="{svg_width // 2}" y="30" 
          font-family="{FONT_FAMILY}" 
          font-size="24" 
          font-weight="{FONT_WEIGHT_BOLD}"
          fill="#333333" 
          text-anchor="middle">
        CARD DECK ({len(cards)} Cards)
    </text>
    
    <line x1="{padding}" y1="45" x2="{svg_width - padding}" y2="45" 
          stroke="#CCCCCC" 
          stroke-width="2"/>
    """

    # Generate cards
    cards_svg = []
    for idx, card in enumerate(cards):
        row = idx // cards_per_row
        col = idx % cards_per_row

        x = padding + col * (card_width + spacing)
        y = 60 + padding + row * (card_height + spacing)  # +60 for title

        cards_svg.append(generate_mini_card_svg(card, x, y, card_width))

    # Group by category stats
    stats = {}
    for card in cards:
        cat = card['category']
        stats[cat] = stats.get(cat, 0) + 1

    stats_text = f"""
    <text x="{svg_width // 2}" y="{svg_height - 10}" 
          font-family="{FONT_FAMILY}" 
          font-size="12" 
          fill="#666666" 
          text-anchor="middle">
        Rock: {stats.get('rock', 0)} | Paper: {stats.get('paper', 0)} | Scissors: {stats.get('scissors', 0)}
    </text>
    """

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
    <rect width="{svg_width}" height="{svg_height}" fill="#F5F5F5"/>
    {title}
    {''.join(cards_svg)}
    {stats_text}
</svg>"""

    return svg.strip()


def generate_player_hand_svg(cards: List[Dict], match_id: str = None) -> str:
    """
    Generate SVG showing player's hand in a match (VIEW 3: Player Hand).

    Shows available cards and used cards with visual distinction.

    Args:
        cards: List of card dicts with id, category, power, used (bool)
        match_id: Optional match ID for title

    Returns:
        str: SVG showing cards in hand view with used/available distinction
    """
    if not cards:
        return '<svg width="400" height="200"><text x="200" y="100" text-anchor="middle" font-family="Arial">Empty hand</text></svg>'

    # Separate available and used cards
    available = [c for c in cards if not c.get('used', False)]
    used = [c for c in cards if c.get('used', False)]

    # Card dimensions
    card_width = 90
    card_height = 126
    spacing = 15

    # Calculate layout
    max_per_row = 5
    available_rows = (len(available) + max_per_row - 1) // max_per_row if available else 0
    used_rows = (len(used) + max_per_row - 1) // max_per_row if used else 0

    # SVG dimensions
    padding = 40
    svg_width = (card_width + spacing) * min(max_per_row, max(len(available), len(used))) + padding * 2
    svg_height = (card_height + spacing) * (available_rows + used_rows) + padding * 3 + 120  # Extra for titles

    # Title
    match_text = f" (Match {match_id[:8]}...)" if match_id else ""
    title = f"""
    <text x="{svg_width // 2}" y="30" 
          font-family="{FONT_FAMILY}" 
          font-size="24" 
          font-weight="{FONT_WEIGHT_BOLD}"
          fill="#333333" 
          text-anchor="middle">
        YOUR HAND{match_text}
    </text>
    
    <text x="{svg_width // 2}" y="55" 
          font-family="{FONT_FAMILY}" 
          font-size="14" 
          fill="#666666" 
          text-anchor="middle">
        {len(available)} Available | {len(used)} Used
    </text>
    """

    cards_svg = []
    current_y = 80

    # Available cards section
    if available:
        section_title = f"""
        <text x="{padding}" y="{current_y}" 
              font-family="{FONT_FAMILY}" 
              font-size="16" 
              font-weight="{FONT_WEIGHT_BOLD}"
              fill="#00AA00">
            ✓ AVAILABLE CARDS ({len(available)})
        </text>
        <line x1="{padding}" y1="{current_y + 5}" x2="{svg_width - padding}" y2="{current_y + 5}" 
              stroke="#00AA00" stroke-width="2"/>
        """
        cards_svg.append(section_title)
        current_y += 30

        for idx, card in enumerate(available):
            row = idx // max_per_row
            col = idx % max_per_row
            x = padding + col * (card_width + spacing)
            y = current_y + row * (card_height + spacing)
            cards_svg.append(generate_mini_card_svg(card, x, y, card_width, grayscale=False))

        current_y += (available_rows * (card_height + spacing)) + 30

    # Used cards section
    if used:
        section_title = f"""
        <text x="{padding}" y="{current_y}" 
              font-family="{FONT_FAMILY}" 
              font-size="16" 
              font-weight="{FONT_WEIGHT_BOLD}"
              fill="#AA0000">
            ✗ USED CARDS ({len(used)})
        </text>
        <line x1="{padding}" y1="{current_y + 5}" x2="{svg_width - padding}" y2="{current_y + 5}" 
              stroke="#AA0000" stroke-width="2"/>
        """
        cards_svg.append(section_title)
        current_y += 30

        for idx, card in enumerate(used):
            row = idx // max_per_row
            col = idx % max_per_row
            x = padding + col * (card_width + spacing)
            y = current_y + row * (card_height + spacing)
            cards_svg.append(generate_mini_card_svg(card, x, y, card_width, grayscale=True))

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
    <!-- Background -->
    <rect width="{svg_width}" height="{svg_height}" fill="#FAFAFA"/>
    
    <!-- Green felt table texture -->
    <defs>
        <pattern id="felt" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
            <rect width="20" height="20" fill="#2F5233" opacity="0.1"/>
        </pattern>
    </defs>
    <rect y="70" width="{svg_width}" height="{svg_height - 70}" fill="url(#felt)"/>
    
    {title}
    {''.join(cards_svg)}
</svg>"""

    return svg.strip()

