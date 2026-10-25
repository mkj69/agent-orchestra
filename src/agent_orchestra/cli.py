"""Locate the agent-orchestra skill files."""

from __future__ import annotations

import argparse
import sysconfig
from pathlib import Path


def skill_path() -> Path:
    source = Path(__file__).resolve().parents[2] / "skills" / "agent-orchestra"
    if (source / "SKILL.md").is_file():
        return source
    return Path(sysconfig.get_path("data")) / "share" / "agent-orchestra"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent-orchestra", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("skill-path", help="print the directory containing SKILL.md")
    args = parser.parse_args(argv)
    if args.command == "skill-path":
        path = skill_path()
        if not (path / "SKILL.md").is_file():
            parser.error(f"Skill files were not found at {path}")
        print(path)
    return 0
