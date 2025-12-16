"""
SVG Card Generator - generates scalable vector graphics for cards.

Uses configuration from card_display_config.py for all visual settings.
"""
from game_app.configs.card_display_config import *

def generate_card_svg(card_id: int, category: str, power: int) -> str:
    """
    Generate SVG representation of a card using configuration.

    Args:
        card_id: Unique card identifier
        category: Card category (rock, paper, scissors)
        power: Card power level (1-9)

    Returns:
        str: Complete SVG as XML string
    """
    # Get colors and text from config
    bg_color = CATEGORY_COLORS.get(category.lower(), CATEGORY_COLORS["rock"])
    border_color = get_rarity_color(power)
    rarity_text = get_rarity_name(power)
    symbol = CATEGORY_SYMBOLS.get(category.lower(), "[?]")

    # Power bar calculation
    power_bar_width = int((power / MAX_POWER) * LAYOUT_FULL["power_bar_width"])

    # Decorative lines
    decorative_lines = ""
    if SHOW_DECORATIVE_LINES:
        decorative_lines = f"""
    <line x1="30" y1="100" x2="270" y2="100" 
          stroke="{DECORATIVE_LINE_COLOR}" 
          stroke-width="{DECORATIVE_LINE_WIDTH}" 
          opacity="{DECORATIVE_LINE_OPACITY}"/>
    <line x1="30" y1="320" x2="270" y2="320" 
          stroke="{DECORATIVE_LINE_COLOR}" 
          stroke-width="{DECORATIVE_LINE_WIDTH}" 
          opacity="{DECORATIVE_LINE_OPACITY}"/>"""

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{CARD_WIDTH}" height="{CARD_HEIGHT}" xmlns="http://www.w3.org/2000/svg">
    <!-- Card border (rarity indicator) -->
    <rect width="{CARD_WIDTH}" height="{CARD_HEIGHT}" fill="{border_color}" rx="{BORDER_RADIUS}" ry="{BORDER_RADIUS}"/>
    
    <!-- Card background -->
    <rect x="10" y="10" width="{CARD_WIDTH - 20}" height="{CARD_HEIGHT - 20}" fill="{bg_color}" rx="{BORDER_RADIUS - 2}" ry="{BORDER_RADIUS - 2}"/>
    
    <!-- Category symbol (top right) -->
    <text x="{LAYOUT_FULL['symbol_x']}" y="{LAYOUT_FULL['symbol_y']}" 
          font-family="{FONT_FAMILY}" 
          font-size="{FONT_SIZE_SYMBOL}" 
          font-weight="{FONT_WEIGHT_BOLD}"
          fill="{TEXT_COLOR}" 
          text-anchor="end">
        {symbol}
    </text>
    
    <!-- Category name (centered, top) -->
    <text x="{LAYOUT_FULL['title_x']}" y="{LAYOUT_FULL['title_y']}" 
          font-family="{FONT_FAMILY}" 
          font-size="{FONT_SIZE_TITLE}" 
          font-weight="{FONT_WEIGHT_BOLD}"
          fill="{TEXT_COLOR}" 
          text-anchor="middle">
        {category.upper()}
    </text>
    
    <!-- Power text (center) -->
    <text x="{LAYOUT_FULL['power_x']}" y="{LAYOUT_FULL['power_y']}" 
          font-family="{FONT_FAMILY}" 
          font-size="{FONT_SIZE_TEXT}" 
          fill="{TEXT_COLOR}" 
          text-anchor="middle">
        POWER: {power}
    </text>
    
    <!-- Power bar background -->
    <rect x="{LAYOUT_FULL['power_bar_x']}" y="{LAYOUT_FULL['power_bar_y']}" 
          width="{LAYOUT_FULL['power_bar_width']}" height="{LAYOUT_FULL['power_bar_height']}" 
          fill="{POWER_BAR_BACKGROUND}" 
          stroke="{POWER_BAR_BORDER}" 
          stroke-width="{POWER_BAR_BORDER_WIDTH}" 
          rx="{POWER_BAR_CORNER_RADIUS}" ry="{POWER_BAR_CORNER_RADIUS}"/>
    
    <!-- Power bar filled (proportional to power) -->
    <rect x="{LAYOUT_FULL['power_bar_x']}" y="{LAYOUT_FULL['power_bar_y']}" 
          width="{power_bar_width}" height="{LAYOUT_FULL['power_bar_height']}" 
          fill="{POWER_BAR_FILL}" 
          rx="{POWER_BAR_CORNER_RADIUS}" ry="{POWER_BAR_CORNER_RADIUS}"/>
    
    <!-- Rarity text -->
    <text x="{LAYOUT_FULL['rarity_x']}" y="{LAYOUT_FULL['rarity_y']}" 
          font-family="{FONT_FAMILY}" 
          font-size="{FONT_SIZE_SMALL}" 
          fill="{TEXT_COLOR}" 
          text-anchor="middle">
        {rarity_text}
    </text>
    
    <!-- Card ID (bottom) -->
    <text x="{LAYOUT_FULL['id_x']}" y="{LAYOUT_FULL['id_y']}" 
          font-family="{FONT_FAMILY}" 
          font-size="{FONT_SIZE_SMALL}" 
          fill="{TEXT_COLOR}" 
          text-anchor="middle">
        ID: {card_id}
    </text>
    {decorative_lines}
</svg>"""

    return svg.strip()


def generate_card_svg_thumbnail(card_id: int, category: str, power: int) -> str:
    """
    Generate smaller SVG thumbnail using configuration.

    Args:
        card_id: Unique card identifier
        category: Card category (rock, paper, scissors)
        power: Card power level (1-9)

    Returns:
        str: SVG thumbnail as XML string
    """
    # Get colors and text from config
    bg_color = CATEGORY_COLORS.get(category.lower(), CATEGORY_COLORS["rock"])
    border_color = get_rarity_color(power)
    symbol = CATEGORY_SYMBOLS.get(category.lower(), "[?]")

    # Power bar calculation
    power_bar_width = int((power / MAX_POWER) * LAYOUT_THUMBNAIL["power_bar_width"])

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{THUMBNAIL_WIDTH}" height="{THUMBNAIL_HEIGHT}" xmlns="http://www.w3.org/2000/svg">
    <!-- Card border -->
    <rect width="{THUMBNAIL_WIDTH}" height="{THUMBNAIL_HEIGHT}" fill="{border_color}" rx="{THUMBNAIL_BORDER_RADIUS}" ry="{THUMBNAIL_BORDER_RADIUS}"/>
    
    <!-- Card background -->
    <rect x="5" y="5" width="{THUMBNAIL_WIDTH - 10}" height="{THUMBNAIL_HEIGHT - 10}" fill="{bg_color}" rx="{THUMBNAIL_BORDER_RADIUS - 1}" ry="{THUMBNAIL_BORDER_RADIUS - 1}"/>
    
    <!-- Category symbol -->
    <text x="{LAYOUT_THUMBNAIL['symbol_x']}" y="{LAYOUT_THUMBNAIL['symbol_y']}" 
          font-family="{FONT_FAMILY}" 
          font-size="{THUMBNAIL_FONT_SIZE_SYMBOL}" 
          font-weight="{FONT_WEIGHT_BOLD}"
          fill="{TEXT_COLOR}" 
          text-anchor="end">
        {symbol}
    </text>
    
    <!-- Category name -->
    <text x="{LAYOUT_THUMBNAIL['title_x']}" y="{LAYOUT_THUMBNAIL['title_y']}" 
          font-family="{FONT_FAMILY}" 
          font-size="{THUMBNAIL_FONT_SIZE_TITLE}" 
          font-weight="{FONT_WEIGHT_BOLD}"
          fill="{TEXT_COLOR}" 
          text-anchor="middle">
        {category.upper()}
    </text>
    
    <!-- Power -->
    <text x="{LAYOUT_THUMBNAIL['power_x']}" y="{LAYOUT_THUMBNAIL['power_y']}" 
          font-family="{FONT_FAMILY}" 
          font-size="{THUMBNAIL_FONT_SIZE_TEXT}" 
          fill="{TEXT_COLOR}" 
          text-anchor="middle">
        PWR: {power}
    </text>
    
    <!-- Power bar mini -->
    <rect x="{LAYOUT_THUMBNAIL['power_bar_x']}" y="{LAYOUT_THUMBNAIL['power_bar_y']}" 
          width="{LAYOUT_THUMBNAIL['power_bar_width']}" height="{LAYOUT_THUMBNAIL['power_bar_height']}" 
          fill="{POWER_BAR_BACKGROUND}" 
          stroke="{POWER_BAR_BORDER}" 
          stroke-width="1" 
          rx="2" ry="2"/>
    <rect x="{LAYOUT_THUMBNAIL['power_bar_x']}" y="{LAYOUT_THUMBNAIL['power_bar_y']}" 
          width="{power_bar_width}" height="{LAYOUT_THUMBNAIL['power_bar_height']}" 
          fill="{POWER_BAR_FILL}" 
          rx="2" ry="2"/>
    
    <!-- ID -->
    <text x="{LAYOUT_THUMBNAIL['id_x']}" y="{LAYOUT_THUMBNAIL['id_y']}" 
          font-family="{FONT_FAMILY}" 
          font-size="{THUMBNAIL_FONT_SIZE_SMALL}" 
          fill="{TEXT_COLOR}" 
          text-anchor="middle">
        ID: {card_id}
    </text>
</svg>"""

    return svg.strip()
