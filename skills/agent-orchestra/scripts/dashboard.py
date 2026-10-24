#!/usr/bin/env python3
"""Generate a local HTML progress page from job output, logs, and task files."""

import argparse
import html
import json
import os
from pathlib import Path
import subprocess
import time


def codex_output_path(argv):
    """Return the exact -o value for a codex exec process, if present."""
    if not argv or not any(Path(arg).name == "codex" for arg in argv):
        return None
    if "exec" not in argv:
        return None
    for index, arg in enumerate(argv):
        if arg in ("-o", "--output-last-message") and index + 1 < len(argv):
            return Path(argv[index + 1])
        if arg.startswith("--output-last-message="):
            return Path(arg.split("=", 1)[1])
    return None


def running_outputs(proc_root=Path("/proc")):
    found = set()
    try:
        entries = proc_root.iterdir()
    except OSError:
        return found
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            argv = [a.decode(errors="replace") for a in (entry / "cmdline").read_bytes().split(b"\0") if a]
        except OSError:
            continue
        output = codex_output_path(argv)
        if output:
            found.add(output.resolve())
    return found


def last_codex_note(log):
    try:
        lines = log.read_text(errors="replace").splitlines()
    except OSError:
        return ""
    markers = [i for i, line in enumerate(lines) if line.strip() == "codex"]
    if markers:
        block = []
        for line in lines[markers[-1] + 1:]:
            if line.strip() in {"exec", "codex", "thinking", "tokens used", "file update", "apply_patch"} or line.startswith("diff --git"):
                break
            if line.strip():
                block.append(line.strip())
        return " ".join(block)[:400]
    return " ".join(line.strip() for line in lines[-5:] if line.strip())[:400]


def last_assistant_text(path):
    note = ""
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return note
    for line in lines:
        try:
            data = json.loads(line)
        except ValueError:
            continue
        message = data.get("message", data)
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        content = message.get("content", [])
        if isinstance(content, str):
            note = content
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text" and item.get("text", "").strip():
                    note = item["text"]
    return note.strip()[:400]


def age(timestamp, now=None):
    seconds = max(0, int((now or time.time()) - timestamp))
    return f"{seconds // 60}m ago" if seconds >= 60 else f"{seconds}s ago"


def board_tail(path, count=25):
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return []
    start = lines.index("## Log") + 1 if "## Log" in lines else 0
    return [line for line in lines[start:] if line.strip()][-count:]


def git_log(repo):
    try:
        result = subprocess.run(["git", "-C", str(repo), "log", "--oneline", "-8"],
                                text=True, capture_output=True, check=False)
    except OSError:
        return []
    return result.stdout.splitlines() if result.returncode == 0 else []


def collect_rows(outdir, config, running=None, now=None):
    running = running_outputs() if running is None else running
    now = time.time() if now is None else now
    jobs = config.get("jobs", {})
    names = set(jobs)
    if outdir.exists():
        names.update(path.stem for path in outdir.glob("*.log"))
        names.update(path.stem for path in outdir.glob("*.out"))
    rows = []
    for name in sorted(names):
        output = outdir / f"{name}.out"
        log = outdir / f"{name}.log"
        label = jobs.get(name, name)
        if isinstance(label, dict):
            label = label.get("label", name)
        active = output.resolve() in running
        done = output.exists() and output.stat().st_size > 0
        status = "running" if active else "returned" if done else "stopped" if log.exists() else "queued"
        note = output.read_text(errors="replace")[:400] if done and not active else last_codex_note(log)
        stamp = log.stat().st_mtime if log.exists() else output.stat().st_mtime if output.exists() else now
        rows.append(("Codex", name, str(label), status, age(stamp, now), note))
    for name, entry in config.get("leaders", {}).items():
        if not isinstance(entry, dict) or not entry.get("path"):
            continue
        path = Path(entry["path"])
        if not path.exists():
            continue
        freshness = int(entry.get("active_seconds", 600))
        status = "active" if now - path.stat().st_mtime < freshness else "idle or finished"
        rows.append(("Leader", name, entry.get("label", name), status,
                     age(path.stat().st_mtime, now), last_assistant_text(path)))
    return rows


def render_page(rows, board, commits):
    order = {"running": 0, "active": 0, "stopped": 1, "queued": 2, "idle or finished": 3, "returned": 3}
    rows = sorted(rows, key=lambda row: (order.get(row[3], 9), row[1]))
    cells = []
    for kind, name, label, status, elapsed, note in rows:
        values = [kind, f"{label} ({name})", status, elapsed, note]
        cells.append("<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in values) + "</tr>")
    recent = "".join(f"<li>{html.escape(line)}</li>" for line in reversed(board))
    history = "".join(f"<li><code>{html.escape(line)}</code></li>" for line in commits)
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<meta http-equiv='refresh' content='30'><title>Agent orchestra dashboard</title>"
            "<style>body{font:14px/1.5 system-ui;margin:2rem;background:#111827;color:#e5e7eb}"
            "table{border-collapse:collapse;width:100%}td,th{padding:.55rem;border-bottom:1px solid #475569;text-align:left;vertical-align:top}"
            "td:last-child{max-width:40rem;overflow-wrap:anywhere}section{display:inline-block;vertical-align:top;width:min(48%,45rem)}"
            "li{margin:.3rem 0;overflow-wrap:anywhere}@media(max-width:700px){section{width:100%}}</style></head><body>"
            f"<h1>Agent orchestra</h1><p>{len(rows)} jobs, refreshed every 30 seconds</p>"
            "<table><thead><tr><th>Kind</th><th>Task</th><th>Status</th><th>Updated</th><th>Last note</th></tr></thead><tbody>"
            + "".join(cells) + "</tbody></table>"
            f"<section><h2>Board</h2><ul>{recent}</ul></section><section><h2>Recent commits</h2><ul>{history}</ul></section>"
            "</body></html>")


def generate(repo, outdir, board, destination, config):
    page = render_page(collect_rows(outdir, config), board_tail(board), git_log(repo))
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_name(destination.name + ".tmp")
    temp.write_text(page)
    temp.replace(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="generate once and exit")
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--config", type=Path, default=Path(os.environ["ORCH_CONFIG"]) if os.environ.get("ORCH_CONFIG") else None)
    args = parser.parse_args()
    if args.interval < 1:
        parser.error("--interval must be positive")
    repo = Path(os.environ.get("ORCH_REPO", Path.cwd())).resolve()
    outdir = Path(os.environ.get("ORCH_OUTPUT_DIR", repo / "notes/jobs")).resolve()
    board = Path(os.environ.get("ORCH_BOARD", repo / "notes/board.md")).resolve()
    destdir = Path(os.environ.get("ORCH_DASHBOARD_DIR", repo / "notes/dashboard")).resolve()
    config = json.loads(args.config.read_text()) if args.config else {}
    while True:
        try:
            generate(repo, outdir, board, destdir / "index.html", config)
        except Exception as exc:
            if args.once:
                raise
            print(f"dashboard generation failed: {exc}", flush=True)
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
