#!/usr/bin/env python3
"""Recover Agent prompts and SendMessage follow-ups from a transcript JSONL."""

import argparse
import json
from pathlib import Path
import re

AGENT_NAMES = {"Agent", "spawn_agent"}
MESSAGE_NAMES = {"SendMessage", "send_message"}


def content_blocks(record):
    message = record.get("message", record)
    if not isinstance(message, dict):
        return []
    content = message.get("content", [])
    return content if isinstance(content, list) else []


def extract(lines):
    agents = []
    by_key = {}
    unassigned = []
    for line_number, line in enumerate(lines, 1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        for block in content_blocks(record):
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                name = block.get("name", "").split(".")[-1]
                payload = block.get("input", {})
                if not isinstance(payload, dict):
                    continue
                if name in AGENT_NAMES and isinstance(payload.get("prompt") or payload.get("message"), str):
                    task = payload.get("task_name") or payload.get("description") or f"agent_{len(agents)+1}"
                    item = {"task": task, "tool_use_id": block.get("id"),
                            "prompt": payload.get("prompt") or payload.get("message"),
                            "followups": [], "line": line_number}
                    agents.append(item)
                    for key in (task, block.get("id"), payload.get("agent_id")):
                        if key:
                            by_key[str(key)] = item
                elif name in MESSAGE_NAMES:
                    target = payload.get("recipient") or payload.get("target") or payload.get("agent_id")
                    message = payload.get("content") or payload.get("message")
                    if target and isinstance(message, str):
                        followup = {"line": line_number, "message": message}
                        owner = by_key.get(str(target))
                        if owner is None:
                            unassigned.append({"target": str(target), **followup})
                        else:
                            owner["followups"].append(followup)
            elif block.get("type") == "tool_result":
                owner = by_key.get(str(block.get("tool_use_id")))
                if owner is None:
                    continue
                raw = block.get("content", "")
                if isinstance(raw, list):
                    raw = " ".join(part.get("text", "") for part in raw if isinstance(part, dict))
                match = re.search(r'(?:["\']?agentId["\']?|agent_id|Agent ID)\s*[:=]\s*["\']?([\w-]+)', str(raw))
                if match:
                    owner["agent_id"] = match.group(1)
                    by_key[match.group(1)] = owner
                    remaining = []
                    for followup in unassigned:
                        if followup["target"] == match.group(1):
                            owner["followups"].append({k: v for k, v in followup.items() if k != "target"})
                        else:
                            remaining.append(followup)
                    unassigned = remaining
    for agent in agents:
        agent["followups"].sort(key=lambda item: item["line"])
    return {"agents": agents, "unassigned_followups": unassigned}


def safe_name(value):
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("._")
    return name[:80] or "agent"


def write_outputs(data, destination):
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "manifest.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    for index, agent in enumerate(data["agents"], 1):
        name = f"{index:03d}_{safe_name(agent['task'])}.txt"
        parts = ["ORIGINAL PROMPT", agent["prompt"]]
        for followup in agent["followups"]:
            parts.extend([f"FOLLOW-UP FROM TRANSCRIPT LINE {followup['line']}", followup["message"]])
        (destination / name).write_text("\n\n".join(parts) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transcript", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    with args.transcript.open(errors="replace") as source:
        data = extract(source)
    write_outputs(data, args.output_dir)
    print(f"Recovered {len(data['agents'])} Agent prompts and {len(data['unassigned_followups'])} unassigned follow-ups")


if __name__ == "__main__":
    main()
