"""
Overlay speech bubbles onto generated images.

Usage:
  uv run overlay.py input.png output.png --left "migwọ" --right "Vrẹndo"
  uv run overlay.py input.png output.png --left "migwọ"
  uv run overlay.py input.png output.png --right "Omamọ urhiọke"

Speech bubbles are positioned near speakers. Use the Python API with pos_left/pos_right
tuples (x_fraction, y_fraction) for precise per-scene placement, where (0,0) is top-left
and (1,1) is bottom-right.
"""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BUBBLE_COLOR = (255, 255, 255, 230)
OUTLINE_COLOR = (60, 60, 60, 255)
TEXT_COLOR = (30, 30, 30, 255)
BUBBLE_PADDING = 20
BUBBLE_RADIUS = 18
TAIL_SIZE = 15
MARGIN = 25


def get_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


def fit_font_size(text: str, max_width: int, max_size: int = 42, min_size: int = 22) -> ImageFont.FreeTypeFont:
    """Find the largest font size that fits the text within max_width."""
    for size in range(max_size, min_size - 1, -2):
        font = get_font(size)
        bbox = font.getbbox(text)
        text_w = bbox[2] - bbox[0]
        if text_w + BUBBLE_PADDING * 2 <= max_width:
            return font
    return get_font(min_size)


def draw_bubble(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont,
                center_x: int, bottom_y: int, tail_side: str = "left",
                img_width: int = 1024, img_height: int = 1024):
    """Draw a speech bubble with text and a small tail pointer.

    Clamps the bubble to stay within image bounds.
    """
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    bw = text_w + BUBBLE_PADDING * 2
    bh = text_h + BUBBLE_PADDING * 2

    # Position bubble centered on center_x, above bottom_y
    bx0 = center_x - bw // 2
    by0 = bottom_y - bh - TAIL_SIZE
    bx1 = bx0 + bw
    by1 = by0 + bh

    # Clamp horizontally
    if bx0 < MARGIN:
        shift = MARGIN - bx0
        bx0 += shift
        bx1 += shift
    if bx1 > img_width - MARGIN:
        shift = bx1 - (img_width - MARGIN)
        bx0 -= shift
        bx1 -= shift

    # Clamp vertically — don't go above top margin
    if by0 < MARGIN:
        shift = MARGIN - by0
        by0 += shift
        by1 += shift

    # Draw bubble background
    draw.rounded_rectangle((bx0, by0, bx1, by1), radius=BUBBLE_RADIUS,
                           fill=BUBBLE_COLOR, outline=OUTLINE_COLOR, width=2)

    # Draw tail (small triangle pointing down)
    tail_x = max(bx0 + 20, min(center_x, bx1 - 20))

    tail_points = [
        (tail_x - 8, by1),
        (tail_x + 8, by1),
        (tail_x, by1 + TAIL_SIZE),
    ]
    draw.polygon(tail_points, fill=BUBBLE_COLOR, outline=OUTLINE_COLOR, width=1)
    # Clean up outline overlap at tail join
    draw.line([(tail_x - 7, by1), (tail_x + 7, by1)], fill=BUBBLE_COLOR, width=3)

    # Draw text
    tx = bx0 + BUBBLE_PADDING
    ty = by0 + BUBBLE_PADDING - bbox[1]
    draw.text((tx, ty), text, fill=TEXT_COLOR, font=font)

    return bx0, by0, bx1, by1 + TAIL_SIZE


def overlay_bubbles(input_path: Path, output_path: Path,
                    left_text: str | None = None, right_text: str | None = None,
                    pos_left: tuple[float, float] | None = None,
                    pos_right: tuple[float, float] | None = None):
    """Overlay one or two speech bubbles onto an image.

    Args:
        pos_left: (x_frac, y_frac) position for left bubble, where 0-1 maps to image dims.
                  The bubble's tail points to this position. Defaults to sensible auto position.
        pos_right: Same for right bubble.
    """
    img = Image.open(input_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    w, h = img.size
    max_bubble_w = w // 2 - MARGIN * 2 if (left_text and right_text) else w - MARGIN * 2

    if left_text and right_text:
        # Two bubbles
        left_font = fit_font_size(left_text, max_bubble_w)
        right_font = fit_font_size(right_text, max_bubble_w)

        if pos_left:
            lx, ly = int(pos_left[0] * w), int(pos_left[1] * h)
        else:
            lx, ly = w // 4, h - MARGIN - 20

        if pos_right:
            rx, ry = int(pos_right[0] * w), int(pos_right[1] * h)
        else:
            rx, ry = 3 * w // 4, h - MARGIN - 20

        draw_bubble(draw, left_text, left_font, lx, ly, tail_side="left", img_width=w, img_height=h)
        draw_bubble(draw, right_text, right_font, rx, ry, tail_side="right", img_width=w, img_height=h)

    elif left_text:
        font = fit_font_size(left_text, max_bubble_w)
        if pos_left:
            cx, cy = int(pos_left[0] * w), int(pos_left[1] * h)
        else:
            cx, cy = w // 3, h - MARGIN - 20
        draw_bubble(draw, left_text, font, cx, cy, tail_side="left", img_width=w, img_height=h)

    elif right_text:
        font = fit_font_size(right_text, max_bubble_w)
        if pos_right:
            cx, cy = int(pos_right[0] * w), int(pos_right[1] * h)
        else:
            cx, cy = 2 * w // 3, h - MARGIN - 20
        draw_bubble(draw, right_text, font, cx, cy, tail_side="right", img_width=w, img_height=h)

    result = Image.alpha_composite(img, overlay).convert("RGB")
    result.save(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Overlay speech bubbles with Urhobo text onto images")
    parser.add_argument("input", help="Path to input image")
    parser.add_argument("output", help="Path to save output image")
    parser.add_argument("--left", "-l", help="Text for the left person's speech bubble")
    parser.add_argument("--right", "-r", help="Text for the right person's speech bubble")

    args = parser.parse_args()

    if not args.left and not args.right:
        print("Error: provide at least one of --left or --right text")
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    out = overlay_bubbles(input_path, Path(args.output), args.left, args.right)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
