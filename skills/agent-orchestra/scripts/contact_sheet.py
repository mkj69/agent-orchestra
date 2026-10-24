#!/usr/bin/env python3
"""Tile screenshots or frames extracted from videos into one review image."""

import argparse
from pathlib import Path
import subprocess
import tempfile


def build_sheet(paths, output, columns=4, thumb_width=400, label_height=30):
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise SystemExit("Pillow is required: python3 -m pip install Pillow") from exc
    if not paths:
        raise ValueError("No images supplied")
    tiles = []
    for path in paths:
        with Image.open(path) as source:
            image = source.convert("RGB")
        image.thumbnail((thumb_width, thumb_width * 3))
        tiles.append((path, image))
    cell_height = max(image.height for _, image in tiles) + label_height
    rows = (len(tiles) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * thumb_width, rows * cell_height), "#ffffff")
    draw = ImageDraw.Draw(sheet)
    for index, (path, image) in enumerate(tiles):
        x = index % columns * thumb_width
        y = index // columns * cell_height
        sheet.paste(image, (x, y + label_height))
        draw.text((x + 5, y + 5), path.name[:55], fill="#111111")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("images", nargs="*", type=Path)
    parser.add_argument("--video", action="append", default=[], type=Path)
    parser.add_argument("--every", type=int, default=10, help="seconds between extracted frames")
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--thumb-width", type=int, default=400)
    args = parser.parse_args()
    if args.every < 1 or args.columns < 1 or args.thumb_width < 50:
        parser.error("sampling interval, columns, and thumb width must be positive")
    with tempfile.TemporaryDirectory() as temp:
        paths = list(args.images)
        for index, video in enumerate(args.video):
            pattern = Path(temp) / f"video{index}_%04d.png"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(video.resolve()), "-vf",
                            f"fps=1/{args.every}", str(pattern)], check=True)
            paths.extend(sorted(Path(temp).glob(f"video{index}_*.png")))
        build_sheet(paths, args.output, args.columns, args.thumb_width)
    print(args.output)


if __name__ == "__main__":
    main()
