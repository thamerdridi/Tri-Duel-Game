"""
Card Display Configuration

This file contains all visual settings for card rendering (SVG and PNG).
Modify these values to change card appearance without touching the code.
"""

# ============================================================
# COLOR SCHEMES
# ============================================================

# Card category background colors (hex format)
CATEGORY_COLORS = {
    "rock": "#8B4513",      # Brown - earthy, solid
    "paper": "#4682B4",     # Steel Blue - smooth, clean
    "scissors": "#DC143C",  # Crimson - sharp, aggressive
}

# Rarity border colors based on power level
RARITY_COLORS = {
    "legendary": "#FFD700",  # Gold (power >= 7)
    "rare": "#C0C0C0",       # Silver (power 5-6)
    "common": "#CD853F",     # Bronze (power 1-4)
}

# Text color (usually white for contrast)
TEXT_COLOR = "#FFFFFF"

# Power bar colors
POWER_BAR_BACKGROUND = "#323232"  # Dark gray
POWER_BAR_FILL = "#00FF00"        # Green
POWER_BAR_BORDER = "#FFFFFF"      # White


# ============================================================
# RARITY CONFIGURATION
# ============================================================

# Power level thresholds for rarity
RARITY_THRESHOLDS = {
    "legendary": 6,  # power >= 7
    "rare": 4,       # power >= 5 and < 7
    "common": 0,     # power < 5
}

# Rarity display names
RARITY_NAMES = {
    "legendary": "★ LEGENDARY ★",
    "rare": "☆ RARE ☆",
    "common": "COMMON",
}


# ============================================================
# CATEGORY SYMBOLS
# ============================================================

# ASCII symbols for categories (displayed in corner)
CATEGORY_SYMBOLS = {
    "rock": "[R]",
    "paper": "[P]",
    "scissors": "[S]",
}

# Emoji symbols (for display_text and lists)
CATEGORY_EMOJI = {
    "rock": "🪨",
    "paper": "📄",
    "scissors": "✂️",
}


# ============================================================
# CARD DIMENSIONS
# ============================================================

# Full size card dimensions (SVG and PNG)
CARD_WIDTH = 300
CARD_HEIGHT = 420

# Thumbnail dimensions
THUMBNAIL_WIDTH = 150
THUMBNAIL_HEIGHT = 210

# Border width
BORDER_WIDTH = 10
THUMBNAIL_BORDER_WIDTH = 5

# Border radius (rounded corners)
BORDER_RADIUS = 10
THUMBNAIL_BORDER_RADIUS = 5


# ============================================================
# TYPOGRAPHY
# ============================================================

# Font family (fallback: Arial, sans-serif)
FONT_FAMILY = "Arial, Helvetica, sans-serif"

# Font sizes for full card
FONT_SIZE_TITLE = 48      # Category name (e.g., "ROCK")
FONT_SIZE_TEXT = 36       # Power text (e.g., "POWER: 9")
FONT_SIZE_SMALL = 24      # Rarity and ID
FONT_SIZE_SYMBOL = 18     # Category symbol in corner

# Font sizes for thumbnail
THUMBNAIL_FONT_SIZE_TITLE = 20
THUMBNAIL_FONT_SIZE_TEXT = 18
THUMBNAIL_FONT_SIZE_SMALL = 14
THUMBNAIL_FONT_SIZE_SYMBOL = 18

# Font weights
FONT_WEIGHT_BOLD = "bold"
FONT_WEIGHT_NORMAL = "normal"


# ============================================================
# LAYOUT POSITIONS (for SVG rendering)
# ============================================================

# Full card layout
LAYOUT_FULL = {
    "symbol_x": 260,
    "symbol_y": 45,
    "title_x": 150,
    "title_y": 80,
    "power_x": 150,
    "power_y": 200,
    "power_bar_x": 50,
    "power_bar_y": 220,
    "power_bar_width": 200,
    "power_bar_height": 30,
    "rarity_x": 150,
    "rarity_y": 300,
    "id_x": 150,
    "id_y": 370,
}

# Thumbnail layout
LAYOUT_THUMBNAIL = {
    "symbol_x": 130,
    "symbol_y": 25,
    "title_x": 75,
    "title_y": 45,
    "power_x": 75,
    "power_y": 110,
    "power_bar_x": 25,
    "power_bar_y": 125,
    "power_bar_width": 100,
    "power_bar_height": 15,
    "id_x": 75,
    "id_y": 175,
}


# ============================================================
# DECORATIVE ELEMENTS
# ============================================================

# Decorative lines in SVG (opacity 0-1)
DECORATIVE_LINE_COLOR = "#FFFFFF"
DECORATIVE_LINE_OPACITY = 0.3
DECORATIVE_LINE_WIDTH = 1

# Show decorative lines?
SHOW_DECORATIVE_LINES = True


# ============================================================
# POWER BAR CONFIGURATION
# ============================================================

# Maximum power value (for bar calculation)
MAX_POWER = 6

# Power bar style
POWER_BAR_ROUNDED_CORNERS = True  # Use rounded corners?
POWER_BAR_CORNER_RADIUS = 4

# Power bar border
POWER_BAR_BORDER_WIDTH = 2


# ============================================================
# CACHE CONFIGURATION
# ============================================================

# Maximum number of cached cards (LRU cache)
CACHE_MAX_SIZE = 128

# Cache TTL in seconds (for HTTP Cache-Control header)
CACHE_TTL_SECONDS = 3600  # 1 hour


# ============================================================
# ALTERNATIVE COLOR THEMES (commented out - uncomment to use)
# ============================================================

# Dark Mode Theme
# CATEGORY_COLORS = {
#     "rock": "#5C3D2E",
#     "paper": "#2C5282",
#     "scissors": "#822C2C",
# }
# TEXT_COLOR = "#E0E0E0"
# POWER_BAR_BACKGROUND = "#1A1A1A"

# Pastel Theme
# CATEGORY_COLORS = {
#     "rock": "#D4A574",
#     "paper": "#A0C4E8",
#     "scissors": "#E89898",
# }
# RARITY_COLORS = {
#     "legendary": "#FFE066",
#     "rare": "#D4D4D4",
#     "common": "#E8C4A0",
# }

# Neon Theme
# CATEGORY_COLORS = {
#     "rock": "#FF6B35",
#     "paper": "#00D9FF",
#     "scissors": "#FF006E",
# }
# POWER_BAR_FILL = "#00FF41"
# TEXT_COLOR = "#FFFFFF"


# ============================================================
# VALIDATION
# ============================================================

def validate_config():
    """
    Validate configuration values.

    Raises:
        ValueError: If configuration is invalid
    """
    # Check all categories have colors
    required_categories = ["rock", "paper", "scissors"]
    for cat in required_categories:
        if cat not in CATEGORY_COLORS:
            raise ValueError(f"Missing color for category: {cat}")
        if cat not in CATEGORY_SYMBOLS:
            raise ValueError(f"Missing symbol for category: {cat}")

    # Check rarity configuration
    if RARITY_THRESHOLDS["legendary"] <= RARITY_THRESHOLDS["rare"]:
        raise ValueError("Legendary threshold must be greater than rare threshold")

    # Check dimensions
    if CARD_WIDTH <= 0 or CARD_HEIGHT <= 0:
        raise ValueError("Card dimensions must be positive")

    return True


def get_rarity_from_power(power: int) -> str:
    """
    Get rarity level based on power value.

    Args:
        power: Card power level

    Returns:
        str: Rarity level ("legendary", "rare", or "common")
    """
    if power >= RARITY_THRESHOLDS["legendary"]:
        return "legendary"
    elif power >= RARITY_THRESHOLDS["rare"]:
        return "rare"
    else:
        return "common"


def get_rarity_color(power: int) -> str:
    """
    Get border color based on power level.

    Args:
        power: Card power level

    Returns:
        str: Hex color code
    """
    rarity = get_rarity_from_power(power)
    return RARITY_COLORS[rarity]


def get_rarity_name(power: int) -> str:
    """
    Get display name for rarity based on power.

    Args:
        power: Card power level

    Returns:
        str: Rarity display name
    """
    rarity = get_rarity_from_power(power)
    return RARITY_NAMES[rarity]


# Validate on import
validate_config()

