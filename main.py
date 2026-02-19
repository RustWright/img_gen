"""
Image generation using Google Gemini API.

Supports two backends:
  - Imagen 4: Dedicated image model, fast, high quality
  - Gemini (Nano Banana): Conversational model that can generate images with
    interleaved text reasoning — better for complex/creative prompts

Usage:
  uv run main.py "a cat astronaut floating in space"
  uv run main.py --model gemini "a cat astronaut floating in space"
  uv run main.py --aspect 16:9 --count 2 "sunset over cyberpunk tokyo"
  uv run main.py upscale output/some_image.png --scale 2
"""

import argparse
import os
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

OUTPUT_DIR = Path("output")

# Available models and their per-image cost (USD)
IMAGEN_MODELS = {
    "imagen-fast": ("imagen-4.0-fast-generate-001", 0.02),
    "imagen": ("imagen-4.0-generate-001", 0.04),
    "imagen-ultra": ("imagen-4.0-ultra-generate-001", 0.06),
}

# Gemini models — cost is token-based, so we estimate conservatively
# ~1000 input tokens + ~image output ≈ $0.03-0.05 per generation
GEMINI_MODELS = {
    "gemini": ("gemini-2.5-flash-image", 0.035),
    "gemini-pro": ("gemini-3-pro-image-preview", 0.07),
}

ALL_MODELS = {**IMAGEN_MODELS, **GEMINI_MODELS}

ASPECT_RATIOS = ["1:1", "16:9", "9:16", "4:3", "3:4"]


def get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("Error: GEMINI_API_KEY not set. Add it to .env or export it.")
        print("Get a key at: https://aistudio.google.com/apikey")
        sys.exit(1)
    return genai.Client(api_key=api_key)


def generate_imagen(
    client: genai.Client,
    prompt: str,
    model: str = "imagen",
    count: int = 1,
    aspect_ratio: str = "1:1",
    person_generation: str = "allow_adult",
) -> list[Image.Image]:
    """Generate images using Imagen 4."""
    model_id, _ = IMAGEN_MODELS[model]
    print(f"Generating with {model_id}...")

    response = client.models.generate_images(
        model=model_id,
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=count,
            aspect_ratio=aspect_ratio,
            person_generation=person_generation,
        ),
    )

    images = []
    if response.generated_images:
        for gen_img in response.generated_images:
            images.append(gen_img.image._pil_image)
    return images


def generate_gemini(
    client: genai.Client,
    prompt: str,
    model: str = "gemini",
    aspect_ratio: str = "1:1",
) -> tuple[list[Image.Image], str | None]:
    """Generate images using Gemini (conversational image generation).

    Returns (images, text_response). Gemini can return reasoning text alongside
    the generated image, which can be useful for understanding its interpretation.
    """
    model_id, _ = GEMINI_MODELS[model]
    print(f"Generating with {model_id}...")

    response = client.models.generate_content(
        model=model_id,
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
        ),
    )

    images = []
    text_parts = []

    if response.candidates and response.candidates[0].content:
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                text_parts.append(part.text)
            elif part.inline_data is not None:
                img = Image.open(BytesIO(part.inline_data.data))
                images.append(img)

    text = "\n".join(text_parts) if text_parts else None
    return images, text


def save_images(images: list[Image.Image], prompt: str) -> list[Path]:
    """Save images to the output directory with timestamped filenames."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = "".join(c if c.isalnum() or c in " -_" else "" for c in prompt[:40]).strip()
    slug = slug.replace(" ", "_")

    saved = []
    for i, img in enumerate(images):
        suffix = f"_{i+1}" if len(images) > 1 else ""
        filename = OUTPUT_DIR / f"{ts}_{slug}{suffix}.png"
        img.save(filename)
        saved.append(filename)
        print(f"  [{i+1}] {filename} ({img.width}x{img.height})")
    return saved


def print_cost(model: str, count: int):
    """Print estimated cost for the generation run."""
    _, cost_per_image = ALL_MODELS[model]
    total = cost_per_image * count
    print(f"\n  Cost: {count} image(s) x ${cost_per_image:.3f} = ${total:.3f}")


def upscale_local(input_path: Path, scale: int) -> Path:
    """Upscale an image locally using Lanczos resampling."""
    img = Image.open(input_path)
    new_size = (img.width * scale, img.height * scale)
    upscaled = img.resize(new_size, Image.LANCZOS)

    stem = input_path.stem
    out_path = input_path.parent / f"{stem}_upscaled_{scale}x.png"
    upscaled.save(out_path)
    return out_path


def cmd_generate(args):
    """Handle the generate (default) command."""
    client = get_client()

    if args.model in IMAGEN_MODELS:
        images = generate_imagen(
            client,
            prompt=args.prompt,
            model=args.model,
            count=args.count,
            aspect_ratio=args.aspect,
            person_generation=args.person,
        )
        text = None
    else:
        images, text = generate_gemini(
            client,
            prompt=args.prompt,
            model=args.model,
            aspect_ratio=args.aspect,
        )

    if not images:
        print("No images generated. The prompt may have been blocked by safety filters.")
        print("Try rephrasing or adjusting the --person flag.")
        sys.exit(1)

    if text:
        print(f"\nModel response:\n{text}")

    print(f"\nGenerated {len(images)} image(s):")
    saved = save_images(images, args.prompt)
    print_cost(args.model, len(images))

    if len(saved) > 1:
        print(f"\n  Tip: to upscale a favourite, run:")
        print(f"    uv run main.py upscale {saved[0]} --scale 2")


def cmd_upscale(args):
    """Handle the upscale subcommand."""
    input_path = Path(args.image)
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    out = upscale_local(input_path, args.scale)
    img = Image.open(out)
    print(f"Upscaled {args.scale}x -> {out} ({img.width}x{img.height})")


def main():
    parser = argparse.ArgumentParser(
        description="Generate images with Google Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  %(prog)s "a cat astronaut floating in space"
  %(prog)s -m imagen-fast -n 4 "neon jellyfish"
  %(prog)s -m gemini -a 16:9 "watercolor mountain village at dawn"
  %(prog)s upscale output/image.png --scale 4

models:
  imagen-fast   Imagen 4 Fast      ~$0.02/img   Quick drafts, iteration
  imagen        Imagen 4 Standard  ~$0.04/img   General use (default)
  imagen-ultra  Imagen 4 Ultra     ~$0.06/img   Highest quality
  gemini        Gemini 2.5 Flash   ~$0.035/img  Creative prompts, returns text reasoning
  gemini-pro    Gemini 3 Pro       ~$0.07/img   Complex/multi-reference prompts

notes:
  Cost is per-image, so --count 4 costs 4x. Estimated cost is shown after each run.
  Images are saved to output/ with timestamped filenames.
  Set GEMINI_API_KEY in .env or as an environment variable.
""",
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- generate (default when no subcommand) ---
    gen_parser = subparsers.add_parser(
        "generate", aliases=["gen"],
        help="Generate images from a text prompt (default command)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Generate images from a text prompt using Imagen 4 or Gemini.",
        epilog="""examples:
  %(prog)s "a cat astronaut floating in space"
  %(prog)s -m imagen-fast -n 4 "neon jellyfish"
  %(prog)s -m gemini -a 16:9 "watercolor mountain village at dawn"
""",
    )
    gen_parser.add_argument("prompt", help="Text prompt describing the image to generate")
    gen_parser.add_argument(
        "--model", "-m",
        choices=list(ALL_MODELS.keys()),
        default="imagen",
        help="Model to use (default: imagen). See main --help for model details",
    )
    gen_parser.add_argument(
        "--aspect", "-a",
        choices=ASPECT_RATIOS,
        default="1:1",
        help="Aspect ratio (default: 1:1)",
    )
    gen_parser.add_argument(
        "--count", "-n",
        type=int,
        default=1,
        choices=range(1, 5),
        help="Number of images to generate, 1-4 (default: 1). Imagen only; cost scales linearly",
    )
    gen_parser.add_argument(
        "--person",
        choices=["dont_allow", "allow_adult", "allow_all"],
        default="allow_adult",
        help="Person generation policy (default: allow_adult). Imagen only",
    )
    gen_parser.set_defaults(func=cmd_generate)

    # --- upscale ---
    up_parser = subparsers.add_parser(
        "upscale",
        help="Upscale an image locally using Lanczos resampling (free, no API call)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Upscale a previously generated image using local Lanczos resampling.\nNo API call is made — this is free and runs locally.",
        epilog="""examples:
  %(prog)s output/20260216_cat_astronaut_1.png
  %(prog)s output/20260216_cat_astronaut_1.png --scale 4
""",
    )
    up_parser.add_argument("image", help="Path to the image file to upscale")
    up_parser.add_argument(
        "--scale", "-s",
        type=int,
        default=2,
        choices=[2, 3, 4],
        help="Upscale factor: 2x, 3x, or 4x (default: 2)",
    )
    up_parser.set_defaults(func=cmd_upscale)

    # If first arg isn't a known subcommand or --help, assume "generate"
    subcommands = {"generate", "gen", "upscale"}
    argv = sys.argv[1:]
    if argv and argv[0] not in subcommands and argv[0] not in ("-h", "--help"):
        argv = ["generate"] + argv
    args = parser.parse_args(argv)

    args.func(args)


if __name__ == "__main__":
    main()
