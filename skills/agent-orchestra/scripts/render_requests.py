#!/usr/bin/env python3
"""Render worker frame requests outside their sandbox using an operator-supplied command."""

import argparse
import json
import math
from pathlib import Path
import shlex
import subprocess
import time

from contact_sheet import build_sheet


def handle(request, worktrees, output, command, limit):
    job = output / request.name.removesuffix(".json.running")
    job.mkdir(parents=True, exist_ok=True)
    try:
        spec = json.loads(request.read_text())
        tree = Path(spec["worktree"]).resolve()
        if not tree.is_dir() or tree == worktrees or not tree.is_relative_to(worktrees):
            raise ValueError("worktree must be a child directory inside the allowed root")
        times = spec["times"]
        if not isinstance(times, list) or not 1 <= len(times) <= 24 or any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0 for value in times
        ):
            raise ValueError("times must contain 1–24 nonnegative finite numbers")
        themes = spec.get("themes", ["light", "dark"])
        if not isinstance(themes, list) or not themes or len(themes) != len(set(themes)) or any(
            theme not in ("light", "dark") for theme in themes
        ):
            raise ValueError("themes must be a nonempty subset of light and dark")
        result = subprocess.run(
            [*command, str(job), "--at", *map(str, times), "--themes", *themes],
            cwd=tree, capture_output=True, text=True, timeout=limit,
        )
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr or f"render exited {result.returncode}")
        for theme in themes:
            frames = sorted((job / theme).glob("at-*.png"))
            if len(frames) != len(times):
                raise ValueError(f"expected {len(times)} {theme} frames; got {len(frames)}")
            build_sheet(frames, job / f"sheet-{theme}.png", columns=3, thumb_width=640)
        (job / "DONE").write_text("ok\n")
    except Exception as error:
        (job / "ERROR").write_text(f"{type(error).__name__}: {error}\n")
    finally:
        request.rename(request.with_name(request.name.removesuffix(".running") + ".handled"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worktrees", required=True, type=Path, help="allowed worktree root")
    parser.add_argument("--requests", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--render-command", required=True, help="command accepting OUTPUT --at TIMES --themes THEMES")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--poll", type=float, default=1)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    command = shlex.split(args.render_command)
    if not command or args.timeout < 1 or args.poll <= 0:
        parser.error("render command must be nonempty; timeout and poll must be positive")
    worktrees = args.worktrees.resolve(strict=True)
    args.requests.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    while True:
        for request in sorted(args.requests.glob("*.json")):
            claimed = request.with_name(request.name + ".running")
            try:
                request.rename(claimed)
            except FileNotFoundError:
                continue
            handle(claimed, worktrees, args.output, command, args.timeout)
        if args.once:
            break
        time.sleep(args.poll)


if __name__ == "__main__":
    main()
