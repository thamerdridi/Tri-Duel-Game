"""
Card Image Generator - generates simple PNG images of cards.

Uses ASCII symbols instead of emoji for maximum compatibility.
Works perfectly on all devices without font dependencies.
"""
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


def get_category_symbol(category: str) -> str:
    """
    Get ASCII symbol representation for card category.

    Args:
        category: Card category (rock, paper, scissors)

    Returns:
        str: ASCII symbol character
    """
    symbol_map = {
        "rock": "[R]",      # Simple ASCII bracket notation
        "paper": "[P]",
        "scissors": "[S]"
    }
    return symbol_map.get(category.lower(), "[?]")


def get_category_color(category: str) -> tuple:
    """
    Get background color for card category.

    Args:
        category: Card category (rock, paper, scissors)

    Returns:
        tuple: RGB color tuple
    """
    colors = {
        "rock": (139, 69, 19),      # Brown
        "paper": (70, 130, 180),    # Steel Blue
        "scissors": (220, 20, 60)   # Crimson
    }
    return colors.get(category.lower(), (128, 128, 128))


def get_rarity_color(power: int) -> tuple:
    """
    Get border color based on card power (rarity).

    Args:
        power: Card power level

    Returns:
        tuple: RGB color for border
    """
    if power >= 6:
        return (255, 215, 0)  # Gold - Legendary
    elif power >= 4:
        return (192, 192, 192)  # Silver - Rare
    else:
        return (205, 133, 63)  # Bronze - Common


def generate_card_image(card_id: int, category: str, power: int) -> BytesIO:
    """
    Generate a PNG image of a card.

    Args:
        card_id: Unique card identifier
        category: Card category (rock, paper, scissors)
        power: Card power level (1-9)

    Returns:
        BytesIO: PNG image as bytes
    """
    # Card dimensions
    width, height = 300, 420

    # Create image
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Colors
    bg_color = get_category_color(category)
    border_color = get_rarity_color(power)
    text_color = (255, 255, 255)

    # Draw border (rarity indicator)
    border_width = 10
    draw.rectangle(
        [(0, 0), (width, height)],
        fill=border_color
    )

    # Draw background
    draw.rectangle(
        [(border_width, border_width), (width - border_width, height - border_width)],
        fill=bg_color
    )

    # Try to load a font, fallback to default if not available
    try:
        title_font = ImageFont.truetype("arial.ttf", 48)
        text_font = ImageFont.truetype("arial.ttf", 32)
        small_font = ImageFont.truetype("arial.ttf", 24)
    except:
        # Use default font if arial not available
        title_font = ImageFont.load_default(48)
        text_font = ImageFont.load_default(32)
        small_font = ImageFont.load_default(24)

    # Draw category name (centered, top)
    category_text = category.upper()
    bbox = draw.textbbox((0, 0), category_text, font=title_font)
    text_width = bbox[2] - bbox[0]
    draw.text(
        ((width - text_width) / 2, 40),
        category_text,
        fill=text_color,
        font=title_font
    )

    # Draw power (large, center)
    power_text = f"POWER: {power}"
    bbox = draw.textbbox((0, 0), power_text, font=text_font)
    text_width = bbox[2] - bbox[0]
    draw.text(
        ((width - text_width) / 2, height / 2 - 30),
        power_text,
        fill=text_color,
        font=text_font
    )

    # Draw power bar
    bar_width = 200
    bar_height = 30
    bar_x = (width - bar_width) / 2
    bar_y = height / 2 + 40

    # Background bar
    draw.rectangle(
        [(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)],
        fill=(50, 50, 50),
        outline=text_color,
        width=2
    )

    # Filled bar (proportional to power)
    filled_width = (power / 6) * bar_width
    draw.rectangle(
        [(bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height)],
        fill=(0, 255, 0)
    )

    # Draw rarity text
    if power >= 6:
        rarity_text = "LEGENDARY"
    elif power >= 4:
        rarity_text = "RARE"
    else:
        rarity_text = "COMMON"

    bbox = draw.textbbox((0, 0), rarity_text, font=small_font)
    text_width = bbox[2] - bbox[0]
    draw.text(
        ((width - text_width) / 2, height - 120),
        rarity_text,
        fill=text_color,
        font=small_font
    )

    # Draw card ID (bottom)
    id_text = f"ID: {card_id}"
    bbox = draw.textbbox((0, 0), id_text, font=small_font)
    text_width = bbox[2] - bbox[0]
    draw.text(
        ((width - text_width) / 2, height - 60),
        id_text,
        fill=text_color,
        font=small_font
    )

    # Draw category symbol (top right)
    symbol = get_category_symbol(category)
    symbol_font_size = 24
    try:
        symbol_font = ImageFont.truetype("arial.ttf", symbol_font_size)
    except:
        symbol_font = ImageFont.load_default(symbol_font_size)

    bbox = draw.textbbox((0, 0), symbol, font=symbol_font)
    text_width = bbox[2] - bbox[0]
    draw.text(
        (width - text_width - 10, 10),
        symbol,
        fill=text_color,
        font=symbol_font
    )

    # Save to BytesIO
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return img_io


def generate_card_thumbnail(card_id: int, category: str, power: int) -> BytesIO:
    """
    Generate a smaller thumbnail image of a card (150x210).

    Args:
        card_id: Unique card identifier
        category: Card category (rock, paper, scissors)
        power: Card power level (1-9)

    Returns:
        BytesIO: PNG thumbnail as bytes
    """
    # Smaller dimensions for thumbnail
    width, height = 150, 210

    # Create image
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Colors
    bg_color = get_category_color(category)
    border_color = get_rarity_color(power)
    text_color = (255, 255, 255)

    # Draw border
    border_width = 5
    draw.rectangle(
        [(0, 0), (width, height)],
        fill=border_color
    )

    # Draw background
    draw.rectangle(
        [(border_width, border_width), (width - border_width, height - border_width)],
        fill=bg_color
    )

    # Use default font for thumbnail
    try:
        font = ImageFont.truetype("arial.ttf", 20)
        small_font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Draw category
    bbox = draw.textbbox((0, 0), category.upper(), font=font)
    text_width = bbox[2] - bbox[0]
    draw.text(
        ((width - text_width) / 2, 20),
        category.upper(),
        fill=text_color,
        font=font
    )

    # Draw power
    power_text = f"PWR: {power}"
    bbox = draw.textbbox((0, 0), power_text, font=font)
    text_width = bbox[2] - bbox[0]
    draw.text(
        ((width - text_width) / 2, height / 2 - 10),
        power_text,
        fill=text_color,
        font=font
    )

    # Draw ID
    id_text = f"ID: {card_id}"
    bbox = draw.textbbox((0, 0), id_text, font=small_font)
    text_width = bbox[2] - bbox[0]
    draw.text(
        ((width - text_width) / 2, height - 40),
        id_text,
        fill=text_color,
        font=small_font
    )

    # Draw category symbol (top right)
    symbol = get_category_symbol(category)
    symbol_font_size = 16
    try:
        symbol_font = ImageFont.truetype("arial.ttf", symbol_font_size)
    except:
        symbol_font = ImageFont.load_default(symbol_font_size)

    bbox = draw.textbbox((0, 0), symbol, font=symbol_font)
    text_width = bbox[2] - bbox[0]
    draw.text(
        (width - text_width - 5, 5),
        symbol,
        fill=text_color,
        font=symbol_font
    )

    # Save to BytesIO
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return img_io

