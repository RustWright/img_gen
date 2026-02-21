"""Batch apply speech bubbles to greeting scene images.

Reads scene definitions from a TOML file (default: scenes.toml).

Usage:
  uv run apply_bubbles.py                    # uses scenes.toml
  uv run apply_bubbles.py my_scenes.toml     # uses a custom file
"""

import sys
import tomllib
from pathlib import Path

from overlay import overlay_bubbles

OUTPUT_DIR = Path("output")
FINAL_DIR = Path("output/final")


def load_scenes(path: Path) -> list[dict]:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return data.get("scenes", [])


def main():
    scenes_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("scenes.toml")

    if not scenes_file.exists():
        print(f"Error: scenes file not found: {scenes_file}")
        print(f"Copy scenes.example.toml to {scenes_file} and fill in your scene data.")
        sys.exit(1)

    scenes = load_scenes(scenes_file)
    if not scenes:
        print(f"No scenes found in {scenes_file}")
        sys.exit(1)

    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    ok = 0
    for scene in scenes:
        input_path = OUTPUT_DIR / scene["input"]
        output_path = FINAL_DIR / scene["output"]

        if not input_path.exists():
            print(f"  SKIP (not found): {scene['input']}")
            continue

        pos_left = tuple(scene["pos_left"]) if "pos_left" in scene else None
        pos_right = tuple(scene["pos_right"]) if "pos_right" in scene else None

        overlay_bubbles(
            input_path, output_path,
            left_text=scene.get("left"),
            right_text=scene.get("right"),
            pos_left=pos_left,
            pos_right=pos_right,
        )
        print(f"  OK: {scene['output']}")
        ok += 1

    print(f"\nDone! {ok}/{len(scenes)} images processed, saved to {FINAL_DIR}/")


if __name__ == "__main__":
    main()
