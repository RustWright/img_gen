# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All scripts are run with `uv run`. No build or test step required.

```bash
# Generate images
uv run main.py "a cat astronaut floating in space"
uv run main.py -m imagen-fast -n 4 "neon jellyfish"
uv run main.py -m gemini -a 16:9 "watercolor mountain village at dawn"
uv run main.py upscale output/image.png --scale 4

# Apply speech bubbles to a single image
uv run overlay.py input.png output.png --left "migwọ" --right "Vrẹndo"

# Batch apply speech bubbles from scenes.toml
uv run apply_bubbles.py
uv run apply_bubbles.py my_custom_scenes.toml
```

## Environment

Requires `GEMINI_API_KEY` in `.env` (copy from `.env.example`). Python 3.12, managed by `uv`.

## Architecture

Three independent scripts, no shared state beyond `overlay.py` being imported by `apply_bubbles.py`:

**`main.py`** — Image generation CLI. Two backends:
- **Imagen 4** (`imagen-fast`, `imagen`, `imagen-ultra`): dedicated image model via `client.models.generate_images()`
- **Gemini** (`gemini`, `gemini-pro`): conversational model via `client.models.generate_content()` with `response_modalities=["TEXT", "IMAGE"]`; returns interleaved text reasoning alongside images

Images are saved to `output/` with timestamped filenames. The `upscale` subcommand is local-only (Lanczos, no API call). If the first CLI argument isn't a known subcommand, it's treated as a `generate` prompt.

**`overlay.py`** — Speech bubble renderer using Pillow. Draws rounded-rectangle bubbles with triangle tails onto images using RGBA compositing. Positions are specified as `(x_frac, y_frac)` fractions of image dimensions. Font size auto-fits to bubble width. Depends on `DejaVuSans-Bold.ttf` at `/usr/share/fonts/truetype/dejavu/`.

**`apply_bubbles.py`** — Batch runner that reads scene definitions from a TOML file (`scenes.toml` by default) and calls `overlay_bubbles()` for each. Input images are read from `output/`, results saved to `output/final/`. See `scenes.example.toml` for the schema — each `[[scenes]]` block specifies `input`, `output`, optional `left`/`right` text, and optional `pos_left`/`pos_right` position arrays.

## scenes.toml schema

```toml
[[scenes]]
input = "filename_inside_output_dir.png"   # required
output = "filename_for_output_final.png"   # required
left = "speech text"                        # optional
right = "speech text"                       # optional
pos_left = [0.30, 0.25]                    # optional, (x, y) as fractions 0.0–1.0
pos_right = [0.85, 0.20]                   # optional
```
